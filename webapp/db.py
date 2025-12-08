import streamlit as st
import pymongo
import bcrypt
import certifi

# Use the provided URI
MONGO_URI = 
DB_NAME = "document_vault" # Using a specific DB name for this app, overriding URI default if needed, or just use URI's db. 
# The URI has /prescription_db. Let's try to use a separate DB 'document_vault' if possible, or collection 'vault_users' in prescription_db.
# Best practice: Use the DB from URI but separate collection.
COLLECTION_NAME = "vault_users"

@st.cache_resource
def init_connection():
    try:
        client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        return client
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def get_collection():
    client = init_connection()
    if client:
        db = client.get_database("prescription_db") # Using the DB from URI
        return db[COLLECTION_NAME]
    return None

def create_user(username, password, name):
    col = get_collection()
    if col is None: return False, "Database error"
    
    if col.find_one({"username": username}):
        return False, "Username already exists"
    
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    user_doc = {
        "username": username,
        "password": hashed,
        "name": name
    }
    
    try:
        col.insert_one(user_doc)
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {e}"

def verify_user(username, password):
    col = get_collection()
    if col is None: return None, "Database error"
    
    user = col.find_one({"username": username})
    if not user:
        return None, "Invalid username or password"
        
    if bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return user, "Success"
    
    return None, "Invalid username or password"
