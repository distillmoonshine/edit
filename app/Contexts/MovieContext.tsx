import React from "react";
import Movie from "@/app/Data/Movie";
import {EditorContext} from "@/app/Contexts/EditorContext";

export const MovieContext = React.createContext(new Movie());

export default function MovieContextStore(props: any) {
    const socket = React.useContext(EditorContext).socket;

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