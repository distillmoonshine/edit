import Movie from "@/app/Data/Movie";
import React, {useContext} from "react";
import Layer from "@/app/Data/Layers/Layer";
import {AppContext, AppContextData} from "@/app/appContext";
import { useEffect } from "react";

interface LayerSelectorProps {
    movie: Movie,
    onMovieChange?: Function
}

export default function LayerSelector(props: LayerSelectorProps) {
    const [, forceUpdate] = React.useReducer(() => ({}), {});
    function addLayer() {
        console.log("Layer added");
        if (props.movie.addLayer(new Layer())) {
            console.log(props.movie.layers);
            forceUpdate();
            if (props.onMovieChange != undefined) props.onMovieChange(props.movie);
        } else {
            alert("Failed to add layer.");
        }

    }

    let layerDisplay = props.movie.layers.map((layer: Layer) => {
        return <li key={layer.id}>{layer.name}</li>
    });
    return (
        <div>
            Layers
            <button onClick={addLayer}>Add</button>
            {layerDisplay}
        </div>
    )

}