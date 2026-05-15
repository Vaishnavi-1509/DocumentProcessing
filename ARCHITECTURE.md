# Architecture Documentation

## System Overview

The Claim Processing Pipeline is a multi-agent system that processes insurance claim PDFs using a directed acyclic graph (DAG) of AI agents orchestrated by LangGraph.

```
┌─────────────────────────────────────────────────────────────┐
│                         FASTAPI ENDPOINT                     │
│                        POST /api/process                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      PDF CONVERSION                          │
│                  (PyMuPDF, DPI=150)                          │
│              PDF file → List of PNG images                  │
│                   (Base64 encoded)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   LANGGRAPH WORKFLOW                         │
│                                                              │
│  START → SEGREGATOR → [ID | DISCHARGE | BILL] → AGGREGATOR │
│           (classify)   (parallel execution)      (merge)     │
│                                                              │
│  Each agent calls Gemini 2.0 Flash vision API               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL JSON RESPONSE                       │
│  {                                                           │
│    "claim_id": "...",                                        │
│    "segregation": {...},                                     │
│    "identity": {...},                                        │
│    "discharge_summary": {...},                              │
│    "itemized_bill": {...}                                    │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Workflow

### 1. Request Entry Point (`app/api/routes.py`)

```python
@router.post("/api/process")
async def process_claim(claim_id: str, file: UploadFile):
    # 1. Validate file is PDF
    # 2. Read bytes: pdf_bytes = await file.read()
    # 3. Convert to images: page_images = pdf_to_base64_images(pdf_bytes)
    # 4. Create initial state dict with all 7 required keys
    # 5. Execute: result = claim_graph.invoke(initial_state)
    # 6. Return result["final_result"] as JSON
```

### 2. PDF to Images Conversion (`app/utils/pdf_utils.py`)

```
Input:  PDF bytes (binary)
         ↓
      PyMuPDF (fitz) opens PDF from memory
         ↓
      For each page:
        - Render to pixmap at DPI=150
        - Encode as PNG
        - Base64 encode
         ↓
Output: List[str] where each str is base64 PNG
```

**Why DPI=150?**
- 72 DPI: Too blurry for OCR/vision
- 150 DPI: Sweet spot — clear text, reasonable token size
- 300+ DPI: High token cost for minimal quality gain

### 3. LangGraph State Machine (`app/workflow/graph.py`)

The graph is built with these components:

```python
StateGraph(ClaimState)
  ├─ Node: segregator → routes to 3 agents
  ├─ Node: id_agent → updates id_extraction
  ├─ Node: discharge_agent → updates discharge_extraction
  ├─ Node: bill_agent → updates itemized_extraction
  └─ Node: aggregator → produces final_result

Edges:
  START → segregator
  segregator → [id_agent | discharge_agent | bill_agent]  (via router function)
  [id_agent | discharge_agent | bill_agent] → aggregator
  aggregator → END
```

**Key: add_conditional_edges with Send**

After segregator completes, the router function returns:
```python
[
    Send("id_agent", state),
    Send("discharge_agent", state),
    Send("bill_agent", state),
]
```

This tells LangGraph:
- Run all 3 nodes in parallel
- Each receives a copy of the full state
- When all 3 finish, merge their state updates
- Pass merged state to aggregator

### 4. Segregator Agent (`app/workflow/nodes/segregator.py`)

**Input State:** 
```python
{
    "page_images": ["base64_img_0", "base64_img_1", ...],
    ...
}
```

**Process:**
```
For page 0:
  Gemini Vision: "Classify this page into one of: claim_forms, cheque_or_bank_details, ..."
  Response: "identity_document"
  
For page 1:
  Gemini Vision: "Classify this page..."
  Response: "itemized_bill"

... (one API call per page)
```

**Output State:**
```python
{
    "segregation_result": {0: "identity_document", 1: "itemized_bill", ...},
    ...
}
```

**Design Note:** Per-page calls (not batch)
- More reliable JSON parsing
- Easier debugging
- Slightly higher latency (offset by parallel agents later)

### 5. Extraction Agents (Parallel Execution)

All three agents follow the same pattern:

#### ID Agent (`app/workflow/nodes/id_agent.py`)

**Filter:** `segregation_result[i] == "identity_document"`

**Input Pages:** Only those pages

**Prompt:**
```
Extract these fields from identity document:
- patient_name
- dob
- id_numbers (array)
- policy_details (object with policy_number, insurer)

Return as JSON.
```

**Output:** `{"id_extraction": {patient_name, dob, ...}}`

#### Discharge Summary Agent (`app/workflow/nodes/discharge_agent.py`)

**Filter:** `segregation_result[i] == "discharge_summary"`

**Fields:**
- diagnosis
- admit_date
- discharge_date
- physician_name
- hospital_name

#### Itemized Bill Agent (`app/workflow/nodes/bill_agent.py`)

**Filter:** `segregation_result[i] == "itemized_bill"`

**Fields:**
- line_items: array of {description, quantity, unit_price}
- total_amount

### 6. Aggregator (`app/workflow/nodes/aggregator.py`)

**Input State:** Merged state with all 6 keys populated

**Process:**
```python
final_result = {
    "claim_id": state["claim_id"],
    "segregation": state["segregation_result"],
    "identity": state["id_extraction"],
    "discharge_summary": state["discharge_extraction"],
    "itemized_bill": state["itemized_extraction"],
}
```

**Output:** `{"final_result": {...}}`

## State Management

### ClaimState TypedDict

```python
class ClaimState(TypedDict):
    claim_id: str                      # user input
    page_images: list[str]             # PDF→PNG→base64
    segregation_result: dict           # segregator output
    id_extraction: dict                # id_agent output
    discharge_extraction: dict         # discharge_agent output
    itemized_extraction: dict          # bill_agent output
    final_result: dict                 # aggregator output
```

**Flow:**
1. API creates initial state with empty dicts
2. Segregator updates segregation_result
3. Three agents update their respective dicts (in parallel)
4. Aggregator reads all 4 and creates final_result
5. API returns final_result to client

## API Integration with Gemini

Each agent uses the same pattern:

```python
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# Build content parts
parts = [
    {"inline_data": {"mime_type": "image/png", "data": base64_string}},
    "Your prompt here...",
]

# Call Gemini
response = model.generate_content(parts)
text = response.text

# Parse JSON (with markdown fence stripping)
import json, re
raw = re.sub(r"^```(?:json)?\s*", "", text.strip())
raw = re.sub(r"\s*```$", "", raw)
result = json.loads(raw)
```

## Error Handling

Each node has a safety guard:

```python
relevant_indices = [i for i, t in seg.items() if t == "desired_type"]

if not relevant_indices:
    return {"extraction_key": {"error": "no pages found"}}
```

This prevents crashes if a PDF doesn't have a certain doc type (e.g., no identity document).

## Token Usage & Costs

### Per-request costs (Gemini 2.0 Flash):

For a 3-page claim:
- **Segregator**: 3 calls × ~1 page image each = ~6000 tokens input
- **ID Agent**: 1 image × low cost = ~2000 tokens
- **Discharge Agent**: 1 image × low cost = ~2000 tokens
- **Bill Agent**: 1 image × low cost = ~2000 tokens

**Total**: ~12,000 input tokens ≈ $0.001-0.002 per claim

### Optimizations:

1. **DPI=150**: Reduces PNG file size → fewer tokens
2. **Parallel agents**: 3 agents run simultaneously, not sequentially
3. **Per-page segregation**: Each call is smaller, more reliable

## Scaling Considerations

### Current Bottleneck
- **Gemini API latency**: 30-60 seconds per claim (sequential Gemini calls)
- Network I/O: Each API call has ~1 second overhead

### To Scale to 1000s of Claims/Day

1. **Batch processing endpoint**: `/api/batch` accepts multiple PDFs
2. **Async processing**: Use FastAPI `background_tasks`
3. **Queue system**: RabbitMQ/Redis for job queue
4. **Webhooks**: Return results via callback URL
5. **Caching**: Cache segregation results for identical PDFs

Example async version:
```python
from fastapi import BackgroundTasks

@router.post("/api/process-async")
async def process_claim_async(
    claim_id: str, 
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(run_workflow, claim_id, file)
    return {"status": "processing", "claim_id": claim_id}
```

## Testing Strategy

### Unit Tests (Individual Nodes)

```python
# Test segregator in isolation
from app.workflow.nodes.segregator import segregator_node
from app.utils.pdf_utils import pdf_to_base64_images

with open("test.pdf", "rb") as f:
    images = pdf_to_base64_images(f.read())
    
state = {"claim_id": "TEST", "page_images": images, ...}
result = segregator_node(state)
assert "0" in result["segregation_result"]
```

### Integration Tests (Full Workflow)

```python
from app.workflow.graph import claim_graph

result = claim_graph.invoke(initial_state)
assert "claim_id" in result["final_result"]
assert "identity" in result["final_result"]
```

### E2E Tests (API Endpoint)

```python
import requests
files = {"file": open("test.pdf", "rb")}
data = {"claim_id": "TEST"}
response = requests.post("http://localhost:8000/api/process", files=files, data=data)
assert response.status_code == 200
assert "segregation" in response.json()
```

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Client → Internet → Load Balancer                       │
└──────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
    ┌───▼────┐                   ┌───▼────┐
    │ Instance 1                │ Instance 2
    │ (FastAPI server)          │ (FastAPI server)
    │ Port 8000                 │ Port 8000
    └────┬────┘                 └────┬────┘
         │                           │
         └──────────────┬────────────┘
                        │
              ┌─────────▼────────────┐
              │  Gemini API (Cloud)  │
              └──────────────────────┘
```

Each instance runs the same code. Load balancer distributes requests.

## Security Considerations

1. **API Key**: Store in environment variable, never in code
2. **File Upload**: Validate file extension, check MIME type
3. **Request Size**: Set max upload size (e.g., 50MB)
4. **Rate Limiting**: Add token bucket or sliding window
5. **CORS**: Configure allowed origins if frontend is separate

## Monitoring & Logging

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Processing claim {claim_id}")
logger.info(f"Pages: {len(page_images)}")
logger.info(f"Segregation: {segregation_result}")
```

Monitor:
- Average processing time per claim
- Gemini API errors/quota exhaustion
- PDF processing failures
- JSON parsing failures in agents

## Files Reference

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point |
| `app/api/routes.py` | HTTP endpoint |
| `app/workflow/state.py` | State schema |
| `app/workflow/graph.py` | LangGraph assembly |
| `app/workflow/nodes/*.py` | Individual agents |
| `app/utils/pdf_utils.py` | PDF→images conversion |

---

This architecture is designed for clarity and maintainability. Each component has a single responsibility, making it easy for students to understand and explain in interviews/videos.
