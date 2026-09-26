"""
ConversationManager for YojanaVaani (Phase 3).

Orchestrates Stage 1 (Fixed Baseline Interview):
- Tracks question progression across conversation sessions.
- Dispenses Hindi baseline questions in strict statutory sequence.
- Parses spoken vernacular responses (Hindi, Hinglish, English, numerals) into
  structured fields in CitizenProfile.
- Promotes conversation state to 'scheme_matching' once all baseline facts are gathered.
"""

import re
import uuid
from typing import Dict, Optional, Tuple, Any

from app.models.conversation import (
    CitizenProfile,
    ConversationState,
    ConversationStatus,
    ConversationTurn,
    IncomeBracket,
    SocialCategoryEnum,
    GenderEnum,
)
from app.services.baseline_interview import (
    BASELINE_QUESTIONS,
    TOTAL_BASELINE_QUESTIONS,
    BaselineQuestion,
    get_question_by_field,
    get_question_by_index,
)


# Mapping of Hindi number words to integers (1 - 100)
HINDI_NUMBER_WORDS: Dict[str, int] = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20,
    "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24, "पच्चीस": 25, "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाईस": 28, "उनतीस": 29, "तीस": 30,
    "इकतीस": 31, "बत्तीस": 32, "तैंतीस": 33, "चौंतीस": 34, "पैंतीस": 35, "छत्तीस": 36, "सैंतीस": 37, "अड़तीस": 38, "उनतालीस": 39, "चालीस": 40,
    "इकतालीस": 41, "बयालीस": 42, "तैंतालीस": 43, "चवालीस": 44, "पैंतालीस": 45, "छियालीस": 46, "सैंतालीस": 47, "अड़तालीस": 48, "उनचास": 49, "पचास": 50,
    "इक्यावन": 51, "बावन": 52, "तिरेपन": 53, "चौवन": 54, "पचपन": 55, "छप्पन": 56, "सत्तावन": 57, "अट्ठावन": 58, "उनसठ": 59, "साठ": 60,
    "इकसठ": 61, "बासठ": 62, "तिरसठ": 63, "चौंसठ": 64, "पैंसठ": 65, "छियासठ": 66, "सरसठ": 67, "अड़सठ": 68, "उनहत्तर": 69, "सत्तर": 70,
    "इकहत्तर": 71, "बहत्तर": 72, "तिहत्तर": 73, "चौहत्तर": 74, "पचहत्तर": 75, "छिहत्तर": 76, "सतहत्तर": 77, "अठहत्तर": 78, "उन्नासी": 79, "अस्सी": 80,
    "इक्यासी": 81, "बयासी": 82, "तिरासी": 83, "चौरासी": 84, "पचासी": 85, "छियासी": 86, "सत्तासी": 87, "अठासी": 88, "नवासी": 89, "नब्बे": 90,
    "इक्यानवे": 91, "बानवे": 92, "तिरानवे": 93, "चौरानवे": 94, "पंचानवे": 95, "छियानवे": 96, "सत्तानवे": 97, "अट्ठानवे": 98, "निन्यानवे": 99, "सौ": 100
}

# Devanagari digit translation table
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# Known States and Common Districts for normalization
INDIAN_STATES_MAP: Dict[str, str] = {
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "उत्तर प्रदेश": "Uttar Pradesh",
    "यूपी": "Uttar Pradesh",
    "delhi": "Delhi",
    "दिल्ली": "Delhi",
    "bihar": "Bihar",
    "बिहार": "Bihar",
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    "मध्य प्रदेश": "Madhya Pradesh",
    "rajasthan": "Rajasthan",
    "राजस्थान": "Rajasthan",
    "haryana": "Haryana",
    "हरियाणा": "Haryana",
    "punjab": "Punjab",
    "पंजाब": "Punjab",
    "maharashtra": "Maharashtra",
    "महाराष्ट्र": "Maharashtra",
    "gujarat": "Gujarat",
    "गुजरात": "Gujarat",
    "jharkhand": "Jharkhand",
    "झारखंड": "Jharkhand",
    "uttarakhand": "Uttarakhand",
    "उत्तराखंड": "Uttarakhand",
    "west bengal": "West Bengal",
    "पश्चिम बंगाल": "West Bengal",
}

# Common Districts mapping (Devanagari & English -> (DistrictName, DefaultState))
COMMON_DISTRICTS_MAP: Dict[str, Tuple[str, str]] = {
    # Uttar Pradesh
    "barabanki": ("Barabanki", "Uttar Pradesh"),
    "बाराबंकी": ("Barabanki", "Uttar Pradesh"),
    "lucknow": ("Lucknow", "Uttar Pradesh"),
    "लखनऊ": ("Lucknow", "Uttar Pradesh"),
    "varanasi": ("Varanasi", "Uttar Pradesh"),
    "वाराणसी": ("Varanasi", "Uttar Pradesh"),
    "बनारस": ("Varanasi", "Uttar Pradesh"),
    "gorakhpur": ("Gorakhpur", "Uttar Pradesh"),
    "गोरखपुर": ("Gorakhpur", "Uttar Pradesh"),
    "prayagraj": ("Prayagraj", "Uttar Pradesh"),
    "प्रयागराज": ("Prayagraj", "Uttar Pradesh"),
    "इलाहाबाद": ("Prayagraj", "Uttar Pradesh"),
    "kanpur": ("Kanpur", "Uttar Pradesh"),
    "कानपुर": ("Kanpur", "Uttar Pradesh"),
    "ayodhya": ("Ayodhya", "Uttar Pradesh"),
    "अयोध्या": ("Ayodhya", "Uttar Pradesh"),
    "फैजाबाद": ("Ayodhya", "Uttar Pradesh"),
    "agra": ("Agra", "Uttar Pradesh"),
    "आगरा": ("Agra", "Uttar Pradesh"),
    "meerut": ("Meerut", "Uttar Pradesh"),
    "मेरठ": ("Meerut", "Uttar Pradesh"),
    "jhansi": ("Jhansi", "Uttar Pradesh"),
    "झांसी": ("Jhansi", "Uttar Pradesh"),
    "bareilly": ("Bareilly", "Uttar Pradesh"),
    "बरेली": ("Bareilly", "Uttar Pradesh"),
    "aligarh": ("Aligarh", "Uttar Pradesh"),
    "अलीगढ़": ("Aligarh", "Uttar Pradesh"),

    # Delhi
    "shahdara": ("Shahdara", "Delhi"),
    "शाहदरा": ("Shahdara", "Delhi"),
    "central delhi": ("Central Delhi", "Delhi"),
    "new delhi": ("New Delhi", "Delhi"),
    "नई दिल्ली": ("New Delhi", "Delhi"),
    "south delhi": ("South Delhi", "Delhi"),
    "north delhi": ("North Delhi", "Delhi"),
    "east delhi": ("East Delhi", "Delhi"),
    "west delhi": ("West Delhi", "Delhi"),

    # Bihar
    "patna": ("Patna", "Bihar"),
    "पटना": ("Patna", "Bihar"),
    "gaya": ("Gaya", "Bihar"),
    "गया": ("Gaya", "Bihar"),

    # Madhya Pradesh
    "bhopal": ("Bhopal", "Madhya Pradesh"),
    "भोपाल": ("Bhopal", "Madhya Pradesh"),
    "indore": ("Indore", "Madhya Pradesh"),
    "इंदौर": ("Indore", "Madhya Pradesh"),
    "rewa": ("Rewa", "Madhya Pradesh"),
    "रीवा": ("Rewa", "Madhya Pradesh"),
}


class ConversationManager:
    """
    Manages conversational sessions and drives Stage 1 fixed baseline interview.
    """

    def __init__(self):
        # In-memory store of active conversation sessions keyed by conversation_id
        self.sessions: Dict[str, ConversationState] = {}

    def create_conversation(self, conversation_id: Optional[str] = None) -> ConversationState:
        """Initializes and registers a new conversation session."""
        cid = conversation_id or str(uuid.uuid4())
        state = ConversationState(
            conversation_id=cid,
            citizen_profile=CitizenProfile(),
            status=ConversationStatus.baseline_interview,
            current_question_index=0,
            baseline_complete=False
        )
        self.sessions[cid] = state
        return state

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieves an existing conversation session by ID."""
        return self.sessions.get(conversation_id)

    def get_next_question(self, conversation_id: str) -> Optional[str]:
        """
        Returns the Hindi text of the next unanswered baseline question,
        or None if the baseline interview has completed.
        Appends the question to conversation_history as an 'assistant' turn.
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise KeyError(f"Conversation ID '{conversation_id}' not found.")

        if conv.baseline_complete or conv.current_question_index >= TOTAL_BASELINE_QUESTIONS:
            return None

        q = get_question_by_index(conv.current_question_index)
        if not q:
            return None

        # Add assistant question to conversation history if not already recorded as the last turn
        if not (conv.conversation_history and conv.conversation_history[-1].text == q.hindi_text):
            conv.conversation_history.append(
                ConversationTurn(speaker="assistant", text=q.hindi_text)
            )

        return q.hindi_text

    def get_current_question_metadata(self, conversation_id: str) -> Optional[BaselineQuestion]:
        """Returns the full metadata object of the current question for the session."""
        conv = self.get_conversation(conversation_id)
        if not conv or conv.baseline_complete or conv.current_question_index >= TOTAL_BASELINE_QUESTIONS:
            return None
        return get_question_by_index(conv.current_question_index)

    def record_answer(
        self,
        conversation_id: str,
        question_field: str,
        answer_text: str
    ) -> ConversationState:
        """
        Stores and parses the citizen's answer for the designated baseline question.
        Updates citizen_profile, logs conversation turn, and advances question pointer.
        When the final question is answered, flips status to 'scheme_matching' and
        baseline_complete to True.
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise KeyError(f"Conversation ID '{conversation_id}' not found.")

        # Record citizen response turn
        clean_raw_text = answer_text.strip()
        conv.conversation_history.append(
            ConversationTurn(speaker="citizen", text=clean_raw_text)
        )

        # Parse field-specific value into citizen profile
        self._parse_and_store(conv, question_field, clean_raw_text)

        # Advance question pointer
        conv.current_question_index += 1

        # Check if all 9 baseline questions have been answered
        if conv.current_question_index >= TOTAL_BASELINE_QUESTIONS:
            conv.baseline_complete = True
            conv.status = ConversationStatus.scheme_matching

        return conv

    def run_agentic_followup(self, conversation_id: str) -> ConversationState:
        """
        Stage 2 Agentic Follow-Up Loop handoff.
        Triggered when baseline interview is complete (status == 'scheme_matching').
        Passes citizen_profile and stated_need to the LangGraph agent, updating
        candidate_schemes, missing_facts, and dialogue history.
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise KeyError(f"Conversation ID '{conversation_id}' not found.")

        from app.services.agent import YojanaVaaniAgent
        agent = YojanaVaaniAgent()
        result = agent.run(
            citizen_profile=conv.citizen_profile.model_dump(),
            stated_need=conv.stated_need or ""
        )

        conv.candidate_schemes = result.candidate_schemes
        conv.missing_facts = result.missing_facts

        if result.response_type == "request_document":
            conv.status = ConversationStatus.awaiting_document
        elif result.response_type == "escalated":
            conv.status = ConversationStatus.escalated
        elif result.response_type == "results_ready":
            conv.status = ConversationStatus.results_ready
        else:
            conv.status = ConversationStatus.scheme_matching

        if result.response_text:
            conv.conversation_history.append(
                ConversationTurn(speaker="assistant", text=result.response_text)
            )

        return conv

    # -------------------------------------------------------------------------
    # PARSING LOGIC FOR SPOKEN HINDI / VERNACULAR RESPONSES
    # -------------------------------------------------------------------------

    def _parse_and_store(self, conv: ConversationState, field_name: str, raw_text: str) -> None:
        """Dispatches answer parsing based on the target field name."""
        profile = conv.citizen_profile

        if field_name == "name":
            profile.name = self._parse_name(raw_text)

        elif field_name == "age":
            profile.age = self._parse_age(raw_text)

        elif field_name == "gender":
            profile.gender = self._parse_gender(raw_text)

        elif field_name == "state_district":
            state, district = self._parse_location(raw_text)
            profile.state = state
            profile.district = district

        elif field_name == "approx_income_bracket":
            profile.approx_income_bracket = self._parse_income_bracket(raw_text)

        elif field_name == "social_category":
            profile.social_category = self._parse_social_category(raw_text)

        elif field_name == "occupation":
            profile.occupation = self._parse_occupation(raw_text)

        elif field_name == "disability_status":
            profile.disability_status = self._parse_disability(raw_text)

        elif field_name == "stated_need":
            conv.stated_need = raw_text.strip()

        else:
            # Fallback for unrecognized field names
            pass

    def _parse_name(self, text: str) -> str:
        """Cleans conversational framing words from citizen name."""
        clean = text.strip()
        # Remove common speech introductory prefixes
        prefixes = [
            r"^मेरा नाम\s*",
            r"^हमारा नाम\s*",
            r"^मेरा शुभ नाम\s*",
            r"^नाम\s*",
            r"^my name is\s*",
            r"^i am\s*",
            r"^naam\s*",
        ]
        for p in prefixes:
            clean = re.sub(p, "", clean, flags=re.IGNORECASE)

        # Remove trailing auxiliary verbs e.g. "है", "हूं"
        clean = re.sub(r"\s+है$", "", clean)
        clean = re.sub(r"\s+हूँ$", "", clean)
        clean = re.sub(r"\s+hai$", "", clean, flags=re.IGNORECASE)
        clean = clean.strip(" .,।?!\"'")
        return clean if clean else text.strip()

    def _parse_age(self, text: str) -> Optional[int]:
        """Extracts numerical age from Devanagari digits, English digits, or Hindi number words."""
        norm_text = text.translate(DEVANAGARI_DIGITS)

        # 1. Check for standard digits (e.g. "42", "42 वर्ष", "42 saal")
        digit_match = re.search(r"\b(\d{1,3})\b", norm_text)
        if digit_match:
            val = int(digit_match.group(1))
            if 0 < val <= 120:
                return val

        # 2. Check for Hindi number words
        words = norm_text.split()
        for w in words:
            clean_w = w.strip(".,।?!")
            if clean_w in HINDI_NUMBER_WORDS:
                val = HINDI_NUMBER_WORDS[clean_w]
                if 0 < val <= 120:
                    return val

        # 3. Handle English words
        eng_num_map = {
            "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
            "sixty": 60, "seventy": 70, "eighty": 80
        }
        for eng_word, num in eng_num_map.items():
            if eng_word in norm_text.lower():
                return num

        return None

    def _parse_gender(self, text: str) -> str:
        """Categorizes gender into Female, Male, Transgender, or Other."""
        lower = text.lower()
        if any(w in lower or w in text for w in ["महिला", "स्त्री", "aurat", "female", "woman", "लड़की", "बेटी"]):
            return GenderEnum.FEMALE.value
        if any(w in lower or w in text for w in ["पुरुष", "आदमी", "male", "man", "लड़का", "बेटा", "मर्द"]):
            return GenderEnum.MALE.value
        if any(w in lower or w in text for w in ["ट्रांसजेंडर", "किन्नर", "transgender", "third gender"]):
            return GenderEnum.TRANSGENDER.value
        return GenderEnum.OTHER.value

    def _parse_location(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parses state and district from free-form spoken location utterances."""
        lower = text.lower().strip()
        detected_state: Optional[str] = None
        detected_district: Optional[str] = None

        # 1. Direct district match from COMMON_DISTRICTS_MAP
        for key, (dist_name, default_st) in COMMON_DISTRICTS_MAP.items():
            if key in lower or key in text:
                detected_district = dist_name
                detected_state = default_st
                break

        # 2. Check for State match from INDIAN_STATES_MAP
        for key, state_name in INDIAN_STATES_MAP.items():
            if key in lower or key in text:
                detected_state = state_name
                break

        # 3. If district is not found yet, inspect split parts (comma, 'में', etc.)
        if not detected_district:
            parts = [p.strip() for p in re.split(r"[,/|]+|\bमें\b|\s+and\s+", text) if p.strip()]
            if len(parts) >= 2:
                p0, p1 = parts[0], parts[1]
                # Check if p0 is state
                p0_is_state = any(k in p0.lower() or k in p0 for k in INDIAN_STATES_MAP)
                p1_is_state = any(k in p1.lower() or k in p1 for k in INDIAN_STATES_MAP)

                if p0_is_state:
                    detected_state = next(v for k, v in INDIAN_STATES_MAP.items() if k in p0.lower() or k in p0)
                    dist_key = p1.lower().strip(" .,।?!")
                    detected_district = COMMON_DISTRICTS_MAP.get(dist_key, (p1.strip(" .,।?!"), detected_state))[0]
                elif p1_is_state:
                    detected_state = next(v for k, v in INDIAN_STATES_MAP.items() if k in p1.lower() or k in p1)
                    dist_key = p0.lower().strip(" .,।?!")
                    detected_district = COMMON_DISTRICTS_MAP.get(dist_key, (p0.strip(" .,।?!"), detected_state))[0]
                else:
                    detected_state = p0
                    detected_district = p1

        # Fallback if text contains only state or single location
        if not detected_state and not detected_district:
            detected_state = text.strip(" .,।?!")

        return detected_state, detected_district

    def _parse_income_bracket(self, text: str) -> str:
        """Maps spoken income statements to standard IncomeBracket enum."""
        lower = text.lower().translate(DEVANAGARI_DIGITS)

        # Explicit Below 2 lakh phrases:
        if any(term in lower or term in text for term in [
            "2 लाख से कम", "दो लाख से कम", "2 lakh se kam", "do lakh se kam",
            "गरीब", "bpl", "अंत्योदय", "below 2", "less than 2",
            "50000", "50 हजार", "1 lakh", "1 लाख", "एक लाख", "डेढ़ लाख", "1.5"
        ]):
            return IncomeBracket.BELOW_2_LAKH.value

        # Explicit Above 5 lakh phrases:
        if any(term in lower or term in text for term in [
            "5 लाख से ज्यादा", "5 लाख से ज़्यादा", "पांच लाख से ज्यादा", "5 lakh se zyada",
            "above 5", "more than 5", "paanch lakh se adhik", "6 lakh", "6 लाख", "7 lakh", "7 लाख",
            "8 lakh", "8 लाख", "10 lakh", "10 लाख"
        ]):
            return IncomeBracket.ABOVE_5_LAKH.value

        # Explicit 2 to 5 lakh phrases:
        if any(term in lower or term in text for term in [
            "2 से 5 लाख", "दो से पांच लाख", "2 to 5", "do se paanch",
            "3 lakh", "3 लाख", "4 lakh", "4 लाख", "ढाई लाख", "तीन लाख", "चार लाख", "2-5"
        ]):
            return IncomeBracket.BETWEEN_2_AND_5_LAKH.value

        # Heuristic based on extracted digits
        num_match = re.search(r"(\d+(?:\.\d+)?)", lower)
        if num_match:
            val = float(num_match.group(1))
            # If val is expressed in Lakhs (e.g. 1.5, 3, 4, 7):
            if val <= 15:
                if val < 2:
                    return IncomeBracket.BELOW_2_LAKH.value
                elif 2 <= val <= 5:
                    return IncomeBracket.BETWEEN_2_AND_5_LAKH.value
                else:
                    return IncomeBracket.ABOVE_5_LAKH.value
            # If val is expressed in raw Rupees (e.g. 50000, 180000, 350000):
            else:
                if val < 200000:
                    return IncomeBracket.BELOW_2_LAKH.value
                elif 200000 <= val <= 500000:
                    return IncomeBracket.BETWEEN_2_AND_5_LAKH.value
                else:
                    return IncomeBracket.ABOVE_5_LAKH.value

        # Default fallback to below 2 lakh as target user demographic is typically rural/BPL
        return IncomeBracket.BELOW_2_LAKH.value

    def _parse_social_category(self, text: str) -> str:
        """Classifies social reservation category into General, OBC, SC, ST."""
        lower = text.lower()

        # SC: अनुसूचित जाति, दलित
        if any(term in lower or term in text for term in ["एससी", "sc", "अनुसूचित जाति", "scheduled caste", "दलित"]):
            return SocialCategoryEnum.SC.value

        # ST: अनुसूचित जनजाति, आदिवासी
        if any(term in lower or term in text for term in ["एसटी", "st", "अनुसूचित जनजाति", "scheduled tribe", "आदिवासी"]):
            return SocialCategoryEnum.ST.value

        # OBC: अन्य पिछड़ा वर्ग
        if any(term in lower or term in text for term in ["ओबीसी", "obc", "अन्य पिछड़ा वर्ग", "other backward class", "पिछड़ा"]):
            return SocialCategoryEnum.OBC.value

        # General: सामान्य
        if any(term in lower or term in text for term in ["सामान्य", "general", "gen", "समान्य", "unreserved"]):
            return SocialCategoryEnum.GENERAL.value

        return SocialCategoryEnum.GENERAL.value

    def _parse_occupation(self, text: str) -> str:
        """Normalizes citizen's primary occupation."""
        lower = text.lower()
        if any(term in lower or term in text for term in ["खेती", "किसान", "farmer", "agriculture", "कृषक", "kisan"]):
            return "Farmer"
        if any(term in lower or term in text for term in ["मजदूर", "मजदूरी", "labour", "laborer", "daily wage", "दिहाड़ी"]):
            return "Daily Wage Laborer"
        if any(term in lower or term in text for term in ["छात्र", "छात्रा", "विद्यार्थी", "student", "पढ़ाई", "study"]):
            return "Student"
        if any(term in lower or term in text for term in ["व्यापार", "दुकान", "business", "shop", "दुकानदार", "व्यापारी"]):
            return "Small Business / Self-Employed"
        if any(term in lower or term in text for term in ["गृहणी", "हाउसवाइफ", "homemaker", "housewife"]):
            return "Homemaker"
        if any(term in lower or term in text for term in ["बेरोजगार", "unemployed", "कोई काम नहीं"]):
            return "Unemployed"

        # If citizen states a specific job (e.g. "ड्राइवर", "दर्जी"), retain cleaned string
        return text.strip(" .,।?!")

    def _parse_disability(self, text: str) -> bool:
        """Determines whether citizen or family has a disability."""
        lower = text.lower()
        # Explicit negation first: "नहीं", "नहीं है", "no", "nahi", "nahin"
        if any(term in lower or term in text for term in ["नहीं", "nahin", "nahi", "no", "नहीं है", "कोई नहीं", "none"]):
            return False

        # Positive indicator: "हाँ", "haan", "दिव्यांग", "handicapped"
        if any(term in lower or term in text for term in ["हाँ", "haan", "ha", "yes", "दिव्यांग", "divyang", "विकलांग"]):
            return True

        return False


# Global singleton instance for API routes
conversation_manager = ConversationManager()
