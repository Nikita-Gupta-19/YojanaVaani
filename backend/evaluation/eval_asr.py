#!/usr/bin/env python3
"""
ASR Accuracy Evaluation Script — Phase 8.

Evaluates Word Error Rate (WER) of the Hindi Automatic Speech Recognition (ASR) pipeline
(Whisper fine-tune `vasista22/whisper-hindi-small` / AI4Bharat IndicWhisper) broken down by:
1. Short structured responses (Stage 1 Baseline Interview answers)
2. Complex, open-ended vernacular queries (Stage 1 stated_need / Stage 2 queries)

Computes:
- Word Error Rate (WER) per sample and per category using `jiwer`
- Character Error Rate (CER)
- Average transcription latency (seconds)
- Mean ASR confidence score
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Any
import jiwer

# Ensure backend directory is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.asr_service import get_asr_provider
from app.services.tts_service import get_tts_provider

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("eval_asr")


# Structured test suite across Baseline answers and Open-ended queries
ASR_EVAL_DATASET: List[Dict[str, str]] = [
    # -------------------------------------------------------------------------
    # Category 1: Fixed Baseline Interview Short Responses
    # -------------------------------------------------------------------------
    {
        "id": "base_01_name",
        "category": "baseline_short",
        "reference": "मेरा नाम रामेश्वर यादव है",
        "description": "Citizen name reply",
    },
    {
        "id": "base_02_age",
        "category": "baseline_short",
        "reference": "मेरी उम्र पैंतालीस साल है",
        "description": "Citizen age reply",
    },
    {
        "id": "base_03_gender",
        "category": "baseline_short",
        "reference": "पुरुष",
        "description": "Gender reply",
    },
    {
        "id": "base_04_location",
        "category": "baseline_short",
        "reference": "उत्तर प्रदेश जिला बाराबंकी",
        "description": "State and district reply",
    },
    {
        "id": "base_05_income",
        "category": "baseline_short",
        "reference": "सालाना डेढ़ लाख रुपये के करीब",
        "description": "Income bracket reply",
    },
    {
        "id": "base_06_social_cat",
        "category": "baseline_short",
        "reference": "अन्य पिछड़ा वर्ग ओबीसी",
        "description": "Social reservation category reply",
    },
    {
        "id": "base_07_occupation",
        "category": "baseline_short",
        "reference": "हम छोटे सीमांत किसान हैं",
        "description": "Occupation reply",
    },
    {
        "id": "base_08_disability",
        "category": "baseline_short",
        "reference": "नहीं परिवार में कोई दिव्यांग नहीं है",
        "description": "Disability status reply",
    },

    # -------------------------------------------------------------------------
    # Category 2: Complex Open-Ended Stated Need Queries
    # -------------------------------------------------------------------------
    {
        "id": "stated_01_solar_pump",
        "category": "open_ended",
        "reference": "फसल सिंचाई के लिए सोलर पंप योजना और कृषि ऋण में सरकारी सब्सिडी चाहिए",
        "description": "Solar irrigation and crop subsidy query",
    },
    {
        "id": "stated_02_scholarship",
        "category": "open_ended",
        "reference": "बेटी की कॉलेज की पढ़ाई के लिए सरकारी छात्रवृत्ति योजना की जानकारी दीजिए",
        "description": "Higher education scholarship for daughter",
    },
    {
        "id": "stated_03_housing",
        "category": "open_ended",
        "reference": "कच्चे मकान की जगह पक्का घर बनाने के लिए ग्रामीण आवास योजना का लाभ कैसे मिलेगा",
        "description": "PMAY rural pucca house grant request",
    },
    {
        "id": "stated_04_vendor_loan",
        "category": "open_ended",
        "reference": "सड़क पर दुकान लगाने वालों के लिए बिना गारंटी का छोटा लोन चाहिए",
        "description": "PM SVANidhi street vendor microcredit request",
    },
    {
        "id": "stated_05_widow_pension",
        "category": "open_ended",
        "reference": "पति की मृत्यु के बाद विधवा पेंशन और राशन कार्ड सहायता प्राप्त करनी है",
        "description": "Widow pension and food security request",
    },
    {
        "id": "stated_06_disability_device",
        "category": "open_ended",
        "reference": "दिव्यांग पेंशन और कृत्रिम अंग अथवा सहायक उपकरण योजना के लिए आवेदन करना है",
        "description": "Assistive devices and Divyangjan pension request",
    },
]


def run_asr_evaluation() -> Dict[str, Any]:
    """Runs ASR evaluation and returns structured metrics."""
    asr = get_asr_provider()
    tts = get_tts_provider()

    results: List[Dict[str, Any]] = []
    category_metrics: Dict[str, Dict[str, Any]] = {
        "baseline_short": {"refs": [], "hyps": [], "latencies": [], "confs": []},
        "open_ended": {"refs": [], "hyps": [], "latencies": [], "confs": []},
    }

    logger.info("=" * 80)
    logger.info("  1. ASR ACCURACY EVALUATION (Whisper Hindi vs Ground Truth)")
    logger.info("=" * 80)

    for item in ASR_EVAL_DATASET:
        ref_text = item["reference"]
        cat = item["category"]

        # Synthesize reference audio in Hindi
        audio_bytes = tts.synthesize(text=ref_text, language_code="hi")

        start_time = time.perf_counter()
        trans_res = asr.transcribe(audio_bytes=audio_bytes, language_code="hi")
        latency = round(time.perf_counter() - start_time, 3)

        hyp_text = trans_res.text.strip()
        conf = round(trans_res.confidence, 3)

        # Word Error Rate on this sample
        sample_wer = round(jiwer.wer(ref_text, hyp_text), 4) if ref_text and hyp_text else 1.0
        sample_cer = round(jiwer.cer(ref_text, hyp_text), 4) if ref_text and hyp_text else 1.0

        item_result = {
            "id": item["id"],
            "category": cat,
            "description": item["description"],
            "reference": ref_text,
            "hypothesis": hyp_text,
            "wer": sample_wer,
            "cer": sample_cer,
            "confidence": conf,
            "latency_sec": latency,
        }
        results.append(item_result)

        category_metrics[cat]["refs"].append(ref_text)
        category_metrics[cat]["hyps"].append(hyp_text)
        category_metrics[cat]["latencies"].append(latency)
        category_metrics[cat]["confs"].append(conf)

        logger.info(f"[{item['id']}] Category: {cat}")
        logger.info(f"  Ref : {ref_text}")
        logger.info(f"  Hyp : {hyp_text}")
        logger.info(f"  WER : {sample_wer * 100:.1f}% | CER: {sample_cer * 100:.1f}% | Conf: {conf} | Latency: {latency}s\n")

    # Aggregate Metrics per Category
    summary: Dict[str, Any] = {}
    for cat, data in category_metrics.items():
        cat_wer = round(jiwer.wer(data["refs"], data["hyps"]), 4)
        cat_cer = round(jiwer.cer(data["refs"], data["hyps"]), 4)
        avg_lat = round(sum(data["latencies"]) / len(data["latencies"]), 3)
        avg_conf = round(sum(data["confs"]) / len(data["confs"]), 3)

        summary[cat] = {
            "num_samples": len(data["refs"]),
            "wer": cat_wer,
            "cer": cat_cer,
            "avg_latency_sec": avg_lat,
            "avg_confidence": avg_conf,
        }

    all_refs = [r["reference"] for r in results]
    all_hyps = [r["hypothesis"] for r in results]
    total_wer = round(jiwer.wer(all_refs, all_hyps), 4)
    total_cer = round(jiwer.cer(all_refs, all_hyps), 4)
    total_avg_lat = round(sum(r["latency_sec"] for r in results) / len(results), 3)
    total_avg_conf = round(sum(r["confidence"] for r in results) / len(results), 3)

    summary["overall"] = {
        "num_samples": len(results),
        "wer": total_wer,
        "cer": total_cer,
        "avg_latency_sec": total_avg_lat,
        "avg_confidence": total_avg_conf,
    }

    logger.info("-" * 80)
    logger.info(f"ASR Baseline Short Answer WER : {summary['baseline_short']['wer'] * 100:.1f}%")
    logger.info(f"ASR Open-Ended Query WER      : {summary['open_ended']['wer'] * 100:.1f}%")
    logger.info(f"ASR Overall System WER        : {summary['overall']['wer'] * 100:.1f}%")
    logger.info(f"ASR Mean Latency              : {total_avg_lat}s")
    logger.info("-" * 80)

    return {
        "summary": summary,
        "detailed_results": results,
    }


if __name__ == "__main__":
    run_asr_evaluation()
