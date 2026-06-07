import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def generate_settlement_letter(decision: str, claimant_data: dict, decision_details: dict) -> str:
    name = claimant_data.get("name", "Valued Customer")
    address = claimant_data.get("address", "On File")
    policy = claimant_data.get("policy", "N/A")
    claim_number = claimant_data.get("claim_number", "N/A")

    if decision == "APPROVE":
        payout = decision_details.get("payout_amount", 0)
        deductible = decision_details.get("deductible_applied", 0)
        total = decision_details.get("settlement_amount", 0)

        letter = f"""CLAIM SETTLEMENT NOTICE
ClaimPilot Insurance Corp.

Date: {datetime.utcnow().strftime('%B %d, %Y')}
Claim Number: {claim_number}
Policy Number: {policy}

Dear {name},

We have completed our review of your claim. We are pleased to inform you that your claim has been APPROVED.

SETTLEMENT DETAILS:
- Total Claim Amount: ${total:,.2f}
- Deductible Applied: ${deductible:,.2f}
- Net Settlement Amount: ${payout:,.2f}

The settlement amount of ${payout:,.2f} will be deposited to your account within 3-5 business days.

Thank you for choosing ClaimPilot Insurance.

Sincerely,
Claims Settlement Department
ClaimPilot Insurance Corp."""
    elif decision == "REJECT":
        letter = f"""CLAIM DECISION NOTICE
ClaimPilot Insurance Corp.

Date: {datetime.utcnow().strftime('%B %d, %Y')}
Claim Number: {claim_number}
Policy Number: {policy}

Dear {name},

We have completed our review of your claim. Unfortunately, your claim has been REJECTED.

REASON: {decision_details.get('reasoning', 'The submitted claim does not meet the coverage criteria outlined in your policy.')}

If you believe this decision was made in error, you may appeal by contacting our claims department within 30 days.

Sincerely,
Claims Settlement Department
ClaimPilot Insurance Corp."""
    else:
        letter = f"""CLAIM ESCALATION NOTICE
ClaimPilot Insurance Corp.

Date: {datetime.utcnow().strftime('%B %d, %Y')}
Claim Number: {claim_number}
Policy Number: {policy}

Dear {name},

Your claim requires additional review by a senior claims adjuster.

REASON: {decision_details.get('reasoning', 'Your claim has been flagged for additional review due to complexity or risk factors.')}

A dedicated adjuster will review your case and contact you within 24-48 hours.

Sincerely,
Claims Settlement Department
ClaimPilot Insurance Corp."""

    return letter


def render_decision_pdf(text_content: str, output_path: str) -> str:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        doc = SimpleDocTemplate(output_path, pagesize=letter,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()

        story = []
        for line in text_content.strip().split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            if line.isupper() and len(line) > 3:
                story.append(Paragraph(line, styles["Title"]))
                story.append(Spacer(1, 12))
            elif line.startswith("- ") or line.startswith("* "):
                story.append(Paragraph(f"&bull; {line[2:]}", styles["Normal"]))
            elif ":" in line and line.index(":") < 30:
                parts = line.split(":", 1)
                bold_style = ParagraphStyle("BoldNormal", parent=styles["Normal"], spaceAfter=4)
                story.append(Paragraph(f"<b>{parts[0]}:</b>{parts[1]}", bold_style))
            else:
                story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 4))

        doc.build(story)
        logger.info(f"PDF generated: {output_path}")
        return output_path

    except ImportError:
        logger.warning("ReportLab not installed. Saving as text file instead.")
        txt_path = output_path.replace(".pdf", ".txt")
        with open(txt_path, "w") as f:
            f.write(text_content)
        logger.info(f"Text decision saved: {txt_path}")
        return txt_path
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise
