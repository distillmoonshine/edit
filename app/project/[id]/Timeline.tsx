'use client'
import React from "react";
import EditorComponent from "@/app/project/[id]/EditorComponent";
import {EditorSocketContext} from "@/app/Contexts/socket";

export default function Timeline(props: any) {
    const socket = React.useContext(EditorSocketContext);
    React.useEffect(() => {

    });
    return (
        <EditorComponent>
            <>Timeline</>

        </EditorComponent>
    )
}