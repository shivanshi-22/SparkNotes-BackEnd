from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.routes import summarizer, quiz, flashcards
import os
import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("⚠️  Or set environment variables manually")

app = FastAPI(title="StudyBuddy API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug router
debug_router = APIRouter()

@debug_router.get("/env")
async def check_environment():
    """Check if environment variables are set"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Key from environment: {api_key}")  # This will show in server logs
    return {
        "api_key_set": api_key is not None,
        "api_key_length": len(api_key) if api_key else 0,
        "api_key_starts_with": api_key[:15] + "..." if api_key and len(api_key) > 15 else "Not set",
        "api_key_format_correct": api_key.startswith("sk-or-v1-") if api_key else False,
        "environment_check": "✅ PASS" if api_key else "❌ FAIL"
    }

@debug_router.post("/test-api-quick")
async def test_openrouter_api_quick():
    """Quick test with current working free models"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return {"error": "API key not found in environment variables."}
    
    # Test with most reliable free model
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "StudyBuddy App"
    }

    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [{"role": "user", "content": "Say 'API test successful!'"}],
        "max_tokens": 20
    }

    try:
        print("📡 Testing with DeepSeek R1 (most reliable free model)...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            json=payload, 
            headers=headers,
            timeout=15
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "✅ SUCCESS",
                "status_code": response.status_code,
                "model_used": "deepseek/deepseek-r1:free",
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", "No content"),
                "message": "API is working correctly!"
            }
        elif response.status_code == 429:
            return {
                "status": "⚠️ RATE LIMITED",
                "status_code": response.status_code,
                "message": "You've hit the daily rate limit (50 requests/day for free tier)",
                "solution": "Wait 24 hours or purchase credits for higher limits"
            }
        else:
            return {
                "status": "❌ ERROR",
                "status_code": response.status_code,
                "response": response.text[:300],
                "message": "API call failed - check your API key"
            }
            
    except Exception as e:
        return {"status": "❌ ERROR", "error": str(e), "message": "Connection failed"}

@debug_router.get("/list-free-models")
async def list_current_free_models():
    """Get current list of free models"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return {"error": "API key not found"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json()
            # Get free models (pricing.prompt = "0")
            free_models = []
            for model in models.get("data", []):
                pricing = model.get("pricing", {})
                if pricing.get("prompt") == "0" or pricing.get("prompt") == 0:
                    free_models.append({
                        "id": model["id"],
                        "name": model.get("name", "Unknown"),
                        "context_length": model.get("context_length", "Unknown")
                    })
            
            return {
                "status": "success",
                "total_models": len(models.get("data", [])),
                "free_models_count": len(free_models),
                "recommended_free_models": [
                    "deepseek/deepseek-r1:free",
                    "deepseek/deepseek-v3:free", 
                    "mistralai/mistral-7b-instruct:free",
                    "google/gemma-2-2b-it:free",
                    "meta-llama/llama-3.2-3b-instruct:free"
                ],
                "all_free_models": free_models[:20]  # First 20 free models
            }
        else:
            return {
                "status": "error",
                "status_code": response.status_code,
                "response": response.text[:200]
            }
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

@debug_router.post("/test-summarize-only")
async def test_summarize_only():
    """Test only the summarize function with detailed debugging"""
    test_content = "Machine learning is a subset of artificial intelligence (AI) that focuses on algorithms that can learn and make decisions from data. It includes supervised learning, unsupervised learning, and reinforcement learning."
    
    try:
        print("🔍 Starting summarize test...")
        from app.services.summarize import generate_summary_using_openrouter
        summary = generate_summary_using_openrouter(test_content)
        
        return {
            "status": "✅ SUCCESS" if summary and "Unable to generate AI summary" not in summary else "⚠️ FALLBACK",
            "test_content": test_content,
            "summary_result": summary,
            "summary_length": len(summary) if summary else 0,
            "is_fallback": "Unable to generate AI summary" in summary if summary else True
        }
    except Exception as e:
        print(f"❌ Summarize test error: {e}")
        return {
            "status": "❌ ERROR",
            "error": str(e),
            "test_content": test_content
        }

@debug_router.post("/test-all-services")
async def test_all_services():
    """Test all three services with sample data"""
    test_content = "Machine learning is a subset of artificial intelligence (AI) that focuses on algorithms that can learn and make decisions from data. It includes supervised learning, unsupervised learning, and reinforcement learning."
    
    results = {}
    
    # Test Summarization
    try:
        from app.services.summarize import generate_summary_using_openrouter
        summary = generate_summary_using_openrouter(test_content)
        results["summarization"] = {
            "status": "✅ SUCCESS" if summary and "Unable to generate AI summary" not in summary else "⚠️ FALLBACK",
            "result": summary,
            "is_fallback": "Unable to generate AI summary" in summary if summary else True
        }
    except Exception as e:
        results["summarization"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Test Flashcards
    try:
        from app.services.flashcard_generator import generate_flashcards_using_openrouter
        flashcards = generate_flashcards_using_openrouter(test_content)
        results["flashcards"] = {
            "status": "✅ SUCCESS" if flashcards and len(flashcards) > 0 else "❌ FAILED",
            "result": flashcards,
            "count": len(flashcards) if flashcards else 0
        }
    except Exception as e:
        results["flashcards"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Test Quiz
    try:
        from app.services.quiz_generator import generate_quiz_using_openrouter
        quiz = generate_quiz_using_openrouter(test_content)
        results["quiz"] = {
            "status": "✅ SUCCESS" if quiz and len(quiz) > 0 else "❌ FAILED",
            "result": quiz,
            "count": len(quiz) if quiz else 0
        }
    except Exception as e:
        results["quiz"] = {"status": "❌ ERROR", "error": str(e)}
    
    return {
        "test_content": test_content,
        "results": results,
        "overall_status": "All services working" if all("SUCCESS" in r.get("status", "") for r in results.values()) else "Some services have issues"
    }

# Register all routes
app.include_router(debug_router, prefix="/debug")
app.include_router(summarizer.router, prefix="/api")
app.include_router(quiz.router, prefix="/api")
app.include_router(flashcards.router, prefix="/api")

@app.get("/")
async def root():
    api_key_set = os.getenv("OPENROUTER_API_KEY") is not None
    return {
        "message": "StudyBuddy API is running", 
        "api_key_configured": api_key_set,
        "version": "2.0.0",
        "status": "✅ Ready" if api_key_set else "⚠️ API Key Required",
        "endpoints": {
            "summarize": "/api/summarize",
            "flashcards": "/api/generate-flashcards", 
            "quiz": "/api/generate-quiz",
            "debug": "/debug/test-api-quick"
        }
    }

@app.get("/health")
async def health_check():
    api_key = os.getenv("OPENROUTER_API_KEY")
    return {
        "status": "healthy", 
        "api_key_set": api_key is not None,
        "api_key_valid_format": api_key.startswith("sk-or-v1-") if api_key else False,
        "timestamp": "2025-07-23"
    }