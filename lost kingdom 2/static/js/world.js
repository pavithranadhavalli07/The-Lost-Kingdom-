/**
 * World & Zone definitions, collision zones, and map rendering
 */
class GameWorld {
    constructor() {
        this.width = 1100;
        this.height = 700;

        this.zones = [
            {
                id: "village",
                name: "Village of Oakhaven",
                subtitle: "The peaceful realm of foundational learning",
                color: "#15803d",
                bounds: { x: 30, y: 30, w: 480, h: 310 },
                npc: "Elder Sophia",
                topic: "Algebra"
            },
            {
                id: "library",
                name: "Alexandrian Archive",
                subtitle: "Halls of ancient codices & theoretical proofs",
                color: "#0369a1",
                bounds: { x: 590, y: 30, w: 480, h: 310 },
                npc: "Scholar Theron",
                topic: "Geometry"
            },
            {
                id: "arena",
                name: "Vanguard Arena",
                subtitle: "Tactical training grounds of applied physics & mechanics",
                color: "#b45309",
                bounds: { x: 30, y: 370, w: 480, h: 300 },
                npc: "Master Kael",
                topic: "Science"
            },
            {
                id: "temple",
                name: "Aetheria Sky Temple",
                subtitle: "Celestial sanctum of logic runes & cryptographic seals",
                color: "#6d28d9",
                bounds: { x: 590, y: 370, w: 480, h: 300 },
                npc: "Guardian Lyra",
                topic: "Logic"
            }
        ];

        this.npcs = [
            {
                id: "sophia",
                name: "Elder Sophia",
                title: "Village Matron & Arithmetician",
                zone: "village",
                x: 270,
                y: 180,
                color: "#22c55e",
                accent: "#86efac",
                dialogueTone: "Gentle / Encouraging",
                subject: "Algebra"
            },
            {
                id: "theron",
                name: "Scholar Theron",
                title: "Keeper of the Alexandrian Scrolls",
                zone: "library",
                x: 830,
                y: 180,
                color: "#38bdf8",
                accent: "#7dd3fc",
                dialogueTone: "Scholarly / Rigorous",
                subject: "Geometry"
            },
            {
                id: "kael",
                name: "Master Kael",
                title: "Vanguard Tactician",
                zone: "arena",
                x: 270,
                y: 520,
                color: "#f59e0b",
                accent: "#fde047",
                dialogueTone: "Commanding / Tactical",
                subject: "Science"
            },
            {
                id: "lyra",
                name: "Guardian Lyra",
                title: "Sanctum Diviner",
                zone: "temple",
                x: 830,
                y: 520,
                color: "#a855f7",
                accent: "#d8b4fe",
                dialogueTone: "Ethereal / Philosophical",
                subject: "Logic & Cryptography"
            }
        ];

        // Ambient particles (floating spores, magical runes, embers)
        this.particles = [];
        for (let i = 0; i < 40; i++) {
            this.particles.push({
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                radius: Math.random() * 2 + 1,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4 - 0.2,
                alpha: Math.random() * 0.7 + 0.3,
                zone: null
            });
        }
    }

    getCurrentZone(x, y) {
        for (let z of this.zones) {
            const b = z.bounds;
            if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
                return z;
            }
        }
        return {
            id: "crossroads",
            name: "Sanctum Crossroads",
            subtitle: "The nexus between realms",
            color: "#64748b"
        };
    }

    getNearbyNPC(x, y, proximityThreshold = 65) {
        for (let npc of this.npcs) {
            const dx = npc.x - x;
            const dy = npc.y - y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist <= proximityThreshold) {
                return npc;
            }
        }
        return null;
    }

    updateParticles() {
        for (let p of this.particles) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = this.width;
            if (p.x > this.width) p.x = 0;
            if (p.y < 0) p.y = this.height;
            if (p.y > this.height) p.y = 0;
        }
    }

    render(ctx, time) {
        // Base ground
        ctx.fillStyle = "#090d16";
        ctx.fillRect(0, 0, this.width, this.height);

        // Render Crossroads stone path
        ctx.fillStyle = "#1e293b";
        // Horizontal path
        ctx.fillRect(0, 335, this.width, 35);
        // Vertical path
        ctx.fillRect(525, 0, 50, this.height);

        // Path cobblestone dashes
        ctx.strokeStyle = "rgba(148, 163, 184, 0.2)";
        ctx.lineWidth = 1;
        for (let x = 10; x < this.width; x += 30) {
            ctx.strokeRect(x, 340, 20, 25);
        }
        for (let y = 10; y < this.height; y += 30) {
            ctx.strokeRect(535, y, 30, 20);
        }

        // Render Zones
        for (let z of this.zones) {
            this._renderZone(ctx, z, time);
        }

        // Render NPCs
        for (let npc of this.npcs) {
            this._renderNPC(ctx, npc, time);
        }

        // Render Ambient particles
        for (let p of this.particles) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha * 0.6})`;
            ctx.fill();
        }
    }

    _renderZone(ctx, zone, time) {
        const b = zone.bounds;
        ctx.save();

        // Zone backdrop panel
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(b.x, b.y, b.w, b.h);

        // Glowing border
        ctx.strokeStyle = zone.color;
        ctx.lineWidth = 2;
        ctx.strokeRect(b.x, b.y, b.w, b.h);

        // Subtle corner accents
        const cornerSize = 12;
        ctx.fillStyle = zone.color;
        ctx.fillRect(b.x, b.y, cornerSize, 3);
        ctx.fillRect(b.x, b.y, 3, cornerSize);
        ctx.fillRect(b.x + b.w - cornerSize, b.y, cornerSize, 3);
        ctx.fillRect(b.x + b.w - 3, b.y, 3, cornerSize);

        // Zone Header Banner
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(b.x + 8, b.y + 8, b.w - 16, 26);
        ctx.fillStyle = "#f8fafc";
        ctx.font = "600 13px 'Cinzel', serif";
        ctx.fillText(zone.name.toUpperCase(), b.x + 16, b.y + 25);

        ctx.fillStyle = "rgba(203, 213, 225, 0.7)";
        ctx.font = "10px 'Inter', sans-serif";
        ctx.fillText(zone.topic, b.x + b.w - 100, b.y + 25);

        // Zone-specific thematic architectural props
        if (zone.id === "village") {
            // Central village fountain
            ctx.beginPath();
            ctx.arc(b.x + 130, b.y + 160, 32, 0, Math.PI * 2);
            ctx.fillStyle = "#1e293b";
            ctx.fill();
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 2;
            ctx.stroke();

            // Water ripple
            const ripple = (Math.sin(time / 400) + 1) * 8;
            ctx.beginPath();
            ctx.arc(b.x + 130, b.y + 160, 12 + ripple, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(56, 189, 248, 0.5)";
            ctx.stroke();

            // Cottages
            ctx.fillStyle = "#334155";
            ctx.fillRect(b.x + 350, b.y + 70, 90, 70);
            ctx.fillStyle = "#b45309";
            ctx.beginPath();
            ctx.moveTo(b.x + 340, b.y + 70);
            ctx.lineTo(b.x + 395, b.y + 35);
            ctx.lineTo(b.x + 450, b.y + 70);
            ctx.fill();
        } else if (zone.id === "library") {
            // Bookshelves
            for (let i = 0; i < 3; i++) {
                ctx.fillStyle = "#451a03";
                ctx.fillRect(b.x + 40 + i * 80, b.y + 60, 60, 110);
                ctx.strokeStyle = "#b45309";
                ctx.strokeRect(b.x + 40 + i * 80, b.y + 60, 60, 110);
                // Shelf lines
                ctx.fillStyle = "#0284c7";
                ctx.fillRect(b.x + 45 + i * 80, b.y + 80, 50, 6);
                ctx.fillRect(b.x + 45 + i * 80, b.y + 115, 50, 6);
                ctx.fillRect(b.x + 45 + i * 80, b.y + 145, 50, 6);
            }
            // Reading table with glowing scroll
            ctx.fillStyle = "#78350f";
            ctx.fillRect(b.x + 320, b.y + 140, 90, 50);
            ctx.fillStyle = "#38bdf8";
            ctx.fillRect(b.x + 350, b.y + 155, 30, 20);
        } else if (zone.id === "arena") {
            // Combat ring
            ctx.beginPath();
            ctx.arc(b.x + 140, b.y + 160, 50, 0, Math.PI * 2);
            ctx.strokeStyle = "#f59e0b";
            ctx.lineWidth = 3;
            ctx.setLineDash([8, 6]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Targets & dummies
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(b.x + 370, b.y + 100, 18, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#ffffff";
            ctx.beginPath();
            ctx.arc(b.x + 370, b.y + 100, 10, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#ef4444";
            ctx.beginPath();
            ctx.arc(b.x + 370, b.y + 100, 4, 0, Math.PI * 2);
            ctx.fill();
        } else if (zone.id === "temple") {
            // Floating magical crystal dais
            ctx.beginPath();
            ctx.arc(b.x + 240, b.y + 160, 65, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(168, 85, 247, 0.4)";
            ctx.lineWidth = 4;
            ctx.stroke();

            // Levitating crystal in center
            const floatY = Math.sin(time / 300) * 8;
            ctx.fillStyle = "#c084fc";
            ctx.beginPath();
            ctx.moveTo(b.x + 240, b.y + 140 + floatY);
            ctx.lineTo(b.x + 255, b.y + 165 + floatY);
            ctx.lineTo(b.x + 240, b.y + 190 + floatY);
            ctx.lineTo(b.x + 225, b.y + 165 + floatY);
            ctx.closePath();
            ctx.fill();
            ctx.strokeStyle = "#f3e8ff";
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        ctx.restore();
    }

    _renderNPC(ctx, npc, time) {
        ctx.save();
        const bob = Math.sin(time / 250 + npc.x) * 3;

        // Ground shadow
        ctx.beginPath();
        ctx.ellipse(npc.x, npc.y + 18, 14, 6, 0, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
        ctx.fill();

        // Aura glow
        ctx.beginPath();
        ctx.arc(npc.x, npc.y + bob, 22, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${this._hexToRgb(npc.color)}, 0.15)`;
        ctx.fill();

        // NPC Robe / Body
        ctx.fillStyle = npc.color;
        ctx.beginPath();
        ctx.arc(npc.x, npc.y - 4 + bob, 10, 0, Math.PI * 2); // Head
        ctx.fill();

        ctx.fillStyle = "#1e293b";
        ctx.beginPath();
        ctx.moveTo(npc.x - 12, npc.y + 16 + bob);
        ctx.lineTo(npc.x, npc.y + 4 + bob);
        ctx.lineTo(npc.x + 12, npc.y + 16 + bob);
        ctx.closePath();
        ctx.fill();

        // Scarf/Accent
        ctx.fillStyle = npc.accent;
        ctx.fillRect(npc.x - 6, npc.y + 4 + bob, 12, 4);

        // Nameplate & Interactive Indicator
        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(npc.x - 55, npc.y - 38 + bob, 110, 18);
        ctx.strokeStyle = npc.color;
        ctx.lineWidth = 1;
        ctx.strokeRect(npc.x - 55, npc.y - 38 + bob, 110, 18);

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px 'Inter', sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(npc.name, npc.x, npc.y - 25 + bob);

        // "Talk [E]" prompt icon
        ctx.fillStyle = "#facc15";
        ctx.font = "9px 'Inter', sans-serif";
        ctx.fillText("💬 Press [E] or Click", npc.x, npc.y + 32);

        ctx.restore();
    }

    _hexToRgb(hex) {
        hex = hex.replace("#", "");
        if (hex.length === 3) hex = hex.split("").map(c => c + c).join("");
        const num = parseInt(hex, 16);
        return `${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}`;
    }
}

window.GameWorld = GameWorld;
