import asyncio
import threading
import logging
logger = logging.getLogger(__name__)
import errno
import traceback

import av
from av import AudioFrame, VideoFrame
import fractions
import time
from aiortc.mediastreams import VIDEO_PTIME, VIDEO_CLOCK_RATE, VIDEO_TIME_BASE, MediaStreamTrack
from aiortc.contrib.media import MediaStreamError, AUDIO_PTIME, REAL_TIME_FORMATS, PlayerStreamTrack
from av.frame import Frame
from av.packet import Packet
from typing import Optional, Set, Union, Tuple
from collections import deque



"""
playlist_decode: Decodes video files and enqueues the frames into audio/video tracks. Intended to run on separate thread.

playlist_decode(
    loop: asyncio.events,               # asyncio loop
    playlist_queue: deque,              # deque containing video files
    audio_track: PlaylistStreamTrack,   # audio track containing queue for decoded audio frames
    video_track: PlaylistStreamTrack,   # video track containing queue for decoded video frames
    thread_quit: threading.Event        # If thread_quit is "set" (thread_quit.set()) then decoding loop exits
)
"""
def playlist_decode(
    loop, playlist_queue, audio_track, video_track, thread_quit
):
    print("Playlist decode start", audio_track, video_track)
    audio_sample_rate = 48000
    audio_samples = 0
    audio_time_base = fractions.Fraction(1, audio_sample_rate)
    audio_resampler = av.AudioResampler(
        format="s16",
        layout="stereo",
        rate=audio_sample_rate,
        frame_size=int(audio_sample_rate * AUDIO_PTIME),
    )

    container = 0
    current_streams = []

    if len(playlist_queue) == 0:
        return None
    file = playlist_queue.popleft()
    current_streams = []
    audio_exists, video_exists = False, False
    container = av.open(file=file, format=None, mode="r", options={}, timeout=None)

    # set up CURRENT_STREAMS array to be used in container.decode(*streams) method
    for stream in container.streams:
        if stream.type == "audio" and not audio_exists:
            current_streams.append(stream)
            audio_exists = True  # limit to only one audio track
        elif stream.type == "video" and not video_exists:
            current_streams.append(stream)
            video_exists = True  # limit to only one video track

    while not thread_quit.is_set():
        try:
            frame = next(container.decode(*current_streams))
        except Exception as exc:
            print(traceback.format_exc())
            if isinstance(exc, StopIteration):
                # end of video file reached, move onto next video file if exists
                if len(playlist_queue) == 0:
                    print("End of playlist")
                    return None
                file = playlist_queue.popleft()
                print("STOPITERATION, loading next file: ", file)
                current_streams = []
                audio_exists, video_exists = False, False
                container = av.open(file=file, format=None, mode="r", options={}, timeout=None)

                # set up CURRENT_STREAMS array to be used in container.decode(*streams) method
                for stream in container.streams:
                    if stream.type == "audio" and not audio_exists:
                        current_streams.append(stream)
                        audio_exists = True  # limit to only one audio track
                    elif stream.type == "video" and not video_exists:
                        current_streams.append(stream)
                        video_exists = True  # limit to only one video track

                print(container, current_streams)

                time.sleep(0.05)
                continue
            if isinstance(exc, av.FFmpegError) and exc.errno == errno.EAGAIN:
                time.sleep(0.01)
                continue
            if audio_track:
                asyncio.run_coroutine_threadsafe(audio_track._queue.put(None), loop)
            if video_track:
                asyncio.run_coroutine_threadsafe(video_track._queue.put(None), loop)
            break
        if isinstance(frame, AudioFrame) and audio_track:
            for frame in audio_resampler.resample(frame):
                # fix timestamps
                frame.pts = audio_samples
                frame.time_base = audio_time_base
                audio_samples += frame.samples

                frame_time = frame.time
                asyncio.run_coroutine_threadsafe(audio_track._queue.put(frame), loop)
        elif isinstance(frame, VideoFrame) and video_track:
            if frame.pts is None:  # pragma: no cover
                logger.warning(
                    "MediaPlayer(%s) Skipping video frame with no pts", container.name
                )
                continue

            asyncio.run_coroutine_threadsafe(video_track._queue.put(frame), loop)

class MediaPlaylist:
    def __init__(self):
        # audio and video tracks for playlist, decoded frames to be enqueued here
        self.__audio: Optional[PlayerStreamTrack] = PlaylistStreamTrack(self, kind="audio")
        self.__video: Optional[PlayerStreamTrack] = PlaylistStreamTrack(self, kind="video")
        self.__thread: Optional[threading.Thread] = None
        self.__playlist_queue = deque()
        self.__started = set()
        self.__thread_quit: threading.Event = None
        self.__thread: threading.Thread = None
        self._throttle_playback = False

    def add_file(self, file):
        self.__playlist_queue.append(file)
        if len(self.__started) == 0:
            self._start(1)

    def _start(self, track: PlayerStreamTrack):
        self.__started.add(track)
        if self.__thread is None:
            self.__log_debug("Starting worker thread")
            print("Start work!")
            self.__thread_quit = threading.Event()
            self.__thread = threading.Thread(
                name="media-playlist-decoder",
                target=playlist_decode,
                args=(
                    asyncio.get_event_loop(),
                    self.__playlist_queue,
                    self.__audio,
                    self.__video,
                    self.__thread_quit
                )
            )
            self.__thread.start()
    def stop(self):
        self.__thread_quit.set()

    def _stop(self):
        print("_stop called")

    @property
    def audio(self) -> MediaStreamTrack:
        """
        A :class:`aiortc.MediaStreamTrack` instance if the file contains audio.
        """
        return self.__audio

    @property
    def video(self) -> MediaStreamTrack:
        """
        A :class:`aiortc.MediaStreamTrack` instance if the file contains video.
        """
        return self.__video

    def __log_debug(self, msg: str, *args) -> None:
        logger.debug(f"MediaPlayer(%s) {msg}", *args)



class PlaylistStreamTrack(MediaStreamTrack):
    def __init__(self, player, kind):
        super().__init__()
        self.kind = kind
        self._player = player
        self._queue = asyncio.Queue()
        self._start = None

    async def recv(self) -> Union[Frame, Packet]:
        if self.readyState != "live":
            raise MediaStreamError

        self._player._start(self)
        data = await self._queue.get()
        if data is None:
            pass
            self.stop()
            raise MediaStreamError
        if isinstance(data, Frame):
            data_time = data.time
        elif isinstance(data, Packet):
            data_time = float(data.pts * data.time_base)

        # control playback rate
        if (
            # self._player is not None
            # and self._player._throttle_playback
            # and data_time is not None
            True
        ):
            if self._start is None:
                self._start = time.time() - data_time
            else:
                wait = self._start + data_time - time.time()
                await asyncio.sleep(wait)

        return data

    def stop(self):
        print("PlaylistStreamTrack stop called")