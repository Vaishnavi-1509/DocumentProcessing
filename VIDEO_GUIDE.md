# Video Explanation Guide

## Overview

Create a **3-5 minute** video explanation covering the entire claim processing pipeline. This guide outlines what to show and explain.

## Video Tools

**Recommended:** Loom, OBS Studio, ScreenFlow (Mac), or Camtasia

### Quick Setup
- **Loom** (easiest): Visit loom.com, record screen + camera, instant share link
- **OBS Studio** (free): Record entire workflow, export as MP4
- **VS Code**: Record with built-in terminal and code

## Video Structure (Script)

### Segment 1: Introduction (0:00-0:30)

**Show:** Title slide or code editor

**Say:**
> "Hi, I'm [Name]. Today I'm showing you a Claim Processing Pipeline built with FastAPI and LangGraph. This service automatically processes insurance claim PDFs using AI vision, classifying documents and extracting key information using Google Gemini."

### Segment 2: Architecture Overview (0:30-1:15)

**Show:** 
- Open `ARCHITECTURE.md` or draw the workflow diagram
- Show the 5-node LangGraph structure

**Say:**
> "The system has 5 AI agents orchestrated by LangGraph:
> 
> 1. **Segregator**: Takes a PDF, converts pages to images, and classifies each page into 9 document types: identity documents, discharge summaries, itemized bills, prescriptions, and more.
> 
> 2. **ID Agent**: Processes pages classified as identity documents and extracts patient name, date of birth, ID numbers, and policy details.
> 
> 3. **Discharge Summary Agent**: Takes discharge summary pages and extracts diagnosis, admission/discharge dates, physician name, and hospital name.
> 
> 4. **Itemized Bill Agent**: Processes bill pages to extract line items (description, quantity, unit price) and calculate the total.
> 
> 5. **Aggregator**: Combines all extracted data into the final JSON response."

**Visual Aids:**
- Show this diagram:
```
START → SEGREGATOR → [ID | DISCHARGE | BILL] → AGGREGATOR → END
         (classify)   (parallel execution)
```

### Segment 3: PDF to Images Conversion (1:15-1:45)

**Show:** 
- Open `app/utils/pdf_utils.py`
- Highlight the key code

**Say:**
> "First, let's see how we handle PDFs. The `pdf_to_base64_images` function takes a PDF file and converts each page into a PNG image at 150 DPI. We base64 encode these images so they can be sent to OPENAI's vision API.
>
> Why 150 DPI? It's the sweet spot between clarity and token cost — high enough to read text, but not so high that it wastes expensive API tokens."

**Code to highlight:**
```python
def pdf_to_base64_images(pdf_bytes: bytes, dpi: int = 150) -> list[str]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        encoded = base64.b64encode(png_bytes).decode("utf-8")
        images.append(encoded)
    return images
```

### Segment 4: Segregator Agent (1:45-2:30)

**Show:** 
- Open `app/workflow/nodes/segregator.py`
- Show the OpenAI API call

**Say:**
> "The Segregator Agent classifies each page. Here's how it works:
>
> For every page image, we send it to Gemini 2.0 Flash with a prompt that says: 'Classify this page into one of these 9 categories: claim_forms, identity_document, discharge_summary, itemized_bill, prescription, investigation_report, cash_receipt, cheque_or_bank_details, or other.'
>
> Gemini looks at the page and responds with just the category name. We validate it against our list and store the result: page 0 is an identity document, page 1 is a bill, etc.
>
> One important design decision: we classify pages one-by-one instead of sending all pages at once. This makes JSON parsing more reliable and easier to debug."

**Code to highlight:**
```python
for i, b64_img in enumerate(page_images):
    parts = [
        {"inline_data": {"mime_type": "image/png", "data": b64_img}},
        "Classify this page into: claim_forms, cheque_or_bank_details, ..."
    ]
    response = model.generate_content(parts)
    doc_type = response.text.strip().lower()
    results[i] = doc_type
```

### Segment 5: LangGraph Parallel Execution (2:30-3:15)

**Show:** 
- Open `app/workflow/graph.py`
- Highlight the fan-out logic

**Say:**
> "After the Segregator finishes, all three extraction agents run in parallel.
>
> LangGraph's `add_conditional_edges` with a router function returns `Send` objects. We return three Send objects — one for ID Agent, one for Discharge Agent, one for Bill Agent. LangGraph starts all three simultaneously.
>
> Each agent has access to the full state, including:
> - All page images
> - The segregation results (which pages are which type)
>
> The ID Agent filters for identity_document pages and extracts patient info. The Discharge Agent filters for discharge_summary pages and extracts medical info. The Bill Agent filters for itemized_bill pages and extracts costs.
>
> They all update different parts of the state, so there's no conflict. When all three finish, their updates are merged, and the Aggregator gets the complete state."

**Code to highlight:**
```python
def route_to_extractors(state: ClaimState) -> list[Send]:
    return [
        Send("id_agent", state),
        Send("discharge_agent", state),
        Send("bill_agent", state),
    ]

graph.add_conditional_edges("segregator", route_to_extractors)
graph.add_edge("id_agent", "aggregator")
graph.add_edge("discharge_agent", "aggregator")
graph.add_edge("bill_agent", "aggregator")
```

### Segment 6: Extraction Agents (3:15-3:50)

**Show:** 
- Open one extraction agent (e.g., `app/workflow/nodes/id_agent.py`)
- Run the API and show a real result

**Say:**
> "Each extraction agent follows the same pattern. Here's the ID Agent:
>
> It filters the segregation results to find only pages marked as identity_document. Then it sends those pages to OpenAi with a prompt: 'Extract patient_name, dob, id_numbers, and policy_details. Return as JSON.'
>
> OpenAi looks at the page(s), finds the information, and returns it as structured JSON. We strip any markdown formatting that OpenAi adds and parse the JSON. If parsing fails, we return an error.
>
> The same logic applies to Discharge Summary and Itemized Bill agents — each focuses on extracting the fields relevant to their document type."

**Code to highlight:**
```python
parts = [image1, image2, ...]
parts.append("Extract patient_name, dob, id_numbers, policy_details. Return JSON.")
response = model.generate_content(parts)
raw = response.text.strip()
raw = re.sub(r"^```(?:json)?\s*", "", raw)  # Strip markdown
result = json.loads(raw)
```

### Segment 7: Live Demo (3:50-4:30)

**Show:** 
- Browser with http://localhost:8000/docs
- Upload a sample PDF
- Show the response

**Say:**
> "Let's see it in action. I'm opening the API documentation at localhost:8000/docs. FastAPI automatically generates this interactive interface.
>
> I'll click the /api/process endpoint, try it out, enter a claim ID, and upload a sample PDF claim document.
>
> [Wait for response]
>
> Perfect! You can see the complete JSON response with:
> - Segregation results showing which pages are which type
> - Identity data extracted from the ID page
> - Discharge summary information
> - Itemized bill with line items and total
>
> All of this happened automatically — segregation, parallel extraction, and aggregation — in about 60 seconds."

### Segment 8: Key Takeaways (4:30-4:50)

**Show:** 
- Diagram or summary slide

**Say:**
> "Here are the key architectural decisions:
>
> 1. **Parallel Execution**: Three agents run simultaneously, reducing latency compared to sequential processing.
>
> 2. **Segregation First**: By classifying pages upfront, each extraction agent only processes relevant pages, improving accuracy and token efficiency.
>
> 3. **Gemini Vision**: We send page images directly to Gemini's vision model instead of extracting text. This preserves layout and tables, which is critical for claims.
>
> 4. **Structured Output**: Agents return JSON, making results easy to parse and integrate with downstream systems.
>
> 5. **Simple Error Handling**: If a document type isn't present, agents return an error field instead of crashing.
>
> This architecture is scalable, maintainable, and designed to be understood by anyone — whether you're a student learning AI or a company processing thousands of claims."

### Segment 9: Closing (4:50-5:00)

**Show:** 
- GitHub repo or summary

**Say:**
> "The complete code is on GitHub with full documentation. Check out the README for setup instructions, the ARCHITECTURE file for a deep dive, and the QUICKSTART guide to get running in minutes.
>
> Thanks for watching!"


