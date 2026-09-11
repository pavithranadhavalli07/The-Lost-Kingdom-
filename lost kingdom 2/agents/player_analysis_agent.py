import time
from agents.base_agent import BaseAgent

class PlayerAnalysisAgent(BaseAgent):
    """
    Agent 1 — Player Analysis Agent
    Monitors player interactions, submission speed, error streaks, hesitation metrics,
    and interaction velocity. Dispatches enriched analytics to the shared pipeline.
    """
    def __init__(self):
        super().__init__("Player Analysis Agent", "Monitors actions, response timing, error patterns, and velocity")
        self.session_history = []
        self.metadata = {
            "recent_response_time_ms": 0,
            "average_response_time_ms": 4500,
            "consecutive_mistakes": 0,
            "consecutive_correct": 0,
            "hesitation_level": "Normal",
            "interaction_velocity": "Moderate"
        }

    def process(self, event_name, payload, shared_state):
        if event_name == "challenge_submitted":
            return self._analyze_challenge_submission(payload, shared_state)
        elif event_name == "player_moved":
            return self._analyze_movement(payload, shared_state)
        elif event_name == "npc_talked":
            return self._analyze_npc_interaction(payload, shared_state)
        elif event_name == "hint_requested":
            return self._analyze_hint_request(payload, shared_state)
        return None

    def _analyze_challenge_submission(self, payload, shared_state):
        is_correct = payload.get("is_correct", False)
        response_time = payload.get("response_time_ms", 4000)
        topic = payload.get("topic", "General")
        difficulty = payload.get("difficulty", "medium")

        # Benchmark response times per difficulty
        benchmarks = {"easy": 4000, "medium": 7000, "hard": 12000, "expert": 18000}
        expected = benchmarks.get(difficulty.lower(), 6000)

        # Update streaks
        if is_correct:
            self.metadata["consecutive_correct"] += 1
            self.metadata["consecutive_mistakes"] = 0
        else:
            self.metadata["consecutive_mistakes"] += 1
            self.metadata["consecutive_correct"] = 0

        self.metadata["recent_response_time_ms"] = response_time
        self.session_history.append({
            "correct": is_correct,
            "time_ms": response_time,
            "topic": topic,
            "timestamp": time.time()
        })

        # Calculate average response time
        total_times = [item["time_ms"] for item in self.session_history[-10:]]
        avg_time = int(sum(total_times) / len(total_times))
        self.metadata["average_response_time_ms"] = avg_time

        # Calculate Hesitation
        if response_time > expected * 1.6:
            hesitation = "High Hesitation"
        elif response_time < expected * 0.4:
            hesitation = "Rapid / Instinctive"
        else:
            hesitation = "Paced / Normal"
        self.metadata["hesitation_level"] = hesitation

        # Velocity
        if response_time < 3000:
            velocity = "High Velocity"
        elif response_time > 10000:
            velocity = "Low Velocity"
        else:
            velocity = "Moderate Velocity"
        self.metadata["interaction_velocity"] = velocity

        analysis_result = {
            "is_correct": is_correct,
            "consecutive_mistakes": self.metadata["consecutive_mistakes"],
            "consecutive_correct": self.metadata["consecutive_correct"],
            "response_time_ms": response_time,
            "hesitation_level": hesitation,
            "interaction_velocity": velocity,
            "topic": topic,
            "difficulty": difficulty
        }

        action_summary = (
            f"Analyzed {topic} answer: {'Correct' if is_correct else 'Incorrect'} "
            f"in {response_time/1000:.1f}s ({hesitation}, Streak: {self.metadata['consecutive_correct'] if is_correct else -self.metadata['consecutive_mistakes']})"
        )
        self.log_action(action_summary, self.metadata)
        shared_state["player_analysis"] = analysis_result
        return analysis_result

    def _analyze_movement(self, payload, shared_state):
        loc = payload.get("location", "village")
        action_summary = f"Player navigated to {loc.capitalize()}."
        self.log_action(action_summary)
        return {"event": "movement", "location": loc}

    def _analyze_npc_interaction(self, payload, shared_state):
        npc = payload.get("npc", "Elder Sophia")
        action_summary = f"Player initiated dialogue with {npc}."
        self.log_action(action_summary)
        return {"event": "npc_talk", "npc": npc}

    def _analyze_hint_request(self, payload, shared_state):
        self.metadata["hesitation_level"] = "Requested Support"
        action_summary = "Player requested hint assistance."
        self.log_action(action_summary)
        if "player_analysis" in shared_state:
            shared_state["player_analysis"]["hint_used"] = True
        return {"event": "hint_used"}
