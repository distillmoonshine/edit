import React, { createContext } from "react"
import Movie from "@/app/Data/Movie";
import App from "next/app";

export class AppContextData {
    currentMovie: Movie | undefined;
}

export const AppContext = React.createContext<AppContextData>(new AppContextData());
