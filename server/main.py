import asyncio
from aiohttp import web
import socketio
import json
import aiohttp_cors

from aiortc import RTCIceCandidate, RTCRtpSender, RTCIceGatherer, RTCIceServer, RTCConfiguration, RTCPeerConnection, \
    RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaBlackhole
from aiortc.contrib.signaling import create_signaling

app = web.Application()
socket = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
socket.attach(app)

# RTC_CONFIG = RTCConfiguration([
#     RTCIceServer(urls="stun:stun.l.google.com:19302"),
#     # RTCIceServer(urls="stun:stun.relay.metered.ca:80"),
#     RTCIceServer(urls="turn:a.relay.metered.ca:80?transport=tcp", username="1a5f80da82906d67074d0b1b",
#                  credential="BbANpvUHocXnj0Cg"),
#     RTCIceServer(urls="turn:a.relay.metered.ca:443", username="1a5f80da82906d67074d0b1b",
#                  credential="BbANpvUHocXnj0Cg"),
#     RTCIceServer(urls="turn:a.relay.metered.ca:443?transport=tcp", username="1a5f80da82906d67074d0b1b",
#                  credential="BbANpvUHocXnj0Cg")
# ])

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

@socket.on("offer")
async def offer_socket(sid, data):
    return await offer(data)
#
# @socket.on("offer")
# async def test(sid):
#     return

import logging

logger = logging.getLogger("pc")
pcs = set()


async def offer(params):
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(msg, *args)

    log_info("Created PC")

    # prepare local media
    player = MediaPlayer("/Users/mjkwak/Developer/Moonshine/video-editor/server/videos/marcrober.mp4")
    recorder = MediaBlackhole()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("track")
    def on_track(track):
        print("Track %s received", track.kind)

        if track.kind == "audio":
            pc.addTrack(player.audio)
            recorder.addTrack(track)
        elif track.kind == "video":
            pc.addTrack(track)

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    pc.addTrack(player.video)
    pc.addTrack(player.audio)

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


def test(request):
    content = open("index.html", "r").read()
    return web.Response(content_type="text/html", text=content)


def servefile(request):
    content = open("client.js", "r").read()
    return web.Response(content_type="text/html", text=content)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # set up cors
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )})

    # cors.add(app.router.add_post("/offer", offer))
    app.router.add_get("/test", test)
    app.router.add_get("/client.js", servefile)

    for route in app.router.routes():
        print(route, route.handler)
        if not route.handler:
            cors.add(route)

    web.run_app(app)
