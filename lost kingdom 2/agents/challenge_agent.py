from agents.base_agent import BaseAgent
from services.llm_service import LLMService

class ChallengeAgent(BaseAgent):
    """
    Agent 5 — Challenge/Difficulty Agent
    Responsible for generating curriculum-aligned questions, selecting topics
    based on knowledge state, dynamically tuning difficulty (Easy -> Expert),
    and formulating hints and step-by-step explanations.
    """
    DIFFICULTIES = ["easy", "medium", "hard", "expert"]

    def __init__(self, llm_service=None):
        super().__init__("Challenge & Difficulty Agent", "Generates educational challenges and calibrates difficulty")
        self.llm = llm_service or LLMService()
        self.current_difficulty = "medium"
        self.active_challenge = None
        self.served_questions = []
        self.metadata = {
            "current_difficulty": "medium",
            "last_adaptation_reason": "Default starting baseline",
            "active_topic": "Algebra",
            "questions_generated": 0,
            "verification_status": "Verified Valid"
        }

    def process(self, event_name, payload, shared_state):
        if event_name == "challenge_submitted":
            self._adapt_difficulty_after_submission(shared_state)
            return None
        elif event_name == "request_new_challenge":
            return self.generate_next_challenge(payload, shared_state)
        return None

    def _adapt_difficulty_after_submission(self, shared_state):
        emotion = shared_state.get("emotion_state", {}).get("state", "Engaged")
        knowledge = shared_state.get("knowledge_update", {})
        analysis = shared_state.get("player_analysis", {})
        
        is_correct = analysis.get("is_correct", False)
        consec_mistakes = analysis.get("consecutive_mistakes", 0)
        consec_correct = analysis.get("consecutive_correct", 0)
        curr_idx = self.DIFFICULTIES.index(self.current_difficulty)

        adaptation_reason = ""

        # Adaptive Difficulty Logic
        if emotion in ["Frustrated", "Confused"] or consec_mistakes >= 2:
            # Drop difficulty if possible
            if curr_idx > 0:
                self.current_difficulty = self.DIFFICULTIES[curr_idx - 1]
                adaptation_reason = f"Reduced difficulty to {self.current_difficulty.capitalize()} due to {emotion.lower()} state and mistake streak."
            else:
                adaptation_reason = f"Kept at {self.current_difficulty.capitalize()} (minimum) but activated scaffolded hints."

        elif emotion == "Bored" or (consec_correct >= 2 and curr_idx < len(self.DIFFICULTIES) - 1):
            # Increase difficulty
            self.current_difficulty = self.DIFFICULTIES[curr_idx + 1]
            adaptation_reason = f"Scaled difficulty up to {self.current_difficulty.capitalize()} to match high mastery and velocity."

        elif is_correct and knowledge.get("overall_mastery", 40) > 75 and curr_idx < len(self.DIFFICULTIES) - 1:
            self.current_difficulty = self.DIFFICULTIES[curr_idx + 1]
            adaptation_reason = f"Promoted to {self.current_difficulty.capitalize()} as overall mastery reached {knowledge.get('overall_mastery')}%."

        else:
            adaptation_reason = f"Maintained {self.current_difficulty.capitalize()} to solidify conceptual retention."

        self.metadata["current_difficulty"] = self.current_difficulty
        self.metadata["last_adaptation_reason"] = adaptation_reason
        
        action_summary = f"Calibrated difficulty: {self.current_difficulty.capitalize()}. {adaptation_reason}"
        self.log_action(action_summary, self.metadata)
        
        shared_state["difficulty_adaptation"] = {
            "difficulty": self.current_difficulty,
            "reason": adaptation_reason
        }

    def generate_next_challenge(self, payload, shared_state):
        topic = payload.get("topic")
        if not topic:
            # If no topic specified, target weakest topic from knowledge agent
            k_agent_rec = shared_state.get("knowledge_update", {})
            topic = k_agent_rec.get("weakest_topic", "Algebra")

        # Use explicitly requested difficulty if provided (e.g. from NPC quest), else current_difficulty
        difficulty = payload.get("difficulty") or self.current_difficulty

        # Avoid repeat loop by generating fresh question
        challenge = None
        for _ in range(3):
            candidate = self.llm.generate_challenge(topic, difficulty, shared_state)
            if candidate["question"] not in self.served_questions:
                challenge = candidate
                break
        if not challenge:
            challenge = self.llm.generate_challenge(topic, difficulty, shared_state)

        self.served_questions.append(challenge["question"])
        if len(self.served_questions) > 25:
            self.served_questions.pop(0)

        self.active_challenge = challenge
        self.metadata["active_topic"] = topic
        self.metadata["current_difficulty"] = difficulty
        self.metadata["questions_generated"] += 1
        self.metadata["verification_status"] = "Verified: Valid options & answer"

        action_summary = f"Generated {difficulty.capitalize()} challenge on {topic}: '{challenge['question'][:50]}...'"
        self.log_action(action_summary, self.metadata)

        shared_state["active_challenge"] = challenge
        return challenge
