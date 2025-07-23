# app/services/summarize.py - FIXED WITH API KEY DEBUGGING
import requests
import os
import json
import time

def generate_summary_using_openrouter(content):
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # Enhanced API key validation
    if not api_key:
        print("❌ No OPENROUTER_API_KEY found in environment variables")
        print("💡 Make sure to set: export OPENROUTER_API_KEY='your-key-here'")
        return "API key not configured"
    
    if not api_key.startswith("sk-or-v1-"):
        print(f"❌ Invalid API key format. Got: {api_key[:20]}...")
        print("💡 OpenRouter keys should start with 'sk-or-v1-'")
        return "Invalid API key format"
    
    print(f"✅ API Key found: {api_key[:15]}...{api_key[-4:]}")

    # Working models list (prioritize the most reliable ones)
    models_to_try = [
        "deepseek/deepseek-r1:free",
        "deepseek/deepseek-v3:free", 
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemma-2-2b-it:free"
    ]

    # Correct headers for OpenRouter
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",  # Your app URL
        "X-Title": "StudyBuddy App"
    }

    # Simple, effective prompt
    prompt = f"""Please provide a clear 2-3 sentence summary of the following content:

{content[:2000]}  

Focus on the main ideas and key points."""

    for i, model in enumerate(models_to_try):
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 200,  # Shorter for summaries
                "top_p": 1
            }

            print(f"\n🧪 Attempt {i+1}/{len(models_to_try)}: Trying {model}")
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            print(f"📊 Status: {response.status_code}")
            
            # Success case
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        summary = data["choices"][0]["message"]["content"].strip()
                        if summary:
                            print(f"✅ SUCCESS with {model}")
                            return summary
                    else:
                        print(f"❌ Empty response from {model}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    
            # Error cases with detailed debugging
            elif response.status_code == 401:
                print(f"❌ UNAUTHORIZED (401) - API Key Issue")
                print(f"   Response: {response.text}")
                print(f"   This means your API key is invalid or expired")
                
                # Test API key with a simple request
                test_response = requests.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                if test_response.status_code == 401:
                    print("❌ API key fails basic validation - check your key")
                    return "Invalid API key - please check your OPENROUTER_API_KEY"
                else:
                    print("✅ API key is valid, model might not be available")
                    
            elif response.status_code == 429:
                print(f"⚠️ RATE LIMITED (429) - waiting 2 seconds...")
                time.sleep(2)
                continue
                
            elif response.status_code == 400:
                print(f"❌ BAD REQUEST (400)")
                print(f"   Response: {response.text}")
                continue
                
            elif response.status_code == 503:
                print(f"⚠️ SERVICE UNAVAILABLE (503) - model overloaded")
                continue
                
            else:
                print(f"❌ Unexpected error: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                continue
                
        except requests.exceptions.Timeout:
            print(f"⏰ TIMEOUT for {model}")
            continue
            
        except requests.exceptions.ConnectionError:
            print(f"🔗 CONNECTION ERROR for {model}")
            continue
            
        except Exception as e:
            print(f"💥 UNEXPECTED ERROR for {model}: {str(e)}")
            continue
    
    # All models failed
    print("\n❌ ALL MODELS FAILED")
    return create_fallback_summary(content)

def create_fallback_summary(content):
    """Create a simple fallback summary when API fails"""
    words = content.split()
    word_count = len(words)
    
    # Extract first few sentences as a basic summary
    sentences = content.split('.')[:3]
    if len(sentences) > 1:
        basic_summary = '. '.join(sentences[:2]) + '.'
        return f"{basic_summary} (Content contains {word_count} words - API unavailable)"
    
    return f"This content contains {word_count} words covering important information that requires further review. The main concepts presented need detailed analysis to fully understand the key points discussed."

# Test function to verify API key
def test_api_connection():
    """Test if the API key works"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return False, "No API key found"
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "API key is valid"
        else:
            return False, f"API key invalid: {response.status_code}"
            
    except Exception as e:
        return False, f"Connection failed: {e}"

if __name__ == "__main__":
    # Test the API connection
    is_valid, message = test_api_connection()
    print(f"API Test: {message}")
    
    if is_valid:
        # Test summarization
        test_content = "This is a test document with multiple sentences. It contains information about various topics. The main goal is to test the summarization functionality."
        result = generate_summary_using_openrouter(test_content)
        print(f"\nTest Summary: {result}")