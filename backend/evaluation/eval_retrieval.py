#!/usr/bin/env python3
"""
Retrieval Accuracy Evaluation Script — Phase 8.

Evaluates semantic search and RAG retrieval over ChromaDB index (`yojana_schemes`)
using multilingual sentence embeddings (`paraphrase-multilingual-mpnet-base-v2`).

Dataset:
35 manually curated vernacular Hindi citizen queries mapped to ground truth scheme targets
spanning all 5 priority domains (Agriculture, Education, Women & Child, Health, Housing/Labour).

Metrics:
- Top-1 Accuracy (%)
- Top-3 Accuracy (%)
- Top-5 Accuracy (%)
- Mean Reciprocal Rank (MRR)
- Sectoral category breakdown
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.mcp.tools import search_schemes

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("eval_retrieval")

# 35 Ground truth query-to-scheme evaluation benchmark pairs
RETRIEVAL_BENCHMARK_PAIRS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. Agriculture & Farmers (7 pairs)
    # -------------------------------------------------------------------------
    {
        "id": "agri_01",
        "category": "Agriculture & Farmers",
        "query": "किसानों को फसल सिंचाई और सोलर पंप लगाने के लिए सरकारी सब्सिडी",
        "target_keywords": ["solar", "irrigation", "pump", "farmer", "krishi", "kisan"],
        "target_schemes": ["National Solar Science Fellowship Programme", "Kisan Credit Card", "Krishak Durghatna Kalyan Yojana"],
    },
    {
        "id": "agri_02",
        "category": "Agriculture & Farmers",
        "query": "छोटे सीमांत किसानों के लिए सालाना ₹6000 की आर्थिक सहायता सम्मान निधि",
        "target_keywords": ["kisan", "samman", "farmer", "krishi", "assistance"],
        "target_schemes": ["PM-KISAN", "Krishak Durghatna Kalyan Yojana", "Kisan"],
    },
    {
        "id": "agri_03",
        "category": "Agriculture & Farmers",
        "query": "खेती के दौरान किसान की दुर्घटना या मृत्यु होने पर परिवार को मुआवजा",
        "target_keywords": ["durghatna", "accidental", "death", "krishak", "farmer"],
        "target_schemes": ["Krishak Durghatna Kalyan Yojana", "Accidental Death Assistance for the Construction Workers"],
    },
    {
        "id": "agri_04",
        "category": "Agriculture & Farmers",
        "query": "दुधारू पशुओं और डेयरी पालन के लिए पशुपालक प्रोत्साहन योजना",
        "target_keywords": ["pashupalak", "dairy", "animal", "cattle"],
        "target_schemes": ["Mukhyamantri Pragatishil Pashupalak Protsahan Yojana", "Animal Husbandry"],
    },
    {
        "id": "agri_05",
        "category": "Agriculture & Farmers",
        "query": "गोबर और जैविक कचरे से बायोगैस संयंत्र लगाने हेतु गोवर्धन योजना",
        "target_keywords": ["gobardhan", "biogas", "waste", "clean"],
        "target_schemes": ["GOBARdhan Scheme", "Galvanizing Organic Bio-Agro Resources Dhan"],
    },
    {
        "id": "agri_06",
        "category": "Agriculture & Farmers",
        "query": "फसल कटाई के बाद अनाज भंडारण और गोदाम निर्माण हेतु वित्तीय सहायता",
        "target_keywords": ["storage", "warehouse", "godown", "agriculture"],
        "target_schemes": ["Agriculture Infrastructure Fund", "Rural Godown"],
    },
    {
        "id": "agri_07",
        "category": "Agriculture & Farmers",
        "query": "किसान क्रेडिट कार्ड द्वारा बिना गारंटी कम ब्याज पर अल्पकालिक फसल ऋण",
        "target_keywords": ["kisan credit card", "kcc", "crop loan", "interest subsidy"],
        "target_schemes": ["Kisan Credit Card", "Interest Subvention for Short Term Crop Loans"],
    },

    # -------------------------------------------------------------------------
    # 2. Education & Learning (8 pairs)
    # -------------------------------------------------------------------------
    {
        "id": "edu_01",
        "category": "Education & Learning",
        "query": "कॉलेज में पढ़ने वाले दिव्यांग विद्यार्थियों के लिए विशेष उच्च शिक्षा सहायता",
        "target_keywords": ["disabilities", "college", "higher education", "special needs"],
        "target_schemes": ["Persons With Disabilities Scheme In Colleges: Higher Education For Persons With Special Needs"],
    },
    {
        "id": "edu_02",
        "category": "Education & Learning",
        "query": "अनुसूचित जाति के छात्रों के लिए विदेश में उच्च शिक्षा हेतु वित्तीय अनुदान",
        "target_keywords": ["sc students", "higher studies abroad", "abroad scholarship"],
        "target_schemes": ["Financial Assistance to SC Students for Pursuing Higher Studies Abroad"],
    },
    {
        "id": "edu_03",
        "category": "Education & Learning",
        "query": "गरीब मेधावी विद्यार्थियों के लिए मेरिट कम मीन्स छात्रवृत्ति योजना",
        "target_keywords": ["merit cum means", "financial assistance", "scholarship", "tuition fee"],
        "target_schemes": ["Merit Cum Means Linked Financial Assistance Scheme", "Merit Scholarship for College Students"],
    },
    {
        "id": "edu_04",
        "category": "Education & Learning",
        "query": "कक्षा 1 से 12 तक के बच्चों के लिए मुफ्त पाठ्यपुस्तक वितरण योजना",
        "target_keywords": ["free supply of text books", "text books", "school books"],
        "target_schemes": ["Free Supply of Text Books", "Free Supply of Stationery"],
    },
    {
        "id": "edu_05",
        "category": "Education & Learning",
        "query": "तकनीकी शिक्षा में डिप्लोमा और डिग्री कर रही बालिकाओं के लिए प्रगति छात्रवृत्ति",
        "target_keywords": ["pragati", "aicte", "girl students", "technical degree"],
        "target_schemes": ["Pragati Scholarship Scheme For Girl Students (Technical Degree)", "Pragati Scholarship"],
    },
    {
        "id": "edu_06",
        "category": "Education & Learning",
        "query": "अल्पसंख्यक समुदाय के छात्रों के लिए पोस्ट-मैट्रिक और उच्च शिक्षा स्कॉलरशिप",
        "target_keywords": ["minority", "post-matric", "scholarship"],
        "target_schemes": ["Post Matric Scholarship Schemes Minorities", "Post Matric Scholarship"],
    },
    {
        "id": "edu_07",
        "category": "Education & Learning",
        "query": "युवाओं को अपना स्वरोजगार स्थापित करने के लिए राजीव गांधी स्वावलंबन लोन योजना",
        "target_keywords": ["rajiv gandhi", "swavlamban", "rojgar", "self employment"],
        "target_schemes": ["Rajiv Gandhi Swavlamban Rojgar Yojna", "Self Employment Scheme"],
    },
    {
        "id": "edu_08",
        "category": "Education & Learning",
        "query": "सैनिकों और पूर्व सैनिकों के बच्चों के लिए प्रधानमंत्री छात्रवृत्ति योजना",
        "target_keywords": ["prime minister scholarship", "pmss", "ex-servicemen", "wards"],
        "target_schemes": ["Prime Minister's Scholarship Scheme For Wards Of States/UTs Police Personnel", "PMSS"],
    },

    # -------------------------------------------------------------------------
    # 3. Women & Child Welfare (7 pairs)
    # -------------------------------------------------------------------------
    {
        "id": "women_01",
        "category": "Women & Child",
        "query": "गरीब बेसहारा विधवा महिलाओं की बेटियों और अनाथ कन्याओं के विवाह हेतु आर्थिक सहायता",
        "target_keywords": ["daughters of poor widows", "marriage", "orphan girls", "financial assistance"],
        "target_schemes": ["Financial Assistance For The Marriage Of Daughters Of Poor Widows And Orphan Girls"],
    },
    {
        "id": "women_02",
        "category": "Women & Child",
        "query": "संकटग्रस्त और निराश्रित विधवा महिलाओं के लिए मासिक पेंशन योजना",
        "target_keywords": ["widow pension", "women in distress", "delhi pension scheme", "destitute women"],
        "target_schemes": ["Delhi Pension Scheme To Women In Distress (Widow Pension)", "Indira Gandhi National Widow Pension Scheme"],
    },
    {
        "id": "women_03",
        "category": "Women & Child",
        "query": "बालिकाओं के जन्म और स्कूली शिक्षा को बढ़ावा देने के लिए दिल्ली लाडली योजना",
        "target_keywords": ["ladli", "girl child", "school education"],
        "target_schemes": ["Delhi Ladli Scheme", "Mukhyamantri Kanya Sumangala Yojana"],
    },
    {
        "id": "women_04",
        "category": "Women & Child",
        "query": "गर्भवती और धात्री माताओं के लिए ₹5000 की मातृत्व वंदना वित्तीय पोषण सहायता",
        "target_keywords": ["matru vandana", "pmmvvy", "pregnant women", "maternity benefit"],
        "target_schemes": ["Pradhan Mantri Matru Vandana Yojana", "Maternity Benefit Scheme"],
    },
    {
        "id": "women_05",
        "category": "Women & Child",
        "query": "असंगठित क्षेत्र की पंजीकृत निर्माण श्रमिक महिलाओं के लिए कन्या विवाह सहायता",
        "target_keywords": ["kanya vivah", "marriage assistance", "construction workers"],
        "target_schemes": ["Financial Assistance for the Marriage of the Children of the Construction Workers", "Kanya Vivah Sahayta Yojana"],
    },
    {
        "id": "women_06",
        "category": "Women & Child",
        "query": "ग्रामीण गरीब महिलाओं के स्वयं सहायता समूह (SHG) के गठन और रिवाल्विंग फंड",
        "target_keywords": ["self help group", "shg", "nrlm", "aajeevika", "deendayal"],
        "target_schemes": ["Deendayal Antyodaya Yojana - National Rural Livelihoods Mission", "DAY-NRLM"],
    },
    {
        "id": "women_07",
        "category": "Women & Child",
        "query": "गरीब ग्रामीण महिलाओं को मुफ्त एलपीजी गैस सिलेंडर कनेक्शन योजना (उज्ज्वला)",
        "target_keywords": ["lpg", "ujjwala", "gas connection", "bpl women"],
        "target_schemes": ["Pradhan Mantri Ujjwala Yojana", "Ujjwala 2.0"],
    },

    # -------------------------------------------------------------------------
    # 4. Health & Wellness / Disability (7 pairs)
    # -------------------------------------------------------------------------
    {
        "id": "health_01",
        "category": "Health & Wellness",
        "query": "गंभीर बीमारी और सर्जरी के लिए दिल्ली आरोग्य कोष के तहत वित्तीय सहायता",
        "target_keywords": ["delhi arogya kosh", "financial assistance", "surgery", "treatment"],
        "target_schemes": ["Delhi Arogya Kosh", "Arogya Nidhi"],
    },
    {
        "id": "health_02",
        "category": "Health & Wellness",
        "query": "पंजीकृत निर्माण श्रमिकों के लिए विकलांगता व दिव्यांग पेंशन सहायता",
        "target_keywords": ["disability pension", "construction workers", "divyang"],
        "target_schemes": ["Disability Pension for the Construction Workers", "Divyangjan Pension"],
    },
    {
        "id": "health_03",
        "category": "Health & Wellness",
        "query": "गरीब परिवारों के लिए प्रति वर्ष 5 लाख रुपये तक का मुफ्त स्वास्थ्य बीमा (आयुष्मान भारत)",
        "target_keywords": ["ayushman bharat", "pmjay", "health insurance", "5 lakh"],
        "target_schemes": ["Ayushman Bharat - PM-JAY", "Pradhan Mantri Jan Arogya Yojana"],
    },
    {
        "id": "health_04",
        "category": "Health & Wellness",
        "query": "वरिष्ठ नागरिकों और 60 वर्ष से अधिक आयु के बुजुर्गों के लिए वृद्धावस्था पेंशन",
        "target_keywords": ["old age pension", "senior citizen", "vridhavastha"],
        "target_schemes": ["Indira Gandhi National Old Age Pension Scheme", "Old Age Pension Scheme"],
    },
    {
        "id": "health_05",
        "category": "Health & Wellness",
        "query": "दिव्यांग व्यक्तियों के लिए ट्राइसाइकिल और कृत्रिम अंग वितरण योजना (एडीआईपी)",
        "target_keywords": ["adip", "assistive devices", "tricycle", "artificial limbs"],
        "target_schemes": ["Assistance to Disabled Persons for Purchase/Fitting of Aids and Appliances (ADIP)", "ADIP Scheme"],
    },
    {
        "id": "health_06",
        "category": "Health & Wellness",
        "query": "टीबी (क्षय रोग) के मरीजों को पौष्टिक आहार हेतु प्रति माह ₹500 निक्षय पोषण सहायता",
        "target_keywords": ["nikshay", "tb", "tuberculosis", "nutrition"],
        "target_schemes": ["Nikshay Poshan Yojana", "National Tuberculosis Elimination Program"],
    },
    {
        "id": "health_07",
        "category": "Health & Wellness",
        "query": "निर्माण श्रमिकों के प्राकृतिक या सामान्य मृत्यु पर आश्रितों को अनुग्रह राशि",
        "target_keywords": ["natural death assistance", "construction workers", "nominee"],
        "target_schemes": ["Natural Death Assistance for the Construction Workers"],
    },

    # -------------------------------------------------------------------------
    # 5. Housing, Shelter & Worker Welfare (6 pairs)
    # -------------------------------------------------------------------------
    {
        "id": "house_01",
        "category": "Housing & Worker Welfare",
        "query": "पंजीकृत निर्माण श्रमिकों के लिए स्वयं का पक्का मकान खरीदने अथवा निर्माण हेतु सहायता",
        "target_keywords": ["purchase/construction of house", "construction workers", "housing grant"],
        "target_schemes": ["Purchase/Construction of House for the Construction Workers"],
    },
    {
        "id": "house_02",
        "category": "Housing & Worker Welfare",
        "query": "होम लोन पर ब्याज सब्सिडी और आर्थिक मदद हेतु वित्तीय सहायता योजना",
        "target_keywords": ["interest subsidy on home loan", "home loan", "housing interest"],
        "target_schemes": ["Financial Assistance as Interest Subsidy on Home Loan", "Credit Linked Subsidy Scheme"],
    },
    {
        "id": "house_03",
        "category": "Housing & Worker Welfare",
        "query": "ग्रामीण क्षेत्र में बेघर और कच्चे मकान में रहने वालों के लिए प्रधानमंत्री आवास योजना",
        "target_keywords": ["awas yojana", "pmay-g", "pucca house", "rural housing"],
        "target_schemes": ["Pradhan Mantri Awaas Yojana - Gramin", "PMAY-G"],
    },
    {
        "id": "house_04",
        "category": "Housing & Worker Welfare",
        "query": "रेहड़ी-पटरी फेरीवालों के लिए 10,000 रुपये का ब्याज मुक्त कार्यशील पूंजी लोन (स्वनिधि)",
        "target_keywords": ["svanidhi", "street vendor", "microcredit", "working capital"],
        "target_schemes": ["PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)", "PM SVANidhi"],
    },
    {
        "id": "house_05",
        "category": "Housing & Worker Welfare",
        "query": "निर्माण श्रमिकों के लिए दिल्ली डीटीसी बसों में मुफ्त यात्रा पास पास योजना",
        "target_keywords": ["dtc non ac buses", "yatra pass", "travel pass", "construction workers"],
        "target_schemes": ["Yatra Pass in DTC non AC Buses for the Construction Workers"],
    },
    {
        "id": "house_06",
        "category": "Housing & Worker Welfare",
        "query": "श्रमिकों के 60 वर्ष पूरे होने पर मासिक पेंशन लाभ योजना",
        "target_keywords": ["pension benefit for the construction workers", "retirement pension"],
        "target_schemes": ["Pension Benefit for the Construction Workers"],
    },
]


def check_hit(retrieved_candidates: List[Dict[str, Any]], target_schemes: List[str], target_keywords: List[str]) -> Optional[int]:
    """
    Checks if any target scheme or characteristic keywords match the retrieved candidate list.
    Returns 1-based rank (1 to K) if hit, or None if miss.
    """
    for rank, cand in enumerate(retrieved_candidates, 1):
        cand_name = cand.get("name", "").lower()
        cand_desc = cand.get("description", "").lower()
        cand_text = f"{cand_name} {cand_desc}"

        # 1. Exact or partial title match
        for target in target_schemes:
            if target.lower() in cand_name or cand_name in target.lower():
                return rank

        # 2. Key semantic tokens match (at least 2 matching tokens)
        matched_tokens = sum(1 for kw in target_keywords if kw.lower() in cand_text)
        if matched_tokens >= 2:
            return rank

    return None


def run_retrieval_evaluation() -> Dict[str, Any]:
    """Runs top-k retrieval evaluation across all 35 benchmark pairs."""
    logger.info("=" * 80)
    logger.info("  2. RETRIEVAL ACCURACY EVALUATION (ChromaDB Vector RAG)")
    logger.info("=" * 80)

    top1_hits = 0
    top3_hits = 0
    top5_hits = 0
    reciprocal_ranks: List[float] = []

    category_stats: Dict[str, Dict[str, int]] = {}
    detailed_results: List[Dict[str, Any]] = []

    for item in RETRIEVAL_BENCHMARK_PAIRS:
        cat = item["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "top1": 0, "top3": 0, "top5": 0}
        category_stats[cat]["total"] += 1

        candidates = search_schemes(query=item["query"], top_k=5)
        hit_rank = check_hit(candidates, item["target_schemes"], item["target_keywords"])

        is_top1 = bool(hit_rank == 1)
        is_top3 = bool(hit_rank and hit_rank <= 3)
        is_top5 = bool(hit_rank and hit_rank <= 5)

        if is_top1:
            top1_hits += 1
            category_stats[cat]["top1"] += 1
        if is_top3:
            top3_hits += 1
            category_stats[cat]["top3"] += 1
        if is_top5:
            top5_hits += 1
            category_stats[cat]["top5"] += 1

        rr = 1.0 / hit_rank if hit_rank else 0.0
        reciprocal_ranks.append(rr)

        top_cand_name = candidates[0].get("name") if candidates else "None"
        detailed_results.append({
            "id": item["id"],
            "category": cat,
            "query": item["query"],
            "target_schemes": item["target_schemes"],
            "retrieved_top1": top_cand_name,
            "hit_rank": hit_rank,
            "top1": is_top1,
            "top3": is_top3,
            "top5": is_top5,
        })

        logger.info(f"[{item['id']}] Cat: {cat[:20]:20} | Rank: {str(hit_rank):4} | Top1: \"{top_cand_name[:40]}\"")

    total_queries = len(RETRIEVAL_BENCHMARK_PAIRS)
    top1_acc = round(top1_hits / total_queries, 4)
    top3_acc = round(top3_hits / total_queries, 4)
    top5_acc = round(top5_hits / total_queries, 4)
    mrr = round(sum(reciprocal_ranks) / total_queries, 4)

    logger.info("-" * 80)
    logger.info(f"Total Benchmark Queries : {total_queries}")
    logger.info(f"Top-1 Retrieval Accuracy: {top1_acc * 100:.1f}% ({top1_hits}/{total_queries})")
    logger.info(f"Top-3 Retrieval Accuracy: {top3_acc * 100:.1f}% ({top3_hits}/{total_queries})")
    logger.info(f"Top-5 Retrieval Accuracy: {top5_acc * 100:.1f}% ({top5_hits}/{total_queries})")
    logger.info(f"Mean Reciprocal Rank    : {mrr:.3f}")
    logger.info("-" * 80)

    # Category Breakdown Summary
    cat_summary = {}
    for c, stats in category_stats.items():
        n = stats["total"]
        cat_summary[c] = {
            "total": n,
            "top1_acc": round(stats["top1"] / n, 4),
            "top3_acc": round(stats["top3"] / n, 4),
            "top5_acc": round(stats["top5"] / n, 4),
        }
        logger.info(f"  {c:26} : Top-3 = {cat_summary[c]['top3_acc']*100:5.1f}% | Top-5 = {cat_summary[c]['top5_acc']*100:5.1f}% (N={n})")

    return {
        "summary": {
            "total_queries": total_queries,
            "top1_accuracy": top1_acc,
            "top3_accuracy": top3_acc,
            "top5_accuracy": top5_acc,
            "mean_reciprocal_rank": mrr,
        },
        "category_breakdown": cat_summary,
        "detailed_results": detailed_results,
    }


if __name__ == "__main__":
    run_retrieval_evaluation()
