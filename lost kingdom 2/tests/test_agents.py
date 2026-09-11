import unittest
import json
from app import create_app
from models import db, Player, KnowledgeState, ChallengeLog

class TestMultiAgentGame(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_player_init_and_persistence(self):
        """Verify player creation, default topics, and return session retrieval."""
        res = self.client.post("/api/player/init", json={"player_id": "test_seeker_1", "username": "Arthur"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["player"]["username"], "Arthur")
        self.assertFalse(data["is_returning_player"])

        # Check knowledge topics initialized
        topics = [t["topic"] for t in data["dashboard"]["topics"]]
        self.assertIn("Algebra", topics)
        self.assertIn("Geometry", topics)
        self.assertIn("Logic", topics)

    def test_npc_adaptive_dialogue(self):
        """Verify dynamic dialogue generation for all 4 NPCs."""
        for npc in ["Elder Sophia", "Scholar Theron", "Master Kael", "Guardian Lyra"]:
            res = self.client.post("/api/npc/talk", json={"player_id": "test_seeker_1", "npc_name": npc})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["status"], "success")
            self.assertIn("dialogue", data["interaction"])
            self.assertTrue(len(data["interaction"]["dialogue"]) > 10)

    def test_challenge_generation_and_validation(self):
        """Verify challenge generation and math validity."""
        res = self.client.get("/api/challenge/get?topic=Algebra&difficulty=easy")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        c = data["challenge"]
        self.assertEqual(c["topic"], "Algebra")
        self.assertEqual(c["difficulty"], "easy")
        self.assertEqual(len(c["options"]), 4)
        self.assertIn(str(c["answer"]), [str(opt) for opt in c["options"]])

    def test_adaptive_loop_frustration_and_difficulty_drop(self):
        """
        Verify the demonstration scenario:
        Mistake streak + slow response -> Frustrated emotion -> Difficulty reduced to Easy.
        """
        # Init player
        self.client.post("/api/player/init", json={"player_id": "test_seeker_2"})

        # Submit 1st wrong answer
        self.client.post("/api/challenge/submit", json={
            "player_id": "test_seeker_2",
            "question": "Solve 2x + 4 = 10",
            "topic": "Algebra",
            "difficulty": "medium",
            "player_answer": "99",
            "correct_answer": "3",
            "response_time_ms": 11000
        })

        # Submit 2nd wrong answer (Streak of 2 mistakes with hesitation)
        res = self.client.post("/api/challenge/submit", json={
            "player_id": "test_seeker_2",
            "question": "Solve 3x + 3 = 12",
            "topic": "Algebra",
            "difficulty": "medium",
            "player_answer": "99",
            "correct_answer": "3",
            "response_time_ms": 9500
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        res_data = data["result"]

        # 1. Player Analysis Agent tracked streak
        self.assertEqual(res_data["player_analysis"]["consecutive_mistakes"], 2)

        # 2. Emotion Agent detected Frustrated or Confused
        self.assertIn(res_data["emotion_state"]["state"], ["Frustrated", "Confused"])

        # 3. Challenge Agent reduced difficulty
        self.assertEqual(res_data["difficulty_adaptation"]["difficulty"], "easy")

    def test_mastery_streak_and_promotion(self):
        """
        Verify high accuracy -> Confident state -> difficulty promotion.
        """
        self.client.post("/api/player/init", json={"player_id": "test_seeker_3"})

        # Submit 1st correct fast answer
        self.client.post("/api/challenge/submit", json={
            "player_id": "test_seeker_3",
            "question": "Solve x + 2 = 5",
            "topic": "Algebra",
            "difficulty": "easy",
            "player_answer": "3",
            "correct_answer": "3",
            "response_time_ms": 1800
        })

        # Submit 2nd correct fast answer
        res = self.client.post("/api/challenge/submit", json={
            "player_id": "test_seeker_3",
            "question": "Solve 2x = 8",
            "topic": "Algebra",
            "difficulty": "easy",
            "player_answer": "4",
            "correct_answer": "4",
            "response_time_ms": 1900
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        res_data = data["result"]

        self.assertIn(res_data["emotion_state"]["state"], ["Confident", "Bored"])
        self.assertIn(res_data["difficulty_adaptation"]["difficulty"], ["medium", "hard"])

    def test_evaluator_simulation_endpoint(self):
        """Verify the simulation shortcuts used by evaluators."""
        res = self.client.post("/api/simulate/scenario", json={
            "player_id": "test_seeker_4",
            "scenario": "frustration_streak"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn(data["dashboard"]["player"]["emotion_state"], ["Frustrated", "Confused"])

if __name__ == "__main__":
    unittest.main()
