/**
 * Multiplayer and WebSocket Telemetry Manager
 * Handles player presence, shared challenges, and live agent telemetry broadcasting.
 */
class MultiplayerManager {
    constructor() {
        this.socket = null;
        this.activeRoom = "Grand-Sanctum";
        this.init();
    }

    init() {
        if (typeof io === "undefined") {
            console.warn("[Multiplayer] Socket.IO client library not loaded.");
            return;
        }

        this.socket = io({ transports: ["websocket", "polling"] });

        this.socket.on("connect", () => {
            const playerId = window.uiManager ? window.uiManager.playerId : "guest";
            const username = window.uiManager ? window.uiManager.username : "Seeker";
            this.socket.emit("join_world", {
                player_id: playerId,
                username: username,
                location: "village",
                x: 270,
                y: 250
            });
            this.updateMultiplayerStatus(true, "Connected to Realm Network");
        });

        this.socket.on("disconnect", () => {
            this.updateMultiplayerStatus(false, "Disconnected");
        });

        // World Presence
        this.socket.on("current_world_players", (data) => {
            if (window.gameEngine && data.players) {
                data.players.forEach(p => {
                    window.gameEngine.otherPlayers[p.player_id] = p;
                });
            }
        });

        this.socket.on("player_joined_world", (p) => {
            if (window.gameEngine) {
                window.gameEngine.otherPlayers[p.player_id] = p;
                if (window.uiManager) {
                    window.uiManager.showNotification(`Adventurer ${p.username} entered the realm.`);
                }
            }
        });

        this.socket.on("other_player_moved", (p) => {
            if (window.gameEngine) {
                window.gameEngine.otherPlayers[p.player_id] = p;
            }
        });

        this.socket.on("player_left_world", (data) => {
            if (window.gameEngine && data.sid) {
                delete window.gameEngine.otherPlayers[data.sid];
            }
        });

        // Agent Telemetry Live Stream
        this.socket.on("agent_event_stream", (entry) => {
            if (window.dashboardManager) {
                window.dashboardManager.appendLiveLog(entry);
            }
        });

        this.socket.on("agent_state_update", (snapshot) => {
            if (window.dashboardManager) {
                window.dashboardManager.renderDashboard(snapshot);
            }
            if (window.uiManager) {
                window.uiManager.updateHUD(snapshot);
            }
        });

        // Shared Room / Quiz
        this.socket.on("room_player_joined", (data) => {
            this.updateRoomRoster(data.room_players);
        });

        this.socket.on("shared_challenge_started", (data) => {
            window.soundEngine.playFanfare();
            if (window.uiManager) {
                window.uiManager.showNotification(`Shared challenge initiated in ${data.room_name}!`);
                window.uiManager.displayChallengeObject(data.challenge);
            }
        });

        this.socket.on("shared_answer_result", (data) => {
            const rosterEl = document.getElementById("mp-leaderboard");
            if (rosterEl) {
                const item = document.createElement("div");
                item.className = "mp-score-row";
                item.innerHTML = `<span>${data.username}</span> <span>${data.is_correct ? '✓' : '✗'} +${data.points} pts (Total: ${data.total_score})</span>`;
                rosterEl.prepend(item);
            }
        });

        this.initDOM();
    }

    initDOM() {
        document.getElementById("btn-toggle-multiplayer")?.addEventListener("click", () => {
            document.getElementById("multiplayer-drawer")?.classList.toggle("active");
        });
        document.getElementById("btn-close-multiplayer")?.addEventListener("click", () => {
            document.getElementById("multiplayer-drawer")?.classList.remove("active");
        });

        document.getElementById("btn-join-room")?.addEventListener("click", () => {
            const roomInput = document.getElementById("mp-room-input");
            const rName = roomInput ? roomInput.value.trim() : "Grand-Sanctum";
            this.activeRoom = rName || "Grand-Sanctum";
            if (this.socket) {
                this.socket.emit("join_room", { room_name: this.activeRoom });
                window.uiManager.showNotification(`Joined room: ${this.activeRoom}`);
            }
        });

        document.getElementById("btn-trigger-shared-challenge")?.addEventListener("click", () => {
            if (this.socket) {
                this.socket.emit("trigger_shared_challenge", {
                    room_name: this.activeRoom,
                    topic: "Algebra",
                    difficulty: "medium"
                });
            }
        });
    }

    broadcastMovement(x, y, location) {
        if (this.socket && this.socket.connected) {
            this.socket.emit("player_move", { x, y, location });
        }
    }

    updateMultiplayerStatus(connected, text) {
        const badge = document.getElementById("mp-status-pill");
        if (badge) {
            badge.textContent = text;
            badge.className = connected ? "status-tag success" : "status-tag error";
        }
    }

    updateRoomRoster(players) {
        const list = document.getElementById("mp-players-list");
        if (!list || !players) return;
        list.innerHTML = "";
        players.forEach(name => {
            const li = document.createElement("li");
            li.textContent = `👤 ${name}`;
            list.appendChild(li);
        });
    }
}

window.MultiplayerManager = MultiplayerManager;
