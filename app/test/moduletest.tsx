'use client'
import React from "react";
import {SocketIOContext} from "@/app/api/socket";
export default function mod() {
    const socket = React.useContext(SocketIOContext);
    return (
        <div>
            Module
        </div>
    )
}