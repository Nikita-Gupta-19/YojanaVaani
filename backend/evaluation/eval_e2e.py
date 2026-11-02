#!/usr/bin/env python3
"""
End-to-End Conversational Task Success Rate Evaluation — Phase 8.

Simulates 20 complete citizen sessions from initialization (/conversation/start)
through all 9 baseline interview turns, Stage 2 RAG agent reasoning, and document OCR
confirmation (if requested), measuring end-to-end task completion and escalation metrics.

Metrics:
- End-to-End Task Completion Rate (%)
- Natural Resolution Rate without Escalation (%)
- Human CSC Escalation Rate (%)
- Mean Dialogue Turns to Resolution
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("eval_e2e")

client = TestClient(app)

E2E_CITIZEN_PERSONAS: List[Dict[str, Any]] = [
    # 1. Agriculture
    {
        "id": "e2e_01_farmer_solar",
        "category": "Agriculture",
        "name": "रामेश्वर यादव",
        "turns": ["रामेश्वर यादव", "45", "पुरुष", "उत्तर प्रदेश बाराबंकी", "डेढ़ लाख", "ओबीसी", "किसान", "नहीं", "सोलर पंप योजना और फसल ऋण सब्सिडी"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_02_farmer_kcc",
        "category": "Agriculture",
        "name": "बलदेव सिंह",
        "turns": ["बलदेव सिंह", "38", "पुरुष", "उत्तर प्रदेश सीतापुर", "1 लाख", "सामान्य", "खेती", "नहीं", "किसान क्रेडिट कार्ड से कम ब्याज पर कर्ज"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_03_dairy_farmer",
        "category": "Agriculture",
        "name": "गोपाल यादव",
        "turns": ["गोपाल यादव", "32", "पुरुष", "उत्तर प्रदेश वाराणसी", "2 लाख", "ओबीसी", "डेयरी पशुपालन", "नहीं", "दुधारू गाय भैंस खरीदने के लिए पशुपालक योजना"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_04_marginal_pmkisan",
        "category": "Agriculture",
        "name": "हरीश चंद्र",
        "turns": ["हरीश चंद्र", "50", "पुरुष", "उत्तर प्रदेश बाराबंकी", "80000", "एससी", "छोटा किसान", "नहीं", "सालाना 6000 रुपये वाली किसान सम्मान निधि"],
        "expect_escalate": False,
    },

    # 2. Education
    {
        "id": "e2e_05_daughter_scholarship",
        "category": "Education",
        "name": "सुनीता देवी",
        "turns": ["सुनीता देवी", "41", "महिला", "उत्तर प्रदेश लखनऊ", "1.2 लाख", "ओबीसी", "गृहणी", "नहीं", "बेटी की बीटेक इंजीनियरिंग की प्रगति स्कॉलरशिप"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_06_sc_higher_studies",
        "category": "Education",
        "name": "रोहित कुमार",
        "turns": ["रोहित कुमार", "23", "पुरुष", "उत्तर प्रदेश कानपुर", "1.5 लाख", "एससी", "विद्यार्थी", "नहीं", "अनुसूचित जाति के छात्रों के लिए विदेश में पढ़ाई छात्रवृत्ति"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_07_merit_scholarship",
        "category": "Education",
        "name": "अंकित मिश्रा",
        "turns": ["अंकित मिश्रा", "20", "पुरुष", "दिल्ली मध्य दिल्ली", "1.8 लाख", "सामान्य", "छात्र", "नहीं", "कॉलेज फीस के लिए मेरिट कम मीन्स स्कॉलरशिप"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_08_free_textbooks",
        "category": "Education",
        "name": "शबाना खातून",
        "turns": ["शबाना खातून", "35", "महिला", "दिल्ली उत्तर पूर्व दिल्ली", "1 लाख", "ओबीसी", "सिलाई काम", "नहीं", "सरकारी स्कूल के बच्चों के लिए मुफ्त किताबें और यूनिफॉर्म"],
        "expect_escalate": False,
    },

    # 3. Women & Child
    {
        "id": "e2e_09_widow_pension",
        "category": "Women & Child",
        "name": "कमला देवी",
        "turns": ["कमला देवी", "48", "महिला", "दिल्ली शाहदरा", "75000", "सामान्य", "गृहणी", "नहीं", "निराश्रित विधवा पेंशन योजना और राशन सहायता"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_10_daughter_marriage",
        "category": "Women & Child",
        "name": "शांति देवी",
        "turns": ["शांति देवी", "44", "महिला", "उत्तर प्रदेश प्रयागराज", "60000", "एससी", "खेतीहर मजदूर", "नहीं", "गरीब विधवा की बेटी के विवाह के लिए सरकारी अनुदान"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_11_delhi_ladli",
        "category": "Women & Child",
        "name": "मीनाक्षी गुप्ता",
        "turns": ["मीनाक्षी गुप्ता", "29", "महिला", "दिल्ली दक्षिण दिल्ली", "1.5 लाख", "सामान्य", "दुकानदार", "नहीं", "नवजात बच्ची के लिए दिल्ली लाडली योजना"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_12_matru_vandana",
        "category": "Women & Child",
        "name": "पूजा शर्मा",
        "turns": ["पूजा शर्मा", "24", "महिला", "उत्तर प्रदेश गोरखपुर", "1.2 लाख", "सामान्य", "गृहणी", "नहीं", "गर्भवती महिलाओं के लिए 5000 रुपये वाली मातृ वंदना योजना"],
        "expect_escalate": False,
    },

    # 4. Health & Disability
    {
        "id": "e2e_13_delhi_arogya",
        "category": "Health",
        "name": "मनोज कुमार",
        "turns": ["मनोज कुमार", "42", "पुरुष", "दिल्ली मध्य दिल्ली", "1.4 लाख", "ओबीसी", "मजदूर", "नहीं", "गंभीर बीमारी के ऑपरेशन के लिए दिल्ली आरोग्य कोष सहायता"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_14_divyang_pension",
        "category": "Health & Disability",
        "name": "रामसेवक",
        "turns": ["रामसेवक", "33", "पुरुष", "उत्तर प्रदेश कानपुर", "80000", "ओबीसी", "बेरोजगार", "हाँ", "दिव्यांग पेंशन और मुफ्त मोटराइज्ड ट्राइसाइकिल उपकरण"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_15_tb_nutrition",
        "category": "Health",
        "name": "जगत नारायण",
        "turns": ["जगत नारायण", "46", "पुरुष", "उत्तर प्रदेश वाराणसी", "90000", "एससी", "मजदूर", "नहीं", "टीबी के इलाज के दौरान पोषण के लिए निक्षय पोषण योजना"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_16_senior_citizen",
        "category": "Health",
        "name": "रामप्रसाद",
        "turns": ["रामप्रसाद", "68", "पुरुष", "उत्तर प्रदेश अयोध्या", "65000", "सामान्य", "वृद्ध", "नहीं", "60 वर्ष से अधिक आयु वालों के लिए वृद्धावस्था पेंशन"],
        "expect_escalate": False,
    },

    # 5. Housing & Urban Livelihood
    {
        "id": "e2e_17_construction_house",
        "category": "Housing & Worker Welfare",
        "name": "दीनानाथ",
        "turns": ["दीनानाथ", "39", "पुरुष", "दिल्ली शाहदरा", "1.3 लाख", "एससी", "निर्माण श्रमिक", "नहीं", "पंजीकृत मजदूर के लिए पक्का मकान बनाने की सहायता"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_18_street_vendor_loan",
        "category": "Housing & Worker Welfare",
        "name": "मुकेश कुमार",
        "turns": ["मुकेश कुमार", "35", "पुरुष", "दिल्ली मध्य दिल्ली", "1.1 लाख", "ओबीसी", "सड़क पर फल की रेहड़ी", "नहीं", "रेहड़ी पटरी वालों के लिए 10000 का स्वनिधि लोन"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_19_worker_travel_pass",
        "category": "Housing & Worker Welfare",
        "name": "सुरेश चंद्र",
        "turns": ["सुरेश चंद्र", "43", "पुरुष", "दिल्ली पूर्व दिल्ली", "1.2 लाख", "सामान्य", "मजदूर", "नहीं", "मजदूरों के लिए डीटीसी बस में फ्री यात्रा पास"],
        "expect_escalate": False,
    },
    {
        "id": "e2e_20_infeasible_car_subsidy",
        "category": "Out-of-Scope (Escalation Expected)",
        "name": "राजेश मल्होत्रा",
        "turns": ["राजेश मल्होत्रा", "54", "पुरुष", "दिल्ली दक्षिण दिल्ली", "8 लाख", "सामान्य", "व्यापारी", "नहीं", "निजी लग्जरी कार और हवाई यात्रा हेतु 90% सरकारी छूट"],
        "expect_escalate": True,
    },
]


def run_e2e_evaluation() -> Dict[str, Any]:
    """Runs complete end-to-end multi-turn evaluation across 20 citizen personas."""
    logger.info("=" * 80)
    logger.info("  6. END-TO-END TASK SUCCESS RATE EVALUATION (20 Citizen Personas)")
    logger.info("=" * 80)

    completed_tasks = 0
    direct_resolutions = 0
    escalations = 0
    total_turns_logged = 0

    category_stats: Dict[str, Dict[str, int]] = {}
    detailed_personas: List[Dict[str, Any]] = []

    for item in E2E_CITIZEN_PERSONAS:
        p_id = item["id"]
        cat = item["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "success": 0, "escalated": 0}
        category_stats[cat]["total"] += 1

        # 1. Start Session
        res_start = client.post("/conversation/start")
        if res_start.status_code != 200:
            logger.error(f"Failed to start conversation for {p_id}")
            continue

        cid = res_start.json()["conversation_id"]
        turns_count = 1
        final_action = None

        # 2. Feed 9 Baseline Answers sequentially
        for ans in item["turns"]:
            res_turn = client.post(f"/conversation/{cid}/respond", data={"text": ans})
            if res_turn.status_code == 200:
                turns_count += 1
                final_action = res_turn.json()["action"]

        # 3. Handle document upload if requested
        if final_action and final_action.get("type") == "request_document":
            res_confirm = client.post(
                f"/conversation/{cid}/confirm_document",
                data={"confirmed": True, "fields": json.dumps({"annual_income": 60000})}
            )
            if res_confirm.status_code == 200:
                turns_count += 1
                final_action = res_confirm.json()["action"]

        # Check outcome
        is_success = False
        is_escalated = False

        if final_action:
            action_type = final_action.get("type")
            if action_type == "present_results":
                is_success = True
                direct_resolutions += 1
                category_stats[cat]["success"] += 1
            elif action_type == "escalate":
                is_escalated = True
                escalations += 1
                category_stats[cat]["escalated"] += 1
                if item["expect_escalate"]:
                    is_success = True  # Correctly escalated an infeasible query!

        if is_success:
            completed_tasks += 1

        total_turns_logged += turns_count

        detailed_personas.append({
            "id": p_id,
            "category": cat,
            "name": item["name"],
            "turns_count": turns_count,
            "final_action_type": final_action.get("type") if final_action else "None",
            "is_success": is_success,
            "is_escalated": is_escalated,
            "schemes_found": len(final_action.get("schemes", [])) if final_action and final_action.get("schemes") else 0,
        })

        res_str = "✓ SUCCESS" if is_success else "✕ FAILED"
        act_str = final_action.get("type") if final_action else "None"
        logger.info(f"[{p_id}] {res_str} | Final Action: {act_str:15} | Turns: {turns_count} | Cat: {cat}")

    total_personas = len(E2E_CITIZEN_PERSONAS)
    success_rate = round(completed_tasks / total_personas, 4)
    direct_res_rate = round(direct_resolutions / total_personas, 4)
    escalation_rate = round(escalations / total_personas, 4)
    avg_turns = round(total_turns_logged / total_personas, 2)

    logger.info("-" * 80)
    logger.info(f"Total Evaluated Personas       : {total_personas}")
    logger.info(f"End-to-End Task Success Rate   : {success_rate * 100:.1f}% ({completed_tasks}/{total_personas})")
    logger.info(f"Direct Scheme Resolution Rate  : {direct_res_rate * 100:.1f}% ({direct_resolutions}/{total_personas})")
    logger.info(f"Escalation Rate to CSC Kiosk   : {escalation_rate * 100:.1f}% ({escalations}/{total_personas})")
    logger.info(f"Average Dialogue Turns/Session : {avg_turns}")
    logger.info("-" * 80)

    # Category breakdown
    cat_summary = {}
    for c, stats in category_stats.items():
        n = stats["total"]
        cat_summary[c] = {
            "total": n,
            "success_rate": round(stats["success"] / n, 4),
            "escalation_rate": round(stats["escalated"] / n, 4),
        }
        logger.info(f"  {c:28} : Success = {cat_summary[c]['success_rate']*100:5.1f}% | Escalated = {cat_summary[c]['escalation_rate']*100:4.1f}% (N={n})")

    return {
        "summary": {
            "total_personas": total_personas,
            "task_success_rate": success_rate,
            "direct_resolution_rate": direct_res_rate,
            "escalation_rate": escalation_rate,
            "avg_dialogue_turns": avg_turns,
        },
        "category_breakdown": cat_summary,
        "detailed_personas": detailed_personas,
    }


if __name__ == "__main__":
    run_e2e_evaluation()
