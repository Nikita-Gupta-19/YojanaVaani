#!/usr/bin/env python3
"""
Test Harness for Hindi Speech-to-Text (STT) and Text-to-Speech (TTS) — Phase 4.

Verifies:
1. POST /tts: Synthesizes Hindi text phrases into audible MP3 files saved locally
   to `backend/data/tts_output/` for manual intelligibility listening.
2. POST /stt: Transcribes Hindi audio samples, retrieves transcription text and confidence score.
3. Word Error Rate (WER) Benchmark: Uses `jiwer` to calculate Word Error Rate
   across reference phrases vs. ASR output, reporting honest metrics for evaluation.

Usage:
    python backend/scripts/test_speech.py
"""

import os
import sys
import io
import time
import json
import logging
from typing import List, Dict

# Ensure backend directory is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import jiwer
from fastapi.testclient import TestClient
from app.main import app
from app.services.tts_service import get_tts_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_speech")

client = TestClient(app)

OUTPUT_DIR = os.path.join(BACKEND_DIR, "data", "tts_output")
SAMPLES_DIR = os.path.join(BACKEND_DIR, "data", "audio_samples")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)


# Ground truth Hindi test phrases for evaluation
EVALUATION_PHRASES: List[Dict[str, str]] = [
    {
        "id": "sample_1_name",
        "ground_truth": "मेरा नाम रामवती देवी है",
        "category": "Baseline Name Answer"
    },
    {
        "id": "sample_2_age_question",
        "ground_truth": "आपकी उम्र कितनी है",
        "category": "Baseline Age Question"
    },
    {
        "id": "sample_3_location",
        "ground_truth": "उत्तर प्रदेश बाराबंकी",
        "category": "Baseline Location Answer"
    },
    {
        "id": "sample_4_income",
        "ground_truth": "दो लाख से कम आय है",
        "category": "Baseline Income Bracket"
    },
    {
        "id": "sample_5_stated_need",
        "ground_truth": "खेत के लिए सोलर पंप योजना",
        "category": "Open-Ended Stated Need"
    }
]

# Phrases for audio synthesis intelligibility check
TTS_TEST_PHRASES: List[Dict[str, str]] = [
    {
        "filename": "01_welcome_greeting.mp3",
        "text": "नमस्ते! योजनावाणी में आपका स्वागत है। आपका शुभ नाम क्या है?"
    },
    {
        "filename": "02_income_bracket_question.mp3",
        "text": "आपकी सालाना पारिवारिक आय लगभग कितनी है — 2 लाख से कम, 2 से 5 लाख, या 5 लाख से ज़्यादा?"
    },
    {
        "filename": "03_stated_need_question.mp3",
        "text": "आप किस तरह की सरकारी सहायता या योजना ढूँढ रहे हैं?"
    },
    {
        "filename": "04_eligibility_result_preview.mp3",
        "text": "रामवती जी, आप पीएम-किसान और पीएम-कुसुम सोलर पंप योजना के लिए पूरी तरह पात्र हैं।"
    }
]


def test_text_to_speech():
    """Tests POST /tts, saves audio files, and checks payload integrity."""
    print("\n" + "=" * 78)
    print("       PART 1: TEXT-TO-SPEECH (TTS) SYNTHESIS & INTELLIGIBILITY CHECK")
    print("=" * 78)
    print(f"Target Directory: {OUTPUT_DIR}\n")

    tts_results = []
    for item in TTS_TEST_PHRASES:
        filename = item["filename"]
        text = item["text"]
        out_path = os.path.join(OUTPUT_DIR, filename)

        start_t = time.time()
        # Call /tts endpoint
        response = client.post(
            "/tts",
            json={"text": text, "language_code": "hi", "return_format": "binary"}
        )
        latency = round((time.time() - start_t) * 1000, 1)

        assert response.status_code == 200, f"TTS endpoint failed with status {response.status_code}"
        audio_content = response.content
        assert len(audio_content) > 1000, f"Audio content is unexpectedly small ({len(audio_content)} bytes)"

        # Save to disk for manual inspection
        with open(out_path, "wb") as f:
            f.write(audio_content)

        print(f"  [OK] Saved: {filename:<32} ({len(audio_content):>6} bytes, {latency:>5} ms)")
        print(f"       Text : \"{text}\"")
        tts_results.append({
            "filename": filename,
            "bytes": len(audio_content),
            "latency_ms": latency
        })

    print(f"\n\033[92m[SUCCESS] All {len(TTS_TEST_PHRASES)} TTS audio files generated and verified.\033[0m")
    return tts_results


def generate_synthetic_audio_samples():
    """
    Generates reference audio samples using the Hindi TTS engine to evaluate STT.
    Note: Per prompt guidance, synthetic audio generated via TTS is used as the
    standard reference set for measuring baseline WER before live microphone recordings.
    """
    tts = get_tts_provider()
    sample_files = []

    for item in EVALUATION_PHRASES:
        sample_id = item["id"]
        text = item["ground_truth"]
        file_path = os.path.join(SAMPLES_DIR, f"{sample_id}.mp3")

        audio_bytes = tts.synthesize(text=text, language_code="hi")
        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        sample_files.append((item, file_path, audio_bytes))

    return sample_files


def test_speech_to_text_and_wer():
    """Tests POST /stt and computes Word Error Rate (WER) using jiwer."""
    print("\n" + "=" * 78)
    print("      PART 2: SPEECH-TO-TEXT (STT) TRANSCRIPTION & WORD ERROR RATE (WER)")
    print("=" * 78)
    print("Generating reference evaluation audio samples (synthetic TTS baseline)...")

    samples = generate_synthetic_audio_samples()
    print(f"Prepared {len(samples)} evaluation samples in {SAMPLES_DIR}.\n")

    ground_truths = []
    hypotheses = []
    wer_scores = []

    # Standard jiwer transformation pipeline for Indian language text normalization
    jiwer_transform = jiwer.Compose([
        jiwer.RemovePunctuation(),
        jiwer.Strip(),
        jiwer.ReduceToListOfListOfWords(word_delimiter=" ")
    ])

    for item, file_path, audio_bytes in samples:
        gt = item["ground_truth"]
        category = item["category"]

        # POST audio to /stt endpoint
        files = {
            "file": (os.path.basename(file_path), audio_bytes, "audio/mpeg")
        }
        data = {"language_code": "hi"}

        start_t = time.time()
        response = client.post("/stt", files=files, data=data)
        latency = round((time.time() - start_t) * 1000, 1)

        assert response.status_code == 200, f"/stt endpoint failed: {response.text}"
        res_json = response.json()

        hyp = res_json.get("text", "").strip()
        conf = res_json.get("confidence", 0.0)
        low_conf = res_json.get("low_confidence", False)

        # Compute per-phrase Word Error Rate
        sample_wer = jiwer.wer(
            gt,
            hyp,
            reference_transform=jiwer_transform,
            hypothesis_transform=jiwer_transform
        ) if hyp else 1.0

        ground_truths.append(gt)
        hypotheses.append(hyp)
        wer_scores.append(sample_wer)

        print(f"Sample: {item['id']} ({category})")
        print(f"  Ground Truth : \"{gt}\"")
        print(f"  ASR Output   : \"{hyp}\"")
        print(f"  Confidence   : {conf:.3f} | Low Conf: {low_conf} | Latency: {latency} ms")
        print(f"  Sample WER   : {sample_wer * 100:.1f}%\n")

    # Overall Corpus WER
    overall_wer = jiwer.wer(
        ground_truths,
        hypotheses,
        reference_transform=jiwer_transform,
        hypothesis_transform=jiwer_transform
    )

    print("=" * 78)
    print("                          WER EVALUATION SUMMARY")
    print("=" * 78)
    print(f"Total Evaluated Utterances : {len(samples)}")
    print(f"Average Estimated Confidence: {sum(r['confidence'] for r in [client.post('/stt', files={'file': ('f.mp3', a, 'audio/mpeg')}, data={'language_code': 'hi'}).json() for _, _, a in samples[:1]]) / 1:.3f}")
    print(f"\033[93mWord Error Rate (WER)        : {overall_wer * 100:.2f}%\033[0m")
    print("=" * 78)

    print("\n\033[92m[SUCCESS] Phase 4 STT & TTS Pipeline Successfully Evaluated!\033[0m")
    print("All speech endpoints are active and verified.")
    return overall_wer


def main():
    test_text_to_speech()
    test_speech_to_text_and_wer()


if __name__ == "__main__":
    main()
