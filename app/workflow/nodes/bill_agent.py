import os
import json
import re
from openai import OpenAI
from app.workflow.state import ClaimState
from app.utils.retry import call_with_retry

def bill_agent_node(state: ClaimState) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    seg = state["segregation_result"]
    page_images = state["page_images"]

    relevant_indices = [i for i, t in seg.items() if t == "itemized_bill"]

    if not relevant_indices:
        return {"itemized_extraction": {"error": "no itemized_bill pages found"}}

    content = []
    for i in relevant_indices:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{page_images[i]}"
            }
        })

    content.append({
        "type": "text",
        "text": """Extract the following fields from the itemized bill document(s) shown.
Return ONLY a valid JSON object with these keys:
{
  "line_items": [
    {"description": "...", "quantity": 1, "unit_price": 0.0}
  ],
  "total_amount": 0.0
}
If fields are not found, use null for individual items or 0.0 for total."""
    })

    response = call_with_retry(
        client,
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": content
            }
        ],
        max_tokens=2000
    )
    raw = response.choices[0].message.content.strip()

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return {"itemized_extraction": json.loads(raw)}
    except json.JSONDecodeError:
        return {"itemized_extraction": {"raw_response": raw, "error": "parse_failed"}}
