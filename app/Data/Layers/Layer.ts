import etro from "etro";
import { v4 as uuidv4 } from "uuid";
export default class Layer {
    public id: string;
    public startTime: number;
    public duration: number;
    public enabled: boolean;
    public name: string

    constructor(startTime: number = 0, duration: number = 0, enabled: boolean = true) {
        this.id = uuidv4();
        this.startTime = startTime;
        this.duration = duration;
        this.enabled = enabled;
        this.name = "Layer";
    }

    // Converts etro.layer.Base layer to Layer
    public static fromEtroLayer(etroLayer: etro.layer.Base) {
        return new Layer(
            etroLayer.startTime,
            etroLayer.duration,
            etroLayer.enabled
        );
    }
}