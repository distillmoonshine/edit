import { Server } from "socket.io";

const socketIOHandler = (request:any, response:any) => {
    if (!request.socket.server.io) {
        // First use, set up server
        const io = new Server(response.socket.server);
        io.on("connection", socket => {
            socket.broadcast.emit("User connected.");
            socket.on("hello", message => {
                socket.emit("hello", "world");
            });
        });

        response.socket.server.io = io;
    } else {
        console.log("Socket.IO is already running.");
    }
    response.end();
}

export const config = {
    api : {
        bodyParser: false
    }
}

export default socketIOHandler