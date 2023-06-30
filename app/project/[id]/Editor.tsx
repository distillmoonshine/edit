'use client'
import React from "react";
import LayerSelector from "@/app/project/[id]/LayerSelector";
import Movie from "@/app/Data/Movie";
import LayerEditor from "@/app/project/[id]/LayerEditor";
import { EditorSocketContext } from "@/app/api/socket";
import {io, Socket} from "socket.io-client";


export default function Editor() {
    console.log("Editor loaded");
    const [, forceUpdate] = React.useReducer(x => x + 1, 0);
    let [currentMovie, setCurrentMovie] = React.useState(new Movie());
    const socket = React.useContext(EditorSocketContext);

    function update(newMovie: Movie) {
        currentMovie = newMovie;
        console.log("Movie update, movie.id : " + currentMovie.id);
        socket.emit("editorAddLayer", "Content");
    }



    React.useEffect(() => {
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