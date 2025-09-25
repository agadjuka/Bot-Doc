#!/usr/bin/env python3
"""
Script to run the bot with proper environment setup
"""
import os
import sys

def setup_environment():
    """Setup environment variables"""
    # Get current directory
    current_dir = os.getcwd()
    
    # Set Google Cloud variables
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(current_dir, 'bot-doc-473208-706e6adceee1.json')
    os.environ['PROJECT_ID'] = 'bot-doc-473208'
    os.environ['GOOGLE_CLOUD_LOCATION'] = 'asia-southeast1'
    os.environ['FIRESTORE_DATABASE'] = 'default'
    
    print("✅ Google Cloud environment configured")
    print(f"  Credentials: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    print(f"  Project ID: {os.environ['PROJECT_ID']}")

def main():
    """Main function"""
    print("🚀 Starting Bot Doc...")
    
    # Setup environment
    setup_environment()
    
    # Check for required tokens
    bot_token = os.getenv('BOT_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if not bot_token or bot_token == 'test_token_placeholder':
        print("❌ BOT_TOKEN not set!")
        print("   Set it with: $env:BOT_TOKEN = 'your_real_bot_token'")
        print("   Or add it to your environment variables")
        return
    
    if not gemini_key or gemini_key == 'test_gemini_key_placeholder':
        print("❌ GEMINI_API_KEY not set!")
        print("   Set it with: $env:GEMINI_API_KEY = 'your_real_gemini_key'")
        print("   Or add it to your environment variables")
        return
    
    print("✅ All tokens configured")
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
