import React from "react";
import EditorComponent from "@/app/project/[id]/EditorComponent";
import {EditorSocketContext} from "@/app/Contexts/socket";
import {create} from "domain";


interface MoviePreviewProps {
    debug?: boolean
}
export default function MoviePreview(props: MoviePreviewProps) {
    const [status, updateStatus] = React.useState({
        ice_gathering_state: "new",
        ice_connection_state: "new",
        signaling_state: "new"
    });

    const socket = React.useContext(EditorSocketContext)
    let description: RTCSessionDescription;
    let videoObj = React.useRef(document.createElement("video"));
    let rtc_connection = React.useRef(new RTCPeerConnection({
        iceServers: [
            {
                urls: "stun:stun.l.google.com:19302"
            }
        ]
    })).current;

    const ice_candidates: RTCIceCandidate[] = [];

    React.useEffect(() => {
        setupConnection();
    })

    // Request playback
    const play = () => {
        socket.emit("editor/play/getDescription", {

        }, (response: any) => {
            // Set
            let description = new RTCSessionDescription({
                sdp: response.sdp,
                type: response.type
            });
            rtc_connection.setRemoteDescription(description).then(() => {
                rtc_connection.createAnswer().then((answer) => {
                    console.log("Answer generated: SDP: ", answer.sdp, ", TYPE: ", answer.type);
                    rtc_connection.setLocalDescription(answer).then(() => {
                        socket.emit("editor/play/setServerDescription", {
                            "sdp": answer.sdp,
                            "type": answer.type
                        });
                    })

                });
            });
        });


    };

    function setupConnection(): RTCPeerConnection {
        rtc_connection.addTransceiver("video", { direction: "recvonly" });
        rtc_connection.addEventListener("icecandidate", e => {
            if (e.candidate) {
                if (ice_candidates.includes(e.candidate)) {
                    return;
                }
                ice_candidates.push(e.candidate);
                console.log("Ice Candidate: ", e.candidate);
                try {
                    socket.emit("editor/play/newICECandidate", {
                        type: "new-ice-candidate",
                        value: {
                            address: e.candidate.address,
                            candidate: e.candidate.candidate,
                            component: e.candidate.component,
                            foundation: e.candidate.foundation,
                            port: e.candidate.port,
                            priority: e.candidate.priority,
                            protocol: e.candidate.protocol,
                            type: e.candidate.type,
                            sdpMid: e.candidate.sdpMid
                        }
                    });
                } catch (e) {
                    console.error("iceCandidate Add Error: ", e);
                }

            }
        });

        // Connect audio / video
        rtc_connection.addEventListener("track", e => {
            console.log("Stream received: ", e.streams[0]);
            console.log("VideoObject: ", videoObj);
            if (videoObj.current.srcObject !== e.streams[0]) {
                // replace video if new video stream is available
                videoObj.current.srcObject = e.streams[0];
            }
        });

        if (props.debug) {
            rtc_connection.addEventListener("icegatheringstatechange", () => {
                updateStatus({ ...status, ice_gathering_state: status.ice_gathering_state + " => " + rtc_connection.iceGatheringState });
            });
            rtc_connection.addEventListener("iceconnectionstatechange", () => {
                updateStatus({ ...status, ice_connection_state: status.ice_connection_state + " => " + rtc_connection.iceConnectionState });
            });
            rtc_connection.addEventListener("signalingstatechange", () => {
                updateStatus({ ...status, signaling_state: status.signaling_state + " => " + rtc_connection.signalingState });
            });
        }
        return rtc_connection;
    }

    function showSDPStatus() {
        console.log("RTC Connection: ", rtc_connection);
        console.log("Local Description: ", rtc_connection.localDescription);
        console.log("Remote Description: ", rtc_connection.remoteDescription);
    }
    return (
        <EditorComponent>
            <video id={"video!"} controls={true} ref={videoObj} playsInline={true} autoPlay={true}></video>
            <button onClick={play}>
                Play
            </button>


            { props.debug ?
                <div>
                    DEBUG<br/>
                    Gathering State: { status.ice_gathering_state }<br/>
                    Connection State: { status.ice_connection_state }<br/>
                    Signaling State: { status.signaling_state }<br/>
                    <button onClick={showSDPStatus}>SDP Status</button>
                </div>
                : <></> }
        </EditorComponent>
    )
}