import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth as firebase_auth
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Initialize Firebase
try:
    firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    firebase_credentials_path = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        "multi-llm-chat-487415-firebase-adminsdk-fbsvc-7ee1f7cdc6.json"
    )

    if firebase_credentials_json:
        cred = credentials.Certificate(json.loads(firebase_credentials_json))
    else:
        cred = credentials.Certificate(firebase_credentials_path)

    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        # App already initialized
        pass
    db = firestore.client()
    print("✅ Firebase initialized successfully")
except Exception as e:
    print(f"⚠️ Firebase not initialized: {e}")
    print("Note: This is normal if firebase service account key is not yet added")
    db = None


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def register_user(email, password, display_name=""):
    """
    Register a new user with Firebase Authentication
    
    Args:
        email (str): User's email
        password (str): User's password
        display_name (str): User's display name
    
    Returns:
        dict: {'success': bool, 'user_id': str or None, 'message': str}
    """
    try:
        user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        
        # Create user document in Firestore
        user_data = {
            "uid": user.uid,
            "email": email,
            "displayName": display_name,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "lastLogin": firestore.SERVER_TIMESTAMP,
            "preferences": {
                "defaultModel": "all",
                "theme": "light",
                "notificationsEnabled": True
            }
        }
        
        db.collection("users").document(user.uid).set(user_data)
        
        print(f"✅ User registered successfully: {email}")
        return {
            'success': True,
            'user_id': user.uid,
            'message': 'User registered successfully'
        }
    except firebase_auth.EmailAlreadyExistsError:
        print(f"❌ Email already exists: {email}")
        return {
            'success': False,
            'user_id': None,
            'message': 'Email already registered'
        }
    except Exception as e:
        print(f"❌ Error registering user: {e}")
        return {
            'success': False,
            'user_id': None,
            'message': f'Registration error: {str(e)}'
        }


def verify_id_token(id_token):
    """
    Verify a Firebase ID token
    
    Args:
        id_token (str): Firebase ID token from client
    
    Returns:
        dict: {'valid': bool, 'uid': str or None, 'email': str or None}
    """
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        
        # Update last login
        db.collection("users").document(uid).update({
            "lastLogin": firestore.SERVER_TIMESTAMP
        })
        
        return {
            'valid': True,
            'uid': uid,
            'email': email
        }
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        return {
            'valid': False,
            'uid': None,
            'email': None
        }


def get_user_data(uid):
    """
    Get user data from Firestore
    
    Args:
        uid (str): User's unique ID
    
    Returns:
        dict: User data or None
    """
    if db is None:
        return None
    
    try:
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"❌ Error getting user data: {e}")
        return None


# ============================================================================
# CHAT HISTORY FUNCTIONS (NEW STRUCTURE)
# ============================================================================

def save_chat_history(user_id, query, responses, models_used=None, tokens_used=None):
    """
    Save chat interaction to Firestore in users/{uid}/chat_history subcollection
    
    Args:
        user_id (str): User's unique ID
        query (str): User's query/question
        responses (dict): Responses from different LLMs
        models_used (list): List of models used
        tokens_used (dict): Token counts per model
    
    Returns:
        bool: Success status
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping save.")
        return False
    
    try:
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        chat_data = {
            "query": query,
            "responses": responses,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "modelsUsed": models_used or list(responses.keys()),
        }
        
        if tokens_used:
            chat_data["tokens"] = tokens_used
        
        # Save to user's chat_history subcollection
        user_ref = db.collection("users").document(user_id)
        user_ref.collection("chat_history").document(timestamp).set(chat_data)
        
        print("✅ Chat history saved to Firebase")
        return True
    except Exception as e:
        print(f"❌ Error saving chat history: {e}")
        return False


def get_chat_history(user_id, limit=50):
    """
    Retrieve chat history from Firestore subcollection
    
    Args:
        user_id (str): User's unique ID
        limit (int): Maximum number of chat records to retrieve
    
    Returns:
        list: List of chat documents or empty list
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping retrieval.")
        return []
    
    try:
        chats = []
        docs = (db.collection("users").document(user_id)
                .collection("chat_history")
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream())
        
        for doc in docs:
            chat_doc = doc.to_dict()
            chat_doc['timestamp'] = doc.id
            chats.append(chat_doc)
        
        print(f"✅ Retrieved {len(chats)} chat records from Firebase")
        return chats
    except Exception as e:
        print(f"❌ Error retrieving chat history: {e}")
        return []


def delete_chat_history(user_id, timestamp=None):
    """
    Delete chat history from Firestore
    
    Args:
        user_id (str): User's unique ID
        timestamp (str): Specific chat timestamp to delete (None = all)
    
    Returns:
        bool: Success status
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping delete.")
        return False
    
    try:
        if timestamp:
            # Delete specific chat
            db.collection("users").document(user_id).collection("chat_history").document(timestamp).delete()
            print("✅ Single chat deleted from Firebase")
        else:
            # Delete all chats for user
            docs = db.collection("users").document(user_id).collection("chat_history").stream()
            for doc in docs:
                doc.reference.delete()
            print("✅ All chat history deleted from Firebase")
        
        return True
    except Exception as e:
        print(f"❌ Error deleting chat history: {e}")
        return False


# ============================================================================
# USER PREFERENCES FUNCTIONS
# ============================================================================

def save_user_preferences(user_id, preferences):
    """
    Save user preferences to Firestore
    
    Args:
        user_id (str): User's unique ID
        preferences (dict): User preferences
    
    Returns:
        bool: Success status
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping save.")
        return False
    
    try:
        # Use set with merge=True to create or update the document
        db.collection("users").document(user_id).set({
            "preferences": preferences,
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
        print("✅ User preferences saved to Firebase")
        return True
    except Exception as e:
        print(f"❌ Error saving preferences: {e}")
        return False


def get_user_preferences(user_id):
    """
    Get user preferences from Firestore
    
    Args:
        user_id (str): User's unique ID
    
    Returns:
        dict: User preferences or None
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping retrieval.")
        return None
    
    try:
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict().get("preferences", {})
        return None
    except Exception as e:
        print(f"❌ Error getting preferences: {e}")
        return None


# ============================================================================
# USAGE LOGGING FUNCTIONS
# ============================================================================

def log_llm_usage(user_id, model_used, tokens_used, cost=0):
    """
    Log LLM usage statistics
    
    Args:
        user_id (str): User's unique ID
        model_used (str): Model used (openai, gemini, openrouter)
        tokens_used (int): Tokens consumed
        cost (float): Cost in USD
    
    Returns:
        bool: Success status
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping usage log.")
        return False
    
    try:
        db.collection("llm_usage").add({
            "userId": user_id,
            "modelUsed": model_used,
            "tokensUsed": tokens_used,
            "cost": cost,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print("✅ Usage logged to Firebase")
        return True
    except Exception as e:
        print(f"❌ Error logging usage: {e}")
        return False


# ============================================================================
# LEGACY FUNCTIONS (For backward compatibility)
# ============================================================================

def save_chat_history_legacy(user_id, query, responses):
    """
    Legacy function - saves to 'conversations' collection
    Kept for backward compatibility
    
    Args:
        user_id (str): User's unique ID
        query (str): User's query
        responses (dict): Responses from LLMs
    
    Returns:
        bool: Success status
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping save.")
        return False
    
    try:
        doc_ref = db.collection("conversations").document(user_id)
        doc_ref.set({
            "user_id": user_id,
            "query": query,
            "responses": responses,
            "timestamp": firestore.SERVER_TIMESTAMP
        }, merge=True)
        print("✅ Conversation saved to Firebase (legacy)")
        return True
    except Exception as e:
        print(f"❌ Error saving to Firebase: {e}")
        return False


def get_chat_history_legacy(user_id):
    """
    Legacy function - retrieves from 'conversations' collection
    
    Args:
        user_id (str): User's unique ID
    
    Returns:
        dict: Chat history or None
    """
    if db is None:
        print("⚠️ Firebase not available. Skipping retrieval.")
        return None
    
    try:
        doc = db.collection("conversations").document(user_id).get()
        if doc.exists:
            print("✅ Chat history retrieved from Firebase (legacy)")
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"❌ Error retrieving from Firebase: {e}")
        return None

