# app/services/summarize.py - FIXED VERSION
import requests
import os
import json

def generate_summary_using_openrouter(content):
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return "API key not configured"

    # Use the same models that work for your other APIs
    models_to_try = [
        "deepseek/deepseek-r1:free",
        "deepseek/deepseek-v3:free",
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "google/gemma-2-2b-it:free"
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "StudyBuddy App"
    }

    # Simplified and more direct prompt
    prompt = f"Please provide a clear and concise summary of the following text in 2-3 sentences:\n\n{content}"

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,  # Reduced from 300
            "temperature": 0.3  # Lower temperature for more consistent results
        }

        try:
            print(f"🧪 Trying summarize model: {model}")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            print(f"📊 Summarize response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📋 Response data keys: {list(data.keys())}")
                
                if "choices" in data and data["choices"]:
                    summary = data["choices"][0]["message"]["content"]
                    print(f"✅ Summarize success with model: {model}")
                    print(f"📝 Summary preview: {summary[:100]}...")
                    return summary.strip()
                else:
                    print(f"❌ No choices in response for model: {model}")
                    print(f"📋 Full response: {data}")
                    continue
                    
            elif response.status_code == 429:
                print(f"⚠️ Rate limit hit for summarize model: {model}")
                continue
            else:
                print(f"❌ Summarize model {model} failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error text: {response.text[:200]}")
                continue
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout for model: {model}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error for model {model}: {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error for model {model}: {e}")
            continue
    
    # Enhanced fallback response
    return f"Unable to generate AI summary due to API limitations. Here's a basic summary: The provided content discusses various topics and contains {len(content.split())} words of information that would benefit from further review and analysis."