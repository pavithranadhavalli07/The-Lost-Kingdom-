from agents.base_agent import BaseAgent

class KnowledgeAgent(BaseAgent):
    """
    Agent 2 — Learning/Knowledge Agent
    Maintains multi-topic mastery (Algebra, Geometry, Logic, Science, Cryptography).
    Applies Bayesian Knowledge Tracing & Elo updates to calculate learning progress,
    identifies strong vs weak concepts, and recommends difficulty targets.
    """
    DEFAULT_TOPICS = ["Algebra", "Geometry", "Logic", "Science", "Cryptography"]

    def __init__(self):
        super().__init__("Knowledge Agent", "Maintains topic mastery, knowledge tracing, and weak/strong concepts")
        self.topic_mastery = {topic: 0.35 for topic in self.DEFAULT_TOPICS}
        self.topic_attempts = {topic: 0 for topic in self.DEFAULT_TOPICS}
        self.topic_correct = {topic: 0 for topic in self.DEFAULT_TOPICS}
        self.recent_mistakes = []
        self.metadata = {
            "overall_mastery": 35,
            "strongest_topic": "Algebra",
            "weakest_topic": "Cryptography",
            "recommended_difficulty": "easy"
        }

    def load_from_db(self, knowledge_records):
        """Populate agent state from persisted database records."""
        for rec in knowledge_records:
            t = rec.topic
            self.topic_mastery[t] = rec.mastery
            self.topic_attempts[t] = rec.attempts
            self.topic_correct[t] = rec.correct_answers
        self._recalculate_metadata()

    def process(self, event_name, payload, shared_state):
        if event_name == "challenge_submitted":
            return self._update_knowledge(payload, shared_state)
        return None

    def _update_knowledge(self, payload, shared_state):
        analysis = shared_state.get("player_analysis", {})
        topic = payload.get("topic", "Algebra")
        difficulty = payload.get("difficulty", "medium").lower()
        is_correct = payload.get("is_correct", False)
        question_text = payload.get("question", "")

        if topic not in self.topic_mastery:
            self.topic_mastery[topic] = 0.30
            self.topic_attempts[topic] = 0
            self.topic_correct[topic] = 0

        current_m = self.topic_mastery[topic]
        self.topic_attempts[topic] += 1
        if is_correct:
            self.topic_correct[topic] += 1

        # Difficulty weight multiplier
        diff_weights = {"easy": 0.05, "medium": 0.09, "hard": 0.14, "expert": 0.20}
        weight = diff_weights.get(difficulty, 0.08)

        # Elo / BKT style adaptive mastery adjustment
        if is_correct:
            # Bonus if fast
            fast_bonus = 0.02 if analysis.get("interaction_velocity") == "High Velocity" else 0.0
            new_m = min(1.0, current_m + weight * (1.0 - current_m) + fast_bonus)
        else:
            # Penalty scales with mistake streak
            streak_penalty = 0.02 * min(3, analysis.get("consecutive_mistakes", 1))
            new_m = max(0.10, current_m - (weight * 0.9 + streak_penalty))
            self.recent_mistakes.append({
                "topic": topic,
                "question": question_text[:80],
                "difficulty": difficulty
            })
            if len(self.recent_mistakes) > 6:
                self.recent_mistakes.pop(0)

        self.topic_mastery[topic] = round(new_m, 3)
        self._recalculate_metadata()

        action_summary = (
            f"Updated {topic} mastery from {int(current_m*100)}% to {int(new_m*100)}% "
            f"({'Mastered concept' if is_correct else 'Identified knowledge gap'}). "
            f"Recommended difficulty: {self.metadata['recommended_difficulty'].capitalize()}."
        )
        self.log_action(action_summary, self.metadata)

        result = {
            "topic": topic,
            "new_mastery": self.topic_mastery[topic],
            "mastery_percent": int(self.topic_mastery[topic] * 100),
            "overall_mastery": self.metadata["overall_mastery"],
            "strongest_topic": self.metadata["strongest_topic"],
            "weakest_topic": self.metadata["weakest_topic"],
            "recommended_difficulty": self.metadata["recommended_difficulty"]
        }
        shared_state["knowledge_update"] = result
        return result

    def _recalculate_metadata(self):
        scores = self.topic_mastery
        avg_score = sum(scores.values()) / max(1, len(scores))
        self.metadata["overall_mastery"] = int(round(avg_score * 100))
        
        sorted_topics = sorted(scores.items(), key=lambda x: x[1])
        self.metadata["weakest_topic"] = sorted_topics[0][0]
        self.metadata["strongest_topic"] = sorted_topics[-1][0]

        # Recommendation logic
        if avg_score < 0.38:
            rec_diff = "easy"
        elif avg_score < 0.65:
            rec_diff = "medium"
        elif avg_score < 0.85:
            rec_diff = "hard"
        else:
            rec_diff = "expert"
        self.metadata["recommended_difficulty"] = rec_diff

    def get_topic_breakdown(self):
        return [
            {
                "topic": t,
                "mastery": round(self.topic_mastery[t], 2),
                "mastery_percent": int(round(self.topic_mastery[t] * 100)),
                "attempts": self.topic_attempts.get(t, 0),
                "correct": self.topic_correct.get(t, 0)
            }
            for t in self.DEFAULT_TOPICS
        ]
