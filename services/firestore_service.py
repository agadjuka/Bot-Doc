"""
Firestore Service for managing user document templates
Handles template storage, retrieval, and management in Firestore
"""
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


class FirestoreService:
    """Service for managing user document templates in Firestore"""
    
    def __init__(self, db_instance: Optional[firestore.Client] = None):
        """
        Initialize FirestoreService with Firestore client
        
        Args:
            db_instance: Firestore client instance. If None, will try to get global instance
        """
        self.db = db_instance
        if not self.db:
            # Try to get global Firestore instance from main.py
            try:
                import main
                self.db = main.db
            except (ImportError, AttributeError):
                print("⚠️ FirestoreService initialized without Firestore - operations will fail")
        
        if self.db:
            print("✅ FirestoreService initialized with Firestore instance")
        else:
            print("❌ FirestoreService initialized without Firestore - operations will fail")
    
    async def add_template(self, user_id: int, template_name: str, file_id: str, file_type: str = 'docx') -> bool:
        """
        Add a new document template to user's collection
        
        Args:
            user_id: Telegram user ID
            template_name: Name of the template
            file_id: Telegram file ID
            file_type: Type of the file (default: 'docx')
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if not template_name or not file_id:
            print("❌ Template name and file_id are required")
            return False
        
        try:
            # Get user document reference
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists, create if not
            user_doc = user_ref.get()
            if not user_doc.exists:
                user_ref.set({
                    'created_at': datetime.now(),
                    'role': 'user'  # Default role
                })
                print(f"✅ Created user document for {user_id}")
            
            # Add template to user's document_templates subcollection
            template_ref = user_ref.collection('document_templates').document()
            template_data = {
                'template_name': template_name,
                'file_id': file_id,
                'file_type': file_type,
                'created_at': datetime.now()
            }
            
            template_ref.set(template_data)
            print(f"✅ Added template '{template_name}' for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding template: {e}")
            return False
    
    async def get_templates(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all templates for a user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of template dictionaries with template_name, file_id, and created_at
        """
        if not self.db:
            print("❌ Firestore not available")
            return []
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists
            user_doc = user_ref.get()
            if not user_doc.exists:
                print(f"❌ User {user_id} document does not exist")
                return []
            
            # Get all templates from user's document_templates subcollection
            templates_ref = user_ref.collection('document_templates')
            templates = templates_ref.stream()
            
            template_list = []
            for template in templates:
                template_data = template.to_dict()
                template_data['template_doc_id'] = template.id  # Add document ID
                template_list.append(template_data)
            
            # Sort by creation date (newest first)
            template_list.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
            
            print(f"✅ Retrieved {len(template_list)} templates for user {user_id}")
            return template_list
            
        except Exception as e:
            print(f"❌ Error getting templates: {e}")
            return []
    
    async def get_template_file_id(self, user_id: int, template_doc_id: str) -> Optional[str]:
        """
        Get file_id of a specific template by its document ID
        
        Args:
            user_id: Telegram user ID
            template_doc_id: Document ID of the template in Firestore
            
        Returns:
            File ID if found, None otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return None
        
        if not template_doc_id:
            print("❌ Template document ID is required")
            return None
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists
            user_doc = user_ref.get()
            if not user_doc.exists:
                print(f"❌ User {user_id} document does not exist")
                return None
            
            # Get specific template document
            template_ref = user_ref.collection('document_templates').document(template_doc_id)
            template_doc = template_ref.get()
            
            if not template_doc.exists:
                print(f"❌ Template {template_doc_id} not found for user {user_id}")
                return None
            
            template_data = template_doc.to_dict()
            file_id = template_data.get('file_id')
            
            if file_id:
                print(f"✅ Retrieved file_id for template {template_doc_id}: {file_id}")
            else:
                print(f"❌ No file_id found for template {template_doc_id}")
            
            return file_id
            
        except Exception as e:
            print(f"❌ Error getting template file_id: {e}")
            return None
    
    async def delete_template(self, user_id: int, template_doc_id: str) -> bool:
        """
        Delete a template from user's collection
        
        Args:
            user_id: Telegram user ID
            template_doc_id: Document ID of the template to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if not template_doc_id:
            print("❌ Template document ID is required")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists
            user_doc = user_ref.get()
            if not user_doc.exists:
                print(f"❌ User {user_id} document does not exist")
                return False
            
            # Delete specific template document
            template_ref = user_ref.collection('document_templates').document(template_doc_id)
            template_doc = template_ref.get()
            
            if not template_doc.exists:
                print(f"❌ Template {template_doc_id} not found for user {user_id}")
                return False
            
            template_ref.delete()
            print(f"✅ Deleted template {template_doc_id} for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting template: {e}")
            return False
    
    async def update_template_name(self, user_id: int, template_doc_id: str, new_name: str) -> bool:
        """
        Update template name
        
        Args:
            user_id: Telegram user ID
            template_doc_id: Document ID of the template to update
            new_name: New name for the template
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if not template_doc_id or not new_name:
            print("❌ Template document ID and new name are required")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists
            user_doc = user_ref.get()
            if not user_doc.exists:
                print(f"❌ User {user_id} document does not exist")
                return False
            
            # Update template name
            template_ref = user_ref.collection('document_templates').document(template_doc_id)
            template_doc = template_ref.get()
            
            if not template_doc.exists:
                print(f"❌ Template {template_doc_id} not found for user {user_id}")
                return False
            
            template_ref.update({
                'template_name': new_name,
                'updated_at': datetime.now()
            })
            
            print(f"✅ Updated template {template_doc_id} name to '{new_name}' for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating template name: {e}")
            return False
    
    async def get_template_info(self, user_id: int, template_doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete template information
        
        Args:
            user_id: Telegram user ID
            template_doc_id: Document ID of the template
            
        Returns:
            Template data dictionary or None if not found
        """
        if not self.db:
            print("❌ Firestore not available")
            return None
        
        if not template_doc_id:
            print("❌ Template document ID is required")
            return None
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists
            user_doc = user_ref.get()
            if not user_doc.exists:
                print(f"❌ User {user_id} document does not exist")
                return None
            
            # Get specific template document
            template_ref = user_ref.collection('document_templates').document(template_doc_id)
            template_doc = template_ref.get()
            
            if not template_doc.exists:
                print(f"❌ Template {template_doc_id} not found for user {user_id}")
                return None
            
            template_data = template_doc.to_dict()
            template_data['template_doc_id'] = template_doc_id  # Add document ID
            
            print(f"✅ Retrieved template info for {template_doc_id}")
            return template_data
            
        except Exception as e:
            print(f"❌ Error getting template info: {e}")
            return None


# Global instance management
_global_firestore_service: Optional[FirestoreService] = None

def get_firestore_service(db_instance: Optional[firestore.Client] = None) -> FirestoreService:
    """
    Get global FirestoreService instance
    
    Args:
        db_instance: Firestore client instance. If None, will try to get global instance
        
    Returns:
        FirestoreService instance
    """
    global _global_firestore_service
    
    if _global_firestore_service is None:
        _global_firestore_service = FirestoreService(db_instance)
    
    return _global_firestore_service
