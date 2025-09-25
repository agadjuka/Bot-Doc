#!/usr/bin/env python3
"""
Script to extract Google Cloud credentials from JSON and create .env file
"""
import json
import os

def setup_credentials_from_json():
    """Extract credentials from JSON and create .env file"""
    print("🔧 Setting up credentials from JSON file...")
    
    # Read the JSON file
    json_file = "google-cloud-credentials.json"
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
        
        print("✅ JSON file loaded successfully")
        
        # Extract project ID
        project_id = credentials.get('project_id', 'bot-doc-473208')
        print(f"✅ Project ID: {project_id}")
        
        # Create .env content
        env_content = f"""# Bot Configuration
BOT_TOKEN=your_bot_token_here

# Google Cloud Configuration (extracted from JSON)
GOOGLE_APPLICATION_CREDENTIALS={os.path.abspath(json_file)}
PROJECT_ID={project_id}
GOOGLE_CLOUD_LOCATION=asia-southeast1

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Webhook URL for production
WEBHOOK_URL=your_webhook_url_here

# Optional: Firestore Database
FIRESTORE_DATABASE=default
"""
        
        # Write .env file
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env file created successfully")
        
        # Set environment variables for current session
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(json_file)
        os.environ['PROJECT_ID'] = project_id
        os.environ['GOOGLE_CLOUD_LOCATION'] = 'asia-southeast1'
        os.environ['FIRESTORE_DATABASE'] = 'default'
        
        print("✅ Environment variables set for current session")
        
        # Show what needs to be configured
        print("\n📋 Next steps:")
        print("1. Edit .env file and add your BOT_TOKEN")
        print("2. Edit .env file and add your GEMINI_API_KEY")
        print("3. Run: python main_local.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    setup_credentials_from_json()
