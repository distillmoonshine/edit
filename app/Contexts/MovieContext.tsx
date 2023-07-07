import React from "react";
import Movie from "@/app/Data/Movie";
import {EditorSocketContext} from "@/app/Contexts/socket";

export const MovieContext = React.createContext(new Movie());

export default function MovieContextStore(props: any) {
    const socket = React.useContext(EditorSocketContext);

    // Once initialized, fetch movie from Socket.IO server
    React.useEffect(() => {
        if (!socket.connected) socket.connect();

    })

    return (
        <MovieContext.Provider value={new Movie()}>
            { props.children }
        </MovieContext.Provider>
    )
}