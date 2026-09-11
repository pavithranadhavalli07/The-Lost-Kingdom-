/**
 * Web Speech API Engine: STT (Speech-to-Text) and TTS (Text-to-Speech)
 */
class VoiceSystem {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.ttsEnabled = true;
        this.synth = window.speechSynthesis || null;
        this.onSpeechResultCallback = null;
        
        this.initSTT();
    }

    initSTT() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
            this.recognition = new SpeechRec();
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = "en-US";

            this.recognition.onstart = () => {
                this.isListening = true;
                this._updateMicUI(true, "Listening... speak now");
            };

            this.recognition.onresult = (event) => {
                let transcript = "";
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    transcript += event.results[i][0].transcript;
                }
                this._updateMicUI(true, `Heard: "${transcript}"`);
                if (event.results[0].isFinal && this.onSpeechResultCallback) {
                    this.onSpeechResultCallback(transcript.trim());
                }
            };

            this.recognition.onerror = (e) => {
                console.warn("[VoiceSystem] Speech recognition error:", e.error);
                this.isListening = false;
                this._updateMicUI(false, `Voice error: ${e.error}`);
            };

            this.recognition.onend = () => {
                this.isListening = false;
                setTimeout(() => this._updateMicUI(false, "Press mic to speak"), 1500);
            };
        } else {
            console.warn("[VoiceSystem] Web SpeechRecognition is not supported in this browser.");
        }
    }

    startListening(onResult) {
        if (!this.recognition) {
            alert("Speech recognition is not supported in this browser or permission was denied. You can continue using direct clicks and text input!");
            return;
        }
        this.onSpeechResultCallback = onResult;
        try {
            if (this.isListening) {
                this.recognition.stop();
            } else {
                this.recognition.start();
            }
        } catch (e) {
            console.error("SpeechRecognition start exception:", e);
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    speakNPC(text, npcName = "Elder Sophia") {
        if (!this.ttsEnabled || !this.synth) return;
        this.synth.cancel(); // Stop any pending speech

        // Clean out parenthetical notes like (The Scholar's Path shines...)
        const spokenText = text.replace(/\([^)]*\)/g, "").trim();
        const utterance = new SpeechSynthesisUtterance(spokenText);

        // Customize voice parameters per NPC
        if (npcName === "Elder Sophia") {
            utterance.pitch = 1.1;
            utterance.rate = 0.92; // Warm, gentle pacing
        } else if (npcName === "Scholar Theron") {
            utterance.pitch = 0.95;
            utterance.rate = 1.05; // Analytical, academic
        } else if (npcName === "Master Kael") {
            utterance.pitch = 0.85;
            utterance.rate = 1.1; // Resolute, commanding
        } else if (npcName === "Guardian Lyra") {
            utterance.pitch = 1.25;
            utterance.rate = 0.88; // Mystical, ethereal
        }

        this.synth.speak(utterance);
    }

    _updateMicUI(active, text) {
        const micBadge = document.getElementById("voice-status-badge");
        const micText = document.getElementById("voice-status-text");
        if (micBadge) {
            micBadge.classList.toggle("listening", active);
        }
        if (micText) {
            micText.textContent = text;
        }
    }
}

window.voiceSystem = new VoiceSystem();
