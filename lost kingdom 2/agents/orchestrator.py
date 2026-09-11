import datetime
from agents.player_analysis_agent import PlayerAnalysisAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.emotion_agent import EmotionAgent
from agents.challenge_agent import ChallengeAgent
from agents.story_npc_agent import StoryNPCAgent
from services.llm_service import LLMService
from models import db, AgentActivityLog, KnowledgeState, StoryMemory

class MultiAgentOrchestrator:
    """
    Central orchestration engine for the autonomous multi-agent system.
    Manages agent lifecycle, event routing, shared blackboard state,
    database logging, and WebSocket telemetry emission.
    """
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.llm_service = LLMService()

        # Instantiate 5 specialized agents
        self.player_analysis_agent = PlayerAnalysisAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.emotion_agent = EmotionAgent()
        self.challenge_agent = ChallengeAgent(self.llm_service)
        self.story_npc_agent = StoryNPCAgent(self.llm_service)

        self.agents = [
            self.player_analysis_agent,
            self.knowledge_agent,
            self.emotion_agent,
            self.story_npc_agent,
            self.challenge_agent
        ]

        self.shared_blackboard = {
            "player_analysis": {},
            "knowledge_update": {},
            "emotion_state": {"state": "Engaged", "confidence_percent": 70},
            "story_state": {},
            "active_challenge": None
        }

        self.recent_activity_logs = []

    def log_agent_activity(self, player_id, agent_name, action_type, log_message, details=None):
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp_str,
            "agent_name": agent_name,
            "action_type": action_type,
            "log_message": log_message,
            "details": details or {}
        }
        self.recent_activity_logs.append(entry)
        if len(self.recent_activity_logs) > 60:
            self.recent_activity_logs.pop(0)

        # Persist to database if db session is available
        try:
            db_log = AgentActivityLog(
                player_id=player_id or "default_player",
                agent_name=agent_name,
                action_type=action_type,
                log_message=log_message,
                details_json=str(details or {})
            )
            db.session.add(db_log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Emit real-time telemetry if SocketIO is active
        if self.socketio:
            try:
                self.socketio.emit("agent_event_stream", entry, broadcast=True)
            except Exception:
                pass

    def handle_challenge_submission(self, player, payload):
        """
        Full autonomous reactive adaptation cycle:
        1. Player Analysis Agent parses submission speed, hesitation, error streaks
        2. Knowledge Agent updates BKT / Elo topic mastery
        3. Emotion Agent re-estimates affective state (Frustrated, Confused, Bored, etc.)
        4. Challenge Agent dynamically adjusts difficulty level
        5. Story/NPC Agent adapts narrative, checks branch unlocks, prepares dialogue tone
        """
        player_id = player.id

        # 1. Player Analysis
        p_analysis = self.player_analysis_agent.process("challenge_submitted", payload, self.shared_blackboard)
        self.log_agent_activity(
            player_id,
            self.player_analysis_agent.name,
            "Analyze Interaction",
            self.player_analysis_agent.last_action,
            p_analysis
        )

        # 2. Knowledge Agent
        k_update = self.knowledge_agent.process("challenge_submitted", payload, self.shared_blackboard)
        self.log_agent_activity(
            player_id,
            self.knowledge_agent.name,
            "Update Mastery",
            self.knowledge_agent.last_action,
            k_update
        )

        # 3. Emotion Agent
        e_update = self.emotion_agent.process("challenge_submitted", payload, self.shared_blackboard)
        self.log_agent_activity(
            player_id,
            self.emotion_agent.name,
            "Detect Affective State",
            self.emotion_agent.last_action,
            e_update
        )

        # 4. Challenge Agent (Difficulty adaptation)
        self.challenge_agent.process("challenge_submitted", payload, self.shared_blackboard)
        diff_info = self.shared_blackboard.get("difficulty_adaptation", {})
        self.log_agent_activity(
            player_id,
            self.challenge_agent.name,
            "Calibrate Difficulty",
            self.challenge_agent.last_action,
            diff_info
        )

        # 5. Story/NPC Agent
        story_update = self.story_npc_agent.process("challenge_submitted", payload, self.shared_blackboard)
        self.log_agent_activity(
            player_id,
            self.story_npc_agent.name,
            "Narrative Reaction",
            self.story_npc_agent.last_action,
            story_update
        )

        # Prepare next challenge automatically
        next_challenge = self.challenge_agent.generate_next_challenge({
            "topic": payload.get("topic")
        }, self.shared_blackboard)
        self.log_agent_activity(
            player_id,
            self.challenge_agent.name,
            "Generate Challenge",
            self.challenge_agent.last_action,
            {"topic": next_challenge.get("topic"), "difficulty": next_challenge.get("difficulty")}
        )

        # Sync persisted state
        self._sync_player_memory(player)

        response_payload = {
            "evaluation": {
                "is_correct": payload.get("is_correct"),
                "answer": payload.get("answer"),
                "explanation": payload.get("explanation")
            },
            "player_analysis": p_analysis,
            "knowledge_update": k_update,
            "emotion_state": e_update,
            "difficulty_adaptation": diff_info,
            "story_state": story_update,
            "next_challenge": next_challenge
        }

        # Broadcast state update to clients
        if self.socketio:
            try:
                self.socketio.emit("agent_state_update", self.get_dashboard_snapshot(player), broadcast=True)
            except Exception:
                pass

        return response_payload

    def handle_npc_interaction(self, player, npc_name, recent_event=None):
        """Processes player talking to an NPC and yields adaptive dialogue."""
        payload = {"npc": npc_name, "recent_event": recent_event}
        self.player_analysis_agent.process("npc_talked", payload, self.shared_blackboard)
        
        dialogue_result = self.story_npc_agent.generate_dialogue_for_npc(payload, self.shared_blackboard)
        self.log_agent_activity(
            player.id,
            self.story_npc_agent.name,
            "Generate Adaptive Dialogue",
            self.story_npc_agent.last_action,
            {"npc": npc_name, "tone": dialogue_result.get("emotion_tone")}
        )
        return dialogue_result

    def handle_hint_request(self, player):
        """Player clicked 'Need a Hint'"""
        self.player_analysis_agent.process("hint_requested", {}, self.shared_blackboard)
        e_update = self.emotion_agent.process("hint_requested", {}, self.shared_blackboard)
        self.log_agent_activity(
            player.id,
            self.emotion_agent.name,
            "Register Scaffold Request",
            self.emotion_agent.last_action,
            e_update
        )
        return {"emotion_state": e_update}

    def _sync_player_memory(self, player):
        """Persists knowledge scores and story progress to SQLite database."""
        try:
            # Sync Knowledge records
            for t_info in self.knowledge_agent.get_topic_breakdown():
                topic_name = t_info["topic"]
                k_rec = KnowledgeState.query.filter_by(player_id=player.id, topic=topic_name).first()
                if not k_rec:
                    k_rec = KnowledgeState(player_id=player.id, topic=topic_name)
                    db.session.add(k_rec)
                k_rec.mastery = t_info["mastery"]
                k_rec.attempts = t_info["attempts"]
                k_rec.correct_answers = t_info["correct"]
                k_rec.last_difficulty = self.challenge_agent.current_difficulty

            # Sync Story memory
            story_mem = StoryMemory.query.filter_by(player_id=player.id).first()
            if not story_mem:
                story_mem = StoryMemory(player_id=player.id)
                db.session.add(story_mem)
            story_mem.active_branch = self.story_npc_agent.active_branch
            story_mem.set_npc_affinities(self.story_npc_agent.npc_memories)

            # Update player object
            player.current_branch = self.story_npc_agent.active_branch
            player.xp += 10
            if player.xp >= player.level * 50:
                player.level += 1
                player.xp = 0

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[Orchestrator] Memory sync warning: {e}")

    def get_dashboard_snapshot(self, player=None):
        """Produces comprehensive real-time telemetry for the Agent Dashboard."""
        return {
            "player": {
                "id": player.id if player else "seeker_1",
                "username": player.username if player else "Seeker",
                "current_location": player.current_location if player else "village",
                "current_branch": self.story_npc_agent.active_branch,
                "branch_title": self.story_npc_agent.BRANCHES[self.story_npc_agent.active_branch]["title"],
                "level": player.level if player else 1,
                "xp": player.xp if player else 0,
                "overall_mastery": self.knowledge_agent.metadata["overall_mastery"],
                "current_difficulty": self.challenge_agent.current_difficulty,
                "emotion_state": self.emotion_agent.current_state,
                "confidence_percent": self.emotion_agent.metadata["confidence_percent"]
            },
            "agents": [a.to_dict() for a in self.agents],
            "topics": self.knowledge_agent.get_topic_breakdown(),
            "branches": self.story_npc_agent.BRANCHES,
            "recent_logs": self.recent_activity_logs[-25:],
            "active_quest": self.story_npc_agent.active_quest
        }
