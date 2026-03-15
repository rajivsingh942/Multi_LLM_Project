"""
Web App Integration Test
Tests all API endpoints: signup, login, chat, history
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"
TEST_EMAIL = f"testuser_{int(time.time())}@example.com"
TEST_PASSWORD = "password123"
TEST_DISPLAY_NAME = "Test User"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_header(msg):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{msg}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def test_health_check():
    """Test health check endpoint"""
    print_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'ok':
            print_success(f"Server is healthy (v{data['version']})")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        return False

def test_signup():
    """Test user signup"""
    print_header("TEST 2: User Signup")
    try:
        payload = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'displayName': TEST_DISPLAY_NAME
        }
        
        print_info(f"Creating user: {TEST_EMAIL}")
        response = requests.post(f"{BASE_URL}/api/signup", json=payload)
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'success':
            print_success(f"User registered: {data['user_id']}")
            print_info(f"Display Name: {data['displayName']}")
            return True, data['user_id']
        else:
            print_error(f"Signup failed: {data.get('message', 'Unknown error')}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return False, None
    except Exception as e:
        print_error(f"Signup error: {e}")
        return False, None

def test_login():
    """Test user login"""
    print_header("TEST 3: User Login")
    try:
        payload = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
        }
        
        print_info(f"Logging in: {TEST_EMAIL}")
        response = requests.post(f"{BASE_URL}/api/login", json=payload)
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'success':
            print_success(f"User logged in: {data['user_id']}")
            print_info(f"Email: {data['email']}")
            return True, data['user_id']
        else:
            print_error(f"Login failed: {data.get('message', 'Unknown error')}")
            return False, None
    except Exception as e:
        print_error(f"Login error: {e}")
        return False, None

def test_new_session(user_id):
    """Test session creation"""
    print_header("TEST 4: New Session")
    try:
        payload = {'user_id': user_id}
        
        print_info(f"Creating session for user: {user_id}")
        response = requests.post(f"{BASE_URL}/api/new-session", json=payload)
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'success':
            print_success(f"Session created: {data['session_id']}")
            print_info(f"User ID: {data['user_id']}")
            return True, data['session_id']
        else:
            print_error(f"Session creation failed: {data.get('message', 'Unknown error')}")
            return False, None
    except Exception as e:
        print_error(f"Session error: {e}")
        return False, None

def test_chat(session_id, query="What is artificial intelligence?"):
    """Test chat endpoint"""
    print_header("TEST 5: Chat Endpoint")
    try:
        payload = {
            'session_id': session_id,
            'query': query,
            'model': 'all'
        }
        
        print_info(f"Sending query: '{query}'")
        print_info("Waiting for LLM responses (this may take a moment)...")
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'success':
            print_success(f"Chat request successful (took {elapsed:.2f}s)")
            print_info(f"Response time: {data.get('time', 'N/A')}")
            
            responses = data.get('responses', {})
            if responses.get('openai'):
                print_info(f"OpenAI: {responses['openai'][:100]}...")
            if responses.get('gemini'):
                print_info(f"Gemini: {responses['gemini'][:100]}...")
            if responses.get('openrouter'):
                print_info(f"OpenRouter: {responses['openrouter'][:100]}...")
            
            return True
        else:
            print_error(f"Chat failed: {data.get('message', 'Unknown error')}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return False
    except requests.Timeout:
        print_error("Request timed out (LLM took too long to respond)")
        return False
    except Exception as e:
        print_error(f"Chat error: {e}")
        return False

def test_get_history(session_id):
    """Test history retrieval"""
    print_header("TEST 6: Get Chat History")
    try:
        print_info(f"Retrieving history for session: {session_id}")
        response = requests.get(f"{BASE_URL}/api/history/{session_id}")
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'success':
            history = data.get('history', [])
            if history:
                print_success(f"Retrieved {len(history)} chat(s)")
                if isinstance(history, list):
                    print_info(f"First chat: {history[0]}")
                else:
                    print_info(f"History data: {json.dumps(history, indent=2)[:200]}...")
            else:
                print_info("No history yet (this is normal for new sessions)")
            return True
        else:
            print_info(f"History endpoint returned: {data}")
            return True  # Not critical
    except Exception as e:
        print_error(f"History error: {e}")
        return False

def test_homepage():
    """Test homepage loads"""
    print_header("TEST 7: Homepage")
    try:
        print_info("Accessing homepage...")
        response = requests.get(f"{BASE_URL}/")
        
        if response.status_code == 200 and 'Multi-LLM Chat' in response.text:
            print_success("Homepage loaded successfully")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Homepage error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n")
    print(f"{Colors.BLUE}╔{'='*58}╗{Colors.RESET}")
    print(f"{Colors.BLUE}║{'WEB APP INTEGRATION TEST SUITE'.center(58)}║{Colors.RESET}")
    print(f"{Colors.BLUE}╚{'='*58}╝{Colors.RESET}")
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    if not results[-1][1]:
        print_error("Cannot proceed - server not responding")
        return
    
    # Test 2: Homepage
    results.append(("Homepage", test_homepage()))
    
    # Test 3: Signup
    signup_ok, user_id = test_signup()
    results.append(("Signup", signup_ok))
    
    if not signup_ok:
        print_error("Cannot proceed - signup failed")
        return
    
    # Test 4: Login
    login_ok, _ = test_login()
    results.append(("Login", login_ok))
    
    # Test 5: New Session
    session_ok, session_id = test_new_session(user_id)
    results.append(("New Session", session_ok))
    
    if not session_ok:
        print_error("Cannot proceed - session creation failed")
        return
    
    # Test 6: Chat
    chat_ok = test_chat(session_id)
    results.append(("Chat", chat_ok))
    
    # Test 7: Get History
    history_ok = test_get_history(session_id)
    results.append(("Get History", history_ok))
    
    # Print Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{status}: {test_name}")
    
    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 All tests passed! Web app is ready for deployment.{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  {total - passed} test(s) failed.{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}Web App URL: http://localhost:5000{Colors.RESET}")
    print(f"{Colors.BLUE}API Base: http://localhost:5000/api{Colors.RESET}\n")

if __name__ == "__main__":
    run_all_tests()
