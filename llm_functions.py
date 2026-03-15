from dotenv import load_dotenv
from openai import OpenAI
import os
import google.genai
import concurrent.futures
import hashlib
import threading

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Models ordered by SPEED (fastest first!)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct")  # 1-2s
GEMINI_MODEL = "gemini-2.5-flash"  # 2-3s
OPEN_AI_MODEL = "gpt-4o-mini"  # 3-4s

# Initialize clients once
gemini_client = google.genai.Client(api_key=gemini_api_key)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Response cache (larger for more hits)
response_cache = {}
MAX_CACHE_SIZE = 500

SYSTEM_PROMPT = "You are a Sales Executve, who is supposed to sell AI courses." \
        " You are very friendly and polite in your responses." \
        "You are not supposed to answer any question, which is not mentioned in the below information, politely say that you don't have the answer." \
        "We have a new course on 'Mastering AI with Python' that covers everything from basics to advanced topics. " \
        "The course is designed for beginers and experienced developers alike." \
        "The price of the course is $199, but we are offering a 20% discount for early sign-ups. " \
        "The course includes hands-on projects, real-world examples, and lifetime access to the materials." \
        "It is being offered by IIT Patna, a premier institute known for quality education." \
        "The faculty of IIT Patna will take classes on Sunday 10am to 1pm IST. " \
        "The course duration is 3 months with a total of 36 hours of live online sessions." \
        " At the end of the course, students will receive a certificate of completion from IIT Patna." \
        " If you don't have any relevant information, politely say that you don't have the answer instead of making up something." \
        "Don't give any wrong information."

def get_cache_key(query, model_name):
    """Generate cache key"""
    return hashlib.md5(f"{query.lower()}_{model_name}".encode()).hexdigest()

def get_cached(query, model_name):
    """Get cached response"""
    key = get_cache_key(query, model_name)
    return response_cache.get(key)

def set_cache(query, model_name, response):
    """Cache response with size management"""
    key = get_cache_key(query, model_name)
    response_cache[key] = response
    if len(response_cache) > MAX_CACHE_SIZE:
        oldest_key = next(iter(response_cache))
        del response_cache[oldest_key]
        
def get_response_from_openai(user_query, open_ai_chat_history):
    """OpenAI response - TIMEOUT: 20 seconds"""
    try:
        if cached := get_cached(user_query, "openai"):
            return cached
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(open_ai_chat_history[-3:])  # Only last 3 messages
        messages.append({"role": "user", "content": user_query})
        
        completion = openai_client.chat.completions.create(
            model=OPEN_AI_MODEL,
            messages=messages,
            timeout=20,
            max_tokens=300  # Shorter responses
        )
        content = completion.choices[0].message.content[:300]
        set_cache(user_query, "openai", content)
        return content
    except Exception as e:
        print(f"OpenAI: Timeout/Error")
        return None
    
def get_gemini_response(user_query, gemini_chat_history):
    """Gemini response - TIMEOUT: 18 seconds"""
    try:
        if cached := get_cached(user_query, "gemini"):
            return cached
        
        history_limited = gemini_chat_history[-3:]  # Only last 3 messages
        if not history_limited:
            full_message = f"System: {SYSTEM_PROMPT}\n\nUser: {user_query}"
        else:
            conversation = "\n".join([f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}" for m in history_limited])
            full_message = f"{conversation}\nUser: {user_query}"
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_message
        )
        content = response.text[:300]
        set_cache(user_query, "gemini", content)
        return content
    except Exception as e:
        print(f"Gemini: Timeout/Error")
        return None

def get_openrouter_response(user_query, openrouter_chat_history):
    """OpenRouter response - TIMEOUT: 15 seconds (FASTEST)"""
    try:
        if cached := get_cached(user_query, "openrouter"):
            return cached
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(openrouter_chat_history[-3:])  # Only last 3 messages
        messages.append({"role": "user", "content": user_query})
        
        completion = openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            timeout=15,
            max_tokens=300
        )
        content = completion.choices[0].message.content[:300]
        set_cache(user_query, "openrouter", content)
        return content
    except Exception as e:
        print(f"OpenRouter: Timeout/Error")
        return None


def get_all_responses_parallel(user_query, open_ai_chat_history, gemini_chat_history, openrouter_chat_history):
    """
    LIGHTNING FAST parallel execution
    Fastest model first: OpenRouter → Gemini → OpenAI
    Individual timeouts: 15s, 18s, 20s
    """
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Start fastest first for better UX
        f_openrouter = executor.submit(get_openrouter_response, user_query, openrouter_chat_history)
        f_gemini = executor.submit(get_gemini_response, user_query, gemini_chat_history)
        f_openai = executor.submit(get_response_from_openai, user_query, open_ai_chat_history)
        
        # Collect with tight timeouts
        try:
            results['openrouter'] = f_openrouter.result(timeout=15)
        except:
            results['openrouter'] = None
        
        try:
            results['gemini'] = f_gemini.result(timeout=18)
        except:
            results['gemini'] = None
        
        try:
            results['openai'] = f_openai.result(timeout=20)
        except:
            results['openai'] = None
    
    return results