'use client'
import React from "react";
import Movie from "@/app/Data/Movie";
import LayerSelector from "@/app/project/[id]/LayerSelector";
import Layer from "@/app/Data/Layers/Layer";
import Editor from "@/app/project/[id]/Editor";
import '../../custom.css'
import '../../globals.css'

import {EditorSocketContext, EditorSocketStore, SocketIOURL} from "@/app/api/socket";
export default function Page() {
    return (
        <div style={{
            width:"100%",
            height: "100%"
        }}>
            <EditorSocketStore>
                <nav style={{
                    backgroundColor: "black",
                    color: "white"
                }}>Editor (Name)</nav>

                <Editor/>
            </EditorSocketStore>
        </div>
    )



}