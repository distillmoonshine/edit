import asyncio
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

import json

from aiortc import RTCIceCandidate, RTCIceGatherer, RTCIceServer, RTCConfiguration, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
from aiortc.contrib.signaling import create_signaling

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret'
RTC_CONFIG = RTCConfiguration([
    RTCIceServer(urls="stun:stun.l.google.com:19302")
])

# TODO: Secure CORS_ALLOWED_ORIGIN
socket = SocketIO(app, logger=True, cors_allowed_origins="*", path="/socket")

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
    player = MediaPlayer("/Users/mjkwak/Developer/Moonshine/video-editor/server/videos/marcrober.mp4")
    # player = MediaPlayer('default:none', format='avfoundation', options={'video_size': '640x480'})
    connection.addTrack(player.video)
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

    return connection


async def create_rtc_connection_offer(connection: RTCPeerConnection):
    offer = await connection.createOffer()

    @connection.on("icecandidate")
    def on_icecandidate():
        print("GATHERING STATE CHANGE")

    await connection.setLocalDescription(offer)

    # wait until iceGatheringState is complete
    while True:
        if connection.iceGatheringState == "complete": break
    return offer


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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    socket.run(app, host="127.0.0.1", port=5000)
