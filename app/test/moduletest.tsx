'use client'
import React from "react";
import {SocketIOContext} from "@/app/Contexts/socket";
export default function mod() {
    const socket = React.useContext(SocketIOContext);
    return (
        <div>
            Module
        </div>
    )
}