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
            "status": "✅ SUCCESS" if summary and "Unable to generate AI summary" not in summary and "API key not configured" not in summary else "⚠️ FALLBACK",
            "test_content": test_content,
            "summary_result": summary,
            "summary_length": len(summary) if summary else 0,
            "is_fallback": any(phrase in summary for phrase in ["Unable to generate AI summary", "API key not configured", "covers important information"]) if summary else True
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
    test_content = "Machine learning is a subset of artificial intelligence (AI) that focuses on algorithms that can learn and make decisions from data. It includes supervised learning, unsupervised learning, and reinforcement learning. Deep learning uses neural networks with multiple layers."
    
    results = {}
    
    # Test Summarization
    try:
        from app.services.summarize import generate_summary_using_openrouter
        summary = generate_summary_using_openrouter(test_content)
        is_success = summary and not any(phrase in summary for phrase in ["Unable to generate AI summary", "API key not configured", "covers important information"])
        results["summarization"] = {
            "status": "✅ SUCCESS" if is_success else "⚠️ FALLBACK",
            "result": summary,
            "is_fallback": not is_success
        }
    except Exception as e:
        results["summarization"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Test Flashcards
    try:
        from app.services.flashcard_generator import generate_flashcards_using_openrouter
        flashcards = generate_flashcards_using_openrouter(test_content)
        is_success = flashcards and len(flashcards) > 0 and all('question' in fc and 'answer' in fc for fc in flashcards)
        results["flashcards"] = {
            "status": "✅ SUCCESS" if is_success else "❌ FAILED",
            "result": flashcards,
            "count": len(flashcards) if flashcards else 0
        }
    except Exception as e:
        results["flashcards"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Test Quiz
    try:
        from app.services.quiz_generator import generate_quiz_using_openrouter
        quiz = generate_quiz_using_openrouter(test_content)
        is_success = quiz and len(quiz) > 0 and all('question' in q and 'options' in q and 'answer' in q for q in quiz)
        results["quiz"] = {
            "status": "✅ SUCCESS" if is_success else "❌ FAILED",
            "result": quiz,
            "count": len(quiz) if quiz else 0
        }
    except Exception as e:
        results["quiz"] = {"status": "❌ ERROR", "error": str(e)}
    
    # Overall status
    success_count = sum(1 for r in results.values() if "SUCCESS" in r.get("status", ""))
    total_services = len(results)
    
    return {
        "test_content": test_content,
        "results": results,
        "overall_status": f"{success_count}/{total_services} services working",
        "all_working": success_count == total_services,
        "summary": {
            "working": [name for name, result in results.items() if "SUCCESS" in result.get("status", "")],
            "failing": [name for name, result in results.items() if "ERROR" in result.get("status", "")],
            "fallback": [name for name, result in results.items() if "FALLBACK" in result.get("status", "")]
        }
    }

# New endpoint for comprehensive API testing
@debug_router.post("/test-full-workflow")
async def test_full_workflow():
    """Test the complete workflow as if called from frontend"""
    test_notes = """
    Artificial Intelligence and Machine Learning

    Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans. Machine Learning (ML) is a subset of AI that focuses on the ability of machines to receive data and learn for themselves without being explicitly programmed.

    Types of Machine Learning:
    1. Supervised Learning - uses labeled data to train algorithms
    2. Unsupervised Learning - finds patterns in data without labels  
    3. Reinforcement Learning - learns through interaction with environment

    Deep Learning is a subset of ML that uses neural networks with multiple layers to model and understand complex patterns in data.
    """
    
    workflow_results = {}
    
    # Test 1: Summarization API
    try:
        import requests
        response = requests.post(
            "http://localhost:8000/api/summarize",
            json={"notes": test_notes},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        workflow_results["summarize_api"] = {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text[:200],
            "endpoint": "/api/summarize"
        }
    except Exception as e:
        workflow_results["summarize_api"] = {
            "success": False,
            "error": str(e),
            "endpoint": "/api/summarize"
        }
    
    # Test 2: Flashcards API
    try:
        response = requests.post(
            "http://localhost:8000/api/generate-flashcards",
            json={"notes": test_notes},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        workflow_results["flashcards_api"] = {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text[:200],
            "endpoint": "/api/generate-flashcards"
        }
    except Exception as e:
        workflow_results["flashcards_api"] = {
            "success": False,
            "error": str(e),
            "endpoint": "/api/generate-flashcards"
        }
    
    # Test 3: Quiz API
    try:
        response = requests.post(
            "http://localhost:8000/api/generate-quiz",
            json={"notes": test_notes},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        workflow_results["quiz_api"] = {
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text[:200],
            "endpoint": "/api/generate-quiz"
        }
    except Exception as e:
        workflow_results["quiz_api"] = {
            "success": False,
            "error": str(e),
            "endpoint": "/api/generate-quiz"
        }
    
    # Summary
    successful_apis = [name for name, result in workflow_results.items() if result.get("success", False)]
    failed_apis = [name for name, result in workflow_results.items() if not result.get("success", False)]
    
    return {
        "test_notes": test_notes[:200] + "..." if len(test_notes) > 200 else test_notes,
        "workflow_results": workflow_results,
        "summary": {
            "total_apis": len(workflow_results),
            "successful": len(successful_apis),
            "failed": len(failed_apis),
            "successful_apis": successful_apis,
            "failed_apis": failed_apis,
            "all_working": len(failed_apis) == 0
        }
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
            "debug": "/debug/test-api-quick",
            "full_test": "/debug/test-full-workflow"
        },
        "postman_collection": {
            "base_url": "http://localhost:8000",
            "test_endpoints": [
                "GET /debug/env",
                "POST /debug/test-api-quick", 
                "POST /debug/test-full-workflow",
                "POST /api/summarize",
                "POST /api/generate-flashcards",
                "POST /api/generate-quiz"
            ]
        }
    }

@app.get("/health")
async def health_check():
    api_key = os.getenv("OPENROUTER_API_KEY")
    return {
        "status": "healthy", 
        "api_key_set": api_key is not None,
        "api_key_valid_format": api_key.startswith("sk-or-v1-") if api_key else False,
        "timestamp": "2025-07-23",
        "services": ["summarize", "flashcards", "quiz"],
        "debug_endpoints": ["/debug/test-api-quick", "/debug/test-full-workflow"]
    }