'use client'
import React from "react";
import EditorComponent from "@/app/project/[id]/EditorComponent";
import {EditorContext} from "@/app/Contexts/EditorContext";


interface MoviePreviewProps {
    debug?: boolean
}


export default function MoviePreview(props: MoviePreviewProps) {
    const [status, updateStatus] = React.useState({
        ice_gathering_state: "new",
        ice_connection_state: "new",
        signaling_state: "new"
    });

    const socket = React.useContext(EditorContext).socket;
    let videoObj = React.useRef<HTMLVideoElement>(null);
    let audioObj = React.useRef<HTMLAudioElement>(null);

    const RTC_CONFIG = {
        iceServers: [
            {
                urls: "stun:stun.l.google.com:19302"
            },
            // {
            //     urls: "stun:stun.relay.metered.ca:80"
            // },
            {
                urls: "turn:a.relay.metered.ca:80?transport=tcp",
                username: "1a5f80da82906d67074d0b1b",
                credential: "BbANpvUHocXnj0Cg",
            },
            {
                urls: "turn:a.relay.metered.ca:443",
                username: "1a5f80da82906d67074d0b1b",
                credential: "BbANpvUHocXnj0Cg",
            },
            {
                urls: "turn:a.relay.metered.ca:443?transport=tcp",
                username: "1a5f80da82906d67074d0b1b",
                credential: "BbANpvUHocXnj0Cg"
            }
        ]
    };

    // let rtc_connection = React.useRef<RTCPeerConnection>(new RTCPeerConnection({
    //     // iceServers: [
    //     //     {
    //     //         urls: "stun:stun.l.google.com:19302"
    //     //     }
    //     // ]
    // })).current;

    const ice_candidates: RTCIceCandidate[] = [];

    React.useEffect(() => {
        setupConnection();
    })

    const newPlay = () => {
        // Create offer
        const rtc_connection = setupConnection()!;
        rtc_connection.createOffer().then(offer => {
            // offer created, set local description
            return rtc_connection.setLocalDescription(offer);
        }).then(() => {
            // wait for ICE gathering to complete
            console.log("Waiting for ICE gathering to complete");
            return new Promise((resolve: Function) : void => {
                if (rtc_connection.iceGatheringState === "complete") {
                    resolve();
                } else {
                    const checkState = () => {
                        if (rtc_connection.iceGatheringState === "complete") {
                            rtc_connection.removeEventListener("icegatheringstatechange", checkState);
                            resolve();
                        }
                    }
                    rtc_connection.addEventListener("icegatheringstatechange", checkState);
                }
            });
        }).then(() => {
            console.log("ICE Gathering Complete");
            return new Promise((resolve: Function) => {
                let offer = rtc_connection.localDescription!;
                // return fetch("http://localhost:8080/offer", {
                //     body: JSON.stringify({
                //         sdp: offer.sdp,
                //         type: offer.type,
                //         video_transform: "none"
                //     }),
                //     headers: {
                //         "Content-Type": "application/json"
                //     },
                //     method: "POST"
                // }).then(resp => {
                //     return resp.json();
                // }).then(answer => {
                //     return rtc_connection.setRemoteDescription(answer);
                // }).catch(error => {
                //     alert(error);
                // });

                // send offer to server
                socket.emit("offer", {
                    sdp: offer.sdp,
                    type: offer.type
                }, (response: any) => {
                    console.log(response);
                    return rtc_connection.setRemoteDescription({
                        sdp: response.sdp,
                        type: response.type
                    });
                });
            })

        }).catch(error => {
            alert(error);
        });
    };

    function setupConnection() {
        try {
            // rtc_connection = new RTCPeerConnection(RTC_CONFIG);
            const rtc_connection = new RTCPeerConnection();
            rtc_connection.addTransceiver("video", {direction: "recvonly"});
            rtc_connection.addTransceiver("audio", {direction: "recvonly"});

            // Connect audio / video
            rtc_connection.addEventListener("track", e => {
                console.log("Track: ", e);
                if (e.track.kind == 'video') {
                    videoObj.current!.srcObject = e.streams[0];
                } else if (e.track.kind == "audio") {
                    audioObj.current!.srcObject = e.streams[0];
                }
                // console.log("Stream received: ", e.streams[0]);
                // console.log("VideoObject: ", videoObj);
                // if (videoObj.current.srcObject !== e.streams[0]) {
                //     // replace video if new video stream is available
                //     videoObj.current.srcObject = e.streams[0];
                // }
            });

            if (props.debug) {
                rtc_connection.addEventListener("icegatheringstatechange", () => {
                    updateStatus({
                        ...status,
                        ice_gathering_state: status.ice_gathering_state + " => " + rtc_connection.iceGatheringState
                    });
                });
                rtc_connection.addEventListener("iceconnectionstatechange", () => {
                    updateStatus({
                        ...status,
                        ice_connection_state: status.ice_connection_state + " => " + rtc_connection.iceConnectionState
                    });
                });
                rtc_connection.addEventListener("signalingstatechange", () => {
                    updateStatus({
                        ...status,
                        signaling_state: status.signaling_state + " => " + rtc_connection.signalingState
                    });
                });
            }
            return rtc_connection;
        } catch (error) {
            console.log("[setupConnection] Error : ", error);
        }
        // rtc_connection.addEventListener("icecandidate", e => {
        //     if (e.candidate) {
        //         if (ice_candidates.includes(e.candidate)) {
        //             return;
        //         }
        //         ice_candidates.push(e.candidate);
        //         console.log("Ice Candidate: ", e.candidate);
        //         try {
        //             socket.emit("editor/play/newICECandidate", {
        //                 type: "new-ice-candidate",
        //                 value: {
        //                     address: e.candidate.address,
        //                     candidate: e.candidate.candidate,
        //                     component: e.candidate.component,
        //                     foundation: e.candidate.foundation,
        //                     port: e.candidate.port,
        //                     priority: e.candidate.priority,
        //                     protocol: e.candidate.protocol,
        //                     type: e.candidate.type,
        //                     sdpMid: e.candidate.sdpMid
        //                 }
        //             });
        //         } catch (e) {
        //             console.error("iceCandidate Add Error: ", e);
        //         }
        //
        //     }
        // });
    }

    function showSDPStatus() {
    //     console.log("RTC Connection: ", rtc_connection);
    //     console.log("Local Description: ", rtc_connection.localDescription);
    //     console.log("Remote Description: ", rtc_connection.remoteDescription);
    //     alert(rtc_connection.connectionState);
    }
    return (
        <EditorComponent>
            <video id={"video!"} controls={true} ref={videoObj} playsInline={true} autoPlay={true}></video>
            <audio autoPlay={true} ref={audioObj}></audio>
            <button onClick={newPlay}>
                Play
            </button>


            { props.debug ?
                <div style={{color: "black"}}>
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