# Claim Processing Pipeline

A FastAPI + LangGraph service that processes PDF insurance claims using OpenAI vision AI.

## Quick Start

### 1. Install & Setup (2 min)

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run Server

```bash
python main.py
```

Server runs at `http://localhost:8000`

### 3. Test API

**Option A: Web UI (Easiest)**
- Open `http://localhost:8000/docs`
- Click `/api/process`
- Enter `claim_id`, upload PDF, click Execute

**Option B: curl**
```bash
curl -X POST http://localhost:8000/api/process \
  -F "claim_id=CLM-001" \
  -F "file=@sample.pdf"
```

## Architecture

The system processes claims through a 5-node LangGraph workflow:

```
PDF Upload → Segregator (classify pages) → [3 parallel agents] → Aggregator → JSON Response
                                           ├─ ID Agent
                                           ├─ Discharge Agent
                                           └─ Bill Agent
```

### Workflow Steps

1. **Segregator**: Classifies each page into 9 document types
   - claim_forms, identity_document, discharge_summary, itemized_bill, prescription, investigation_report, cheque_or_bank_details, cash_receipt, other

2. **Parallel Extraction** (all run simultaneously):
   - **ID Agent**: Extracts patient name, DOB, ID numbers, policy details
   - **Discharge Agent**: Extracts diagnosis, admit/discharge dates, physician, hospital
   - **Bill Agent**: Extracts line items (description, quantity, price), total amount

3. **Aggregator**: Combines all results into final JSON

## API Response Example

```json
{
  "claim_id": "CLM-001",
  "segregation": {
    "0": "identity_document",
    "1": "discharge_summary",
    "2": "itemized_bill"
  },
  "identity": {
    "patient_name": "John Smith",
    "dob": "15-MAR-1985",
    "id_numbers": ["ID-123456"],
    "policy_details": {
      "policy_number": "POL-999",
      "insurer": "ABC Insurance"
    }
  },
  "discharge_summary": {
    "diagnosis": "Pneumonia",
    "admit_date": "2025-01-20",
    "discharge_date": "2025-01-25",
    "physician_name": "Dr. Sarah Johnson",
    "hospital_name": "City Medical Center"
  },
  "itemized_bill": {
    "line_items": [
      {"description": "Room Charges (5 days)", "quantity": 5, "unit_price": 200},
      {"description": "Admission Fee", "quantity": 1, "unit_price": 150}
    ],
    "total_amount": 1150
  }
}
```

## Project Structure

```
vaishnavi_ai/
├── main.py                    # FastAPI app entry
├── requirements.txt
├── .env.example
├── app/
│   ├── api/
│   │   └── routes.py          # POST /api/process endpoint
│   ├── workflow/
│   │   ├── state.py           # ClaimState TypedDict
│   │   ├── graph.py           # LangGraph workflow
│   │   └── nodes/
│   │       ├── segregator.py
│   │       ├── id_agent.py
│   │       ├── discharge_agent.py
│   │       ├── bill_agent.py
│   │       └── aggregator.py
│   └── utils/
│       ├── pdf_utils.py       # PDF→PNG→base64 conversion
│       └── retry.py           # Exponential backoff for rate limits
```

## How It Works

### State Flow
All nodes share and update a `ClaimState` dictionary:
```python
{
    "claim_id": "CLM-001",
    "page_images": ["base64_png_1", "base64_png_2", ...],
    "segregation_result": {0: "identity_document", 1: "itemized_bill", ...},
    "id_extraction": {...},
    "discharge_extraction": {...},
    "itemized_extraction": {...},
    "final_result": {...}
}
```

### Parallel Execution
After segregation:
1. Router returns 3 `Send` objects for id_agent, discharge_agent, bill_agent
2. LangGraph runs all 3 agents simultaneously
3. Each agent updates its state key independently
4. All updates merge automatically
5. Aggregator receives merged state with all data

### Key Features
- **Per-page segregation**: Each page classified individually (more reliable)
- **Shared images**: All agents access same page_images, filter by document type
- **Parallel execution**: 3 agents run concurrently (reduces latency)
- **JSON extraction**: Agents use prompted constraints for structured output
- **Error handling**: Missing document types return `{"error": "no pages found"}` instead of crashing

## Tech Stack

- **FastAPI** - Web framework
- **LangGraph** - Multi-agent orchestration with fan-out parallelism
- **OpenAI GPT-4o** - Vision AI for document understanding
- **PyMuPDF (fitz)** - PDF to PNG conversion at 100 DPI
- **python-dotenv** - Environment configuration

## Testing

### Unit Test Individual Node
```python
from app.utils.pdf_utils import pdf_to_base64_images
from app.workflow.nodes.segregator import segregator_node

with open("sample.pdf", "rb") as f:
    images = pdf_to_base64_images(f.read())

state = {
    "claim_id": "TEST",
    "page_images": images,
    "segregation_result": {},
    "id_extraction": {},
    "discharge_extraction": {},
    "itemized_extraction": {},
    "final_result": {},
}

result = segregator_node(state)
print(result["segregation_result"])
```

### Integration Test Full Workflow
```python
from app.workflow.graph import claim_graph

result = claim_graph.invoke(initial_state)
assert "claim_id" in result["final_result"]
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "OPENAI_API_KEY not found" | Verify `.env` file exists in project root with valid key |
| "Only PDF files accepted" | Check file has `.pdf` extension |
| "PDF has no readable pages" | Use digital PDF (not scanned/image-based) |
| Rate limit (429 error) | System auto-retries with exponential backoff. Wait 2+ min before retrying. |
| Long processing time | Normal (30-60s per PDF). Parallel agents minimize latency. |

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Set `OPENAI_API_KEY` environment variable in deployment platform.

### Cloud Platforms
- **Render**: Set build command as `pip install -r requirements.txt`
- **Railway/Fly.io**: Use Dockerfile above
- Set `OPENAI_API_KEY` in platform environment settings

## Production Optimizations

1. **Batch processing**: Handle multiple PDFs efficiently
2. **Async queuing**: RabbitMQ/Redis for job queue
3. **Caching**: Cache segregation results for identical PDFs
4. **Monitoring**: Track API latency, error rates, token usage
5. **Rate limiting**: Add token bucket limiting per user

## Architecture Decisions

1. **Why Vision API over OCR?** Vision models preserve layout, understand forms/tables, handle handwriting—critical for insurance claims
2. **Why per-page segregation?** More reliable JSON parsing, easier debugging, minimal latency hit vs parallel agents
3. **Why parallel agents?** 3 extractors run simultaneously = ~50% faster than sequential
4. **Why TypedDict not Pydantic?** Simpler for state management, no validation overhead for internal state
5. **Why gpt-4o-mini with retry logic?** Cost-effective vision model; retries handle rate limits gracefully

## Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 13 | FastAPI app setup |
| `routes.py` | 27 | HTTP endpoint handler |
| `state.py` | 8 | State schema definition |
| `graph.py` | 24 | LangGraph workflow assembly |
| `segregator.py` | 50 | Page classification |
| `id_agent.py` | 62 | Identity extraction |
| `discharge_agent.py` | 62 | Discharge summary extraction |
| `bill_agent.py` | 63 | Itemized bill extraction |
| `aggregator.py` | 12 | Result merging |
| `pdf_utils.py` | 15 | PDF→images conversion |
| `retry.py` | 8 | Rate limit retry logic |

**Total Core Code: ~350 lines** (very maintainable)

## Next Steps

- Review architecture at `/docs` Swagger UI
- Integrate with claim management system
- Add batch processing endpoint
- Deploy to production cloud platform
- Monitor via logging/observability tools

---

**Built for portfolio/interviews** — clean, scalable, well-documented.
