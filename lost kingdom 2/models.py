import datetime
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(80), nullable=False, default="Seeker")
    current_location = db.Column(db.String(64), default="village")
    current_branch = db.Column(db.String(64), default="prologue")  # prologue, scholar, vanguard, mystic
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    knowledge_states = db.relationship("KnowledgeState", backref="player", lazy=True, cascade="all, delete-orphan")
    challenge_logs = db.relationship("ChallengeLog", backref="player", lazy=True, cascade="all, delete-orphan")
    story_memory = db.relationship("StoryMemory", backref="player", uselist=False, cascade="all, delete-orphan")
    agent_logs = db.relationship("AgentActivityLog", backref="player", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "current_location": self.current_location,
            "current_branch": self.current_branch,
            "xp": self.xp,
            "level": self.level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class KnowledgeState(db.Model):
    __tablename__ = "knowledge_states"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(64), db.ForeignKey("players.id"), nullable=False)
    topic = db.Column(db.String(64), nullable=False)  # e.g., Algebra, Geometry, Logic, Science, Cryptography
    mastery = db.Column(db.Float, default=0.30)  # 0.0 to 1.0
    attempts = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_difficulty = db.Column(db.String(32), default="easy")
    recent_mistakes_json = db.Column(db.Text, default="[]")
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def get_recent_mistakes(self):
        try:
            return json.loads(self.recent_mistakes_json or "[]")
        except Exception:
            return []

    def set_recent_mistakes(self, mistakes):
        self.recent_mistakes_json = json.dumps(mistakes[-5:])  # keep last 5 mistakes

    def to_dict(self):
        return {
            "topic": self.topic,
            "mastery": round(self.mastery, 2),
            "mastery_percent": int(round(self.mastery * 100)),
            "attempts": self.attempts,
            "correct_answers": self.correct_answers,
            "streak": self.streak,
            "last_difficulty": self.last_difficulty,
            "recent_mistakes": self.get_recent_mistakes()
        }


class StoryMemory(db.Model):
    __tablename__ = "story_memories"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(64), db.ForeignKey("players.id"), nullable=False, unique=True)
    active_branch = db.Column(db.String(64), default="prologue")
    completed_quests_json = db.Column(db.Text, default="[]")
    npc_affinities_json = db.Column(db.Text, default="{}")
    choices_history_json = db.Column(db.Text, default="[]")
    narrative_summary = db.Column(db.Text, default="The seeker has arrived at the Village of Oakhaven.")
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def get_completed_quests(self):
        try:
            return json.loads(self.completed_quests_json or "[]")
        except Exception:
            return []

    def get_npc_affinities(self):
        try:
            return json.loads(self.npc_affinities_json or "{}")
        except Exception:
            return {}

    def get_choices_history(self):
        try:
            return json.loads(self.choices_history_json or "[]")
        except Exception:
            return []

    def set_completed_quests(self, quests):
        self.completed_quests_json = json.dumps(quests)

    def set_npc_affinities(self, affinities):
        self.npc_affinities_json = json.dumps(affinities)

    def add_choice(self, choice_entry):
        history = self.get_choices_history()
        history.append(choice_entry)
        self.choices_history_json = json.dumps(history)

    def to_dict(self):
        return {
            "active_branch": self.active_branch,
            "completed_quests": self.get_completed_quests(),
            "npc_affinities": self.get_npc_affinities(),
            "choices_history": self.get_choices_history(),
            "narrative_summary": self.narrative_summary
        }


class ChallengeLog(db.Model):
    __tablename__ = "challenge_logs"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(64), db.ForeignKey("players.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(64), nullable=False)
    difficulty = db.Column(db.String(32), nullable=False)
    player_answer = db.Column(db.String(256), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    response_time_ms = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "player_answer": self.player_answer,
            "is_correct": self.is_correct,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class AgentActivityLog(db.Model):
    __tablename__ = "agent_activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(64), db.ForeignKey("players.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    agent_name = db.Column(db.String(64), nullable=False)
    action_type = db.Column(db.String(64), nullable=False)
    details_json = db.Column(db.Text, default="{}")
    log_message = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%H:%M:%S"),
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "log_message": self.log_message
        }
