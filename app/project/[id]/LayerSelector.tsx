import Movie from "@/app/Data/Movie";
import React, {useContext} from "react";
import Layer from "@/app/Data/Layers/Layer";
import { useEffect } from "react";
import EditorComponent from "@/app/project/[id]/EditorComponent";
import {MovieContext} from "@/app/Contexts/MovieContext";

export default function LayerSelector(props: {
    onMovieChange?: Function
}) {
    const [, forceUpdate] = React.useReducer(() => ({}), {});
    const movie = React.useContext(MovieContext);
    function addLayer() {
        console.log("Layer added");
        if (movie.addLayer(new Layer())) {
            if (props.onMovieChange != undefined) props.onMovieChange(movie);
            forceUpdate();
        } else {
            alert("Failed to add layer.");
        }

    }

    let layerList = movie.layers.map((layer: Layer) => {
        return <li key={layer.id}>{layer.name}</li>
    });

    return (
        <EditorComponent>
            Layers
            <button onClick={addLayer}>Add</button>
            {layerList}
        </EditorComponent>
    )

}