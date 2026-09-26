#!/usr/bin/env python3
"""
Interactive and Automated Text-Only Test Harness for YojanaVaani Baseline Interview (Phase 3).

Simulates Stage 1 conversation:
- Dispenses Hindi baseline questions turn-by-turn.
- Accepts typed input (representing transcribed speech from IndicWhisper).
- Displays citizen_profile getting incrementally populated.
- Verifies that status transitions to 'scheme_matching' and baseline_complete=True.

Usage:
    # 1. Interactive mode (prompts you for typed answers in terminal):
    python backend/scripts/test_interview_cli.py

    # 2. Automated demo mode (runs complete persona automatically):
    python backend/scripts/test_interview_cli.py --demo

    # 3. Specific persona demo:
    python backend/scripts/test_interview_cli.py --demo --persona student
"""

import os
import sys
import argparse
import json
import time

# Ensure project backend directory is on python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.conversation_manager import ConversationManager
from app.services.baseline_interview import (
    BASELINE_QUESTIONS,
    TOTAL_BASELINE_QUESTIONS,
    get_question_by_index,
)
from app.models.conversation import ConversationStatus


# Preset persona answers for automated validation
DEMO_PERSONAS = {
    "farmer": {
        "title": "रामवती देवी (महिला किसान - बाराबंकी, उत्तर प्रदेश)",
        "answers": [
            "मेरा नाम रामवती देवी है",
            "42 वर्ष",
            "महिला",
            "उत्तर प्रदेश, बाराबंकी",
            "2 लाख से कम, गरीब परिवार",
            "ओबीसी (OBC)",
            "खेती / छोटी किसान",
            "नहीं, कोई दिव्यांगता नहीं है",
            "खेत के लिए सोलर पंप और सिंचाई सहायता (PM-KUSUM) और किसान सम्मान निधि"
        ]
    },
    "student": {
        "title": "अमित कुमार (विद्यार्थी - दिल्ली)",
        "answers": [
            "अमित कुमार",
            "१९ साल",
            "पुरुष",
            "दिल्ली, शाहदरा",
            "2 से 5 लाख सालाना",
            "अनुसूचित जाति (SC)",
            "पढ़ाई / कॉलेज छात्र",
            "नहीं",
            "उच्च शिक्षा के लिए छात्रवृत्ति और लैपटॉप सहायता योजना"
        ]
    },
    "elderly_widow": {
        "title": "शान्ति बाई (बुजुर्ग विधवा - मध्य प्रदेश)",
        "answers": [
            "शान्ति बाई",
            "पैंसठ वर्ष",
            "महिला",
            "मध्य प्रदेश, रीवा",
            "50 हजार से भी कम",
            "सामान्य",
            "कोई काम नहीं, बुजुर्ग",
            "हाँ, चलने में असमर्थ",
            "विधवा पेंशन और मुफ्त राशन की सहायता चाहिए"
        ]
    }
}


def print_header():
    print("\n" + "=" * 78)
    print("      YOJANAVAANI (योजनावाणी) — STAGE 1 BASELINE INTERVIEW TEST HARNESS")
    print("=" * 78)
    print("Fixed sequence interview covering core demographic eligibility criteria.")
    print("Language: Vernacular Hindi (Devanagari) | Output: Structured CitizenProfile\n")


def print_profile_state(profile_dict: dict):
    print("\n  [CITIZEN PROFILE CURRENT STATE]")
    print("  +-------------------------------------------------------------+")
    for k, v in profile_dict.items():
        val_str = f"'{v}'" if isinstance(v, str) else str(v)
        status_color = "\033[92m" if v is not None else "\033[90m"
        reset_color = "\033[0m"
        print(f"  |  {k:<24} : {status_color}{val_str:<32}{reset_color} |")
    print("  +-------------------------------------------------------------+")


def run_interview(demo_mode: bool = False, persona_key: str = "farmer"):
    print_header()

    manager = ConversationManager()
    session = manager.create_conversation()
    cid = session.conversation_id

    print(f"Session Initialized. Conversation ID: {cid}")
    print(f"Initial Status: {session.status.value} | Total Questions: {TOTAL_BASELINE_QUESTIONS}")
    print("-" * 78)

    persona = DEMO_PERSONAS.get(persona_key, DEMO_PERSONAS["farmer"])
    if demo_mode:
        print(f"Running in AUTOMATED DEMO MODE using persona: {persona['title']}\n")

    for q_idx in range(TOTAL_BASELINE_QUESTIONS):
        q_meta = manager.get_current_question_metadata(cid)
        if not q_meta:
            break

        question_text = manager.get_next_question(cid)
        print(f"\n[Turn {q_idx + 1}/{TOTAL_BASELINE_QUESTIONS}] ASSISTANT:")
        print(f"  Hindi  : \033[96m{question_text}\033[0m")
        print(f"  Phonetic: {q_meta.transliteration}")
        print(f"  Field  : {q_meta.field_name} ({q_meta.prompt_explanation})")

        if demo_mode:
            answer = persona["answers"][q_idx]
            time.sleep(0.1)  # Brief pause for readable output
            print(f"CITIZEN (simulated): \033[93m{answer}\033[0m")
        else:
            try:
                answer = input("CITIZEN (type response) > ")
            except (KeyboardInterrupt, EOFError):
                print("\n\nInterview aborted by user.")
                sys.exit(0)

        # Record and parse the answer
        session = manager.record_answer(
            conversation_id=cid,
            question_field=q_meta.field_name,
            answer_text=answer
        )

        # Show updated profile snapshot
        print_profile_state(session.citizen_profile.model_dump())

    # Final Verification and Acceptance Check
    print("\n" + "=" * 78)
    print("                    INTERVIEW COMPLETION VERIFICATION")
    print("=" * 78)

    print(f"1. Baseline Complete Flag : {session.baseline_complete} (Expected: True)")
    print(f"2. Final Session Status   : {session.status.value} (Expected: 'scheme_matching')")
    print(f"3. Stated Need Recorded   : \"{session.stated_need}\"")
    print(f"4. Total History Turns    : {len(session.conversation_history)} turns (9 assistant + 9 citizen = 18)")

    # Assertions
    assert session.baseline_complete is True, "ERROR: baseline_complete is not True!"
    assert session.status == ConversationStatus.scheme_matching, "ERROR: Status did not transition to 'scheme_matching'!"
    assert session.stated_need is not None, "ERROR: stated_need was not recorded!"
    assert len(session.conversation_history) == 18, f"ERROR: Expected 18 turns, got {len(session.conversation_history)}"

    print("\n\033[92m[SUCCESS] All Phase 3 Acceptance Criteria Met!\033[0m")
    print("CitizenProfile is fully populated and ready for Phase 5 LangGraph agentic reasoning.")
    print("=" * 78 + "\n")
    return session


def main():
    parser = argparse.ArgumentParser(description="YojanaVaani Phase 3 Baseline Interview Test Harness")
    parser.add_argument("--demo", action="store_true", help="Run automated interview without interactive prompt")
    parser.add_argument(
        "--persona",
        choices=["farmer", "student", "elderly_widow"],
        default="farmer",
        help="Persona to simulate when running with --demo"
    )
    args = parser.parse_args()

    # If stdin is not a tty (piped or headless), auto-switch to demo
    is_interactive = sys.stdin.isatty() and not args.demo
    run_interview(demo_mode=not is_interactive, persona_key=args.persona)


if __name__ == "__main__":
    main()
