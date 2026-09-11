import json
import random
import os
import re
import requests

class LLMService:
    def __init__(self, gemini_api_key=None, openai_api_key=None):
        self.gemini_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        self.openai_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")

    def generate_challenge(self, topic="Algebra", difficulty="medium", player_context=None):
        """
        Generates an educational question tailored to the topic and difficulty.
        Attempts LLM call if keys exist, otherwise falls back to the rich procedural generator.
        """
        topic = topic or "Algebra"
        difficulty = (difficulty or "medium").lower()
        if difficulty not in ["easy", "medium", "hard", "expert"]:
            difficulty = "medium"

        # Try API if configured
        if self.gemini_key:
            try:
                res = self._call_gemini_challenge(topic, difficulty, player_context)
                if res and self._validate_challenge(res):
                    return res
            except Exception as e:
                print(f"[LLMService] Gemini call failed: {e}. Falling back to procedural engine.")

        if self.openai_key:
            try:
                res = self._call_openai_challenge(topic, difficulty, player_context)
                if res and self._validate_challenge(res):
                    return res
            except Exception as e:
                print(f"[LLMService] OpenAI call failed: {e}. Falling back to procedural engine.")

        # Procedural fallback
        return self._generate_procedural_challenge(topic, difficulty, player_context)

    def generate_npc_dialogue(self, npc_name, player_state, emotion_state, branch_name, recent_event=None):
        """
        Generates dynamic NPC dialogue reflecting the player's emotional state,
        knowledge mastery, current location, and story branch.
        """
        if self.gemini_key:
            try:
                prompt = (
                    f"You are {npc_name}, an NPC in an educational fantasy RPG.\n"
                    f"Player Emotional State: {emotion_state}\n"
                    f"Story Branch: {branch_name}\n"
                    f"Recent Event: {recent_event}\n"
                    f"Player Mastery: {player_state.get('mastery_percent', 40)}%\n"
                    "Provide a short, immersive, 1-2 sentence dialogue line. If frustrated, be encouraging and patient. "
                    "If confident/bored, challenge their intellect. Stay in character."
                )
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = requests.post(url, json=payload, timeout=4)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return text.replace('"', '')
            except Exception:
                pass

        # Procedural contextual dialogue engine
        return self._generate_procedural_npc_dialogue(npc_name, player_state, emotion_state, branch_name, recent_event)

    def _validate_challenge(self, c):
        required = ["question", "topic", "difficulty", "options", "answer", "explanation"]
        if not all(k in c for k in required):
            return False
        if not isinstance(c["options"], list) or len(c["options"]) != 4:
            return False
        if str(c["answer"]).strip() not in [str(opt).strip() for opt in c["options"]]:
            return False
        return True

    def _generate_procedural_challenge(self, topic, difficulty, player_context=None):
        topic_clean = topic.capitalize()
        if "algeb" in topic.lower():
            return self._gen_algebra(difficulty)
        elif "geom" in topic.lower():
            return self._gen_geometry(difficulty)
        elif "logic" in topic.lower():
            return self._gen_logic(difficulty)
        elif "scien" in topic.lower():
            return self._gen_science(difficulty)
        elif "crypt" in topic.lower():
            return self._gen_crypto(difficulty)
        else:
            return self._gen_algebra(difficulty)

    def _gen_algebra(self, diff):
        if diff == "easy":
            a = random.randint(2, 6)
            x = random.randint(2, 9)
            b = random.randint(1, 15)
            c = a * x + b
            question = f"Solve for x: {a}x + {b} = {c}"
            ans = str(x)
            explanation = f"Subtract {b} from both sides to get {a}x = {c - b}, then divide by {a} to get x = {x}."
            hint = f"First isolate the variable term by subtracting {b}."
            options = self._build_distractors(x, [x - 2, x + 1, x + 3])
        elif diff == "medium":
            a = random.randint(3, 8)
            b = random.randint(5, 20)
            x = random.randint(3, 12)
            c = random.randint(1, 4)
            rhs = c * x + (a * x - c * x + b)
            # a*x + b = c*x + d
            diff_coeff = a - c
            constant = rhs - b
            # ensure integer
            x_val = random.randint(2, 8)
            a = random.randint(4, 7)
            c = random.randint(1, 3)
            b = random.randint(2, 10)
            d = (a - c) * x_val + b
            question = f"Solve for x: {a}x + {b} = {c}x + {d}"
            ans = str(x_val)
            explanation = f"Subtract {c}x from both sides: {a - c}x + {b} = {d}. Then subtract {b}: {a - c}x = {d - b}. Divide by {a - c}: x = {x_val}."
            hint = f"Group like terms by moving all x terms to the left."
            options = self._build_distractors(x_val, [x_val + 2, x_val - 1, x_val * 2])
        elif diff == "hard":
            # Quadratic factoring or system
            root1 = random.randint(1, 5)
            root2 = random.randint(2, 6)
            b = -(root1 + root2)
            c = root1 * root2
            sign_b = f"- {abs(b)}" if b < 0 else f"+ {b}"
            question = f"Find the positive roots of: x² {sign_b}x + {c} = 0"
            ans = f"{min(root1, root2)}, {max(root1, root2)}" if root1 != root2 else str(root1)
            explanation = f"Factor into (x - {root1})(x - {root2}) = 0. Therefore the roots are {ans}."
            hint = f"Look for two numbers that multiply to {c} and add up to {abs(b)}."
            fake1 = f"{root1 + 1}, {root2 + 2}"
            fake2 = f"-{root1}, -{root2}"
            fake3 = f"{root1 * 2}, {root2}"
            options = [ans, fake1, fake2, fake3]
            random.shuffle(options)
        else: # expert
            a = random.randint(2, 4)
            b = random.randint(2, 5)
            # a^(2x) = a^b
            power = b * 2
            val = a ** power
            question = f"If {a}^(2x - 2) = {a}^{power}, what is the value of x?"
            ans = str(b + 1)
            explanation = f"Equate exponents: 2x - 2 = {power} -> 2x = {power + 2} -> x = {b + 1}."
            hint = "When the bases are identical, you can equate the exponents."
            options = self._build_distractors(b + 1, [b, b + 2, b + 4])

        return {
            "topic": "Algebra",
            "difficulty": diff,
            "question": question,
            "options": options,
            "answer": ans,
            "explanation": explanation,
            "hint": hint
        }

    def _gen_geometry(self, diff):
        if diff == "easy":
            w = random.randint(3, 9)
            h = random.randint(4, 12)
            area = w * h
            perimeter = 2 * (w + h)
            q_type = random.choice(["area", "perimeter"])
            if q_type == "area":
                question = f"A rectangular temple courtyard has a width of {w}m and a length of {h}m. What is its area?"
                ans = f"{area} m²"
                explanation = f"Area = width × length = {w} × {h} = {area} m²."
                hint = "Multiply the width by the length."
                options = [f"{area} m²", f"{perimeter} m²", f"{area + 10} m²", f"{w * (h - 1)} m²"]
            else:
                question = f"What is the perimeter of a garden measuring {w}m by {h}m?"
                ans = f"{perimeter} m"
                explanation = f"Perimeter = 2 × (width + length) = 2 × ({w} + {h}) = {perimeter} m."
                hint = "Add all four sides together: 2 × (w + l)."
                options = [f"{perimeter} m", f"{area} m", f"{perimeter + 4} m", f"{w + h} m"]
            random.shuffle(options)
        elif diff == "medium":
            # Pythagorean theorem
            triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)]
            a, b, c = random.choice(triples)
            question = f"A right-angled watchtower has base legs of length {a}m and {b}m. What is the hypotenuse?"
            ans = f"{c}m"
            explanation = f"By Pythagorean theorem: a² + b² = c². {a}² + {b}² = {a*a} + {b*b} = {c*c} = {c}²."
            hint = "Use the formula: a² + b² = c²."
            options = [f"{c}m", f"{c + 2}m", f"{a + b}m", f"{c - 1}m"]
            random.shuffle(options)
        elif diff == "hard":
            r = random.choice([7, 14, 21])
            # Area of circle with pi approx 22/7
            area = int((22 / 7) * r * r)
            question = f"An ancient circular dais has a radius of {r} meters. Calculate its area (use π ≈ 22/7)."
            ans = f"{area} m²"
            explanation = f"Area = π × r² = (22/7) × {r}² = {area} m²."
            hint = "Formula for circle area is πr²."
            options = [f"{area} m²", f"{int(2 * 22/7 * r)} m²", f"{area + 44} m²", f"{int(r * r)} m²"]
            random.shuffle(options)
        else: # expert
            # Coordinate geometry slope or distance
            x1, y1 = random.randint(1, 4), random.randint(1, 4)
            dx = random.choice([3, 4, 6])
            dy = random.choice([3, 4, 8])
            x2, y2 = x1 + dx, y1 + dy
            # slope = dy / dx
            # distance formula
            dist_sq = dx * dx + dy * dy
            dist = round(dist_sq ** 0.5, 2)
            question = f"What is the straight-line distance between temple beacons at ({x1}, {y1}) and ({x2}, {y2})?"
            ans = str(dist)
            explanation = f"Distance = √((x2-x1)² + (y2-y1)²) = √({dx}² + {dy}²) = √({dist_sq}) ≈ {dist}."
            hint = "Apply the distance formula √((Δx)² + (Δy)²)."
            options = [str(dist), str(round(dist + 1.5, 2)), str(dx + dy), str(round(dist - 1.2, 2))]
            random.shuffle(options)

        return {
            "topic": "Geometry",
            "difficulty": diff,
            "question": question,
            "options": options,
            "answer": ans,
            "explanation": explanation,
            "hint": hint
        }

    def _gen_logic(self, diff):
        if diff == "easy":
            seq = [2, 4, 8, 16]
            next_val = 32
            question = f"What is the next number in the magical rune sequence: 2, 4, 8, 16, __?"
            ans = "32"
            explanation = "Each term is multiplied by 2 (powers of 2). 16 × 2 = 32."
            hint = "Look at the ratio between consecutive numbers."
            options = ["32", "24", "30", "64"]
        elif diff == "medium":
            puzzles = [
                ("If all Knights tell the truth and Boris says 'I am a Knave', what is Boris?",
                 "Contradiction / Paradox",
                 "A knight cannot claim to be a knave, and a knave cannot speak the truth that he is a knave.",
                 ["Contradiction / Paradox", "A Knight", "A Knave", "A King"]),
                ("Given (A AND NOT B) OR C. If A=True, B=True, C=False, what is the output?",
                 "False",
                 "NOT B is False. A AND False is False. False OR C(False) is False.",
                 ["False", "True", "Indeterminate", "Null"])
            ]
            q, a, exp, opts = random.choice(puzzles)
            question = q
            ans = a
            explanation = exp
            hint = "Evaluate the logical operators step-by-step."
            options = opts
        elif diff == "hard":
            question = "In a tournament of 16 players, each round eliminates half the players. How many total matches are played to determine the champion?"
            ans = "15"
            explanation = "Every match eliminates exactly 1 player. To eliminate 15 players, exactly 15 matches must be played."
            hint = "Think about how many players must lose for 1 champion to remain."
            options = ["15", "16", "8", "31"]
        else: # expert
            question = "In Big-O analysis, what is the time complexity of searching a sorted array of N elements using binary search?"
            ans = "O(log N)"
            explanation = "Binary search divides the search interval in half with each comparison, yielding logarithmic complexity."
            hint = "The search space halves with every iteration."
            options = ["O(log N)", "O(N)", "O(N log N)", "O(1)"]

        random.shuffle(options)
        return {
            "topic": "Logic",
            "difficulty": diff,
            "question": question,
            "options": options,
            "answer": ans,
            "explanation": explanation,
            "hint": hint
        }

    def _gen_science(self, diff):
        items = {
            "easy": [
                ("Which force pulls celestial objects towards the center of planetary bodies?", "Gravity",
                 "Gravity is the universal attractive force between masses.", ["Gravity", "Friction", "Magnetism", "Centrifugal"]),
                ("What state of matter has a definite volume but takes the shape of its container?", "Liquid",
                 "Liquids flow to fit containers while maintaining fixed volume.", ["Liquid", "Solid", "Gas", "Plasma"])
            ],
            "medium": [
                ("If a cart travels 120 meters in 6 seconds at constant speed, what is its velocity?", "20 m/s",
                 "Velocity = Distance / Time = 120m / 6s = 20 m/s.", ["20 m/s", "24 m/s", "720 m/s", "15 m/s"]),
                ("What chemical element is symbolized as 'Au' on the alchemical periodic table?", "Gold",
                 "Au comes from the Latin word 'Aurum', meaning shining dawn or gold.", ["Gold", "Silver", "Iron", "Copper"])
            ],
            "hard": [
                ("According to Newton's Second Law, what force is needed to accelerate a 5kg mass at 4 m/s²?", "20 N",
                 "F = m × a = 5 kg × 4 m/s² = 20 Newtons.", ["20 N", "9 N", "1.25 N", "40 N"]),
                ("In optics, when light passes from air into water, what phenomenon causes it to bend?", "Refraction",
                 "Refraction occurs due to the change in the speed of light across different media.", ["Refraction", "Reflection", "Diffraction", "Dispersion"])
            ],
            "expert": [
                ("What is the kinetic energy of an arrow of mass 0.5 kg flying at 20 m/s?", "100 Joules",
                 "Kinetic Energy = 0.5 × m × v² = 0.5 × 0.5 × 400 = 100 J.", ["100 Joules", "200 Joules", "50 Joules", "10 Joules"]),
                ("Which thermodynamic law establishes that entropy of an isolated system always increases?", "Second Law",
                 "The Second Law of Thermodynamics dictates that total entropy never decreases over time.", ["Second Law", "First Law", "Third Law", "Zeroth Law"])
            ]
        }
        q, a, exp, opts = random.choice(items.get(diff, items["medium"]))
        options = list(opts)
        random.shuffle(options)
        return {
            "topic": "Science",
            "difficulty": diff,
            "question": q,
            "options": options,
            "answer": a,
            "explanation": exp,
            "hint": "Recall foundational physical and chemical principles."
        }

    def _gen_crypto(self, diff):
        shifts = {"easy": 1, "medium": 3, "hard": 5, "expert": 7}
        shift = shifts.get(diff, 2)
        words = ["KEY", "RUNE", "CIPHER", "TEMPLE", "SECRETS"]
        word = random.choice(words)
        
        def caesar(text, s):
            res = ""
            for c in text:
                res += chr((ord(c) - 65 + s) % 26 + 65)
            return res

        encoded = caesar(word, shift)
        question = f"Decipher this ancient Caesar code shifted forward by {shift}: '{encoded}'"
        ans = word
        hint = f"Shift each character backwards in the alphabet by {shift} places."
        explanation = f"Reversing the +{shift} alphabet shift turns '{encoded}' back into '{word}'."
        fake1 = caesar(word, 2)
        fake2 = caesar(word, 4)
        fake3 = "MAGIC"
        options = [ans, fake1, fake2, fake3]
        random.shuffle(options)
        return {
            "topic": "Cryptography",
            "difficulty": diff,
            "question": question,
            "options": options,
            "answer": ans,
            "explanation": explanation,
            "hint": hint
        }

    def _build_distractors(self, correct_val, candidate_offsets):
        opts = [str(correct_val)]
        for off in candidate_offsets:
            if str(off) not in opts:
                opts.append(str(off))
        while len(opts) < 4:
            rand_val = str(correct_val + random.randint(-5, 5))
            if rand_val not in opts:
                opts.append(rand_val)
        random.shuffle(opts)
        return opts

    def _generate_procedural_npc_dialogue(self, npc_name, player_state, emotion_state, branch_name, recent_event):
        mastery = player_state.get("mastery_percent", 50)
        
        # Responses tailored to emotional state and NPC personality
        dialogue_matrix = {
            "Elder Sophia": {
                "Frustrated": [
                    "Breathe gently, young traveler. Even the greatest archmages stumbled on their first runes.",
                    "Patience is your shield. Let us break this puzzle into simpler steps together.",
                    "Do not fear mistakes; they are the stones that pave the road to true wisdom."
                ],
                "Confused": [
                    "Ah, the fog of learning surrounds you. Look closer at the underlying pattern.",
                    "When numbers seem to tangle, start from what you know to be true.",
                    "Take a moment to inspect the hints. A humble inquiry unlocks grand doors."
                ],
                "Engaged": [
                    "Your dedication honors our village! The ancient archives stir as your insight grows.",
                    "Well reasoned! You are beginning to decipher the kingdom's forgotten arithmetic.",
                    "Keep this steady momentum, Seeker. The path before you is brightening."
                ],
                "Confident": [
                    "Splendid resolve! Your mind cuts through complexity like a sunbeam through mist.",
                    "You grasp these secrets with natural grace. The Grand Library awaits your presence!",
                    "Remarkable clarity! Perhaps you are ready to test yourself against the ancient sanctum."
                ],
                "Bored": [
                    "You solve these with ease! Our humble village puzzles can no longer contain your hunger.",
                    "A keen intellect requires sharper whetstones. Go seek Scholar Theron at the Library!",
                    "You breeze through our challenges. Let us see if you can solve the deeper mysteries."
                ]
            },
            "Scholar Theron": {
                "Frustrated": [
                    "Do not despair over a stubborn equation. Mathematics is a dance of adjustments.",
                    "Even Archimedes revised his diagrams a hundred times. Let us inspect the formula again.",
                    "Frustration clouds deduction. Step back, review the theorem, and try once more."
                ],
                "Confused": [
                    "The logic seems elusive? Remember: an equation is merely a balanced scale.",
                    "Notice how the variables interact. Once isolated, the truth becomes undeniable.",
                    "Let us break down this theorem axiom by axiom."
                ],
                "Engaged": [
                    "Fascinating progress! You demonstrate true academic rigor.",
                    "The Alexandrian scrolls glow with your answer. We are decoding the lost manuscripts!",
                    "A disciplined mind is a scholar's greatest instrument. Excellent focus."
                ],
                "Confident": [
                    "Magnificent! Your algebraic fluency rivals the senior scribes of the Citadel.",
                    "Flawless calculation! You have earned the right to inspect the High Crypts.",
                    "Impressive mastery! We shall document your analytical breakthroughs."
                ],
                "Bored": [
                    "Standard proofs bore you, do they? Then prepare for collegiate-level theorems!",
                    "If these exercises are child's play to you, the Sky Temple's glyphs await your challenge.",
                    "I see your restless brilliance. Let me unveil our most intricate enigmas."
                ]
            },
            "Master Kael": {
                "Frustrated": [
                    "Stand firm! A warrior does not drop their sword when a strike is deflected.",
                    "Reset your stance, recruit. Take a deep breath and aim your mind with discipline!",
                    "Every miss teaches your blade how to strike true. Try again!"
                ],
                "Confused": [
                    "Hesitation gets you struck in battle! Break the battlefield into clear coordinates.",
                    "Geometry is the blueprint of combat. Know your angles and you command the arena.",
                    "Focus your eyes! Calculate your trajectory before you release the arrow."
                ],
                "Engaged": [
                    "Solid form! You're calculating combat angles like a seasoned tactician.",
                    "That's it! Keep your guard up and your calculations swift.",
                    "The vanguard needs strategists who can calculate under pressure. Well done!"
                ],
                "Confident": [
                    "A devastating strike of pure logic! You command the battlefield effortlessly!",
                    "Champion caliber! Your mind is as sharp as folded Damascus steel.",
                    "Superb execution! You've mastered our tactical drills with flying colors."
                ],
                "Bored": [
                    "Too easy for you? Then we raise the training dummies and double the speed!",
                    "Show me you can maintain this precision against the Vanguard's supreme trial!",
                    "Don't get complacent! The Sky Temple Guardians do not hold back."
                ]
            },
            "Guardian Lyra": {
                "Frustrated": [
                    "The celestial crystals resonate with your heartbeat. Calm your spirit, traveler.",
                    "Ancient magic requires harmony, not force. Align your thoughts with the cosmos.",
                    "Failure is merely an echo. Listen to the resonance and try again."
                ],
                "Confused": [
                    "The temple glyphs speak in multidimensional symmetries. Look beyond the surface.",
                    "Balance the elements. When the inputs balance, the crystal will illuminate.",
                    "Allow the harmony of logic to guide your intuition."
                ],
                "Engaged": [
                    "The temple spires awaken. The ancient continuum acknowledges your presence.",
                    "A harmonious solution! The stars align with your analytical mind.",
                    "You are restoring the lost equilibrium of the sanctuary."
                ],
                "Confident": [
                    "Astounding resonance! You wield knowledge like radiant celestial light!",
                    "The temple seals bow before your intellect. The grand synthesis is within your reach!",
                    "You walk the path of the Ancients with sovereign confidence."
                ],
                "Bored": [
                    "The mortal realm no longer stretches your mind. Behold the cosmic paradoxes!",
                    "You seek higher dimensions of understanding. Let the ultimate trial commence!",
                    "If our sacred puzzles fail to challenge you, then face the eternal enigma."
                ]
            }
        }

        npc_pool = dialogue_matrix.get(npc_name, dialogue_matrix["Elder Sophia"])
        emotion_pool = npc_pool.get(emotion_state, npc_pool["Engaged"])
        chosen = random.choice(emotion_pool)
        
        # Add branch flair if unlocked
        if branch_name == "scholar":
            chosen += " (The Scholar's Path shines before you.)"
        elif branch_name == "vanguard":
            chosen += " (The Vanguard's Trial beckons your strength.)"
        elif branch_name == "mystic":
            chosen += " (The Mystic's Synthesis aligns around you.)"
            
        return chosen
