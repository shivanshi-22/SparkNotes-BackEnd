from fastapi import APIRouter, Request, HTTPException
from app.services.flashcard_generator import generate_flashcards_using_openrouter

router = APIRouter()

@router.post("/generate-flashcards")
async def generate_flashcards(request: Request):
    try:
        data = await request.json()
        notes = data.get("notes")
        
        if not notes or notes.strip() == "":
            raise HTTPException(status_code=400, detail="Notes are required")

        flashcards = generate_flashcards_using_openrouter(notes)
        
        if not flashcards:
            raise HTTPException(status_code=500, detail="Failed to generate flashcards")
            
        return {"flashcards": flashcards}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Flashcard generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

