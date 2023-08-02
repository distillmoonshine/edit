import asyncio
import threading
import logging
import errno
import av
from av import AudioFrame, VideoFrame
import fractions
import time
from aiortc.mediastreams import VIDEO_PTIME, VIDEO_CLOCK_RATE, VIDEO_TIME_BASE, MediaStreamTrack
from aiortc.contrib.media import MediaStreamError, AUDIO_PTIME, REAL_TIME_FORMATS
import uuid
from av.frame import Frame
from av.packet import Packet
from abc import ABCMeta, abstractmethod
from typing import Optional, Set, Union, Tuple
from pyee.asyncio import AsyncIOEventEmitter
from collections import deque


# class MediaStreamTrack(AsyncIOEventEmitter, metaclass=ABCMeta):
#     """
#     A single media track within a stream.
#     """
#
#     kind = "unknown"
#
#     def __init__(self) -> None:
#         super().__init__()
#         self.__ended = False
#         self._id = str(uuid.uuid4())
#
#     @property
#     def id(self) -> str:
#         """
#         An automatically generated globally unique ID.
#         """
#         return self._id
#
#     @property
#     def readyState(self) -> str:
#         return "ended" if self.__ended else "live"
#
#     @abstractmethod
#     async def recv(self) -> Union[Frame, Packet]:
#         """
#         Receive the next :class:`~av.audio.frame.AudioFrame`, :class:`~av.video.frame.VideoFrame`
#         or :class:`~av.packet.Packet`
#         """
#
#     def stop(self) -> None:
#         if not self.__ended:
#             self.__ended = True
#             self.emit("ended")
#
#             # no more events will be emitted, so remove all event listeners
#             # to facilitate garbage collection.
#             self.remove_all_listeners()


class VideoStreamTrack(MediaStreamTrack):
    """
    A dummy video track which reads green frames.
    """

    kind = "video"

    _start: float
    _timestamp: int

    async def next_timestamp(self) -> Tuple[int, fractions.Fraction]:
        if self.readyState != "live":
            raise MediaStreamError

        if hasattr(self, "_timestamp"):
            self._timestamp += int(VIDEO_PTIME * VIDEO_CLOCK_RATE)
            wait = self._start + (self._timestamp / VIDEO_CLOCK_RATE) - time.time()
            await asyncio.sleep(wait)
        else:
            self._start = time.time()
            self._timestamp = 0
        return self._timestamp, VIDEO_TIME_BASE

    async def recv(self) -> Frame:
        """
        Receive the next :class:`~av.video.frame.VideoFrame`.

        The base implementation just reads a 640x480 green frame at 30fps,
        subclass :class:`VideoStreamTrack` to provide a useful implementation.
        """
        pts, time_base = await self.next_timestamp()

        frame = VideoFrame(width=640, height=480)
        for p in frame.planes:
            p.update(bytes(p.buffer_size))
        frame.pts = pts
        frame.time_base = time_base
        return frame

logger = logging.getLogger(__name__)

def player_worker_decode(
    loop,
    container,
    audio_track,
    video_track,
    quit_event,
    throttle_playback,
    loop_playback = False,
):
    audio_sample_rate = 48000
    audio_samples = 0
    audio_time_base = fractions.Fraction(1, audio_sample_rate)
    audio_resampler = av.AudioResampler(
        format="s16",
        layout="stereo",
        rate=audio_sample_rate,
        frame_size=int(audio_sample_rate * AUDIO_PTIME),
    )

    video_first_pts = None

    frame_time = None
    start_time = time.time()

    while not quit_event.is_set():
        try:
            frame = next(container.decode(*container.streams))
        except Exception as exc:
            print("exception: ", type(exc))
            if isinstance(exc, av.FFmpegError) and exc.errno == errno.EAGAIN:
                time.sleep(0.01)
                continue
            if isinstance(exc, StopIteration) and loop_playback:
                container.seek(0)
                continue
            if audio_track:
                asyncio.run_coroutine_threadsafe(audio_track.put(None), loop)
            if video_track:
                asyncio.run_coroutine_threadsafe(video_track.put(None), loop)
            break

        # read up to 1 second ahead
        if throttle_playback:
            elapsed_time = time.time() - start_time
            if frame_time and frame_time > elapsed_time + 1:
                time.sleep(0.1)

        if isinstance(frame, AudioFrame) and audio_track:
            for frame in audio_resampler.resample(frame):
                # fix timestamps
                frame.pts = audio_samples
                frame.time_base = audio_time_base
                audio_samples += frame.samples

                frame_time = frame.time
                asyncio.run_coroutine_threadsafe(audio_track.put(frame), loop)
        elif isinstance(frame, VideoFrame) and video_track:
            if frame.pts is None:  # pragma: no cover
                logger.warning(
                    "MediaPlayer(%s) Skipping video frame with no pts", container.name
                )
                continue

            # video from a webcam doesn't start at pts 0, cancel out offset
            if video_first_pts is None:
                video_first_pts = frame.pts
            frame.pts -= video_first_pts

            frame_time = frame.time
            asyncio.run_coroutine_threadsafe(video_track.put(frame), loop)
    print("thread task closing")


class StreamDecoder:
    def __init__(self, file, audio_queue, video_queue):
        self.container = av.open(file=file, format=None, mode="r")
        self.thread_quit_event = threading.Event()

        container_format = set(self.container.format.name.split(","))
        self._throttle_playback = not container_format.intersection(REAL_TIME_FORMATS)
        self.thread = threading.Thread(
            name="player",
            target=player_worker_decode,
            args=(
                asyncio.get_event_loop(),
                self.container,
                audio_queue,
                video_queue,
                self.thread_quit_event,
                self._throttle_playback
            )
        )
        print(f"{threading.get_ident()} StreamDecoder for file {file} is created")

    def start_decoder(self):
        self.thread.start()


class PlaylistStreamTrack(MediaStreamTrack):
    def __init__(self, player, kind):
        super().__init__()
        self.kind = kind
        self._player = player
        self._queue = deque()
        self._start = None

    def create_new_stream(self):
        queue = asyncio.Queue()
        self._queue.append(queue)
        return queue

    async def _dequeue(self):
        print("[PlaylistStreamTrack._dequeue]", self._queue)
        if len(self._queue) > 0:
            print("Queue length > 0")
            if not self._queue[0].empty():
                print("frame available")
                return await self._queue[0].get()
            else:
                print("Queue complete, loading next...")
                self._queue.popleft()
                return await self._dequeue()
        else:
            print("Returning none")
            return None

    async def recv(self) -> Union[Frame, Packet]:
        if self.readyState != "live":
            print("Ready state not live")
            raise MediaStreamError

        self._player._start(self)
        data = await self._dequeue()
        # data = await self._queue[0].get()
        print("Obtained data: ", data)

        if data is None:
            print("Data is None")
            self.stop()
            raise MediaStreamError
        if isinstance(data, Frame):
            data_time = data.time
        elif isinstance(data, Packet):
            data_time = float(data.pts * data.time_base)

        # control playback rate
        if (
            self._player is not None
            and self._player._throttle_playback
            and data_time is not None
        ):
            if self._start is None:
                self._start = time.time() - data_time
            else:
                wait = self._start + data_time - time.time()
                await asyncio.sleep(wait)
        print("Returning ", data)
        return data

    def stop(self):
        super().stop()
        if self._player is not None:
            self._player._stop(self)
            self._player = None

    def popleft(self):
        pass


class MediaPlaylist:
    def __init__(self):
        self.__decoders = deque()
        self.__audio = PlaylistStreamTrack(self, kind="audio")
        self.__video = PlaylistStreamTrack(self, kind="video")
        self.__streams = []
        self.__started: Set[PlaylistStreamTrack] = set()
        self.__playlist_queue = deque()
        self._throttle_playback = False     # True if livestream
        self._has_started = False

        self.__streams.append(self.__audio)
        self.__streams.append(self.__video)

        # self.add_file("videos/marcrober.mp4")
        # self.load_next_media()

    @property
    def audio(self) -> MediaStreamTrack:
        return self.__audio

    @property
    def video(self) -> MediaStreamTrack:
        return self.__video

    def add_file(self, file):
        print("[MediaPlaylist.add_file], file: ", file)
        self.__playlist_queue.append(file)
        if not self._has_started:
            self._has_started = True
            self.load_next_media()

    def _start(self, track: PlaylistStreamTrack) -> None:
        self.__started.add(track)
        if len(self.__decoders) > 0 and self.__decoders[0].thread_quit_event.is_set():
            self.__decoders.popleft()
            self.load_next_media()

    def load_next_media(self):
        if len(self.__playlist_queue) == 0:
            assert "No more files in playlist"

        file = self.__playlist_queue.popleft()
        audio_queue = self.__audio.create_new_stream()
        video_queue = self.__video.create_new_stream()
        decoder = StreamDecoder(file, audio_queue, video_queue)
        self.__decoders.append(decoder)
        decoder.start_decoder()

    def _stop(self, track: PlaylistStreamTrack) -> None:
        self.__started.discard(track)
        # find the code stop call was placed
        import traceback
        print(traceback.format_stack())
        print("Stop")

    def __log_debug(self, msg: str, *args) -> None:
        print(f"MediaPlayer {msg}", *args)