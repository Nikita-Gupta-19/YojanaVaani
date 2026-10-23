"""
Synthetic Mock Document Generator for YojanaVaani OCR Evaluation (Phase 6).

LEGAL & PRIVACY COMPLIANCE:
In strict compliance with AGENTS.md, docs/specification.md, and India's DPDP Act 2023,
NO REAL CITIZEN DOCUMENTS (Aadhaar, Ration Cards, Income Certificates, Land Records)
ARE USED. All generated images are 100% synthetic mock test documents with placeholder names,
synthetic registration numbers, and explicit watermarks/disclaimers.
"""

import os
from pathlib import Path
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "mock_documents"


def get_font(size: int = 20):
    """Attempts to find a clean system font or falls back to PIL default."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_document_base(title: str, doc_type_tag: str, width: int = 800, height: int = 500) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    """Creates a realistic document background with synthetic borders and disclaimer watermark."""
    img = Image.new("RGB", (width, height), color=(250, 249, 246))  # Off-white paper background
    draw = ImageDraw.Draw(img)

    # Double border
    draw.rectangle([(15, 15), (width - 15, height - 15)], outline=(40, 70, 120), width=3)
    draw.rectangle([(22, 22), (width - 22, height - 22)], outline=(120, 140, 170), width=1)

    # Header bar
    draw.rectangle([(25, 25), (width - 25, 75)], fill=(230, 238, 248))
    f_title = get_font(22)
    f_sub = get_font(12)

    draw.text((40, 38), title, fill=(20, 40, 80), font=f_title)
    draw.text((width - 200, 42), f"[{doc_type_tag}]", fill=(100, 100, 120), font=f_sub)

    # Synthetic Disclaimer Footer
    f_warn = get_font(11)
    disclaimer = "SYNTHETIC MOCK TEST DOCUMENT FOR YOJANAVAANI CSE MAJOR PROJECT — NOT A REAL IDENTITY DOCUMENT"
    draw.text((40, height - 38), disclaimer, fill=(180, 50, 50), font=f_warn)

    return img, draw


def generate_income_certificates():
    """Generates 3 synthetic Income Certificates."""
    docs = [
        {
            "filename": "income_cert_01_ramesh_kumar.png",
            "title": "REVENUE DEPARTMENT GOVT OF UP - INCOME CERTIFICATE",
            "lines": [
                ("Certificate No", "UP-INC-2026-98741"),
                ("Name of Applicant", "Shri Ramesh Kumar"),
                ("Father / Husband Name", "Rameshwar Dayal"),
                ("Annual Income", "Rs. 48000 (Forty Eight Thousand Only)"),
                ("District", "Barabanki"),
                ("Tehsil", "Haidergarh"),
                ("Issue Date", "14/06/2026"),
                ("Category", "OBC")
            ]
        },
        {
            "filename": "income_cert_02_sunita_devi.png",
            "title": "REVENUE DEPARTMENT GOVT OF NCT DELHI - INCOME CERTIFICATE",
            "lines": [
                ("Certificate No", "DL-INC-2026-44120"),
                ("Name of Applicant", "Smt Sunita Devi"),
                ("Father / Husband Name", "Late Ram Vilas"),
                ("Annual Income", "Rs. 120000 (One Lakh Twenty Thousand Only)"),
                ("District", "Shahdara"),
                ("Tehsil", "Seemapuri"),
                ("Issue Date", "22/08/2026"),
                ("Category", "General (Widow)")
            ]
        },
        {
            "filename": "income_cert_03_mohan_lal.png",
            "title": "BOARD OF REVENUE UTTAR PRADESH - INCOME CERTIFICATE",
            "lines": [
                ("Certificate No", "UP-INC-2026-11294"),
                ("Name of Applicant", "Shri Mohan Lal"),
                ("Father / Husband Name", "Kanhaiya Lal"),
                ("Annual Income", "Rs. 350000 (Three Lakh Fifty Thousand Only)"),
                ("District", "Varanasi"),
                ("Tehsil", "Pindra"),
                ("Issue Date", "10/01/2026"),
                ("Category", "SC")
            ]
        }
    ]

    for item in docs:
        img, draw = create_document_base(item["title"], "INCOME-CERT-SYNTHETIC")
        f_val = get_font(16)

        y = 100
        for label, val in item["lines"]:
            draw.text((60, y), f"{label} : {val}", fill=(10, 10, 10), font=f_val)
            y += 38

        # Draw a synthetic stamp box
        draw.rectangle([(580, 240), (740, 360)], outline=(30, 80, 160), width=2)
        draw.text((605, 275), "VERIFIED", fill=(30, 80, 160), font=get_font(20))
        draw.text((595, 305), "TEHSILDAR SEAL", fill=(30, 80, 160), font=get_font(13))

        img.save(OUTPUT_DIR / item["filename"])


def generate_ration_cards():
    """Generates 3 synthetic Ration Cards."""
    docs = [
        {
            "filename": "ration_card_01_aay_gorakhpur.png",
            "title": "FOOD AND CIVIL SUPPLIES DEPT - NFSA RATION CARD",
            "lines": [
                ("Ration Card No", "214589632014"),
                ("Card Type", "AAY (Antyodaya Anna Yojana)"),
                ("Head of Family", "Ramwati Devi"),
                ("Father / Husband", "Santosh Kumar"),
                ("Total Members", "5 Units"),
                ("Fair Price Shop No", "FPS-GK-882"),
                ("District", "Gorakhpur")
            ]
        },
        {
            "filename": "ration_card_02_phh_delhi.png",
            "title": "DEPT OF FOOD AND SUPPLIES DELHI - NFSA RATION CARD",
            "lines": [
                ("Ration Card No", "110022334455"),
                ("Card Type", "PHH (Priority Household)"),
                ("Head of Family", "Rajesh Kumar"),
                ("Father / Husband", "Balwant Singh"),
                ("Total Members", "4 Units"),
                ("Fair Price Shop No", "FPS-DL-412"),
                ("District", "Central Delhi")
            ]
        },
        {
            "filename": "ration_card_03_bpl_prayagraj.png",
            "title": "UTTAR PRADESH STATE PDS - BPL RATION CARD",
            "lines": [
                ("Ration Card No", "189922334411"),
                ("Card Type", "BPL (Below Poverty Line)"),
                ("Head of Family", "Kalawati Devi"),
                ("Father / Husband", "Shyam Sundar"),
                ("Total Members", "3 Units"),
                ("Fair Price Shop No", "FPS-PR-109"),
                ("District", "Prayagraj")
            ]
        }
    ]

    for item in docs:
        img, draw = create_document_base(item["title"], "RATION-CARD-SYNTHETIC")
        f_val = get_font(16)

        y = 110
        for label, val in item["lines"]:
            draw.text((60, y), f"{label} : {val}", fill=(10, 10, 10), font=f_val)
            y += 42

        # Draw barcode placeholder
        draw.rectangle([(560, 130), (740, 200)], fill=(240, 240, 240), outline=(0, 0, 0), width=1)
        for bx in range(570, 730, 6):
            draw.line([(bx, 140), (bx, 190)], fill=(0, 0, 0), width=2 if (bx % 12 == 0) else 1)

        img.save(OUTPUT_DIR / item["filename"])


def generate_khasra_land_records():
    """Generates 3 synthetic Khasra/Khatauni Land Records."""
    docs = [
        {
            "filename": "khasra_land_01_kishan_lal.png",
            "title": "BOARD OF REVENUE UP - BHULEKH KHASRA KHATAUNI",
            "lines": [
                ("Khasra No", "Plot No 142/2"),
                ("Total Area", "0.84 Hectares (0.8400 Hectare)"),
                ("Farmer Name", "Kishan Lal"),
                ("Father Name", "Bholanath"),
                ("Village", "Mohanlalganj"),
                ("Tehsil", "Mohanlalganj"),
                ("District", "Lucknow"),
                ("Soil / Crop Type", "Irrigated Agriculture (Sinshit)")
            ]
        },
        {
            "filename": "khasra_land_02_ram_prasad.png",
            "title": "REVENUE RECORD EXTRACT - KHATAUNI",
            "lines": [
                ("Khasra No", "Plot No 288/1"),
                ("Total Area", "1.65 Hectares (1.6500 Hectare)"),
                ("Farmer Name", "Ram Prasad"),
                ("Father Name", "Devi Dayal"),
                ("Village", "Haidergarh"),
                ("Tehsil", "Haidergarh"),
                ("District", "Barabanki"),
                ("Soil / Crop Type", "Double Crop Wheat Paddy")
            ]
        },
        {
            "filename": "khasra_land_03_shyam_lal.png",
            "title": "UTTAR PRADESH BHULEKH - LAND HOLDING RECORD",
            "lines": [
                ("Khasra No", "Plot No 95"),
                ("Total Area", "2.45 Hectares (2.4500 Hectare)"),
                ("Farmer Name", "Shyam Lal"),
                ("Father Name", "Brij Mohan"),
                ("Village", "Mauranipur"),
                ("Tehsil", "Mauranipur"),
                ("District", "Jhansi"),
                ("Soil / Crop Type", "Bundelkhand Black Soil")
            ]
        }
    ]

    for item in docs:
        img, draw = create_document_base(item["title"], "BHULEKH-KHASRA-SYNTHETIC")
        f_val = get_font(16)

        y = 100
        for label, val in item["lines"]:
            draw.text((60, y), f"{label} : {val}", fill=(10, 10, 10), font=f_val)
            y += 38

        # Stamp
        draw.rectangle([(570, 240), (740, 360)], outline=(30, 120, 50), width=2)
        draw.text((600, 275), "BHULEKH", fill=(30, 120, 50), font=get_font(20))
        draw.text((585, 305), "CERTIFIED COPY", fill=(30, 120, 50), font=get_font(13))

        img.save(OUTPUT_DIR / item["filename"])


def generate_aadhaar_mock_cards():
    """Generates 3 synthetic Identity Mock Cards (Aadhaar style)."""
    docs = [
        {
            "filename": "aadhaar_card_01_priya_sharma.png",
            "title": "GOVERNMENT OF INDIA - MOCK IDENTITY CARD",
            "lines": [
                ("Name", "Priya Sharma"),
                ("DOB", "12/05/1998"),
                ("Gender", "Female"),
                ("Card Number", "XXXX XXXX 8812"),
                ("State", "Delhi"),
                ("District", "Shahdara")
            ]
        },
        {
            "filename": "aadhaar_card_02_rajesh_patel.png",
            "title": "GOVERNMENT OF INDIA - MOCK IDENTITY CARD",
            "lines": [
                ("Name", "Rajesh Patel"),
                ("DOB", "08/11/1982"),
                ("Gender", "Male"),
                ("Card Number", "XXXX XXXX 3341"),
                ("State", "Uttar Pradesh"),
                ("District", "Barabanki")
            ]
        },
        {
            "filename": "aadhaar_card_03_deepak_kumar.png",
            "title": "GOVERNMENT OF INDIA - MOCK IDENTITY CARD",
            "lines": [
                ("Name", "Deepak Kumar"),
                ("DOB", "25/03/2004"),
                ("Gender", "Male"),
                ("Card Number", "XXXX XXXX 9904"),
                ("State", "Uttar Pradesh"),
                ("District", "Kanpur")
            ]
        }
    ]

    for item in docs:
        img, draw = create_document_base(item["title"], "IDENTITY-MOCK-SYNTHETIC", width=700, height=440)
        f_val = get_font(16)

        # Photo placeholder
        draw.rectangle([(60, 110), (190, 270)], fill=(225, 230, 240), outline=(100, 100, 100), width=1)
        draw.text((95, 180), "PHOTO", fill=(120, 120, 120), font=get_font(18))

        y = 110
        for label, val in item["lines"]:
            draw.text((230, y), f"{label} : {val}", fill=(10, 10, 10), font=f_val)
            y += 40

        img.save(OUTPUT_DIR / item["filename"])


def generate_all_mock_documents():
    """Generates complete set of 12 synthetic documents."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating 12 synthetic mock test documents in {OUTPUT_DIR}...")
    generate_income_certificates()
    generate_ration_cards()
    generate_khasra_land_records()
    generate_aadhaar_mock_cards()
    print("Successfully generated 12 synthetic mock documents (3 Income, 3 Ration, 3 Khasra, 3 Identity).")


if __name__ == "__main__":
    generate_all_mock_documents()
