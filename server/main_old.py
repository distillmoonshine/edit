import asyncio
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin

import json

from aiortc import RTCIceCandidate, RTCRtpSender, RTCIceGatherer, RTCIceServer, RTCConfiguration, RTCPeerConnection, \
    RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaBlackhole
from aiortc.contrib.signaling import create_signaling

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret'
RTC_CONFIG = RTCConfiguration([
    RTCIceServer(urls="stun:stun.l.google.com:19302"),
    # RTCIceServer(urls="stun:stun.relay.metered.ca:80"),
    RTCIceServer(urls="turn:a.relay.metered.ca:80?transport=tcp", username="1a5f80da82906d67074d0b1b",
                 credential="BbANpvUHocXnj0Cg"),
    RTCIceServer(urls="turn:a.relay.metered.ca:443", username="1a5f80da82906d67074d0b1b",
                 credential="BbANpvUHocXnj0Cg"),
    RTCIceServer(urls="turn:a.relay.metered.ca:443?transport=tcp", username="1a5f80da82906d67074d0b1b",
                 credential="BbANpvUHocXnj0Cg")
])

# TODO: Secure CORS_ALLOWED_ORIGIN
socket = SocketIO(app, cors_allowed_origins="*", path="/socket")

rtc_peer_connections = {}


@app.route("/", methods=["GET"])
def home():
    return jsonify({"data": "Hello from Python Flask"})


@socket.on("connection")
def socketio_connect():
    print("Client with sid : " + request.sid + " is connected.")
    emit("connect", {
        "data": f"Response from the server, sid: {request.sid}"
    })


@socket.on("disconnect")
def socketio_disconnected():
    print("Client with sid " + request.sid + " disconnected.")
    if request.sid in rtc_peer_connections:
        asyncio.get_event_loop().run_until_complete(rtc_peer_connections[request.sid].close());
        del rtc_peer_connections[request.sid]
    emit("disconnect", f"user {request.sid} disconnected from server.")


@socket.on("editor/addLayer")
def editorAddLayer(params):
    print("Client with sid " + request.sid + " added layer, params: ", params)


async def create_rtc_connection():
    # connection = RTCPeerConnection()
    connection = RTCPeerConnection(RTC_CONFIG)
    connection.addTransceiver("video", direction="sendonly")
    connection.addTransceiver("audio", direction="sendonly")

    player = MediaPlayer("/Users/mjkwak/Developer/Moonshine/video-editor/server/videos/marcrober.mp4")
    # player = MediaPlayer('default:none', format='avfoundation', options={'video_size': '640x480'})
    connection.addTrack(player.video)
    connection.addTrack(player.audio)
    # SDP : Session Description Protocol detailing media configuration
    # TYPE:
    constraint = {
        "audio": True,
        "video": True
    }

    def onice(cand):
        print("CANDIDATE!!!! : ", cand)

    connection.on("icecandidate", onice)

    @connection.on("signalingstatechange")
    def signalingstatechange():
        print("connection signaling state changed: ", connection.signalingState)

    @connection.on("icegatheringstatechange")
    def icegatheringstatechange():
        print("connection ice gathering state changed: ", connection.iceGatheringState)
        if connection.iceGatheringState == "complete":
            pass
            # candidates = connection.sctp.transport.transport.iceGatherer.getLocalCandidates()
            # print("Candidates: ", candidates)

    @connection.on("iceconnectionstatechange")
    def iceconnectionstatechange():
        print("connection ice connection state changed: ", connection.iceConnectionState)

    @connection.on("track")
    def on_track(track):
        print("Track received: ", track)

    @connection.on("connectionstatechange")
    async def on_connection_state_change():
        print("Connection state changed: ", connection.connectionState)
        if connection.connectionState == "failed":
            print("Closing failed connection.")
            await connection.close()

    return connection


async def create_rtc_connection_offer(connection: RTCPeerConnection):
    offer = await connection.createAnswer()

    @connection.on("icecandidate")
    def on_icecandidate():
        print("GATHERING STATE CHANGE")

    await connection.setLocalDescription(offer)

    # wait until iceGatheringState is complete
    while True:
        if connection.iceGatheringState == "complete": break
    return offer


@socket.on("editor/play/offer_")
def editor_play_offer(params):
    print("Editor offer received. ", params)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(create_rtc_connection())
    loop.run_until_complete(connection.setRemoteDescription(offer))
    answer = loop.run_until_complete(create_rtc_connection_offer(connection))
    return {
        "sdp": answer.sdp,
        "type": answer.type
    }


@socket.on("editor/play/setServerDescription")
def editorPlaySetServerDescription(params):
    assert request.sid in rtc_peer_connections, "WebRTC Connection not established"
    desc = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(rtc_peer_connections[request.sid].setRemoteDescription(desc))


@socket.on("editor/play/newICECandidate")
def editor_play_new_ice_candidate(params):
    assert request.sid in rtc_peer_connections, "WebRTC Connection not established"
    if params["type"] == "new-ice-candidate":
        candidate = params["value"]
        # RTCPeerConnection().iceConnectionState
        candidateObj = RTCIceCandidate(component=candidate["component"], foundation=candidate["foundation"],
                                       ip=candidate["address"], port=candidate["port"], priority=candidate["priority"],
                                       protocol=candidate["protocol"], type=candidate["type"],
                                       sdpMid=candidate["sdpMid"])
        print("New Ice candidate, adding: ", candidateObj)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(rtc_peer_connections[request.sid].addIceCandidate(candidateObj))


@socket.on("editor/play/getDescription")
def editorPlayGetDescription(params):
    print("Client with sid " + request.sid + " requested description")
    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(create_rtc_connection())
    if request.sid in rtc_peer_connections:
        rtc_peer_connections[request.sid].close()
        del rtc_peer_connections[request.sid]
    rtc_peer_connections[request.sid] = connection
    offer = loop.run_until_complete(create_rtc_connection_offer(connection))
    print("ICE Servers: ", RTC_CONFIG.iceServers)
    ice_candid = RTCIceGatherer(RTC_CONFIG.iceServers).getLocalCandidates()
    print("CANDID: ", ice_candid)
    return {
        "sdp": offer.sdp,
        "type": offer.type
    }


def force_codec(pc, sender, forced_codec):
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )


async def offer_dup(params):
    print("DUP")
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()

    # prepare local media
    # player = MediaPlayer(os.path.join(ROOT, "demo-instruct.wav"))
    player = MediaPlayer("/Users/mjkwak/Developer/Moonshine/video-editor/server/videos/marcrober.mp4")

    recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):

        if track.kind == "audio":
            pc.addTrack(player.audio)
            recorder.addTrack(track)
        elif track.kind == "video":
            pc.addTrack(track)

        @track.on("ended")
        async def on_ended():
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

@socket.on("editor/play/offer")
def offer(params):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(offer2(params))


async def offer2(params):
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection(RTC_CONFIG)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # open media source
    player = MediaPlayer("videos/marcrober.mp4")
    # player = MediaPlayer('default:none', format='avfoundation', options={'video_size': '640x480'})
    audio = player.audio
    video = player.video

    if audio:
        audio_sender = pc.addTrack(audio)

    if video:
        video_sender = pc.addTrack(video)

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


@socket.on("offer_new")
def ll(params):
    return asyncio.get_event_loop().run_until_complete(offer_new(params))


async def offer_new(params):
    try:
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        connection = RTCPeerConnection()

        player = MediaPlayer("videos/marcrober.mp4")
        recorder = MediaBlackhole()
        # connection.addTransceiver("video", direction="sendonly")
        # connection.addTransceiver("audio", direction="sendonly")
        @connection.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is ", connection.connectionState)

        @connection.on("track")
        def on_track(track):
            print("Track received: ", track.kind)
            if track.kind == "audio":
                connection.addTrack(player.audio)
                recorder.addTrack(track)
            else:
                connection.addTrack(track)
            @track.on("ended")
            async def on_ended():
                print("Track ended!")


        await connection.setRemoteDescription(offer)
        await recorder.start()
        answer = await connection.createAnswer()
        await connection.setLocalDescription(answer)
        print({"sdp": connection.localDescription.sdp, "type": connection.localDescription.type})
        return {"sdp": connection.localDescription.sdp, "type": connection.localDescription.type}
    except Exception:
        import traceback
        print(traceback.format_exc())


@app.route("/offer", methods=["POST"])
@cross_origin()
def flask_offer():
    try:
        return asyncio.get_event_loop().run_until_complete(offer_dup(request.json))
    except Exception:
        import traceback
        print(traceback.format_exc())


@app.route("/test", methods=["GET"])
def test():
    content = open("index.html", "r").read()
    return content

@app.route("/client.js", methods=["GET"])
def servefile():
    content = open("client.js", "r").read()
    return content

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    socket.run(app, host="127.0.0.1", port=5000)
