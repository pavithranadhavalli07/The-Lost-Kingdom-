from agents.base_agent import BaseAgent
from services.llm_service import LLMService

class StoryNPCAgent(BaseAgent):
    """
    Agent 4 — Story & NPC Agent
    Controls narrative branching, quest progression, dynamic NPC dialogue generation,
    and world events based on player knowledge mastery and emotional state.
    """
    BRANCHES = {
        "prologue": {
            "title": "Prologue: Awakening in Oakhaven",
            "description": "Seek the wisdom of Elder Sophia to begin your journey through the realm.",
            "unlocked": True
        },
        "scholar": {
            "title": "The Scholar's Path (Alexandrian Archive)",
            "description": "Dedicate yourself to decoding lost theorems, geometric proofs, and historic codices.",
            "unlocked": False
        },
        "vanguard": {
            "title": "The Vanguard's Trial (Warrior's Arena)",
            "description": "Apply strategic mechanics, velocity equations, and tactical positioning under pressure.",
            "unlocked": False
        },
        "mystic": {
            "title": "The Mystic's Synthesis (Sky Temple Sanctum)",
            "description": "Harmonize logic runes, cryptographic ciphers, and restore celestial equilibrium.",
            "unlocked": False
        }
    }

    def __init__(self, llm_service=None):
        super().__init__("Story & NPC Agent", "Evolves narrative branches, orchestrates quests, and generates adaptive dialogue")
        self.llm = llm_service or LLMService()
        self.active_branch = "prologue"
        self.active_quest = {
            "id": "quest_oakhaven_init",
            "title": "Awakening of the Seeker",
            "giver": "Elder Sophia",
            "objective": "Speak with Elder Sophia in the Village and solve her introductory challenge.",
            "status": "in_progress"
        }
        self.completed_quests = []
        self.npc_memories = {
            "Elder Sophia": {"interactions": 0, "trust": 50, "last_topic": None},
            "Scholar Theron": {"interactions": 0, "trust": 40, "last_topic": None},
            "Master Kael": {"interactions": 0, "trust": 40, "last_topic": None},
            "Guardian Lyra": {"interactions": 0, "trust": 30, "last_topic": None}
        }
        self.metadata = {
            "active_branch": "prologue",
            "branch_title": self.BRANCHES["prologue"]["title"],
            "active_quest_title": self.active_quest["title"],
            "unlocked_branches": ["prologue"],
            "latest_dialogue": "Welcome to Oakhaven, seeker."
        }

    def process(self, event_name, payload, shared_state):
        if event_name == "challenge_submitted":
            return self._react_to_challenge(payload, shared_state)
        elif event_name == "npc_talked":
            return self.generate_dialogue_for_npc(payload, shared_state)
        elif event_name == "switch_branch":
            return self._switch_branch(payload.get("branch", "scholar"), shared_state)
        return None

    def _react_to_challenge(self, payload, shared_state):
        is_correct = payload.get("is_correct", False)
        topic = payload.get("topic", "General")
        emotion = shared_state.get("emotion_state", {}).get("state", "Engaged")
        knowledge = shared_state.get("knowledge_update", {})
        overall_mastery = knowledge.get("overall_mastery", 35)

        # Check Branch Progression Triggers
        branch_event = None
        if overall_mastery >= 45 and "scholar" not in self.metadata["unlocked_branches"]:
            self.metadata["unlocked_branches"].append("scholar")
            self.BRANCHES["scholar"]["unlocked"] = True
            branch_event = "Unlocked Story Branch: The Scholar's Path (Library)"
            self.active_branch = "scholar"
            self.active_quest = {
                "id": "quest_scholar_codex",
                "title": "The Alexandrian Codex",
                "giver": "Scholar Theron",
                "objective": "Travel to the Grand Library and assist Scholar Theron with ancient theorem calculations.",
                "status": "in_progress"
            }

        elif overall_mastery >= 65 and "vanguard" not in self.metadata["unlocked_branches"]:
            self.metadata["unlocked_branches"].append("vanguard")
            self.BRANCHES["vanguard"]["unlocked"] = True
            branch_event = "Unlocked Story Branch: The Vanguard's Trial (Arena)"
            self.active_branch = "vanguard"
            self.active_quest = {
                "id": "quest_vanguard_tactics",
                "title": "Trial of Ballistics & Angles",
                "giver": "Master Kael",
                "objective": "Visit Master Kael in the Training Arena to solve tactical physics problems.",
                "status": "in_progress"
            }

        elif overall_mastery >= 80 and "mystic" not in self.metadata["unlocked_branches"]:
            self.metadata["unlocked_branches"].append("mystic")
            self.BRANCHES["mystic"]["unlocked"] = True
            branch_event = "Unlocked Story Branch: The Mystic's Synthesis (Sky Temple)"
            self.active_branch = "mystic"
            self.active_quest = {
                "id": "quest_mystic_crystals",
                "title": "Celestial Harmonic Resonance",
                "giver": "Guardian Lyra",
                "objective": "Ascend to the Ancient Sky Temple and align the logic runes with Guardian Lyra.",
                "status": "in_progress"
            }

        self.metadata["active_branch"] = self.active_branch
        self.metadata["branch_title"] = self.BRANCHES[self.active_branch]["title"]
        self.metadata["active_quest_title"] = self.active_quest["title"]

        summary = (
            f"Narrative reacted to {topic} outcome ({'Mastery gained' if is_correct else 'Scaffolding needed'}). "
            f"Active branch: {self.active_branch.capitalize()}."
        )
        if branch_event:
            summary += f" [EVENT: {branch_event}]"

        self.log_action(summary, self.metadata)
        
        shared_state["story_state"] = {
            "active_branch": self.active_branch,
            "branch_title": self.BRANCHES[self.active_branch]["title"],
            "active_quest": self.active_quest,
            "branch_event": branch_event,
            "unlocked_branches": self.metadata["unlocked_branches"]
        }
        return shared_state["story_state"]

    def generate_dialogue_for_npc(self, payload, shared_state):
        npc_name = payload.get("npc", "Elder Sophia")
        emotion = shared_state.get("emotion_state", {}).get("state", "Engaged")
        player_state = shared_state.get("knowledge_update", {"mastery_percent": 50})
        
        # Track memory
        if npc_name in self.npc_memories:
            self.npc_memories[npc_name]["interactions"] += 1
            if emotion == "Confident":
                self.npc_memories[npc_name]["trust"] = min(100, self.npc_memories[npc_name]["trust"] + 5)
            elif emotion == "Frustrated":
                self.npc_memories[npc_name]["trust"] = min(100, self.npc_memories[npc_name]["trust"] + 2)

        # Generate contextual dialogue via LLM or procedural matrix
        dialogue = self.llm.generate_npc_dialogue(
            npc_name=npc_name,
            player_state=player_state,
            emotion_state=emotion,
            branch_name=self.active_branch,
            recent_event=payload.get("recent_event")
        )

        self.metadata["latest_dialogue"] = dialogue
        action_summary = f"Generated adaptive dialogue for {npc_name} (Tone calibrated for {emotion})."
        self.log_action(action_summary, self.metadata)

        response = {
            "npc": npc_name,
            "dialogue": dialogue,
            "emotion_tone": emotion,
            "active_branch": self.active_branch,
            "quest": self.active_quest,
            "npc_memory": self.npc_memories.get(npc_name, {})
        }
        shared_state["latest_dialogue"] = response
        return response

    def _switch_branch(self, new_branch, shared_state):
        if new_branch in self.BRANCHES:
            self.active_branch = new_branch
            self.metadata["active_branch"] = new_branch
            self.metadata["branch_title"] = self.BRANCHES[new_branch]["title"]
            if new_branch not in self.metadata["unlocked_branches"]:
                self.metadata["unlocked_branches"].append(new_branch)
            self.log_action(f"Player transitioned to branch: {new_branch.capitalize()}", self.metadata)
            return {"active_branch": new_branch}
        return None
