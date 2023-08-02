import asyncio

import aiortc.contrib.media
from aiohttp import web
import socketio
import json
import aiohttp_cors
from MediaPlaylist import MediaPlaylist
from MediaPlayer import MediaPlayer

from aiortc import RTCIceCandidate, RTCRtpSender, RTCIceGatherer, RTCIceServer, RTCConfiguration, RTCPeerConnection, RTCRtpTransceiver, RTCSessionDescription
# from aiortc.contrib.media import MediaPlayer, MediaBlackhole, MediaRelay
from aiortc.contrib.signaling import create_signaling

app = web.Application()
socket = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
socket.attach(app)

RTC_CONFIG = RTCConfiguration([
    RTCIceServer(urls="stun:stun.l.google.com:19302"),
    # RTCIceServer(urls="stun:stun.relay.metered.ca:80"),
    # RTCIceServer(urls="turn:a.relay.metered.ca:80?transport=tcp", username="1a5f80da82906d67074d0b1b",
    #              credential="BbANpvUHocXnj0Cg"),
    # RTCIceServer(urls="turn:a.relay.metered.ca:443", username="1a5f80da82906d67074d0b1b",
    #              credential="BbANpvUHocXnj0Cg"),
    # RTCIceServer(urls="turn:a.relay.metered.ca:443?transport=tcp", username="1a5f80da82906d67074d0b1b",
    #              credential="BbANpvUHocXnj0Cg")
])

rtc_peer_connections = {}


def home():
    return web.Response(content_type="text/html", text="Hello from Python")


@socket.on("connection")
async def socketio_connect(sid, data):
    print("Client with sid : " + sid + " is connected.")
    await socket.emit("connect", {
        "data": f"Response from the server, sid: {sid}"
    })


@socket.on("disconnect")
def socketio_disconnected(sid):
    print("Client with sid " + sid + " disconnected.")
    if sid in rtc_peer_connections:
        asyncio.get_event_loop().run_until_complete(rtc_peer_connections[sid].close())
        del rtc_peer_connections[sid]
    socket.emit("disconnect", f"user {sid} disconnected from server.")


@socket.on("editor/addLayer")
def editor_add_layer(sid, data):
    print("Client with sid " + sid + " added layer, params: ", data)

@socket.on("rtc/connect")
async def offer_socket(sid, data):
    return await connect(sid, data)
#
# @socket.on("offer")
# async def test(sid):
#     return

import logging

logger = logging.getLogger("pc")
pcs = {}


async def connect(sid, params):
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs[sid] = pc

    def log_info(msg, *args):
        logger.info(msg, *args)

    log_info("Created PC")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            if sid in pcs:
                del pcs[sid]

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    # @pc.on("track")
    # def on_track(track):
    #     print("Track %s received", track.kind)
    #
    #     if track.kind == "audio":
    #         pc.addTrack(track)
    #     elif track.kind == "video":
    #         pc.addTrack(track)
    #
    #     @track.on("ended")
    #     async def on_ended():
    #         log_info("Track %s ended", track.kind)

    # handle offer
    await pc.setRemoteDescription(offer)


    player = MediaPlaylist()
    player.add_file("videos/marcrober.mp4")
    player.add_file("videos/marcrober1.mp4")
    if player.video:
        pc.addTrack(player.video)
    if player.audio:
        pc.addTrack(player.audio)

    # player = MediaPlayer("videos/marcrober.mp4")
    # if player.video:
    #     pc.addTrack(player.video)
    # if player.audio:
    #     pc.addTrack(player.audio)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    print("WebRTC offer generated and returned to client")
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    # return web.Response(
    #     content_type="application/json",
    #     text=json.dumps(
    #         {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    #     ),
    # )
@socket.on("rtc/stream")
async def stream(sid):
    if sid in pcs:
        print(f"Connection ID: {sid} requested stream")
        # prepare local media
        pc = pcs[sid]
        if pc.connectionState == "connected":
            player = MediaPlayer("videos/marcrober1.mp4")
            # pc.addTrack(player.video)
            # pc.addTrack(player.audio)
            # return
            if player.video:
                pc.addTrack
                print("Video detected, attaching video...")
                # video_sender = pc.addTrack(player.video)
                for sender in pcs[sid].getSenders():
                    if sender.kind == "video":
                        sender.replaceTrack(player.video)
                        break
            if player.audio:
                print("Audio detected, attaching audio...")
                # audio_sender = pc.addTrack(player.audio)
                for sender in pcs[sid].getSenders():
                    if sender.kind == "audio":
                        sender.replaceTrack(player.audio)
                        break


def test(request):
    content = open("index.html", "r").read()
    return web.Response(content_type="text/html", text=content)


def servefile(request):
    content = open("client.js", "r").read()
    return web.Response(content_type="text/html", text=content)


async def offer_restapi(request):
    params = await request.json()
    print(params)
    resp = await connect(params)
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": resp["sdp"], "type": resp["type"]}
        ),
    )


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # set up cors
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )})

    cors.add(app.router.add_post("/offer", offer_restapi))
    app.router.add_get("/test", test)
    app.router.add_get("/client.js", servefile)

    for route in app.router.routes():
        print(route, route.handler)
        if not route.handler:
            cors.add(route)

    web.run_app(app)
