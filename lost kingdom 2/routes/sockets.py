from flask_socketio import emit, join_room, leave_room
from flask import request

# In-memory tracking of active multiplayer rooms and participants
CONNECTED_PLAYERS = {}  # socket_id -> {player_id, username, location, x, y, score}
ACTIVE_ROOMS = {}       # room_name -> {players: [], active_challenge: None}

def register_socket_handlers(socketio, orchestrator):
    @socketio.on("connect")
    def handle_connect():
        sid = request.sid
        CONNECTED_PLAYERS[sid] = {
            "player_id": f"guest_{sid[:6]}",
            "username": "Traveler",
            "location": "village",
            "x": 300,
            "y": 300,
            "score": 0
        }
        emit("connection_ack", {"sid": sid, "status": "connected"})

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        if sid in CONNECTED_PLAYERS:
            p = CONNECTED_PLAYERS.pop(sid)
            for room_name, rdata in ACTIVE_ROOMS.items():
                if sid in rdata["players"]:
                    rdata["players"].remove(sid)
                    emit("room_player_left", {"sid": sid, "username": p["username"]}, to=room_name)
            emit("player_left_world", {"sid": sid}, broadcast=True)

    @socketio.on("join_world")
    def handle_join_world(data):
        sid = request.sid
        p_id = data.get("player_id")
        username = data.get("username", "Seeker")
        location = data.get("location", "village")
        x = data.get("x", 320)
        y = data.get("y", 280)

        CONNECTED_PLAYERS[sid] = {
            "player_id": p_id,
            "username": username,
            "location": location,
            "x": x,
            "y": y,
            "score": 0
        }

        # Broadcast presence to other players
        emit("player_joined_world", CONNECTED_PLAYERS[sid], broadcast=True, include_self=False)
        # Send current online list to the newly connected player
        other_players = [info for s, info in CONNECTED_PLAYERS.items() if s != sid]
        emit("current_world_players", {"players": other_players})

    @socketio.on("player_move")
    def handle_player_move(data):
        sid = request.sid
        if sid in CONNECTED_PLAYERS:
            CONNECTED_PLAYERS[sid]["x"] = data.get("x", 300)
            CONNECTED_PLAYERS[sid]["y"] = data.get("y", 300)
            CONNECTED_PLAYERS[sid]["location"] = data.get("location", "village")
            emit("other_player_moved", {
                "sid": sid,
                "player_id": CONNECTED_PLAYERS[sid]["player_id"],
                "username": CONNECTED_PLAYERS[sid]["username"],
                "location": CONNECTED_PLAYERS[sid]["location"],
                "x": CONNECTED_PLAYERS[sid]["x"],
                "y": CONNECTED_PLAYERS[sid]["y"]
            }, broadcast=True, include_self=False)

    @socketio.on("join_room")
    def handle_join_room(data):
        sid = request.sid
        room_name = data.get("room_name", "Grand-Sanctum")
        join_room(room_name)
        if room_name not in ACTIVE_ROOMS:
            ACTIVE_ROOMS[room_name] = {"players": [], "active_challenge": None}
        if sid not in ACTIVE_ROOMS[room_name]["players"]:
            ACTIVE_ROOMS[room_name]["players"].append(sid)

        p_info = CONNECTED_PLAYERS.get(sid, {})
        emit("room_player_joined", {
            "sid": sid,
            "username": p_info.get("username", "Player"),
            "room_players": [CONNECTED_PLAYERS.get(s, {}).get("username", "Player") for s in ACTIVE_ROOMS[room_name]["players"]]
        }, to=room_name)

    @socketio.on("trigger_shared_challenge")
    def handle_trigger_shared_challenge(data):
        room_name = data.get("room_name", "Grand-Sanctum")
        topic = data.get("topic", "Algebra")
        difficulty = data.get("difficulty", "medium")

        # Generate challenge using orchestrator challenge agent
        challenge = orchestrator.challenge_agent.generate_next_challenge(
            {"topic": topic, "difficulty": difficulty},
            orchestrator.shared_blackboard
        )
        if room_name in ACTIVE_ROOMS:
            ACTIVE_ROOMS[room_name]["active_challenge"] = challenge

        emit("shared_challenge_started", {
            "room_name": room_name,
            "challenge": challenge
        }, to=room_name)

    @socketio.on("submit_shared_answer")
    def handle_submit_shared_answer(data):
        sid = request.sid
        room_name = data.get("room_name", "Grand-Sanctum")
        player_answer = str(data.get("player_answer", "")).strip()
        correct_answer = str(data.get("correct_answer", "")).strip()
        time_ms = data.get("time_ms", 3000)
        p_info = CONNECTED_PLAYERS.get(sid, {})

        is_correct = (player_answer.lower() == correct_answer.lower())
        points = max(10, int(100 - (time_ms / 200))) if is_correct else 0
        p_info["score"] = p_info.get("score", 0) + points

        emit("shared_answer_result", {
            "username": p_info.get("username", "Player"),
            "is_correct": is_correct,
            "points": points,
            "total_score": p_info["score"]
        }, to=room_name)
