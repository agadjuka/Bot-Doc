#!/usr/bin/env python3
"""
Test script for FirestoreService
Tests template management functionality
"""
import asyncio
import os
from services.firestore_service import get_firestore_service

async def test_firestore_service():
    """Test FirestoreService functionality"""
    print("🧪 Testing FirestoreService...")
    
    # Initialize service
    firestore_service = get_firestore_service()
    
    # Test user ID
    test_user_id = 123456789
    
    # Test 1: Add template
    print("\n📝 Test 1: Adding template...")
    success = await firestore_service.add_template(
        user_id=test_user_id,
        template_name="Test Contract Template",
        file_id="BAADBAADrwADBREAAYag8gABhqDyAAE",
        file_type="docx"
    )
    print(f"✅ Add template result: {success}")
    
    # Test 2: Get templates
    print("\n📋 Test 2: Getting templates...")
    templates = await firestore_service.get_templates(test_user_id)
    print(f"✅ Found {len(templates)} templates:")
    for template in templates:
        print(f"  - {template['template_name']} (ID: {template['template_doc_id']})")
    
    # Test 3: Get specific template file_id
    if templates:
        template_doc_id = templates[0]['template_doc_id']
        print(f"\n🔍 Test 3: Getting file_id for template {template_doc_id}...")
        file_id = await firestore_service.get_template_file_id(test_user_id, template_doc_id)
        print(f"✅ File ID: {file_id}")
        
        # Test 4: Get complete template info
        print(f"\n📄 Test 4: Getting complete template info...")
        template_info = await firestore_service.get_template_info(test_user_id, template_doc_id)
        print(f"✅ Template info: {template_info}")
        
        # Test 5: Update template name
        print(f"\n✏️ Test 5: Updating template name...")
        update_success = await firestore_service.update_template_name(
            test_user_id, 
            template_doc_id, 
            "Updated Test Contract Template"
        )
        print(f"✅ Update result: {update_success}")
        
        # Test 6: Delete template
        print(f"\n🗑️ Test 6: Deleting template...")
        delete_success = await firestore_service.delete_template(test_user_id, template_doc_id)
        print(f"✅ Delete result: {delete_success}")
    
    # Test 7: Get templates after deletion
    print("\n📋 Test 7: Getting templates after deletion...")
    templates_after = await firestore_service.get_templates(test_user_id)
    print(f"✅ Found {len(templates_after)} templates after deletion")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    # Check if we have the required environment variables
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        print("⚠️ Warning: No Google credentials found. Firestore operations may fail.")
        print("💡 Set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable")
    
    asyncio.run(test_firestore_service())
