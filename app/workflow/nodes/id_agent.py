import os
import json
import re
from openai import OpenAI
from app.workflow.state import ClaimState
from app.utils.retry import call_with_retry

def id_agent_node(state: ClaimState) -> dict:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    seg = state["segregation_result"]
    page_images = state["page_images"]

    relevant_indices = [i for i, t in seg.items() if t == "identity_document"]

    if not relevant_indices:
        return {"id_extraction": {"error": "no identity_document pages found"}}

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
        "text": """Extract the following fields from the identity document(s) shown.
Return ONLY a valid JSON object with these keys:
{
  "patient_name": "...",
  "dob": "...",
  "id_numbers": ["..."],
  "policy_details": {"policy_number": "...", "insurer": "..."}
}
If a field is not found, use null."""
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
        max_tokens=1000
    )
    raw = response.choices[0].message.content.strip()

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return {"id_extraction": json.loads(raw)}
    except json.JSONDecodeError:
        return {"id_extraction": {"raw_response": raw, "error": "parse_failed"}}
