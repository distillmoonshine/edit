import React from "react";
import LayerSelector from "@/app/project/[id]/LayerSelector";
import Movie from "@/app/Data/Movie";
import LayerEditor from "@/app/project/[id]/LayerEditor";

export default function Editor() {
    const [, forceUpdate] = React.useReducer(x => x + 1, 0);
    let [currentMovie, setCurrentMovie] = React.useState(new Movie());

    function update(newMovie: Movie) {
        currentMovie = newMovie;
        console.log("Movie update, movie.id : " + currentMovie.id);
        forceUpdate();
    }

    return (
        <div>
            <span>Your movie has { currentMovie.layers.length } layers.</span>
            <LayerSelector onMovieChange={update} movie={currentMovie}/>
            { currentMovie.layers.length > 0 ?
                <LayerEditor layer={currentMovie.layers[0]}></LayerEditor> : <></> }

        </div>
    )
}