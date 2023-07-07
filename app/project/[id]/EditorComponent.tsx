import React from "react";


export default function EditorComponent(props: { hidden?: boolean, children: any }) {
    return (
        <div style={{
            padding: "10px",
            backgroundColor: "white",
            display: props.hidden ? "none" : "block",
            border: "1px solid gray",
        }}>
            { props.children }
        </div>
    )
}