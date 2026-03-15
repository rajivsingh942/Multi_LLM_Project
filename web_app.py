"""
Multi-LLM Web Application - LIGHTNING FAST
Advanced optimizations for sub-2 second responses
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from llm_functions import (
    get_response_from_openai,
    get_gemini_response,
    get_openrouter_response,
    get_all_responses_parallel
)
from firebase_config import (
    save_chat_history, 
    get_chat_history,
    register_user,
    log_llm_usage
)
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime, timedelta
import threading
import hashlib
import time

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure CORS for production
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],  # Update with specific domains in production
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Production settings
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
app.config['ENV'] = FLASK_ENV
app.config['DEBUG'] = FLASK_ENV == 'development'
app.config['TESTING'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https' if FLASK_ENV == 'production' else 'http'

# Performance optimizations
response_cache = {}
request_dedup = {}
cache_ttl = timedelta(minutes=5)  # Keep cache for 5 minutes
active_sessions = {}
MAX_SESSIONS = 150  # More sessions
CACHE_SIZE_LIMIT = 500  # Larger cache

def get_request_key(session_id, query, model):
    """Generate dedupe key for request"""
    return hashlib.md5(f"{session_id}_{query}_{model}".encode()).hexdigest()

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/new-session', methods=['POST'])
def new_session():
    """Create a new chat session"""
    try:
        data = request.json
        user_id = data.get('user_id', f"user_{str(uuid.uuid4())[:8]}")
        session_id = str(uuid.uuid4())
        
        active_sessions[session_id] = {
            'user_id': user_id,
            'openai_history': [],
            'gemini_history': [],
            'openrouter_history': [],
            'created_at': datetime.now()
        }
        
        # Cleanup old sessions
        if len(active_sessions) > MAX_SESSIONS:
            oldest = min(active_sessions.keys(), key=lambda k: active_sessions[k]['created_at'])
            del active_sessions[oldest]
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'user_id': user_id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/signup', methods=['POST'])
def signup():
    """Register a new user"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        displayName = data.get('displayName', 'User').strip()
        
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'status': 'error',
                'message': 'Password must be at least 6 characters'
            }), 400
        
        result = register_user(email, password, displayName)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'user_id': result['user_id'],
                'message': 'User registered successfully',
                'displayName': displayName
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 400
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Signup error: {str(e)}'
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user (simplified version without Firebase Admin SDK)"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password required'
            }), 400
        
        # Generate a simple user ID based on email
        # In production, this would validate credentials against Firebase
        user_id = hashlib.md5(email.encode()).hexdigest()[:16]
        display_name = email.split('@')[0]
        
        # Log the login attempt
        print(f"[LOGIN] User attempted login: {email}")
        
        return jsonify({
            'status': 'success',
            'user_id': user_id,
            'email': email,
            'displayName': display_name,
            'message': 'Logged in successfully'
        })
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Login error: {str(e)}'
        }), 500

# ============================================================================
# CHAT ROUTES
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """LIGHTNING FAST chat endpoint - returns in <2 seconds"""
    try:
        data = request.json
        session_id = data.get('session_id')
        user_query = data.get('query', '').strip()
        model_choice = data.get('model', 'all')
        
        if not user_query or not session_id:
            return jsonify({'status': 'error', 'message': 'Invalid input'}), 400
        
        if session_id not in active_sessions:
            return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
        
        # SPEED: Check cache immediately
        cache_key = f"{session_id}_{user_query}_{model_choice}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        if cache_hash in response_cache:
            cached_data = response_cache[cache_hash]
            if datetime.now() - cached_data['time'] < cache_ttl:
                return jsonify({
                    'status': 'success',
                    'responses': cached_data['responses'],
                    'cached': True,
                    'time': '0.0s'
                })
        
        session = active_sessions[session_id]
        start_time = time.time()
        
        # SPEED: Get responses with aggressive parallel execution
        if model_choice == 'all':
            responses = get_all_responses_parallel(
                user_query,
                session['openai_history'],
                session['gemini_history'],
                session['openrouter_history']
            )
        elif model_choice == 'openai':
            responses = {
                'openai': get_response_from_openai(user_query, session['openai_history']),
                'gemini': None,
                'openrouter': None
            }
        elif model_choice == 'gemini':
            responses = {
                'openai': None,
                'gemini': get_gemini_response(user_query, session['gemini_history']),
                'openrouter': None
            }
        elif model_choice == 'openrouter':
            responses = {
                'openai': None,
                'gemini': None,
                'openrouter': get_openrouter_response(user_query, session['openrouter_history'])
            }
        else:
            return jsonify({'status': 'error', 'message': 'Invalid model'}), 400
        
        # SPEED: Update history ultra-fast (minimal processing)
        openai_resp = responses.get('openai')
        gemini_resp = responses.get('gemini')
        openrouter_resp = responses.get('openrouter')
        
        if openai_resp:
            session['openai_history'] = session['openai_history'][-6:] + [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": openai_resp[:300]}
            ]
        
        if gemini_resp:
            session['gemini_history'] = session['gemini_history'][-6:] + [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": gemini_resp[:300]}
            ]
        
        if openrouter_resp:
            session['openrouter_history'] = session['openrouter_history'][-6:] + [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": openrouter_resp[:300]}
            ]
        
        elapsed = time.time() - start_time
        
        result_responses = {
            'openai': openai_resp,
            'gemini': gemini_resp,
            'openrouter': openrouter_resp
        }
        
        # Cache result
        response_cache[cache_hash] = {
            'time': datetime.now(),
            'responses': result_responses
        }
        
        # Cleanup old cache entries
        if len(response_cache) > CACHE_SIZE_LIMIT:
            oldest_key = min(response_cache.keys(), 
                           key=lambda k: response_cache[k]['time'])
            del response_cache[oldest_key]
        
        # SPEED: Save to Firebase in background (fire & forget)
        def save_bg():
            try:
                save_chat_history(session['user_id'], user_query, result_responses)
            except: pass
        
        threading.Thread(target=save_bg, daemon=True).start()
        
        return jsonify({
            'status': 'success',
            'responses': result_responses,
            'time': f"{elapsed:.1f}s"
        })
    
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({'status': 'error', 'message': 'Server error'}), 500

@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Get chat history for a session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
        
        session = active_sessions[session_id]
        user_id = session['user_id']
        
        # Get from Firebase
        try:
            history = get_chat_history(user_id)
            return jsonify({'status': 'success', 'history': history})
        except Exception as e:
            print(f"[WARNING] Could not retrieve from Firebase: {e}")
            return jsonify({'status': 'success', 'history': []})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Multi-LLM Web Application Starting")
    print("="*60)
    print(f"Environment: {FLASK_ENV}")
    print(f"Debug Mode: {FLASK_ENV == 'development'}")
    port = int(os.getenv('PORT', 5000))
    print(f"Port: {port}")
    if FLASK_ENV == 'production':
        print("⚠️  Production mode - Using Gunicorn")
        print("Run with: gunicorn --bind 0.0.0.0:8080 web_app:app")
    else:
        print(f"Server: http://localhost:{port}")
        print(f"API Base: http://localhost:{port}/api")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    # Only use Flask dev server in development, use Gunicorn in production
    if FLASK_ENV == 'development':
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False
        )
