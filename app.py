# render for skip backend
from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "sync_secret_key_change_this"

# Allow your main SmartEdu domain (update this to your actual domain)
ALLOWED_ORIGINS = [
    "https://smartedu-dbqo.onrender.com",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://unacademy.store",
    "https://edu.farham.store"
]

CORS(app, origins=ALLOWED_ORIGINS)

socketio = SocketIO(
    app,
    cors_allowed_origins=ALLOWED_ORIGINS,
    async_mode="gevent",
    logger=False,
    engineio_logger=False
)


# ────────────────────────────────────────────
#  HTTP routes
# ────────────────────────────────────────────

@app.route("/")
def index():
    return {"status": "SmartEdu Sync Server running ✅"}, 200

@app.route("/health")
def health():
    return {"status": "ok"}, 200


# ────────────────────────────────────────────
#  Socket.IO events
# ────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    print(f"[+] Client connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    print(f"[-] Client disconnected: {request.sid}")

@socketio.on("join_room")
def on_join(data):
    """
    Client joins a room identified by class_id.
    data = { class_id: "abc-123" }
    """
    class_id = data.get("class_id")
    if not class_id:
        return
    join_room(class_id)
    print(f"[room] {request.sid} joined room: {class_id}")

@socketio.on("leave_room")
def on_leave(data):
    """
    Client leaves the room.
    data = { class_id: "abc-123" }
    """
    class_id = data.get("class_id")
    if not class_id:
        return
    leave_room(class_id)
    print(f"[room] {request.sid} left room: {class_id}")

@socketio.on("video_seek")
def on_seek(data):
    """
    Broadcast a seek to all OTHER viewers in the same room.
    data = { class_id: "abc-123", time: 42.5 }
    """
    class_id = data.get("class_id")
    time = data.get("time")

    if class_id is None or time is None:
        return

    print(f"[seek] room={class_id} time={time} from={request.sid}")

    # Relay to everyone else in the room (not the sender)
    emit(
        "sync_seek",
        {"time": time, "from": request.sid},
        to=class_id,
        include_self=False
    )

@socketio.on("video_play")
def on_play(data):
    """
    Broadcast play event to sync paused viewers.
    data = { class_id: "abc-123", time: 42.5 }
    """
    class_id = data.get("class_id")
    time = data.get("time")
    if not class_id:
        return
    emit("sync_play", {"time": time}, to=class_id, include_self=False)

@socketio.on("video_pause")
def on_pause(data):
    """
    Broadcast pause event so everyone pauses together.
    data = { class_id: "abc-123", time: 42.5 }
    """
    class_id = data.get("class_id")
    time = data.get("time")
    if not class_id:
        return
    emit("sync_pause", {"time": time}, to=class_id, include_self=False)


# ────────────────────────────────────────────
#  Run
# ────────────────────────────────────────────

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=False)
