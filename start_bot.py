#!/usr/bin/env python3
"""
Simple script to start bot with Google Cloud credentials from JSON
"""
import os
import json
import sys

def setup_from_json():
    """Setup environment from JSON file"""
    current_dir = os.getcwd()
    json_file = os.path.join(current_dir, 'google-cloud-credentials.json')
    
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    # Read JSON file
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            creds = json.load(f)
        
        # Set environment variables from JSON
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_file
        os.environ['PROJECT_ID'] = creds.get('project_id', 'bot-doc-473208')
        os.environ['GOOGLE_CLOUD_LOCATION'] = 'asia-southeast1'
        os.environ['FIRESTORE_DATABASE'] = 'default'
        
        print("✅ Environment configured from JSON:")
        print(f"  Project ID: {os.environ['PROJECT_ID']}")
        print(f"  Credentials: {json_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting Bot Doc...")
    
    # Setup environment from JSON
    if not setup_from_json():
        return
    
    # Check for BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ BOT_TOKEN not set!")
        print("   Set it with: $env:BOT_TOKEN = 'your_bot_token'")
        print("   Or add it to env.local file")
        return
    
    print("✅ BOT_TOKEN found")
    print("🤖 Starting bot...")
    
    # Import and run main
    try:
        from main_local import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
