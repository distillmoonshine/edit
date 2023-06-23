import etro from 'etro'
import Layer from "@/app/Data/Layers/Layer";
import { v4 as uuidv4 } from "uuid";

export default class Movie {
    public id : string;
    private _layers : Layer[];
    public name : string | undefined;
    get layers(): Layer[] {
        return this._layers;
    }
    constructor() {
        this.id = uuidv4();
        this._layers = [];
    }

    // Converts etro.Movie to Movie instance
    public static fromEtroMovie(etroMovie : etro.Movie): Movie {
        let movie = new Movie();
        for (const etroLayer of etroMovie.layers) {
            let layer = Layer.fromEtroLayer(etroLayer);
            movie._layers.push(layer);
        }
        return movie;
    }

    /* Adds the provided layer to the Movie. Returns true when successful. */
    public addLayer(layer : Layer): boolean {
        // Check if the layer being added already exists in the Movie
        for (let i = 0; i < this._layers.length; i++) {
            if (this._layers[i] === layer) {
                // Same layer already exists, exit
                return false;
            }
        }
        this._layers.push(layer);
        return true;
    }

    public removeLayer(indexOrLayer : number | Layer): Layer | undefined {
        if (indexOrLayer instanceof Layer) {
            // Layer received, find given layer and remove
            for (let i = 0; i < this._layers.length; i++) {
                if (this._layers[i] === indexOrLayer) {
                    return this._layers.splice(i, 1)[0];
                }
                // No matching layer found
                return undefined;
            }
        } else {
            // Layer index received, remove at given index
            if (indexOrLayer < this._layers.length) {
                return this._layers.splice(indexOrLayer, 1)[0];
            } else {
                return undefined;
            }
        }
    }

    public getLayerLength(): number {
        return this._layers.length;
    }
}