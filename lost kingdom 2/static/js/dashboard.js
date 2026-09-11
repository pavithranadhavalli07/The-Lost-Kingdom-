/**
 * Agent Developer & Evaluator Dashboard
 * Provides real-time telemetry, 5 agent cards, activity feed, and instant simulation triggers.
 */
class DashboardManager {
    constructor() {
        this.dashboardModal = document.getElementById("dashboard-modal");
        this.initDOM();
    }

    initDOM() {
        // Toggle dashboard button
        document.getElementById("btn-toggle-dashboard")?.addEventListener("click", () => this.toggle(true));
        document.getElementById("btn-close-dashboard")?.addEventListener("click", () => this.toggle(false));

        // Simulation Triggers
        document.getElementById("btn-sim-frustration")?.addEventListener("click", () => this.runSimulation("frustration_streak"));
        document.getElementById("btn-sim-mastery")?.addEventListener("click", () => this.runSimulation("mastery_streak"));
        document.getElementById("btn-sim-reset")?.addEventListener("click", () => this.runSimulation("reset_memory"));
        document.getElementById("btn-sim-branch-scholar")?.addEventListener("click", () => this.runSimulation("switch_branch", { branch: "scholar" }));
        document.getElementById("btn-sim-branch-vanguard")?.addEventListener("click", () => this.runSimulation("switch_branch", { branch: "vanguard" }));
        document.getElementById("btn-sim-branch-mystic")?.addEventListener("click", () => this.runSimulation("switch_branch", { branch: "mystic" }));
    }

    toggle(state) {
        window.soundEngine.playClick();
        if (state !== undefined) {
            this.dashboardModal?.classList.toggle("active", state);
        } else {
            this.dashboardModal?.classList.toggle("active");
        }
    }

    async refreshState() {
        const playerId = window.uiManager ? window.uiManager.playerId : "default_player";
        try {
            const resp = await fetch(`/api/dashboard/state?player_id=${playerId}`);
            const data = await resp.json();
            this.renderDashboard(data);
        } catch (e) {}
    }

    async runSimulation(scenario, extra = {}) {
        window.soundEngine.playClick();
        const playerId = window.uiManager ? window.uiManager.playerId : "default_player";
        const simNotice = document.getElementById("sim-status-notice");
        if (simNotice) {
            simNotice.textContent = `Simulating: ${scenario}...`;
            simNotice.style.display = "block";
        }

        try {
            const resp = await fetch("/api/simulate/scenario", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player_id: playerId, scenario, ...extra })
            });
            const data = await resp.json();
            if (data.status === "success") {
                window.soundEngine.playFanfare();
                if (simNotice) simNotice.textContent = `✓ ${data.message}`;
                this.renderDashboard(data.dashboard);
                if (window.uiManager) {
                    window.uiManager.updateHUD(data.dashboard);
                    window.uiManager.showNotification(data.message);
                }
            }
        } catch (e) {
            if (simNotice) simNotice.textContent = "Simulation failed.";
        }
    }

    renderDashboard(snapshot) {
        if (!snapshot) return;

        // Render Agent Cards
        const grid = document.getElementById("agent-cards-grid");
        if (grid && snapshot.agents) {
            grid.innerHTML = "";
            snapshot.agents.forEach(agent => {
                const card = document.createElement("div");
                card.className = `agent-card ${this._getAgentClass(agent.name)}`;
                card.innerHTML = `
                    <div class="agent-card-header">
                        <span class="agent-name">${agent.name}</span>
                        <span class="agent-status-badge ${agent.status.toLowerCase()}">${agent.status}</span>
                    </div>
                    <div class="agent-role">${agent.role}</div>
                    <div class="agent-action-box">
                        <div class="action-label">LAST DECISION:</div>
                        <div class="action-text">${agent.last_action}</div>
                    </div>
                    <div class="agent-meta-tags">
                        ${this._renderMetaPills(agent)}
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        // Render Activity Stream Log
        const logStream = document.getElementById("agent-activity-stream");
        if (logStream && snapshot.recent_logs) {
            logStream.innerHTML = "";
            snapshot.recent_logs.slice().reverse().forEach(log => {
                const row = document.createElement("div");
                row.className = "log-entry";
                row.innerHTML = `
                    <span class="log-time">${log.timestamp}</span>
                    <span class="log-badge ${this._getAgentClass(log.agent_name)}">${log.agent_name.replace(" Agent", "")}</span>
                    <span class="log-action">[${log.action_type}]</span>
                    <span class="log-msg">${log.log_message}</span>
                `;
                logStream.appendChild(row);
            });
        }

        // Render Story Branches
        const branchTree = document.getElementById("dashboard-branch-tree");
        if (branchTree && snapshot.branches) {
            branchTree.innerHTML = "";
            for (let [bKey, bData] of Object.entries(snapshot.branches)) {
                const isActive = (snapshot.player.current_branch === bKey);
                const isUnlocked = bData.unlocked;
                const node = document.createElement("div");
                node.className = `branch-node ${isActive ? 'active' : ''} ${isUnlocked ? 'unlocked' : 'locked'}`;
                node.innerHTML = `
                    <div class="branch-status">${isActive ? '★ ACTIVE BRANCH' : (isUnlocked ? '✓ UNLOCKED' : '🔒 LOCKED')}</div>
                    <div class="branch-title">${bData.title}</div>
                    <div class="branch-desc">${bData.description}</div>
                `;
                branchTree.appendChild(node);
            }
        }
    }

    _getAgentClass(name) {
        if (name.includes("Analysis")) return "agent-analysis";
        if (name.includes("Knowledge")) return "agent-knowledge";
        if (name.includes("Emotion")) return "agent-emotion";
        if (name.includes("Story")) return "agent-story";
        if (name.includes("Challenge")) return "agent-challenge";
        return "agent-generic";
    }

    _renderMetaPills(agent) {
        const meta = agent.metadata || {};
        let pills = "";
        for (let [k, v] of Object.entries(meta)) {
            if (typeof v !== "object" && typeof v !== "function" && String(v).length < 35) {
                pills += `<span class="meta-pill"><strong>${k.replace(/_/g, " ")}:</strong> ${v}</span>`;
            }
        }
        return pills;
    }

    appendLiveLog(entry) {
        const logStream = document.getElementById("agent-activity-stream");
        if (!logStream) return;
        const row = document.createElement("div");
        row.className = "log-entry live-flash";
        row.innerHTML = `
            <span class="log-time">${entry.timestamp}</span>
            <span class="log-badge ${this._getAgentClass(entry.agent_name)}">${entry.agent_name.replace(" Agent", "")}</span>
            <span class="log-action">[${entry.action_type}]</span>
            <span class="log-msg">${entry.log_message}</span>
        `;
        logStream.prepend(row);
        if (logStream.children.length > 50) {
            logStream.removeChild(logStream.lastChild);
        }
    }
}

window.DashboardManager = DashboardManager;
