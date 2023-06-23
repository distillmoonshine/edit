import Layer from "@/app/Data/Layers/Layer";

export default class ImageLayer extends Layer {
    private image : string | undefined;     // base64 string containing the image
    constructor(image? : string) {
        super();
        this.image = image;
        this.name = "Image";
    }
}