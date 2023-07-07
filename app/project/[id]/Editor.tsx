'use client'
import React from "react";
import LayerSelector from "@/app/project/[id]/LayerSelector";
import Movie from "@/app/Data/Movie";
import LayerEditor from "@/app/project/[id]/LayerEditor";
import { EditorSocketContext } from "@/app/Contexts/socket";
import {io, Socket} from "socket.io-client";
import Timeline from "@/app/project/[id]/Timeline";
import MovieToJSON from "@/app/project/[id]/MovieToJSON";
import {MovieContext} from "@/app/Contexts/MovieContext";
import MoviePreview from "@/app/project/[id]/MoviePreview";


export default function Editor() {
    const DEBUG = true;

    console.log("Editor loaded");
    const [, forceUpdate] = React.useReducer(x => x + 1, 0);
    let currentMovie = React.useContext(MovieContext);
    const socket = React.useContext(EditorSocketContext);

    function update(newMovie: Movie) {
        console.log("Movie update, movie.id : " + currentMovie.id);
        socket.emit("editor/addLayer", "Content");
    }



    React.useEffect(() => {
        // Set page name
        document.title = currentMovie.name === undefined ? "Movie Editor" : "Editor - " + currentMovie.name;

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
        <>
            <style>
                {
                    `button {
                        background-color: lightgray;
                        padding: 2px;
                        margin: 2px;
                    }`
                }
            </style>
            <span>Your movie has { currentMovie.layers.length } layers.</span>
            <MoviePreview debug={DEBUG}/>
            <LayerSelector onMovieChange={update}/>
            { currentMovie.layers.length > 0 ?
                <LayerEditor layer={currentMovie.layers[0]}></LayerEditor> : <></> }
            <Timeline/>
            <MovieToJSON movie={currentMovie}/>
        </>
    )
}