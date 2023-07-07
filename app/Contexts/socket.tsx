'use client'
import React from "react";
import { Socket, io } from 'socket.io-client';
export const SocketIOURL = "http://127.0.0.1:5000";


/* Create Socket context instance with default io() method
 * autoConnect: false  => Prevents error message trying to connect to server
 */
export const EditorSocketContext = React.createContext<Socket>(io({
    autoConnect: false
}));


/* Component that stores the Socket.IO instance
 * Embed components that use the context inside EditorSocketStore
 *
 * e.g.
 * <EditorSocketStore>
 *     <EditorComponent/>
 * </EditorSocketStore>
 */
export const EditorSocketStore = (props: any) => {
    let socketRef = React.useRef(io(SocketIOURL,
        {
            path: '/socket',
            // TODO: Set rejectUnauthorized to true to make the connection secure
            rejectUnauthorized: false,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: 3,
            transports: ['websocket']
        }));
    return <EditorSocketContext.Provider value={socketRef.current}>{props.children}</EditorSocketContext.Provider>
}