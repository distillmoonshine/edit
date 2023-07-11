'use client'
import React from "react";
import EditorComponent from "@/app/project/[id]/EditorComponent";
import {EditorContext} from "@/app/Contexts/EditorContext";

export default function Timeline(props: any) {
    const socket = React.useContext(EditorContext);
    React.useEffect(() => {

    });
    return (
        <EditorComponent>
            <>Timeline</>

        </EditorComponent>
    )
}