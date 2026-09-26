"""
Unit tests for YojanaVaani Phase 3 Baseline Interview and ConversationManager.
"""

import pytest
from app.models.conversation import (
    ConversationState,
    ConversationStatus,
    IncomeBracket,
    SocialCategoryEnum,
    GenderEnum,
)
from app.services.baseline_interview import (
    BASELINE_QUESTIONS,
    TOTAL_BASELINE_QUESTIONS,
    get_baseline_questions,
    get_question_by_field,
    get_question_by_index,
)
from app.services.conversation_manager import ConversationManager


def test_baseline_questions_structure():
    """Verify statutory ordering and structure of all 9 baseline questions."""
    questions = get_baseline_questions()
    assert len(questions) == 9
    assert TOTAL_BASELINE_QUESTIONS == 9

    expected_sequence = [
        "name",
        "age",
        "gender",
        "state_district",
        "approx_income_bracket",
        "social_category",
        "occupation",
        "disability_status",
        "stated_need",
    ]
    for idx, expected_field in enumerate(expected_sequence):
        q = get_question_by_index(idx)
        assert q is not None
        assert q.index == idx
        assert q.field_name == expected_field
        assert len(q.hindi_text) > 0


def test_conversation_initialization():
    """Verify session creation and default state attributes."""
    manager = ConversationManager()
    session = manager.create_conversation("test-conv-1")

    assert session.conversation_id == "test-conv-1"
    assert session.status == ConversationStatus.baseline_interview
    assert session.baseline_complete is False
    assert session.current_question_index == 0
    assert len(session.conversation_history) == 0


def test_sequential_question_delivery():
    """Verify get_next_question dispenses questions sequentially in Hindi."""
    manager = ConversationManager()
    session = manager.create_conversation("test-conv-seq")

    q1 = manager.get_next_question("test-conv-seq")
    assert "नमस्ते" in q1 or "नाम" in q1

    # Record first answer
    manager.record_answer("test-conv-seq", "name", "रामवती")

    # Get second question
    q2 = manager.get_next_question("test-conv-seq")
    assert "उम्र" in q2


def test_full_baseline_interview_progression():
    """Verify complete end-to-end interview flow and state transition to 'scheme_matching'."""
    manager = ConversationManager()
    session = manager.create_conversation("test-conv-full")
    cid = session.conversation_id

    answers = [
        ("name", "मेरा नाम रामवती देवी है"),
        ("age", "42 वर्ष"),
        ("gender", "महिला"),
        ("state_district", "उत्तर प्रदेश, बाराबंकी"),
        ("approx_income_bracket", "2 लाख से कम, गरीब परिवार"),
        ("social_category", "ओबीसी"),
        ("occupation", "खेती / किसान"),
        ("disability_status", "नहीं"),
        ("stated_need", "खेत के लिए सोलर पंप और किसान सम्मान निधि सहायता"),
    ]

    for field, ans in answers:
        q_text = manager.get_next_question(cid)
        assert q_text is not None
        state = manager.record_answer(cid, field, ans)

    # Acceptance criteria verification
    assert state.baseline_complete is True
    assert state.status == ConversationStatus.scheme_matching
    assert manager.get_next_question(cid) is None

    # Verify citizen_profile fields
    profile = state.citizen_profile
    assert profile.name == "रामवती देवी"
    assert profile.age == 42
    assert profile.gender == GenderEnum.FEMALE.value
    assert profile.state == "Uttar Pradesh"
    assert profile.district == "Barabanki"
    assert profile.approx_income_bracket == IncomeBracket.BELOW_2_LAKH.value
    assert profile.social_category == SocialCategoryEnum.OBC.value
    assert profile.occupation == "Farmer"
    assert profile.disability_status is False
    assert state.stated_need == "खेत के लिए सोलर पंप और किसान सम्मान निधि सहायता"

    # Verify conversation history has all 18 turns (9 assistant questions + 9 citizen answers)
    assert len(state.conversation_history) == 18


def test_vernacular_age_parsing():
    """Test various formats of age: Devanagari numerals, words, and phrases."""
    manager = ConversationManager()

    # Digits with year words
    assert manager._parse_age("45 साल") == 45
    assert manager._parse_age("उम्र 30 वर्ष") == 30

    # Devanagari numerals
    assert manager._parse_age("४२") == 42
    assert manager._parse_age("२५ साल") == 25

    # Hindi number words
    assert manager._parse_age("पैंतीस") == 35
    assert manager._parse_age("पचास वर्ष") == 50
    assert manager._parse_age("अट्ठाईस") == 28


def test_vernacular_income_bracket_parsing():
    """Test mapping of spoken vernacular income answers to IncomeBracket enum."""
    manager = ConversationManager()

    # Below 2 Lakh
    assert manager._parse_income_bracket("2 लाख से कम") == IncomeBracket.BELOW_2_LAKH.value
    assert manager._parse_income_bracket("गरीब बीपीएल परिवार") == IncomeBracket.BELOW_2_LAKH.value
    assert manager._parse_income_bracket("1.5 lakh सालाना") == IncomeBracket.BELOW_2_LAKH.value

    # 2 to 5 Lakh
    assert manager._parse_income_bracket("2 से 5 लाख के बीच") == IncomeBracket.BETWEEN_2_AND_5_LAKH.value
    assert manager._parse_income_bracket("लगभग 3 लाख") == IncomeBracket.BETWEEN_2_AND_5_LAKH.value

    # Above 5 Lakh
    assert manager._parse_income_bracket("5 लाख से ज़्यादा") == IncomeBracket.ABOVE_5_LAKH.value
    assert manager._parse_income_bracket("7 लाख सालाना") == IncomeBracket.ABOVE_5_LAKH.value


def test_vernacular_gender_and_disability():
    """Test gender and disability parsing."""
    manager = ConversationManager()

    assert manager._parse_gender("महिला") == GenderEnum.FEMALE.value
    assert manager._parse_gender("स्त्री") == GenderEnum.FEMALE.value
    assert manager._parse_gender("पुरुष") == GenderEnum.MALE.value
    assert manager._parse_gender("आदमी") == GenderEnum.MALE.value

    assert manager._parse_disability("नहीं, कोई नहीं है") is False
    assert manager._parse_disability("हाँ, दिव्यांगता है") is True
