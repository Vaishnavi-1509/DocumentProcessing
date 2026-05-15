from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.workflow.graph import claim_graph
from app.utils.pdf_utils import pdf_to_base64_images

router = APIRouter()

@router.post("/process")
async def process_claim(claim_id: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    try:
        pdf_bytes = await file.read()
        page_images = pdf_to_base64_images(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF error: {str(e)}")

    initial_state = {
        "claim_id": claim_id,
        "page_images": page_images,
        "segregation_result": {},
        "id_extraction": {},
        "discharge_extraction": {},
        "itemized_extraction": {},
        "final_result": {},
    }

    try:
        result = claim_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow error: {str(e)}")

    return JSONResponse(content=result["final_result"])
