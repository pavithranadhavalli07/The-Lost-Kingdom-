/**
 * UI Manager: Handles Dialogue, Challenges, HUD, Mastery Bars, and Sound Triggers
 */
class UIManager {
    constructor() {
        this.playerId = localStorage.getItem("lost_kingdom_player_id") || `player_${Math.random().toString(36).substring(2, 9)}`;
        this.username = localStorage.getItem("lost_kingdom_username") || "Seeker";
        localStorage.setItem("lost_kingdom_player_id", this.playerId);
        localStorage.setItem("lost_kingdom_username", this.username);

        this.currentChallenge = null;
        this.challengeStartTime = 0;
        this.activeNPC = null;
        this.typewriterTimeout = null;

        this.initDOM();
    }

    initDOM() {
        // Dialogue actions
        document.getElementById("btn-dialogue-challenge")?.addEventListener("click", () => this.startChallengeFromNPC());
        document.getElementById("btn-dialogue-quest")?.addEventListener("click", () => this.askQuestDetails());
        document.getElementById("btn-dialogue-close")?.addEventListener("click", () => this.closeNPCDialogue());
        document.getElementById("btn-dialogue-tts")?.addEventListener("click", () => this.readDialogueAloud());
        document.getElementById("btn-dialogue-voice")?.addEventListener("click", () => this.listenToPlayerVoice());

        // Challenge actions
        document.getElementById("btn-hint")?.addEventListener("click", () => this.requestHint());
        document.getElementById("btn-close-challenge")?.addEventListener("click", () => this.closeChallenge());
        document.getElementById("btn-voice-answer")?.addEventListener("click", () => this.voiceAnswerChallenge());

        // Mastery Drawer Toggle
        document.getElementById("btn-toggle-mastery")?.addEventListener("click", () => this.toggleMasteryDrawer());
        document.getElementById("btn-close-mastery")?.addEventListener("click", () => this.toggleMasteryDrawer(false));

        // Audio Mute Toggle
        document.getElementById("btn-mute-toggle")?.addEventListener("click", () => {
            const enabled = window.soundEngine.toggleMute();
            document.getElementById("btn-mute-toggle").innerHTML = enabled ? "🔊 Audio: ON" : "🔇 Audio: OFF";
        });

        // Global Keyboard Navigation & Shortcuts
        window.addEventListener("keydown", (e) => {
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
            
            // Escape key closes modals
            if (e.key === "Escape") {
                this.closeNPCDialogue();
                this.closeChallenge();
                window.dashboardManager?.toggle(false);
                this.toggleMasteryDrawer(false);
            }

            // Number keys 1-4 for quick challenge answering
            if (this.currentChallenge && ["1", "2", "3", "4"].includes(e.key)) {
                const expBox = document.getElementById("challenge-explanation-box");
                if (!expBox || expBox.style.display === "none") {
                    const idx = parseInt(e.key, 10) - 1;
                    if (this.currentChallenge.options && this.currentChallenge.options[idx]) {
                        this.submitAnswer(this.currentChallenge.options[idx]);
                    }
                }
            }

            // Enter key advances when 'Next Challenge' is shown
            if (e.key === "Enter") {
                const nextBtn = document.getElementById("btn-next-challenge");
                if (nextBtn && nextBtn.style.display !== "none") {
                    nextBtn.click();
                }
            }
        });
    }

    async initPlayerSession() {
        try {
            const resp = await fetch("/api/player/init", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player_id: this.playerId, username: this.username })
            });
            const data = await resp.json();
            if (data.status === "success") {
                this.updateHUD(data.dashboard);
                if (data.is_returning_player) {
                    this.showNotification("Welcome back, Seeker! Your previous mastery and quest memories have been restored.");
                } else {
                    this.showNotification("Welcome to the Lost Kingdom! Walk up to Elder Sophia and press [E] to begin.");
                }
                if (window.dashboardManager) {
                    window.dashboardManager.renderDashboard(data.dashboard);
                }
            }
        } catch (e) {
            console.error("Player initialization failed:", e);
        }
    }

    showNotification(message, duration = 4000) {
        const notif = document.getElementById("game-notification");
        if (!notif) return;
        notif.textContent = message;
        notif.classList.add("show");
        setTimeout(() => notif.classList.remove("show"), duration);
    }

    showZoneBanner(title, subtitle) {
        const banner = document.getElementById("zone-banner");
        const titleEl = document.getElementById("zone-banner-title");
        const subEl = document.getElementById("zone-banner-sub");
        if (!banner || !titleEl || !subEl) return;

        titleEl.textContent = title;
        subEl.textContent = subtitle;
        banner.classList.add("active");
        setTimeout(() => banner.classList.remove("active"), 3200);
    }

    async notifyServerMovement(location) {
        try {
            await fetch("/api/player/move", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player_id: this.playerId, location })
            });
        } catch (e) {}
    }

    async openNPCDialogue(npcName) {
        this.activeNPC = npcName;
        const modal = document.getElementById("dialogue-modal");
        const nameEl = document.getElementById("dialogue-npc-name");
        const toneEl = document.getElementById("dialogue-tone-badge");
        const textEl = document.getElementById("dialogue-text");
        const portraitEl = document.getElementById("dialogue-portrait");

        if (!modal) return;
        nameEl.textContent = npcName;
        textEl.textContent = "Approaching...";
        modal.classList.add("active");

        // Set portrait icon/accent
        if (portraitEl) {
            const icons = {
                "Elder Sophia": "🧙‍♀️",
                "Scholar Theron": "📜",
                "Master Kael": "⚔️",
                "Guardian Lyra": "✨"
            };
            portraitEl.textContent = icons[npcName] || "👤";
        }

        try {
            const resp = await fetch("/api/npc/talk", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player_id: this.playerId, npc_name: npcName })
            });
            const data = await resp.json();
            if (data.status === "success" && data.interaction) {
                const inter = data.interaction;
                toneEl.textContent = `Tone: ${inter.emotion_tone} adaptation`;
                this.typewriterEffect(inter.dialogue, textEl);
                this.lastDialogueText = inter.dialogue;
                // Speak if TTS enabled
                window.voiceSystem.speakNPC(inter.dialogue, npcName);
            }
        } catch (e) {
            textEl.textContent = "The winds of the kingdom carry a strange silence... please try again.";
        }
    }

    typewriterEffect(text, element) {
        clearTimeout(this.typewriterTimeout);
        element.textContent = "";
        let i = 0;
        const speed = 18;
        const type = () => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                this.typewriterTimeout = setTimeout(type, speed);
            }
        };
        type();
    }

    readDialogueAloud() {
        if (this.lastDialogueText && this.activeNPC) {
            window.soundEngine.playClick();
            window.voiceSystem.speakNPC(this.lastDialogueText, this.activeNPC);
        }
    }

    listenToPlayerVoice() {
        window.soundEngine.playClick();
        window.voiceSystem.startListening((spokenText) => {
            const textEl = document.getElementById("dialogue-text");
            if (textEl) {
                textEl.innerHTML = `<span style="color:#38bdf8;">You asked: "${spokenText}"</span><br><br>Analyzing your query...`;
            }
            // Send query as custom event to NPC
            setTimeout(async () => {
                const resp = await fetch("/api/npc/talk", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        player_id: this.playerId,
                        npc_name: this.activeNPC,
                        recent_event: `Player asked verbally: "${spokenText}"`
                    })
                });
                const data = await resp.json();
                if (data.status === "success" && data.interaction) {
                    this.typewriterEffect(data.interaction.dialogue, textEl);
                    this.lastDialogueText = data.interaction.dialogue;
                    window.voiceSystem.speakNPC(data.interaction.dialogue, this.activeNPC);
                }
            }, 500);
        });
    }

    closeNPCDialogue() {
        window.soundEngine.playClick();
        const modal = document.getElementById("dialogue-modal");
        if (modal) modal.classList.remove("active");
        if (window.speechSynthesis) window.speechSynthesis.cancel();
    }

    async askQuestDetails() {
        window.soundEngine.playClick();
        const textEl = document.getElementById("dialogue-text");
        try {
            const resp = await fetch(`/api/dashboard/state?player_id=${this.playerId}`);
            const data = await resp.json();
            const q = data.active_quest;
            this.typewriterEffect(`Active Quest: [${q.title}] — ${q.objective}`, textEl);
        } catch (e) {}
    }

    async startChallengeFromNPC() {
        this.closeNPCDialogue();
        const npcTopicMap = {
            "Elder Sophia": "Algebra",
            "Scholar Theron": "Geometry",
            "Master Kael": "Science",
            "Guardian Lyra": "Logic"
        };
        const topic = npcTopicMap[this.activeNPC] || "Algebra";
        await this.loadAndShowChallenge(topic);
    }

    async loadAndShowChallenge(topic = "Algebra") {
        window.soundEngine.playClick();
        const modal = document.getElementById("challenge-modal");
        const qTextEl = document.getElementById("challenge-question-text");
        const topicBadge = document.getElementById("challenge-topic-badge");
        const diffBadge = document.getElementById("challenge-difficulty-badge");
        const optionsContainer = document.getElementById("challenge-options-grid");
        const explanationBox = document.getElementById("challenge-explanation-box");
        const hintBox = document.getElementById("challenge-hint-box");

        modal.classList.add("active");
        qTextEl.textContent = "Consulting the Challenge Agent...";
        optionsContainer.innerHTML = "<div class='loading-spinner'></div>";
        explanationBox.style.display = "none";
        hintBox.style.display = "none";

        try {
            const resp = await fetch("/api/challenge/get", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic })
            });
            const data = await resp.json();
            if (data.status === "success" && data.challenge) {
                this.currentChallenge = data.challenge;
                this.challengeStartTime = Date.now();

                topicBadge.textContent = data.challenge.topic;
                diffBadge.textContent = data.challenge.difficulty.toUpperCase();
                diffBadge.className = `badge diff-${data.challenge.difficulty.toLowerCase()}`;
                qTextEl.textContent = data.challenge.question;

                optionsContainer.innerHTML = "";
                data.challenge.options.forEach((opt, idx) => {
                    const btn = document.createElement("button");
                    btn.className = "option-card";
                    btn.innerHTML = `<span class="option-key">${idx + 1}</span> <span class="option-text">${opt}</span>`;
                    btn.addEventListener("click", () => this.submitAnswer(opt));
                    optionsContainer.appendChild(btn);
                });
            }
        } catch (e) {
            qTextEl.textContent = "Error loading challenge. Please try again.";
        }
    }

    async submitAnswer(chosenAnswer) {
        if (!this.currentChallenge) return;
        const responseTime = Date.now() - this.challengeStartTime;
        const c = this.currentChallenge;

        // Visual click sound
        window.soundEngine.playClick();

        const payload = {
            player_id: this.playerId,
            question: c.question,
            topic: c.topic,
            difficulty: c.difficulty,
            player_answer: chosenAnswer,
            correct_answer: c.answer,
            explanation: c.explanation,
            response_time_ms: responseTime
        };

        try {
            const resp = await fetch("/api/challenge/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (data.status === "success") {
                const res = data.result;
                const isCorrect = res.evaluation.is_correct;

                if (isCorrect) {
                    window.soundEngine.playSuccess();
                } else {
                    window.soundEngine.playError();
                }

                // Show Explanation and Agent Telemetry Banner
                this.displayAnswerFeedback(res);
                this.updateHUD(data.dashboard);
                if (window.dashboardManager) {
                    window.dashboardManager.renderDashboard(data.dashboard);
                }

                // Update current challenge to next generated challenge
                if (res.next_challenge) {
                    this.nextPendingChallenge = res.next_challenge;
                }
            }
        } catch (e) {
            console.error("Submission error:", e);
        }
    }

    displayAnswerFeedback(res) {
        const isCorrect = res.evaluation.is_correct;
        const explanationBox = document.getElementById("challenge-explanation-box");
        const statusBadge = document.getElementById("challenge-result-status");
        const expText = document.getElementById("challenge-result-explanation");
        const telemetryBox = document.getElementById("challenge-agent-telemetry");

        statusBadge.textContent = isCorrect ? "✓ Correct Answer!" : "✗ Needs Review";
        statusBadge.className = isCorrect ? "status-tag success" : "status-tag error";
        expText.innerHTML = `<strong>Explanation:</strong> ${res.evaluation.explanation}`;

        // Agent Adaptation Summary
        telemetryBox.innerHTML = `
            <div class="agent-pill"><strong>Analysis:</strong> ${res.player_analysis.hesitation_level} (${(res.player_analysis.response_time_ms/1000).toFixed(1)}s)</div>
            <div class="agent-pill"><strong>Emotion:</strong> ${res.emotion_state.state} (${res.emotion_state.confidence_percent}%)</div>
            <div class="agent-pill"><strong>Knowledge:</strong> ${res.knowledge_update.topic} → ${res.knowledge_update.mastery_percent}%</div>
            <div class="agent-pill"><strong>Challenge:</strong> ${res.difficulty_adaptation.difficulty.toUpperCase()}</div>
        `;

        explanationBox.style.display = "block";

        // Show "Next Challenge" button
        const nextBtn = document.getElementById("btn-next-challenge");
        if (nextBtn) {
            nextBtn.style.display = "inline-flex";
            nextBtn.onclick = () => {
                explanationBox.style.display = "none";
                if (this.nextPendingChallenge) {
                    this.displayChallengeObject(this.nextPendingChallenge);
                } else {
                    this.loadAndShowChallenge();
                }
            };
        }
    }

    displayChallengeObject(c) {
        this.currentChallenge = c;
        this.challengeStartTime = Date.now();

        const topicBadge = document.getElementById("challenge-topic-badge");
        const diffBadge = document.getElementById("challenge-difficulty-badge");
        const qTextEl = document.getElementById("challenge-question-text");
        const optionsContainer = document.getElementById("challenge-options-grid");
        const explanationBox = document.getElementById("challenge-explanation-box");
        const hintBox = document.getElementById("challenge-hint-box");

        topicBadge.textContent = c.topic;
        diffBadge.textContent = c.difficulty.toUpperCase();
        diffBadge.className = `badge diff-${c.difficulty.toLowerCase()}`;
        qTextEl.textContent = c.question;
        explanationBox.style.display = "none";
        hintBox.style.display = "none";

        optionsContainer.innerHTML = "";
        c.options.forEach((opt, idx) => {
            const btn = document.createElement("button");
            btn.className = "option-card";
            btn.innerHTML = `<span class="option-key">${idx + 1}</span> <span class="option-text">${opt}</span>`;
            btn.addEventListener("click", () => this.submitAnswer(opt));
            optionsContainer.appendChild(btn);
        });
    }

    async requestHint() {
        if (!this.currentChallenge) return;
        window.soundEngine.playClick();
        const hintBox = document.getElementById("challenge-hint-box");
        const hintText = document.getElementById("challenge-hint-text");

        hintText.textContent = this.currentChallenge.hint || "Deconstruct the question step-by-step.";
        hintBox.style.display = "block";

        try {
            await fetch("/api/challenge/hint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player_id: this.playerId })
            });
        } catch (e) {}
    }

    voiceAnswerChallenge() {
        window.soundEngine.playClick();
        window.voiceSystem.startListening((spokenText) => {
            if (!this.currentChallenge) return;
            const clean = spokenText.toLowerCase();
            // Check if spoken text matches an option or option number
            let matchedOption = null;
            if (clean.includes("one") || clean.includes("1") || clean.includes("option a")) {
                matchedOption = this.currentChallenge.options[0];
            } else if (clean.includes("two") || clean.includes("2") || clean.includes("option b")) {
                matchedOption = this.currentChallenge.options[1];
            } else if (clean.includes("three") || clean.includes("3") || clean.includes("option c")) {
                matchedOption = this.currentChallenge.options[2];
            } else if (clean.includes("four") || clean.includes("4") || clean.includes("option d")) {
                matchedOption = this.currentChallenge.options[3];
            } else {
                for (let opt of this.currentChallenge.options) {
                    if (clean.includes(String(opt).toLowerCase())) {
                        matchedOption = opt;
                        break;
                    }
                }
            }

            if (matchedOption) {
                this.submitAnswer(matchedOption);
            } else {
                this.showNotification(`Heard "${spokenText}" - please click an option or try again.`);
            }
        });
    }

    closeChallenge() {
        window.soundEngine.playClick();
        const modal = document.getElementById("challenge-modal");
        if (modal) modal.classList.remove("active");
        this.currentChallenge = null;
    }

    toggleMasteryDrawer(forceState) {
        window.soundEngine.playClick();
        const drawer = document.getElementById("mastery-drawer");
        if (!drawer) return;
        if (forceState !== undefined) {
            drawer.classList.toggle("active", forceState);
        } else {
            drawer.classList.toggle("active");
        }
    }

    updateHUD(dashboard) {
        if (!dashboard) return;
        const p = dashboard.player;

        // XP & Level
        const levelEl = document.getElementById("hud-player-level");
        const xpBar = document.getElementById("hud-xp-fill");
        const branchBadge = document.getElementById("hud-branch-badge");
        const emotionBadge = document.getElementById("hud-emotion-badge");
        const diffBadge = document.getElementById("hud-diff-badge");
        const masteryEl = document.getElementById("hud-overall-mastery");

        if (levelEl) levelEl.textContent = `Lvl ${p.level}`;
        if (xpBar) xpBar.style.width = `${Math.min(100, (p.xp / (p.level * 50)) * 100)}%`;
        if (branchBadge) branchBadge.textContent = p.current_branch.toUpperCase();
        if (diffBadge) {
            diffBadge.textContent = p.current_difficulty.toUpperCase();
            diffBadge.className = `hud-pill diff-${p.current_difficulty.toLowerCase()}`;
        }
        if (masteryEl) masteryEl.textContent = `${p.overall_mastery}%`;

        if (emotionBadge) {
            const icons = {
                "Engaged": "⚡ Engaged",
                "Confident": "🔥 Confident",
                "Frustrated": "⚠️ Frustrated",
                "Confused": "❓ Confused",
                "Bored": "💤 Bored"
            };
            emotionBadge.textContent = icons[p.emotion_state] || p.emotion_state;
            emotionBadge.className = `hud-pill emotion-${p.emotion_state.toLowerCase()}`;
        }

        // Render Topics Drawer
        const topicsList = document.getElementById("mastery-topics-list");
        if (topicsList && dashboard.topics) {
            topicsList.innerHTML = "";
            dashboard.topics.forEach(t => {
                const item = document.createElement("div");
                item.className = "mastery-item";
                item.innerHTML = `
                    <div class="mastery-info">
                        <span class="topic-name">${t.topic}</span>
                        <span class="topic-pct">${t.mastery_percent}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width: ${t.mastery_percent}%"></div>
                    </div>
                    <div class="mastery-stats">
                        <span>Attempts: ${t.attempts}</span>
                        <span>Correct: ${t.correct}</span>
                    </div>
                `;
                topicsList.appendChild(item);
            });
        }
    }
}

window.UIManager = UIManager;
