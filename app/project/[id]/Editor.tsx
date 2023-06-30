'use client'
import React from "react";
import LayerSelector from "@/app/project/[id]/LayerSelector";
import Movie from "@/app/Data/Movie";
import LayerEditor from "@/app/project/[id]/LayerEditor";
import {SocketIOContext, SocketIOURL} from "@/app/api/socket";
import {io, Socket} from "socket.io-client";

let socket : Socket | undefined;

export default function Editor() {
    console.log("Editor loaded");
    const [, forceUpdate] = React.useReducer(x => x + 1, 0);
    let [currentMovie, setCurrentMovie] = React.useState(new Movie());
    let socketRef = React.useRef(io("http://127.0.0.1:5000",
        {
            path: '/socket',
            rejectUnauthorized: false,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            agent: false,
            upgrade:false,
            reconnectionAttempts: 1,
            transports: ['websocket']
        }));

    function update(newMovie: Movie) {
        currentMovie = newMovie;
        console.log("Movie update, movie.id : " + currentMovie.id);
        let socket = socketRef.current;
        socket.emit("editorAddLayer", "Content");
    }



    React.useEffect(() => {
        if (socket == undefined) {
            socket = socketRef.current;
        }
        console.log("Socket connection: " + socket.connected);

        socket.off("connect_error").on("connect_error", (err) => {
            console.warn("CONNECTION ERROR : ", err.message);
        });

        socket.off("connect").on("connect", () => {
            console.log("socket CONNECTED");
        });

        if (!socket.connected) {
            console.log("Connecting to Socket");
            socket.connect();
        }

    });




    return (
        <div>
            <span>Your movie has { currentMovie.layers.length } layers.</span>
            <LayerSelector onMovieChange={update} movie={currentMovie}/>
            { currentMovie.layers.length > 0 ?
                <LayerEditor layer={currentMovie.layers[0]}></LayerEditor> : <></> }

        </div>
    )
}