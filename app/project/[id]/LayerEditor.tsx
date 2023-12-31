import React from "react";
import Layer from "@/app/Data/Layers/Layer";
import EditorComponent from "@/app/project/[id]/EditorComponent";

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

export default function LayerEditor(props: {
    layer: Layer,
    onLayerChange?: Function,
    hidden?: boolean
}) {
    const editorComponents = [];
    editorComponents.push(BaseLayerEditor(props.layer));
    return (
        <EditorComponent hidden={props.hidden}>
            Layer Editor
            <br/>
            {editorComponents}
        </EditorComponent>
    )
}