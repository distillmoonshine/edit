import io from "socket.io-client"

const URL : string = 'http://127.0.0.1:5000'
export const socket = io(URL, {
    autoConnect: false,      // Prevents Socket.IO from connecting to server automatically, use 'socket.connect()' to connect
});