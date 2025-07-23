import requests
import os
import json
import re

def generate_flashcards_using_openrouter(content):
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        return []

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

    prompt = f"""Create exactly 4 flashcards from this content. Return ONLY valid JSON format with no extra text:

{content}

Format:
[
    {{"question": "What is X?", "answer": "X is..."}},
    {{"question": "What is Y?", "answer": "Y is..."}}
]"""

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1200
        }

        try:
            print(f"🧪 Trying flashcard model: {model}")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    content_response = data["choices"][0]["message"]["content"]
                    
                    # Extract JSON from response
                    try:
                        # Remove markdown code blocks and extra text
                        content_response = re.sub(r'```json\s*', '', content_response)
                        content_response = re.sub(r'```\s*$', '', content_response)
                        content_response = content_response.strip()
                        
                        # Find JSON array
                        json_match = re.search(r'\[.*\]', content_response, re.DOTALL)
                        if json_match:
                            flashcards = json.loads(json_match.group())
                            if isinstance(flashcards, list) and len(flashcards) > 0:
                                print(f"✅ Flashcards success with model: {model}")
                                return flashcards
                        
                        # Try parsing entire response as JSON
                        flashcards = json.loads(content_response)
                        if isinstance(flashcards, list) and len(flashcards) > 0:
                            print(f"✅ Flashcards success with model: {model}")
                            return flashcards
                            
                    except json.JSONDecodeError as je:
                        print(f"❌ JSON parse failed for model: {model} - {je}")
                        print(f"Raw response: {content_response[:200]}")
                        continue
            elif response.status_code == 429:
                print(f"⚠️ Rate limit hit for model: {model}")
                continue
            else:
                print(f"❌ Flashcard model {model} failed: {response.status_code}")
                continue
                
        except Exception as e:
            print(f"❌ Flashcard model {model} error: {e}")
            continue
    
    # Enhanced fallback flashcards
    return [
        {
            "question": "What is the main topic discussed in the content?",
            "answer": content[:150] + "..." if len(content) > 150 else content
        },
        {
            "question": "What are the key points mentioned?",
            "answer": "The content covers important information that requires further study and review."
        },
        {
            "question": "Why is this topic important?",
            "answer": "This topic is significant for understanding the subject matter and building knowledge."
        }
    ]