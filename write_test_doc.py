"""
Firebase Write Operation Test
Simple script to create a test document in the 'testing' collection
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

# Initialize Firebase
FIREBASE_KEY = "gen-lang-client-0912421212-firebase-adminsdk-fbsvc-5aaf9afd87.json"
COLLECTION = "testing"

try:
    cred = credentials.Certificate(FIREBASE_KEY)
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass  # Already initialized
    
    db = firestore.client()
    print("✅ Firebase connected successfully\n")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit()

# Create test document
print("="*60)
print("CREATING TEST DOCUMENT")
print("="*60)

# Generate unique document ID
doc_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Test data
test_doc = {
    "title": "Multi-LLM Test Document",
    "description": "Test document created from write operation test script",
    "created_at": datetime.now().isoformat(),
    "app_info": {
        "name": "Multi-LLM Project",
        "database": "Firebase Firestore",
        "collection": COLLECTION,
        "version": "1.0"
    },
    "test_data": {
        "llm_models": ["OpenAI", "Gemini", "OpenRouter"],
        "features": ["Chat", "History", "Analytics"],
        "status": "Active"
    },
    "metadata": {
        "test_type": "write_operation",
        "data_types": ["string", "object", "array", "timestamp"]
    }
}

try:
    print(f"\n📝 Writing document: '{doc_id}'")
    print(f"📂 Collection: '{COLLECTION}'")
    print(f"\n📊 Document content:")
    print("-"*60)
    import json
    print(json.dumps(test_doc, indent=2))
    print("-"*60)
    
    # Write to Firestore
    db.collection(COLLECTION).document(doc_id).set(test_doc)
    
    print(f"\n✅ SUCCESS: Document written!")
    print(f"   Document ID: {doc_id}")
    print(f"   Path: {COLLECTION}/{doc_id}")
    print(f"   Timestamp: {test_doc['created_at']}")
    
    # Verify document was written by reading it back
    print(f"\n🔍 Verifying document...")
    doc = db.collection(COLLECTION).document(doc_id).get()
    
    if doc.exists:
        print(f"✅ VERIFIED: Document exists in Firebase!")
        print(f"\n📋 Document Details:")
        print(f"   Size: {len(json.dumps(doc.to_dict()))} bytes")
        print(f"   Fields: {list(doc.to_dict().keys())}")
        print(f"\n✅ Write operation completed successfully!")
    else:
        print(f"❌ ERROR: Document not found after write")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\n📱 View this document in Firebase Console:")
    print(f"   Collection: {COLLECTION}")
    print(f"   Document ID: {doc_id}")
    print("\n💾 Document successfully persisted in Firebase\n")
    
except Exception as e:
    print(f"\n❌ ERROR: Failed to write document")
    print(f"   Error: {e}")
    print(f"   Type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
