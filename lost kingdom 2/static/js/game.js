/**
 * Core 2D RPG Engine, Player Controller, and Canvas Loop
 */
class GameEngine {
    constructor() {
        this.canvas = document.getElementById("game-canvas");
        this.ctx = this.canvas.getContext("2d");
        this.world = new GameWorld();

        // Player Avatar
        this.player = {
            id: null,
            username: "Seeker",
            x: 270,
            y: 250,
            targetX: 270,
            targetY: 250,
            speed: 3.2,
            facing: "down", // up, down, left, right
            moving: false,
            stepTimer: 0,
            animFrame: 0,
            color: "#f59e0b"
        };

        this.keys = {};
        this.currentZoneId = "village";
        this.nearbyNPC = null;
        this.lastMoveReportTime = 0;
        this.otherPlayers = {}; // sid -> {username, x, y, location}

        this.initEvents();
    }

    init(playerId, username) {
        this.player.id = playerId;
        this.player.username = username || "Seeker";
        this.resize();
        window.addEventListener("resize", () => this.resize());
        requestAnimationFrame((t) => this.loop(t));
    }

    resize() {
        // Keep internal coordinate space 1100x700
        this.canvas.width = 1100;
        this.canvas.height = 700;
    }

    initEvents() {
        window.addEventListener("keydown", (e) => {
            // Ignore keystrokes if typing inside an input or challenge textarea
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
            this.keys[e.key.toLowerCase()] = true;

            if (e.key.toLowerCase() === "e" || e.key === " ") {
                this.interactNearby();
            }
        });

        window.addEventListener("keyup", (e) => {
            this.keys[e.key.toLowerCase()] = false;
        });

        // Click-to-move
        this.canvas.addEventListener("click", (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const scaleX = this.canvas.width / rect.width;
            const scaleY = this.canvas.height / rect.height;
            const clickX = (e.clientX - rect.left) * scaleX;
            const clickY = (e.clientY - rect.top) * scaleY;

            // Check if clicked directly on an NPC
            const clickedNPC = this.world.getNearbyNPC(clickX, clickY, 35);
            if (clickedNPC) {
                this.talkToNPC(clickedNPC.name);
            } else {
                this.player.targetX = clickX;
                this.player.targetY = clickY;
            }
        });
    }

    interactNearby() {
        if (this.nearbyNPC) {
            this.talkToNPC(this.nearbyNPC.name);
        }
    }

    talkToNPC(npcName) {
        window.soundEngine.playClick();
        if (window.uiManager) {
            window.uiManager.openNPCDialogue(npcName);
        }
    }

    update(dt) {
        let vx = 0;
        let vy = 0;

        // Keyboard navigation
        if (this.keys["arrowup"] || this.keys["w"]) {
            vy -= this.player.speed;
            this.player.facing = "up";
        }
        if (this.keys["arrowdown"] || this.keys["s"]) {
            vy += this.player.speed;
            this.player.facing = "down";
        }
        if (this.keys["arrowleft"] || this.keys["a"]) {
            vx -= this.player.speed;
            this.player.facing = "left";
        }
        if (this.keys["arrowright"] || this.keys["d"]) {
            vx += this.player.speed;
            this.player.facing = "right";
        }

        // Click-to-move navigation
        const dx = this.player.targetX - this.player.x;
        const dy = this.player.targetY - this.player.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (vx !== 0 || vy !== 0) {
            // Cancel click-to-move if using keyboard
            this.player.targetX = this.player.x;
            this.player.targetY = this.player.y;
        } else if (dist > 4) {
            vx = (dx / dist) * this.player.speed;
            vy = (dy / dist) * this.player.speed;
            if (Math.abs(dx) > Math.abs(dy)) {
                this.player.facing = dx > 0 ? "right" : "left";
            } else {
                this.player.facing = dy > 0 ? "down" : "up";
            }
        }

        // Apply movement
        if (vx !== 0 || vy !== 0) {
            this.player.x += vx;
            this.player.y += vy;
            this.player.moving = true;

            // Clamping inside world bounds
            this.player.x = Math.max(35, Math.min(this.world.width - 35, this.player.x));
            this.player.y = Math.max(35, Math.min(this.world.height - 35, this.player.y));

            // Footstep audio
            this.player.stepTimer += 1;
            if (this.player.stepTimer % 22 === 0) {
                window.soundEngine.playStep();
                this.player.animFrame = (this.player.animFrame + 1) % 4;
            }

            // Report position to multiplayer socket throttled to 100ms
            const now = Date.now();
            if (now - this.lastMoveReportTime > 100) {
                this.lastMoveReportTime = now;
                if (window.multiplayerManager) {
                    window.multiplayerManager.broadcastMovement(this.player.x, this.player.y, this.currentZoneId);
                }
            }
        } else {
            this.player.moving = false;
        }

        // Check Zone Change
        const zone = this.world.getCurrentZone(this.player.x, this.player.y);
        if (zone.id !== this.currentZoneId && zone.id !== "crossroads") {
            this.currentZoneId = zone.id;
            this.onZoneChanged(zone);
        }

        // Check Nearby NPC
        this.nearbyNPC = this.world.getNearbyNPC(this.player.x, this.player.y, 65);
        this.updateProximityUI();

        // Update world ambient particles
        this.world.updateParticles();
    }

    onZoneChanged(zone) {
        window.soundEngine.playFanfare();
        if (window.uiManager) {
            window.uiManager.showZoneBanner(zone.name, zone.subtitle);
            window.uiManager.notifyServerMovement(zone.id);
        }
    }

    updateProximityUI() {
        const hintEl = document.getElementById("interaction-hint");
        if (!hintEl) return;
        if (this.nearbyNPC) {
            hintEl.style.display = "flex";
            hintEl.innerHTML = `<span>💬</span> Press <strong>[E]</strong> to talk to <strong>${this.nearbyNPC.name}</strong>`;
        } else {
            hintEl.style.display = "none";
        }
    }

    render(time) {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Render World map and NPCs
        this.world.render(this.ctx, time);

        // Render Other Players (Multiplayer)
        for (let sid in this.otherPlayers) {
            this._renderOtherPlayer(this.otherPlayers[sid], time);
        }

        // Render Local Player
        this._renderPlayer(this.player, time);
    }

    _renderPlayer(p, time) {
        const ctx = this.ctx;
        ctx.save();

        const bob = p.moving ? Math.sin(time / 100) * 2 : 0;

        // Shadow
        ctx.beginPath();
        ctx.ellipse(p.x, p.y + 16, 12, 5, 0, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(0, 0, 0, 0.45)";
        ctx.fill();

        // Cloak/Armor Body
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y - 4 + bob, 9, 0, Math.PI * 2); // Head
        ctx.fill();

        // Adventurer Cape
        ctx.fillStyle = "#1e293b";
        ctx.beginPath();
        ctx.moveTo(p.x - 10, p.y + 14 + bob);
        ctx.lineTo(p.x, p.y + 4 + bob);
        ctx.lineTo(p.x + 10, p.y + 14 + bob);
        ctx.closePath();
        ctx.fill();

        // Gold Crest Belt
        ctx.fillStyle = "#eab308";
        ctx.fillRect(p.x - 6, p.y + 3 + bob, 12, 3);

        // Direction Indicator or weapon
        ctx.fillStyle = "#38bdf8";
        if (p.facing === "right") ctx.fillRect(p.x + 7, p.y + 4 + bob, 5, 2);
        if (p.facing === "left") ctx.fillRect(p.x - 12, p.y + 4 + bob, 5, 2);
        if (p.facing === "up") ctx.fillRect(p.x - 2, p.y - 12 + bob, 4, 3);
        if (p.facing === "down") ctx.fillRect(p.x - 2, p.y + 12 + bob, 4, 3);

        // Overhead Player Nametag
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(p.x - 40, p.y - 32 + bob, 80, 16);
        ctx.strokeStyle = "#eab308";
        ctx.lineWidth = 1;
        ctx.strokeRect(p.x - 40, p.y - 32 + bob, 80, 16);

        ctx.fillStyle = "#f8fafc";
        ctx.font = "bold 9px 'Inter', sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(p.username, p.x, p.y - 20 + bob);

        ctx.restore();
    }

    _renderOtherPlayer(p, time) {
        const ctx = this.ctx;
        ctx.save();
        // Shadow
        ctx.beginPath();
        ctx.ellipse(p.x, p.y + 16, 12, 5, 0, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
        ctx.fill();

        // Character body in cyan
        ctx.fillStyle = "#06b6d4";
        ctx.beginPath();
        ctx.arc(p.x, p.y - 4, 8, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "#0f172a";
        ctx.beginPath();
        ctx.moveTo(p.x - 9, p.y + 14);
        ctx.lineTo(p.x, p.y + 4);
        ctx.lineTo(p.x + 9, p.y + 14);
        ctx.closePath();
        ctx.fill();

        // Nametag
        ctx.fillStyle = "rgba(6, 182, 212, 0.85)";
        ctx.fillRect(p.x - 35, p.y - 28, 70, 14);
        ctx.fillStyle = "#000000";
        ctx.font = "bold 9px 'Inter', sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(p.username, p.x, p.y - 18);

        ctx.restore();
    }

    loop(time) {
        this.update(16);
        this.render(time);
        requestAnimationFrame((t) => this.loop(t));
    }
}

window.GameEngine = GameEngine;
