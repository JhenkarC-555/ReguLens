"""
scripts/generate_more_documents.py
Generates realistic, high-quality RBI regulatory documents covering key Fintech domains:
1. RBI Guidelines on Digital Lending (2022)
2. RBI Framework for Default Loss Guarantee (FLDG) in Digital Lending (2023)
3. RBI Master Direction - Guidelines on Regulation of Payment Aggregators (PA) & Payment Gateways (PG)
4. RBI Master Direction - Credit Card and Debit Card Issuance & Conduct (2022)
"""

from pathlib import Path
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


def generate_documents():
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. RBI Digital Lending Guidelines (September 02, 2022)
    # -------------------------------------------------------------------------
    doc_dl = pymupdf.open()
    
    # Page 1
    p1 = doc_dl.new_page(width=595, height=842)
    p1_text = (
        "RESERVE BANK OF INDIA - DEPARTMENT OF REGULATION\n"
        "Document Reference: RBI/2022-23/111 DOR.CRE.REC.66/21.07.001/2022-23\n"
        "Publication Date: September 02, 2022\n\n"
        "Guidelines on Digital Lending\n\n"
        "1. Applicability and Definitions:\n"
        "These guidelines are applicable to all Commercial Banks, Primary (Urban) Co-operative Banks,\n"
        "State Co-operative Banks, and Non-Banking Financial Companies (NBFCs).\n"
        "- Digital Lending: A remote, automated lending process largely using seamless digital technologies.\n"
        "- Lending Service Provider (LSP): An agent of a Regulated Entity who carries out functions such as\n"
        "  customer acquisition, underwriting support, pricing support, disbursement, or recovery.\n"
        "- Digital Lending Apps (DLAs): Mobile and web-based applications offering digital lending services.\n\n"
        "2. Loan Disbursal, Servicing, and Repayment:\n"
        "(a) All loan disbursals and repayments must be executed directly between the bank account of\n"
        "    the borrower and the Regulated Entity (RE), without any pass-through or pool account of any third party.\n"
        "(b) In no case shall disbursal be made to a third-party account, including the account of an LSP.\n"
        "(c) Any fees or charges payable to LSPs in the lending process shall be paid directly by the RE\n"
        "    and shall NOT be charged by the LSP directly to the borrower.\n"
    )
    p1.insert_text((50, 60), p1_text, fontsize=10)

    # Page 2
    p2 = doc_dl.new_page(width=595, height=842)
    p2_text = (
        "Guidelines on Digital Lending (Continued)\n"
        "Document Reference: RBI/2022-23/111 DOR.CRE.REC.66/21.07.001/2022-23\n\n"
        "3. Disclosure to Borrowers and Key Fact Statement (KFS):\n"
        "(a) Regulated Entities must provide a standardized Key Fact Statement (KFS) to the borrower\n"
        "    before the execution of the loan contract, in a format prescribed by RBI.\n"
        "(b) The KFS shall clearly disclose the Annual Percentage Rate (APR), recovery mechanism,\n"
        "    details of grievance redressal officer, and cooling-off / look-up period.\n"
        "(c) Any fee or charge not mentioned in the KFS cannot be charged to the borrower at any stage.\n\n"
        "4. Cooling-off / Look-up Period:\n"
        "A cooling-off period of not less than three (3) days for loans having tenor of seven days or more,\n"
        "and one (1) day for loans having tenor of less than seven days, shall be provided to borrowers.\n"
        "During this period, the borrower may exit the digital loan by paying the principal and proportionate APR.\n\n"
        "5. Protection of Customer Data and Privacy:\n"
        "(a) DLAs shall not collect biometric data of borrowers unless authorized under law.\n"
        "(b) Access to mobile phone resources such as file and media, contact lists, call logs,\n"
        "    and telephony functions is strictly prohibited.\n"
        "(c) One-time access may be taken for camera, microphone, or location solely for KYC onboarding.\n"
    )
    p2.insert_text((50, 60), p2_text, fontsize=10)
    doc_dl.save(str(output_dir / "rbi_digital_lending_guidelines_2022.pdf"))
    doc_dl.close()

    # -------------------------------------------------------------------------
    # 2. RBI Framework for Default Loss Guarantee (FLDG) in Digital Lending (June 08, 2023)
    # -------------------------------------------------------------------------
    doc_fldg = pymupdf.open()
    p1_fldg = doc_fldg.new_page(width=595, height=842)
    p1_fldg_text = (
        "RESERVE BANK OF INDIA - DEPARTMENT OF REGULATION\n"
        "Document Reference: RBI/2023-24/41 DOR.CRE.REC.23/21.07.001/2023-24\n"
        "Publication Date: June 08, 2023\n\n"
        "Guidelines on Default Loss Guarantee (FLDG) in Digital Lending\n\n"
        "1. Background and Purpose:\n"
        "Reference is invited to Para 6 of the Guidelines on Digital Lending dated September 02, 2022.\n"
        "This framework establishes permissible arrangements for Default Loss Guarantee (DLG) between\n"
        "Regulated Entities (REs) and Lending Service Providers (LSPs).\n\n"
        "2. Cap on Default Loss Guarantee (DLG):\n"
        "(a) An RE shall ensure that the total amount of DLG cover on any outstanding portfolio shall\n"
        "    NOT exceed five percent (5%) of the amount of that loan portfolio.\n"
        "(b) In case of implicit guarantee arrangements, the DLG cap of 5% shall strictly apply.\n\n"
        "3. Permissible Forms of DLG:\n"
        "REs shall accept DLG only in one or more of the following explicit forms:\n"
        "1. Cash deposit maintained with the RE;\n"
        "2. Fixed Deposits maintained with a Scheduled Commercial Bank with a lien marked in favor of the RE;\n"
        "3. Bank Guarantee in favor of the RE issued by a Scheduled Commercial Bank.\n\n"
        "4. Customer Protection and NPA Classification:\n"
        "Recognition of individual loan accounts as Non-Performing Assets (NPA) and subsequent provisioning\n"
        "shall be the absolute responsibility of the RE, irrespective of any DLG cover available.\n"
        "DLG invocation shall not postpone the asset classification norms stipulated by RBI.\n"
    )
    p1_fldg.insert_text((50, 60), p1_fldg_text, fontsize=10)
    doc_fldg.save(str(output_dir / "rbi_fldg_digital_lending_2023.pdf"))
    doc_fldg.close()

    # -------------------------------------------------------------------------
    # 3. RBI Payment Aggregators (PA) & Payment Gateways (PG) Guidelines (2020/Updated)
    # -------------------------------------------------------------------------
    doc_pa = pymupdf.open()
    p1_pa = doc_pa.new_page(width=595, height=842)
    p1_pa_text = (
        "RESERVE BANK OF INDIA - DEPARTMENT OF PAYMENT AND SETTLEMENT SYSTEMS\n"
        "Document Reference: RBI/DPSS/2019-20/174 DPSS.CO.PD.No.1810/02.14.008/2019-20\n"
        "Publication Date: March 17, 2020\n\n"
        "Guidelines on Regulation of Payment Aggregators and Payment Gateways\n\n"
        "1. Scope and Authorization:\n"
        "- Payment Aggregators (PAs): Entities that facilitate e-commerce sites and merchants to accept\n"
        "  payment instruments from customers. PAs pool payments, receive them in escrow, and settle to merchants.\n"
        "- Non-bank Payment Aggregators require mandatory prior authorization from RBI under the PSS Act, 2007.\n\n"
        "2. Capital and Net-Worth Requirements:\n"
        "(a) Non-bank PAs existing as on the date of this circular shall achieve a minimum net-worth of\n"
        "    Rs. 15 crore by March 31, 2021, and a net-worth of Rs. 25 crore by the end of third financial year.\n"
        "(b) New applicants for PA authorization must have a minimum net-worth of Rs. 15 crore at application,\n"
        "    and attain Rs. 25 crore within three financial years of grant of authorization.\n"
        "(c) Net-worth shall consist of paid-up equity capital, preference shares, and free reserves.\n\n"
        "3. Escrow Account Operations and Settlement:\n"
        "(a) Non-bank PAs shall maintain the funds collected on behalf of merchants in an Escrow Account\n"
        "    with a Scheduled Commercial Bank.\n"
        "(b) The amount in escrow shall be used strictly for settlement to merchants, refund to customers,\n"
        "    and payment of commission to PAs. No interest shall be payable to merchants.\n"
        "(c) Final settlement to merchants shall be completed within T+1 / T+2 business days.\n"
    )
    p1_pa.insert_text((50, 60), p1_pa_text, fontsize=10)
    doc_pa.save(str(output_dir / "rbi_payment_aggregators_directions.pdf"))
    doc_pa.close()

    # -------------------------------------------------------------------------
    # 4. RBI Master Direction - Credit Card and Debit Card Issuance (April 21, 2022)
    # -------------------------------------------------------------------------
    doc_card = pymupdf.open()
    p1_card = doc_card.new_page(width=595, height=842)
    p1_card_text = (
        "RESERVE BANK OF INDIA - DEPARTMENT OF REGULATION\n"
        "Document Reference: RBI/2022-23/92 DOR.AUT.REC.No.27/24.01.041/2022-23\n"
        "Publication Date: April 21, 2022\n\n"
        "Master Direction - Credit Card and Debit Card - Issuance and Conduct Directions, 2022\n\n"
        "Chapter I - Credit Card Governance:\n"
        "1. Unsolicited Cards and Unsolicited Upgrades:\n"
        "(a) Card-issuers shall not issue unsolicited credit cards or upgrade existing cards without\n"
        "    explicit consent of the customer.\n"
        "(b) If an unsolicited card is issued or activated without consent, the card-issuer shall reverse\n"
        "    all charges immediately and pay a penalty of twice the value of charges to the recipient.\n\n"
        "2. Closure of Credit Card:\n"
        "(a) Any request for closure of a credit card shall be honored by the card-issuer within\n"
        "    seven (7) working days, subject to payment of all dues by the cardholder.\n"
        "(b) Cardholders must be provided multiple channels for closure: helpline, dedicated email,\n"
        "    Interactive Voice Response (IVR), and online banking portal.\n"
        "(c) Failure on the part of card-issuers to close the card within 7 working days shall result\n"
        "    in a penalty of Rs. 500 per day of delay payable to the customer till closure.\n\n"
        "3. Choice of Billing Cycle:\n"
        "Cardholders shall be provided a one-time option to modify their credit card billing cycle\n"
        "as per their convenience, at least once during the lifetime of the credit card.\n"
    )
    p1_card.insert_text((50, 60), p1_card_text, fontsize=10)
    doc_card.save(str(output_dir / "rbi_credit_card_directions_2022.pdf"))
    doc_card.close()

    print(f"Generated 4 new RBI regulatory documents in {output_dir}!")


if __name__ == "__main__":
    generate_documents()
