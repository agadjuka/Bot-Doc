"""
English texts for Telegram bot - Template version
Contains basic message texts for bot template
"""

EN_TRANSLATIONS = {
    # Welcome messages
    "welcome": {
        "start_message": "Hello, {user}! 👋\n\nChoose an action:",
        "main_menu": "🏠 Main Menu\n\nUse /start to begin new work.",
        "choose_language": "🌍 Choose language / Choose language:",
    },
    
    # Interface buttons
    "buttons": {
        "help": "Help",
        "language": "Language",
        "back": "⬅️ Back",
    },
    
    # Error messages
    "errors": {
        "unknown_action": "Unknown action",
        "unsupported_language": "❌ Unsupported language",
        "language_fallback": "❌ Unsupported language. English language set as default.",
    },
    
    # Status messages
    "status": {
        "processing": "Processing...",
    },
    
    # Common messages
    "common": {
        "no_data_to_display": "No data to display",
    },
    
    # Documents and contracts
    "document": {
        "new_contract_start": "📄 **Creating new document.**\n\nPlease copy and send me the company details (company card) in one message. I will analyze them and prepare the document.",
        "info_received": "✅ Information received. Starting processing...",
        "creation_cancelled": "❌ Document creation cancelled.",
    },
}
