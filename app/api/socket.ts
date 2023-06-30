'use client'
import React from "react";
import { Socket, io } from 'socket.io-client';
export const SocketIOURL = "http://localhost:5000";
export const SocketIOContext = React.createContext<{
    socket?: Socket
}>({});