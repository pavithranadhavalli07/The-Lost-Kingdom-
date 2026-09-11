from agents.base_agent import BaseAgent

class EmotionAgent(BaseAgent):
    """
    Agent 3 — Emotion/Engagement Agent
    Analyzes interaction heuristics (error streaks, response delay, rapid clicking,
    hesitation) to estimate gameplay engagement and affective states:
    [Engaged, Confused, Frustrated, Bored, Confident].
    """
    STATES = ["Engaged", "Confused", "Frustrated", "Bored", "Confident"]

    def __init__(self):
        super().__init__("Emotion Agent", "Estimates real-time engagement and affective gameplay states")
        self.current_state = "Engaged"
        self.confidence_score = 0.70
        self.state_history = ["Engaged"]
        self.metadata = {
            "current_state": "Engaged",
            "confidence_percent": 70,
            "detected_triggers": ["Initial session startup", "Exploration pace normal"],
            "intervention_recommended": False
        }

    def process(self, event_name, payload, shared_state):
        if event_name == "challenge_submitted":
            return self._evaluate_affective_state(payload, shared_state)
        elif event_name == "hint_requested":
            return self._evaluate_hint_request(payload, shared_state)
        return None

    def _evaluate_affective_state(self, payload, shared_state):
        analysis = shared_state.get("player_analysis", {})
        consec_mistakes = analysis.get("consecutive_mistakes", 0)
        consec_correct = analysis.get("consecutive_correct", 0)
        response_time = analysis.get("response_time_ms", 4000)
        hesitation = analysis.get("hesitation_level", "Normal")
        velocity = analysis.get("interaction_velocity", "Moderate")

        triggers = []
        old_state = self.current_state

        # Decision Tree for Gameplay Affective State
        if consec_mistakes >= 2:
            if response_time > 8000 or hesitation == "High Hesitation":
                # Multiple mistakes + high hesitation -> Confused
                new_state = "Confused"
                conf = min(0.95, 0.65 + consec_mistakes * 0.10)
                triggers.append(f"{consec_mistakes} consecutive errors with prolonged hesitation")
            else:
                # Multiple mistakes with fast impulsive clicks -> Frustrated
                new_state = "Frustrated"
                conf = min(0.95, 0.70 + consec_mistakes * 0.10)
                triggers.append(f"{consec_mistakes} repeated failures with rapid attempts")
            intervention = True

        elif consec_correct >= 2:
            if response_time < 3500 and velocity == "High Velocity":
                # Blazing through easy questions -> Bored (needs harder challenge)
                new_state = "Bored"
                conf = min(0.90, 0.60 + consec_correct * 0.08)
                triggers.append(f"{consec_correct} correct answers at high velocity (potential under-stimulation)")
                intervention = False
            else:
                # Normal pace + correct -> Confident
                new_state = "Confident"
                conf = min(0.95, 0.75 + consec_correct * 0.05)
                triggers.append(f"{consec_correct} correct answers with steady focus")
                intervention = False

        else:
            # Single success/error, moderate pacing -> Engaged
            new_state = "Engaged"
            conf = 0.80
            triggers.append("Balanced interaction pace and active problem-solving")
            intervention = False

        self.current_state = new_state
        self.confidence_score = conf
        self.state_history.append(new_state)
        if len(self.state_history) > 10:
            self.state_history.pop(0)

        self.metadata["current_state"] = new_state
        self.metadata["confidence_percent"] = int(round(conf * 100))
        self.metadata["detected_triggers"] = triggers
        self.metadata["intervention_recommended"] = intervention

        action_summary = (
            f"Detected affective state: {new_state} ({int(conf*100)}% confidence). "
            f"Triggers: {', '.join(triggers)}."
        )
        self.log_action(action_summary, self.metadata)

        result = {
            "state": new_state,
            "confidence_percent": int(round(conf * 100)),
            "triggers": triggers,
            "intervention_recommended": intervention
        }
        shared_state["emotion_state"] = result
        return result

    def _evaluate_hint_request(self, payload, shared_state):
        self.current_state = "Confused"
        self.confidence_score = 0.85
        self.metadata["current_state"] = "Confused"
        self.metadata["confidence_percent"] = 85
        self.metadata["detected_triggers"] = ["Player explicitly requested conceptual scaffold / hint"]
        self.metadata["intervention_recommended"] = True
        self.log_action("Detected Confusion via active hint request.", self.metadata)
        
        result = {
            "state": "Confused",
            "confidence_percent": 85,
            "triggers": ["Player requested hint"],
            "intervention_recommended": True
        }
        shared_state["emotion_state"] = result
        return result
