import requests
import json
import os
import uuid
import io
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "integration_test@example.com"
TEST_PASSWORD = "testpassword"
TEST_HOUSE_NAME = "Test House"
TEST_NODE_LOCATION = "Test Location"
TEST_NODE_TYPE = "Test Type"

def print_test_result(test_name: str, success: bool, message: str = ""):
    """Print test result in a formatted way"""
    status = "SUCCESS" if success else "FAILED"
    print(f"Test {test_name}: {status}")
    if message:
        print(f"Message: {message}")
    print("-" * 50)

def get_headers(access_token: str = None) -> Dict[str, str]:
    """Get headers with optional authorization"""
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers

def test_signup() -> bool:
    """Test user registration"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers=get_headers()
        )
        
        if response.status_code in [200, 400]:  # 400 if user already exists
            print_test_result("Signup", True, 
                            "User created" if response.status_code == 200 else "User already exists")
            return True
        else:
            print_test_result("Signup", False, f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("Signup", False, str(e))
        return False

def test_login() -> tuple[bool, str]:
    """Test user login and return access token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            print_test_result("Login", True)
            return True, access_token
        else:
            print_test_result("Login", False, f"Unexpected status code: {response.status_code}")
            return False, None
    except Exception as e:
        print_test_result("Login", False, str(e))
        return False, None

def test_create_house(access_token: str) -> tuple[bool, int]:
    """Test house creation and return house ID"""
    try:
        response = requests.post(
            f"{BASE_URL}/houses/",
            json={"name": TEST_HOUSE_NAME},
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            house_id = response.json()["id"]
            print_test_result("Create House", True)
            return True, house_id
        else:
            print_test_result("Create House", False, f"Unexpected status code: {response.status_code}")
            return False, None
    except Exception as e:
        print_test_result("Create House", False, str(e))
        return False, None

def test_create_node(access_token: str, house_id: int) -> tuple[bool, int]:
    """Test node creation and return node ID"""
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/",
            json={
                "house_id": house_id,
                "location": TEST_NODE_LOCATION,
                "type": TEST_NODE_TYPE
            },
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            node_id = response.json()["id"]
            print_test_result("Create Node", True)
            return True, node_id
        else:
            print_test_result("Create Node", False, f"Unexpected status code: {response.status_code}")
            return False, None
    except Exception as e:
        print_test_result("Create Node", False, str(e))
        return False, None

def test_protected_endpoint(access_token: str) -> bool:
    """Test protected endpoint access"""
    try:
        response = requests.get(
            f"{BASE_URL}/maintenance/test-maintenance",
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            print_test_result("Protected Endpoint", True)
            return True
        else:
            print_test_result("Protected Endpoint", False, f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("Protected Endpoint", False, str(e))
        return False

def test_upload_legacy_document(access_token: str, house_id: int, node_id: int) -> tuple[bool, int]:
    """Test legacy document upload and return document ID"""
    try:
        # Create temporary test file
        temp_file_path = "temp_test_document.txt"
        with open(temp_file_path, "w") as f:
            f.write("This is a test document content")
        
        # Prepare multipart form data
        files = {
            'file': ('temp_test_document.txt', open(temp_file_path, 'rb'), 'text/plain')
        }
        data = {
            'house_id': str(house_id),
            'node_id': str(node_id),
            'type': 'TXT',
            'version': '1.0'
        }
        
        response = requests.post(
            f"{BASE_URL}/legacy-documents",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Clean up temporary file
        os.remove(temp_file_path)
        
        if response.status_code == 200:
            doc_id = response.json()["id"]
            print_test_result("Upload Legacy Document", True)
            return True, doc_id
        else:
            print_test_result("Upload Legacy Document", False, f"Unexpected status code: {response.status_code}")
            return False, None
    except Exception as e:
        print_test_result("Upload Legacy Document", False, str(e))
        return False, None

def test_get_legacy_documents(access_token: str, node_id: int) -> bool:
    """Test retrieving legacy documents"""
    try:
        response = requests.get(
            f"{BASE_URL}/legacy-documents/{node_id}",
            headers=get_headers(access_token)
        )
        
        if response.status_code == 200:
            documents = response.json()
            success = len(documents) > 0
            print_test_result("Get Legacy Documents", success, 
                            f"Found {len(documents)} documents" if success else "No documents found")
            return success
        else:
            print_test_result("Get Legacy Documents", False, f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print_test_result("Get Legacy Documents", False, str(e))
        return False

def main():
    """Main test execution function"""
    print("Starting Integration Tests...")
    print("=" * 50)
    
    # Test signup
    if not test_signup():
        print("Signup failed, aborting tests")
        return
    
    # Test login
    login_success, access_token = test_login()
    if not login_success:
        print("Login failed, aborting tests")
        return
    
    # Test house creation
    house_success, house_id = test_create_house(access_token)
    if not house_success:
        print("House creation failed, aborting tests")
        return
    
    # Test node creation
    node_success, node_id = test_create_node(access_token, house_id)
    if not node_success:
        print("Node creation failed, aborting tests")
        return
    
    # Test protected endpoint
    if not test_protected_endpoint(access_token):
        print("Protected endpoint test failed, continuing with other tests")
    
    # Test legacy document upload
    upload_success, doc_id = test_upload_legacy_document(access_token, house_id, node_id)
    if not upload_success:
        print("Document upload failed, aborting tests")
        return
    
    # Test legacy document retrieval
    if not test_get_legacy_documents(access_token, node_id):
        print("Document retrieval failed")
    
    print("\nIntegration Tests Completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 