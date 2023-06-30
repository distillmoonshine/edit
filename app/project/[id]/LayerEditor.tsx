import React from "react";
import Layer from "@/app/Data/Layers/Layer";

function IncompatibleEditorComponent() {
    return (
        <div>
            The selected layer does not support this editor module.<br/>
            Please select a different layer.
        </div>
    )
}

// function InputField()
function increment(layer: Layer, selector: Function) {

}

export function BaseLayerEditor(layer:Layer, onLayerChange: Function | undefined = undefined) {
    // Editor for base layer
    let editorComponents = [];
    let addStartTime = () => {
        layer.startTime += 1;
        if (onLayerChange != undefined) onLayerChange();
    }
    editorComponents.push(<div key={"addStartTime"} onClick={addStartTime}>Add Start Time</div>)
    return editorComponents
// private startTime: number;
// private duration: number;
// private enabled: boolean;
// protected name: string
}

interface LayerEditorProps {
    layer: Layer,
    onLayerChange?: Function
}

export default function LayerEditor(props: LayerEditorProps) {
    const editorComponents = [];
    editorComponents.push(BaseLayerEditor(props.layer));
    return (
        <div>
            Layer Editor
            <br/>
            {editorComponents}
        </div>
    )
}