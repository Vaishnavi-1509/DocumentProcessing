# Quick Start Guide

## 1. Install Python Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- LangGraph (multi-agent orchestration)
- google-generativeai (Gemini API)
- pymupdf (PDF processing)
- python-dotenv (config management)

## 2. Get Your Google API Key (2 minutes)

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. Open `.env` file in the project root
5. Replace `AIza...add_your_key_here...` with your actual key
6. Save the file

Your `.env` should look like:
```
GOOGLE_API_KEY=AIzaSyD1234567890abcdefg...
```

## 3. Start the Server (5 seconds)

```bash
python main.py
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete [uvicorn]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 4. Test the API (1 minute)

### Option A: Web Browser (Easiest)

1. Open browser: http://localhost:8000/docs
2. Click `/api/process` endpoint
3. Click "Try it out"
4. Enter `claim_id`: `TEST-001`
5. Upload a PDF file
6. Click "Execute"
7. See the results below!

### Option B: Command Line

```bash
curl -X POST http://localhost:8000/api/process \
  -F "claim_id=TEST-001" \
  -F "file=@your_sample.pdf" \
  | python3 -m json.tool
```

## How It Works

When you upload a PDF:

1. **Segregator Agent** classifies each page into 9 types (ID, discharge, bill, etc.)
2. **Three Agents Run in Parallel**:
   - ID Agent → extracts patient name, DOB, policy details
   - Discharge Agent → extracts diagnosis, dates, physician info
   - Bill Agent → extracts line items and totals
3. **Aggregator** combines all results into one JSON response

## Example Response

```json
{
  "claim_id": "TEST-001",
  "segregation": {
    "0": "identity_document",
    "1": "itemized_bill",
    "2": "discharge_summary"
  },
  "identity": {
    "patient_name": "John Doe",
    "dob": "1985-03-15",
    "id_numbers": ["ID-123456"],
    "policy_details": {
      "policy_number": "POL-999",
      "insurer": "ABC Insurance"
    }
  },
  "itemized_bill": {
    "line_items": [
      {"description": "Hospital Room", "quantity": 2, "unit_price": 500}
    ],
    "total_amount": 1000
  },
  "discharge_summary": {
    "diagnosis": "Common Cold",
    "admit_date": "2024-01-10",
    "discharge_date": "2024-01-12",
    "physician_name": "Dr. Smith",
    "hospital_name": "City Hospital"
  }
}
```

## Troubleshooting

**Q: "GOOGLE_API_KEY not found"**
- Check `.env` file exists in project root
- Restart the server after editing `.env`

**Q: "Only PDF files are accepted"**
- Make sure your file ends with `.pdf`

**Q: "PDF has no readable pages"**
- Use a clear, digital PDF (not scanned/image-based)
- Try a different PDF file

**Q: Takes a long time (1-2 minutes)**
- This is normal! Gemini vision processes each page
- Parallel agents speed it up

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check API docs at http://localhost:8000/docs
- Deploy to cloud (Render/Railway/Fly.io)

---

**That's it!** Your claim processing pipeline is running. 🚀
