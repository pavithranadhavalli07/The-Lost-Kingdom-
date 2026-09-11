import uuid
import datetime
from flask import Blueprint, request, jsonify, current_app
from models import db, Player, KnowledgeState, StoryMemory, ChallengeLog

api_bp = Blueprint("api", __name__, url_prefix="/api")

def get_or_create_player(player_id=None, username="Seeker"):
    if not player_id:
        player_id = f"player_{uuid.uuid4().hex[:8]}"
    
    player = Player.query.filter_by(id=player_id).first()
    if not player:
        player = Player(id=player_id, username=username or "Seeker", current_location="village")
        db.session.add(player)
        
        # Init default knowledge states for all 5 topics
        for topic in ["Algebra", "Geometry", "Logic", "Science", "Cryptography"]:
            ks = KnowledgeState(player_id=player.id, topic=topic, mastery=0.35)
            db.session.add(ks)
            
        story_mem = StoryMemory(
            player_id=player.id,
            active_branch="prologue",
            narrative_summary="The seeker has arrived at the Village of Oakhaven."
        )
        db.session.add(story_mem)
        db.session.commit()
    return player

@api_bp.route("/player/init", methods=["POST"])
def init_player():
    orchestrator = current_app.orchestrator
    data = request.get_json() or {}
    player_id = data.get("player_id")
    username = data.get("username", "Seeker")
    
    player = get_or_create_player(player_id, username)
    
    # Hydrate knowledge agent from SQLite memory
    k_records = KnowledgeState.query.filter_by(player_id=player.id).all()
    orchestrator.knowledge_agent.load_from_db(k_records)
    
    # Hydrate story memory
    sm = StoryMemory.query.filter_by(player_id=player.id).first()
    if sm:
        orchestrator.story_npc_agent.active_branch = sm.active_branch
        orchestrator.story_npc_agent.npc_memories = sm.get_npc_affinities()

    # Log session continuation or initialization
    is_returning = len(player.challenge_logs) > 0
    log_msg = f"Player {player.username} {'resumed previous session' if is_returning else 'embarked on new quest'}."
    orchestrator.log_agent_activity(
        player.id,
        orchestrator.player_analysis_agent.name,
        "Session Init",
        log_msg,
        {"is_returning": is_returning, "total_previous_challenges": len(player.challenge_logs)}
    )

    return jsonify({
        "status": "success",
        "player": player.to_dict(),
        "is_returning_player": is_returning,
        "dashboard": orchestrator.get_dashboard_snapshot(player)
    })

@api_bp.route("/player/move", methods=["POST"])
def move_player():
    orchestrator = current_app.orchestrator
    data = request.get_json() or {}
    player_id = data.get("player_id")
    location = data.get("location", "village")
    
    player = get_or_create_player(player_id)
    player.current_location = location
    db.session.commit()
    
    orchestrator.player_analysis_agent.process("player_moved", {"location": location}, orchestrator.shared_blackboard)
    orchestrator.log_agent_activity(
        player.id,
        orchestrator.player_analysis_agent.name,
        "Navigation",
        f"Player entered {location.capitalize()}."
    )
    return jsonify({"status": "success", "current_location": location})

@api_bp.route("/npc/talk", methods=["POST"])
def talk_npc():
    orchestrator = current_app.orchestrator
    data = request.get_json() or {}
    player_id = data.get("player_id")
    npc_name = data.get("npc_name", "Elder Sophia")
    recent_event = data.get("recent_event")
    
    player = get_or_create_player(player_id)
    dialogue = orchestrator.handle_npc_interaction(player, npc_name, recent_event)
    return jsonify({"status": "success", "interaction": dialogue})

@api_bp.route("/challenge/get", methods=["GET", "POST"])
def get_challenge():
    orchestrator = current_app.orchestrator
    data = request.get_json() if request.method == "POST" else request.args
    topic = data.get("topic")
    difficulty = data.get("difficulty")
    
    challenge = orchestrator.challenge_agent.generate_next_challenge(
        {"topic": topic, "difficulty": difficulty},
        orchestrator.shared_blackboard
    )
    return jsonify({"status": "success", "challenge": challenge})

@api_bp.route("/challenge/submit", methods=["POST"])
def submit_challenge():
    orchestrator = current_app.orchestrator
    data = request.get_json() or {}
    player_id = data.get("player_id")
    question = data.get("question", "")
    topic = data.get("topic", "Algebra")
    difficulty = data.get("difficulty", "medium")
    player_answer = str(data.get("player_answer", "")).strip()
    correct_answer = str(data.get("correct_answer", "")).strip()
    explanation = data.get("explanation", "")
    response_time_ms = int(data.get("response_time_ms", 4000))
    
    player = get_or_create_player(player_id)
    is_correct = (player_answer.lower() == correct_answer.lower())

    # Persist log to DB
    log_entry = ChallengeLog(
        player_id=player.id,
        question=question,
        topic=topic,
        difficulty=difficulty,
        player_answer=player_answer,
        is_correct=is_correct,
        response_time_ms=response_time_ms
    )
    db.session.add(log_entry)
    db.session.commit()

    # Execute full multi-agent adaptive pipeline
    pipeline_payload = {
        "question": question,
        "topic": topic,
        "difficulty": difficulty,
        "player_answer": player_answer,
        "correct_answer": correct_answer,
        "answer": correct_answer,
        "is_correct": is_correct,
        "response_time_ms": response_time_ms,
        "explanation": explanation
    }
    adaptation_result = orchestrator.handle_challenge_submission(player, pipeline_payload)
    
    return jsonify({
        "status": "success",
        "result": adaptation_result,
        "dashboard": orchestrator.get_dashboard_snapshot(player)
    })

@api_bp.route("/challenge/hint", methods=["POST"])
def request_hint():
    orchestrator = current_app.orchestrator
    data = request.get_json() or {}
    player_id = data.get("player_id")
    player = get_or_create_player(player_id)
    
    hint_res = orchestrator.handle_hint_request(player)
    return jsonify({"status": "success", "hint_feedback": hint_res})

@api_bp.route("/dashboard/state", methods=["GET"])
def dashboard_state():
    orchestrator = current_app.orchestrator
    player_id = request.args.get("player_id")
    player = Player.query.filter_by(id=player_id).first() if player_id else None
    return jsonify(orchestrator.get_dashboard_snapshot(player))

@api_bp.route("/simulate/scenario", methods=["POST"])
def simulate_scenario():
    """Demo helper to let evaluators instantly observe agent adaptation triggers."""
    orchestrator = current_app.orchestrator
    data = request.get_json() or {}
    scenario = data.get("scenario", "frustration_streak")
    player_id = data.get("player_id")
    player = get_or_create_player(player_id)

    if scenario == "frustration_streak":
        # Simulate 2 consecutive wrong answers with hesitation
        orchestrator.handle_challenge_submission(player, {
            "question": "Solve 3x + 4 = 19",
            "topic": "Algebra",
            "difficulty": "medium",
            "player_answer": "10",
            "correct_answer": "5",
            "answer": "5",
            "is_correct": False,
            "response_time_ms": 11000,
            "explanation": "Subtract 4 and divide by 3."
        })
        res = orchestrator.handle_challenge_submission(player, {
            "question": "Solve 2x + 6 = 18",
            "topic": "Algebra",
            "difficulty": "medium",
            "player_answer": "8",
            "correct_answer": "6",
            "answer": "6",
            "is_correct": False,
            "response_time_ms": 9500,
            "explanation": "Subtract 6 and divide by 2."
        })
        msg = "Triggered Frustration Streak: Low mastery, Frustrated affective state, Difficulty reduced to Easy."

    elif scenario == "mastery_streak":
        # Simulate 2 fast correct answers
        orchestrator.handle_challenge_submission(player, {
            "question": "Solve 5x = 25",
            "topic": "Algebra",
            "difficulty": "easy",
            "player_answer": "5",
            "correct_answer": "5",
            "answer": "5",
            "is_correct": True,
            "response_time_ms": 2100,
            "explanation": "Divide by 5."
        })
        res = orchestrator.handle_challenge_submission(player, {
            "question": "Solve 4x - 8 = 16",
            "topic": "Algebra",
            "difficulty": "medium",
            "player_answer": "6",
            "correct_answer": "6",
            "answer": "6",
            "is_correct": True,
            "response_time_ms": 2300,
            "explanation": "Add 8 and divide by 4."
        })
        msg = "Triggered Mastery Streak: High mastery, Confident state, Difficulty increased, Story progress unlocked."

    elif scenario == "switch_branch":
        target_branch = data.get("branch", "scholar")
        orchestrator.story_npc_agent.active_branch = target_branch
        msg = f"Switched narrative branch to {target_branch.capitalize()}."

    elif scenario == "reset_memory":
        KnowledgeState.query.filter_by(player_id=player.id).delete()
        ChallengeLog.query.filter_by(player_id=player.id).delete()
        db.session.commit()
        for topic in ["Algebra", "Geometry", "Logic", "Science", "Cryptography"]:
            db.session.add(KnowledgeState(player_id=player.id, topic=topic, mastery=0.35))
        db.session.commit()
        orchestrator.knowledge_agent.load_from_db(KnowledgeState.query.filter_by(player_id=player.id).all())
        orchestrator.emotion_agent.current_state = "Engaged"
        orchestrator.challenge_agent.current_difficulty = "medium"
        orchestrator.story_npc_agent.active_branch = "prologue"
        msg = "Reset player memory and restored baseline state."

    else:
        msg = "Unknown scenario."

    return jsonify({
        "status": "success",
        "message": msg,
        "dashboard": orchestrator.get_dashboard_snapshot(player)
    })
