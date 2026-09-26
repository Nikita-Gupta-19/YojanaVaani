"""
Baseline interview questions and metadata for Stage 1 of YojanaVaani.

Per project specification:
Stage 1 is a FIXED baseline interview covering fields that almost every scheme's
eligibility depends on, asked in the same order for every citizen in natural,
spoken-appropriate Hindi (Devanagari script).

Order of fields:
1. name
2. age
3. gender
4. state / district
5. approximate income bracket
6. social category
7. occupation
8. disability status
9. stated need (open-ended goal)
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class BaselineQuestion:
    """Definition of a fixed baseline interview question."""
    index: int
    field_name: str
    hindi_text: str
    transliteration: str
    prompt_explanation: str
    sample_answers: List[str]


BASELINE_QUESTIONS: List[BaselineQuestion] = [
    BaselineQuestion(
        index=0,
        field_name="name",
        hindi_text="नमस्ते! आपका नाम क्या है?",
        transliteration="Namaste! Aapka naam kya hai?",
        prompt_explanation="Citizen's full name",
        sample_answers=["रामवती देवी", "रमेश कुमार", "अमित सिंह", "सुनीता शर्मा"]
    ),
    BaselineQuestion(
        index=1,
        field_name="age",
        hindi_text="आपकी उम्र कितने साल है?",
        transliteration="Aapki umar kitne saal hai?",
        prompt_explanation="Citizen's age in completed years",
        sample_answers=["42 वर्ष", "पैंतालीस साल", "30", "पचपन"]
    ),
    BaselineQuestion(
        index=2,
        field_name="gender",
        hindi_text="आप महिला हैं या पुरुष?",
        transliteration="Aap mahila hain ya purush?",
        prompt_explanation="Gender identification (Female, Male, Transgender, Other)",
        sample_answers=["महिला", "पुरुष", "Female", "आदमी"]
    ),
    BaselineQuestion(
        index=3,
        field_name="state_district",
        hindi_text="आप किस राज्य और ज़िले में रहते हैं?",
        transliteration="Aap kis rajya aur zile mein rehte hain?",
        prompt_explanation="Geographic location (State and District of permanent residence)",
        sample_answers=["उत्तर प्रदेश, बाराबंकी", "दिल्ली, शाहदra", "बिहार, पटना", "UP Lucknow"]
    ),
    BaselineQuestion(
        index=4,
        field_name="approx_income_bracket",
        hindi_text="साल भर में आपके पूरे घर की कुल कमाई कितनी हो जाती है — 2 लाख से कम, 2 से 5 लाख, या 5 लाख से ज़्यादा?",
        transliteration="Saal bhar mein aapke poore ghar ki kul kamai kitni ho jaati hai — 2 lakh se kam, 2 se 5 lakh, ya 5 lakh se zyada?",
        prompt_explanation="Approximate annual household income tier",
        sample_answers=["2 लाख से कम", "दो से पांच लाख", "पांच लाख से ज्यादा", "डेढ़ लाख सालाना", "गरीब परिवार"]
    ),
    BaselineQuestion(
        index=5,
        field_name="social_category",
        hindi_text="आप किस जाति या वर्ग में आते हैं — सामान्य, ओबीसी, एससी, या एसटी?",
        transliteration="Aap kis jaati ya varg mein aate hain — Samanya, OBC, SC, ya ST?",
        prompt_explanation="Social category for statutory reservation/affirmative action benefits",
        sample_answers=["ओबीसी", "सामान्य", "एससी", "एसटी", "OBC", "General"]
    ),
    BaselineQuestion(
        index=6,
        field_name="occupation",
        hindi_text="आप क्या काम करते हैं — जैसे खेती, मजदूरी, दुकान, या घर का काम?",
        transliteration="Aap kya kaam karte hain — jaise kheti, majdoori, dukaan, ya ghar ka kaam?",
        prompt_explanation="Primary occupation or economic activity",
        sample_answers=["खेती / किसान", "दिहाड़ी मजदूरी", "पढ़ाई / छात्र", "दुकान / छोटा व्यापार", "गृहणी"]
    ),
    BaselineQuestion(
        index=7,
        field_name="disability_status",
        hindi_text="क्या परिवार में किसी को कोई शारीरिक परेशानी या दिव्यांगता (हाथ-पैर की दिक्कत) है?",
        transliteration="Kya parivar mein kisi ko koi sharirik pareshani ya divyangta hai?",
        prompt_explanation="Disability status of citizen or dependent family member",
        sample_answers=["नहीं", "हाँ, 40 प्रतिशत दिव्यांगता", "नहीं है", "हाँ"]
    ),
    BaselineQuestion(
        index=8,
        field_name="stated_need",
        hindi_text="आपको सरकार से किस काम के लिए मदद चाहिए — जैसे खेती, मकान, पेंशन, या बच्चों की पढ़ाई?",
        transliteration="Aapko sarkar se kis kaam ke liye madad chahiye — jaise kheti, makaan, pension, ya bacchon ki padhai?",
        prompt_explanation="Open-ended expression of citizen need or welfare goal",
        sample_answers=[
            "खेत के लिए सोलर पंप और खाद-बीज की सहायता चाहिए",
            "बेटी की पढ़ाई और शादी के लिए सरकारी योजना",
            "मकान बनाने के लिए सहायता या लोन",
            "वृद्धावस्था या विधवा पेंशन योजना"
        ]
    )
]

TOTAL_BASELINE_QUESTIONS = len(BASELINE_QUESTIONS)


def get_baseline_questions() -> List[BaselineQuestion]:
    """Returns the ordered list of all fixed baseline interview questions."""
    return list(BASELINE_QUESTIONS)


def get_question_by_index(index: int) -> Optional[BaselineQuestion]:
    """Returns the question at the specified zero-based index, or None if index is out of bounds."""
    if 0 <= index < len(BASELINE_QUESTIONS):
        return BASELINE_QUESTIONS[index]
    return None


def get_question_by_field(field_name: str) -> Optional[BaselineQuestion]:
    """Returns the question corresponding to the given field name, or None if not found."""
    for q in BASELINE_QUESTIONS:
        if q.field_name == field_name:
            return q
    return None
