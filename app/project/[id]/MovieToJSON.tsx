'use client'
import React from "react";
import Movie from "@/app/Data/Movie";
import EditorComponent from "@/app/project/[id]/EditorComponent";
import {MovieContext} from "@/app/Contexts/MovieContext";
export default function MovieToJSON(props : any) {
    let currentMovie = React.useContext(MovieContext);
    return (
        <EditorComponent>
            <h6>Movie to JSON</h6>
            { JSON.stringify(currentMovie) }
        </EditorComponent>
    )
}