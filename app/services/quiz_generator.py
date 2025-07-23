import requests
import os
import json
import re

def generate_quiz_using_openrouter(content):
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

    prompt = f"""Create exactly 3 multiple choice questions from this content. Return ONLY valid JSON format:

{content}

Format:
[
    {{
        "question": "What is X?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A"
    }}
]"""

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1500
        }

        try:
            print(f"🧪 Trying quiz model: {model}")
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
                    
                    try:
                        # Clean response
                        content_response = re.sub(r'```json\s*', '', content_response)
                        content_response = re.sub(r'```\s*$', '', content_response)
                        content_response = content_response.strip()
                        
                        # Find JSON array
                        json_match = re.search(r'\[.*\]', content_response, re.DOTALL)
                        if json_match:
                            quiz = json.loads(json_match.group())
                            if isinstance(quiz, list) and len(quiz) > 0:
                                # Validate quiz structure
                                if all('question' in q and 'options' in q and 'answer' in q for q in quiz):
                                    print(f"✅ Quiz success with model: {model}")
                                    return quiz
                        
                        # Try parsing entire response
                        quiz = json.loads(content_response)
                        if isinstance(quiz, list) and len(quiz) > 0:
                            if all('question' in q and 'options' in q and 'answer' in q for q in quiz):
                                print(f"✅ Quiz success with model: {model}")
                                return quiz
                            
                    except json.JSONDecodeError as je:
                        print(f"❌ Quiz JSON parse failed for model: {model} - {je}")
                        print(f"Raw response: {content_response[:200]}")
                        continue
            elif response.status_code == 429:
                print(f"⚠️ Rate limit hit for model: {model}")
                continue
            else:
                print(f"❌ Quiz model {model} failed: {response.status_code}")
                continue
                
        except Exception as e:
            print(f"❌ Quiz model {model} error: {e}")
            continue
    
    # Enhanced fallback quiz
    return [
        {
            "question": "Based on the provided content, what is the main subject being discussed?",
            "options": ["Technical concepts", "General knowledge", "Specific topic from content", "Multiple related topics"],
            "answer": "Specific topic from content"
        },
        {
            "question": "What type of information was provided in the content?",
            "options": ["Detailed explanations", "Brief overview", "Step-by-step instructions", "Mixed information types"],
            "answer": "Mixed information types"
        },
        {
            "question": "How would you best use this content for studying?",
            "options": ["Memorize everything", "Focus on key concepts", "Skip difficult parts", "Read once quickly"],
            "answer": "Focus on key concepts"
        }
    ]
