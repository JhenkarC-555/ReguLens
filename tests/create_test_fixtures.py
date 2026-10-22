"""
tests/create_test_fixtures.py
Generates clearly labeled synthetic PDF test fixtures for automated testing and demo validation.
Labels all materials clearly as SYNTHETIC TEST FIXTURES to ensure research integrity.
"""

from pathlib import Path
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


def create_synthetic_fixtures(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Synthetic KYC Master Direction Version 1 (Baseline)
    v1_path = output_dir / "synthetic_kyc_baseline_2016.pdf"
    doc1 = pymupdf.open()
    
    # Page 1: Title and Customer Acceptance Policy
    page1 = doc1.new_page(width=595, height=842)
    p1_text = (
        "RESERVE BANK OF INDIA - REGULATORY GUIDELINES\n"
        "[SYNTHETIC TEST FIXTURE - FOR TESTING PURPOSES ONLY]\n\n"
        "Master Direction - Know Your Customer (KYC) Direction, 2016\n"
        "Document Reference: RBI/DBR/2015-16/18 Master Direction DBR.AML.BC.No.81/14.01.001/2015-16\n"
        "Publication Date: February 25, 2016\n\n"
        "Chapter I - Preliminary\n"
        "Section 1. Short Title and Commencement:\n"
        "(a) These Directions shall be called the Reserve Bank of India (Know Your Customer (KYC)) Directions, 2016.\n"
        "(b) They shall come into force with immediate effect.\n\n"
        "Section 2. Applicability:\n"
        "The provisions of these Directions shall apply to every Regulated Entity (RE) licensed or authorized by RBI.\n\n"
        "Chapter II - Customer Acceptance Policy\n"
        "Section 3. Customer Due Diligence (CDD) Requirements:\n"
        "Regulated Entities shall ensure that no account is opened in anonymous or fictitious/benami name.\n"
        "No account shall be opened where the RE is unable to apply appropriate Customer Due Diligence measures.\n"
    )
    page1.insert_text((50, 60), p1_text, fontsize=10)

    # Page 2: Officially Valid Documents and Risk Categorization
    page2 = doc1.new_page(width=595, height=842)
    p2_text = (
        "Chapter III - Identification Procedures\n"
        "[SYNTHETIC TEST FIXTURE - FOR TESTING PURPOSES ONLY]\n\n"
        "Section 4. Officially Valid Documents (OVD):\n"
        "For undertaking Customer Due Diligence of individuals, REs shall obtain any one of the following:\n"
        "1. Passport\n"
        "2. Driving licence issued by regional licensing authority\n"
        "3. Proof of possession of Aadhaar number\n"
        "4. Voter's Identity Card issued by Election Commission of India\n"
        "5. Job card issued by NREGA duly signed by an officer of the State Government\n"
        "6. Letter issued by the National Population Register containing details of name and address.\n\n"
        "Section 5. Periodic KYC Updation:\n"
        "REs shall carry out periodic KYC updation based on customer risk categorization:\n"
        "- High-risk customers: KYC updation shall be carried out at least once every two (2) years.\n"
        "- Medium-risk customers: KYC updation shall be carried out at least once every eight (8) years.\n"
        "- Low-risk customers: KYC updation shall be carried out at least once every ten (10) years.\n"
        "Physical presence of the client shall not be insisted upon at the time of periodic updation.\n"
    )
    page2.insert_text((50, 60), p2_text, fontsize=10)
    doc1.save(str(v1_path))
    doc1.close()

    # 2. Synthetic KYC Master Direction Version 2 (Revised with Video-CIP and Digital Verification)
    v2_path = output_dir / "synthetic_kyc_revised_2023.pdf"
    doc2 = pymupdf.open()
    
    # Page 1: Updated Title and Customer Acceptance
    page1 = doc2.new_page(width=595, height=842)
    p1_rev_text = (
        "RESERVE BANK OF INDIA - REGULATORY GUIDELINES\n"
        "[SYNTHETIC TEST FIXTURE - FOR TESTING PURPOSES ONLY]\n\n"
        "Master Direction - Know Your Customer (KYC) Direction, 2016 (Updated as of 2023)\n"
        "Document Reference: RBI/DBR/2022-23/94 Master Direction DBR.AML.BC.No.81/14.01.001/2022-23\n"
        "Publication Date: May 04, 2023\n\n"
        "Chapter I - Preliminary\n"
        "Section 1. Short Title and Commencement:\n"
        "(a) These Directions shall be called the Reserve Bank of India (Know Your Customer (KYC)) Directions, 2016.\n"
        "(b) They shall come into force with immediate effect.\n\n"
        "Section 2. Applicability:\n"
        "The provisions of these Directions shall apply to every Regulated Entity (RE) licensed, registered or authorized by RBI.\n\n"
        "Chapter II - Customer Acceptance Policy\n"
        "Section 3. Customer Due Diligence (CDD) Requirements:\n"
        "Regulated Entities shall ensure that no account is opened in anonymous or fictitious/benami name.\n"
        "No account shall be opened where the RE is unable to apply appropriate Customer Due Diligence measures.\n"
        "Digital KYC and Video-based Customer Identification Process (V-CIP) are permitted modes of undertaking CDD.\n"
    )
    page1.insert_text((50, 60), p1_rev_text, fontsize=10)

    # Page 2: Updated Identification, V-CIP addition, and periodic update
    page2 = doc2.new_page(width=595, height=842)
    p2_rev_text = (
        "Chapter III - Identification Procedures\n"
        "[SYNTHETIC TEST FIXTURE - FOR TESTING PURPOSES ONLY]\n\n"
        "Section 4. Officially Valid Documents (OVD):\n"
        "For undertaking Customer Due Diligence of individuals, REs shall obtain any one of the following:\n"
        "1. Passport\n"
        "2. Driving licence issued by regional licensing authority\n"
        "3. Proof of possession of Aadhaar number\n"
        "4. Voter's Identity Card issued by Election Commission of India\n"
        "5. Job card issued by NREGA duly signed by an officer of the State Government\n"
        "6. Letter issued by the National Population Register containing details of name and address.\n\n"
        "Section 4A. Video-based Customer Identification Process (V-CIP):\n"
        "Regulated Entities may undertake CDD via Video-based Customer Identification Process (V-CIP).\n"
        "The video interaction must be conducted live and in real-time by an authorized bank official.\n"
        "Geotagging and facial matching liveness checks must be enforced during the V-CIP session.\n\n"
        "Section 5. Periodic KYC Updation:\n"
        "REs shall carry out periodic KYC updation based on customer risk categorization:\n"
        "- High-risk customers: KYC updation shall be carried out at least once every two (2) years.\n"
        "- Medium-risk customers: KYC updation shall be carried out at least once every eight (8) years.\n"
        "- Low-risk customers: KYC updation shall be carried out at least once every ten (10) years.\n"
        "REs shall provide electronic channels (Net Banking, Mobile App, Email) for low-risk periodic re-KYC submission.\n"
    )
    page2.insert_text((50, 60), p2_rev_text, fontsize=10)
    doc2.save(str(v2_path))
    doc2.close()

    # 3. Synthetic Empty PDF (0 pages or empty text)
    empty_path = output_dir / "synthetic_empty.pdf"
    doc_empty = pymupdf.open()
    doc_empty.new_page(width=595, height=842)  # Page with no text
    doc_empty.save(str(empty_path))
    doc_empty.close()

    # 4. Synthetic Scanned PDF (Only a non-text drawing/rect, simulating an image without OCR text)
    scanned_path = output_dir / "synthetic_scanned_image.pdf"
    doc_scan = pymupdf.open()
    page_scan = doc_scan.new_page(width=595, height=842)
    # Draw shapes representing an image, but no text
    shape = page_scan.new_shape()
    shape.draw_rect(pymupdf.Rect(50, 50, 400, 600))
    shape.finish(color=(0.5, 0.5, 0.5), fill=(0.9, 0.9, 0.9))
    shape.commit()
    doc_scan.save(str(scanned_path))
    doc_scan.close()

    print(f"Created synthetic fixtures in {output_dir}")


if __name__ == "__main__":
    fixtures_dir = Path("tests/fixtures")
    create_synthetic_fixtures(fixtures_dir)
    # Also populate data/raw with sample synthetic fixtures so users can demo immediately
    data_raw_dir = Path("data/raw")
    create_synthetic_fixtures(data_raw_dir)
