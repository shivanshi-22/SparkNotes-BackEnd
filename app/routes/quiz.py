from fastapi import APIRouter, Request, HTTPException
from app.services.quiz_generator import generate_quiz_using_openrouter

router = APIRouter()

@router.post("/generate-quiz")
async def generate_quiz(request: Request):
    try:
        data = await request.json()
        notes = data.get("notes")
        
        if not notes or notes.strip() == "":
            raise HTTPException(status_code=400, detail="Notes are required")

        quiz_json = generate_quiz_using_openrouter(notes)
        
        if not quiz_json:
            raise HTTPException(status_code=500, detail="Failed to generate quiz")
            
        return {"quiz": quiz_json}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
