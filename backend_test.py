import requests
import sys
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

class BalaLabAPITester:
    def __init__(self):
        self.base_url = "https://lab-report-hub-1.preview.emergentagent.com/api"
        self.admin_token = None
        self.user_token = None
        self.admin_user = None
        self.normal_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.uploaded_report_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for multipart
                    headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content and response.headers.get('content-type', '').startswith('application/json') else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No error details')
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response text: {response.text[:200]}")
                return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        success, _ = self.run_test(
            "API Root",
            "GET",
            "/",
            200
        )
        return success

    def test_admin_register(self):
        """Register admin account"""
        success, response = self.run_test(
            "Admin Registration",
            "POST",
            "/auth/register",
            200,
            data={"email": "admin@test.com", "password": "admin123", "role": "admin"}
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.admin_user = response['user']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            
        return success

    def test_user_register(self):
        """Register normal user account"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "/auth/register",
            200,
            data={"email": "user@test.com", "password": "user123", "role": "user"}
        )
        
        if success and 'token' in response:
            self.user_token = response['token']
            self.normal_user = response['user']
            print(f"   User token obtained: {self.user_token[:20]}...")
            
        return success

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@test.com", "password": "admin123"}
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.admin_user = response['user']
            
        return success

    def test_user_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "/auth/login",
            200,
            data={"email": "user@test.com", "password": "user123"}
        )
        
        if success and 'token' in response:
            self.user_token = response['token']
            self.normal_user = response['user']
            
        return success

    def test_invalid_login(self):
        """Test invalid login credentials"""
        success, _ = self.run_test(
            "Invalid Login",
            "POST",
            "/auth/login",
            401,
            data={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        return success

    def test_get_me_admin(self):
        """Test /auth/me endpoint for admin"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Get Me (Admin)",
            "GET",
            "/auth/me",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   User info: {response.get('email')} ({response.get('role')})")
            
        return success

    def test_get_me_user(self):
        """Test /auth/me endpoint for user"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        success, response = self.run_test(
            "Get Me (User)",
            "GET",
            "/auth/me",
            200,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        if success:
            print(f"   User info: {response.get('email')} ({response.get('role')})")
            
        return success

    def test_get_me_unauthorized(self):
        """Test /auth/me without token"""
        success, _ = self.run_test(
            "Get Me (Unauthorized)",
            "GET",
            "/auth/me",
            403,  # Expecting 403 due to missing Authorization header
        )
        return success

    def create_test_image_file(self):
        """Create a small test image file"""
        # Create a simple 1x1 pixel PNG
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.write(png_data)
        temp_file.close()
        
        return temp_file.name

    def test_upload_report_admin(self):
        """Test file upload by admin"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
        
        # Create test file
        test_file_path = self.create_test_image_file()
        
        try:
            with open(test_file_path, 'rb') as f:
                success, response = self.run_test(
                    "Upload Report (Admin)",
                    "POST",
                    "/reports/upload",
                    200,
                    data={"user_email": "user@test.com"},
                    files={"file": ("test_report.png", f, "image/png")},
                    headers={'Authorization': f'Bearer {self.admin_token}'}
                )
            
            if success and 'id' in response:
                self.uploaded_report_id = response['id']
                print(f"   Uploaded report ID: {self.uploaded_report_id}")
                
        finally:
            # Clean up temp file
            os.unlink(test_file_path)
            
        return success

    def test_upload_report_user_forbidden(self):
        """Test file upload by regular user (should fail)"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
        
        test_file_path = self.create_test_image_file()
        
        try:
            with open(test_file_path, 'rb') as f:
                success, _ = self.run_test(
                    "Upload Report (User - Forbidden)",
                    "POST",
                    "/reports/upload",
                    403,
                    data={"user_email": "user@test.com"},
                    files={"file": ("test_report.png", f, "image/png")},
                    headers={'Authorization': f'Bearer {self.user_token}'}
                )
                
        finally:
            os.unlink(test_file_path)
            
        return success

    def test_list_reports_admin(self):
        """Test listing reports as admin"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "List Reports (Admin)",
            "GET",
            "/reports",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   Found {len(response)} reports for admin")
            
        return success

    def test_list_reports_user(self):
        """Test listing reports as user"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        success, response = self.run_test(
            "List Reports (User)",
            "GET",
            "/reports",
            200,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        if success:
            print(f"   Found {len(response)} reports for user")
            
        return success

    def test_download_report_user(self):
        """Test downloading report as user"""
        if not self.user_token or not self.uploaded_report_id:
            print("❌ Skipping - No user token or uploaded report available")
            return False
            
        success, _ = self.run_test(
            "Download Report (User)",
            "GET",
            f"/reports/{self.uploaded_report_id}/download",
            200,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        return success

    def test_preview_report_user(self):
        """Test previewing report as user"""
        if not self.user_token or not self.uploaded_report_id:
            print("❌ Skipping - No user token or uploaded report available")
            return False
            
        success, _ = self.run_test(
            "Preview Report (User)",
            "GET",
            f"/reports/{self.uploaded_report_id}/preview",
            200,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        return success

    def test_delete_report_user_forbidden(self):
        """Test deleting report as user (should fail)"""
        if not self.user_token or not self.uploaded_report_id:
            print("❌ Skipping - No user token or uploaded report available")
            return False
            
        success, _ = self.run_test(
            "Delete Report (User - Forbidden)",
            "DELETE",
            f"/reports/{self.uploaded_report_id}",
            403,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        return success

    def test_delete_report_admin(self):
        """Test deleting report as admin"""
        if not self.admin_token or not self.uploaded_report_id:
            print("❌ Skipping - No admin token or uploaded report available")
            return False
            
        success, _ = self.run_test(
            "Delete Report (Admin)",
            "DELETE",
            f"/reports/{self.uploaded_report_id}",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            self.uploaded_report_id = None  # Clear since deleted
            
        return success

    def test_list_users_admin(self):
        """Test listing users as admin"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "List Users (Admin)",
            "GET",
            "/users",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   Found {len(response)} users")
            
        return success

    def test_list_users_user_forbidden(self):
        """Test listing users as regular user (should fail)"""
        if not self.user_token:
            print("❌ Skipping - No user token available")
            return False
            
        success, _ = self.run_test(
            "List Users (User - Forbidden)",
            "GET",
            "/users",
            403,
            headers={'Authorization': f'Bearer {self.user_token}'}
        )
        
        return success

def main():
    print("🧪 Starting Bala Lab API Tests")
    print("=" * 50)
    
    tester = BalaLabAPITester()
    
    # Run all tests in order
    tests = [
        tester.test_api_root,
        tester.test_admin_register,
        tester.test_user_register,
        tester.test_admin_login,
        tester.test_user_login,
        tester.test_invalid_login,
        tester.test_get_me_admin,
        tester.test_get_me_user,
        tester.test_get_me_unauthorized,
        tester.test_upload_report_admin,
        tester.test_upload_report_user_forbidden,
        tester.test_list_reports_admin,
        tester.test_list_reports_user,
        tester.test_download_report_user,
        tester.test_preview_report_user,
        tester.test_delete_report_user_forbidden,
        tester.test_list_users_admin,
        tester.test_list_users_user_forbidden,
        tester.test_delete_report_admin,  # Clean up at end
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary:")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%" if tester.tests_run > 0 else "   Success rate: 0%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())