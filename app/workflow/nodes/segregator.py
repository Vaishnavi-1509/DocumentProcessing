import os
from openai import OpenAI
from app.workflow.state import ClaimState
from app.utils.retry import call_with_retry

VALID_TYPES = {
    "claim_forms", "cheque_or_bank_details", "identity_document",
    "itemized_bill", "discharge_summary", "prescription",
    "investigation_report", "cash_receipt", "other"
}

def segregator_node(state: ClaimState) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    page_images = state["page_images"]
    results = {}

    for i, b64_img in enumerate(page_images):
        response = call_with_retry(
            client,
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_img}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """You are classifying a single page from an insurance claim document.
Classify this page into EXACTLY ONE of these categories:
claim_forms, cheque_or_bank_details, identity_document, itemized_bill,
discharge_summary, prescription, investigation_report, cash_receipt, other

Respond with ONLY the category name, nothing else."""
                        }
                    ]
                }
            ],
            max_tokens=10
        )
        doc_type = response.choices[0].message.content.strip().lower()
        if doc_type not in VALID_TYPES:
            doc_type = "other"
        results[i] = doc_type

    return {"segregation_result": results}
