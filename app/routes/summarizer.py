from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.services.summarize import generate_summary_using_openrouter

router = APIRouter()

class NotesRequest(BaseModel):
    notes: str

@router.post("/summarize")
async def summarize_notes(data: NotesRequest):
    notes = data.notes
    if not notes or notes.strip() == "":
        raise HTTPException(status_code=400, detail="Notes are required.")
    
    try:
        # Use the actual summarization service
        summary = generate_summary_using_openrouter(notes)
        
        if summary == "Summary failed.":
            raise HTTPException(status_code=500, detail="Failed to generate summary")
            
        return {"summary": summary}
    except Exception as e:
        print(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Alternative endpoint that accepts JSON in request body (for Postman)
@router.post("/summarize-alt")
async def summarize_notes_alt(request: Request):
    try:
        data = await request.json()
        notes = data.get("notes")
        
        if not notes or notes.strip() == "":
            raise HTTPException(status_code=400, detail="Notes are required.")
        
        summary = generate_summary_using_openrouter(notes)
        
        if summary == "Summary failed.":
            raise HTTPException(status_code=500, detail="Failed to generate summary")
            
        return {"summary": summary}
    except Exception as e:
        print(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")