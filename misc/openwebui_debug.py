import json
import os

import requests

# Configuration - UPDATE THESE
BASE_URL = "http://localhost:3000"  # Your Open WebUI URL
API_KEY = os.environ.get("OPENWEBUI_API_KEY")  # Your API key
JWT_TOKEN = os.environ.get("JWT_TOKEN")


def test_connection():
    """Test different API endpoints to find the right one"""
    print("🔧 Debugging Open WebUI API Connection")
    print("=" * 50)

    # Test basic connectivity first
    print(f"Testing base URL: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Base URL accessible - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach base URL: {e}")
        print("Please check your BASE_URL in the script")
        return

    # Try different API endpoints that might exist
    endpoints_to_try = [
        "/api/v1/knowledge/",  # Based on your upload script
        "/api/v1/knowledge",
        "/api/v1/files/",  # File endpoint from your script
        "/api/v1/files",
        "/api/models",  # Basic test endpoint from your script
        "/api/v1/knowledge/collections/",
        "/api/v1/knowledge/collections",
        "/api/knowledge/collections/",
        "/api/knowledge/collections",
        "/api/v1/documents/",
        "/api/v1/documents",
        "/api/documents/",
        "/api/documents",
        "/api/v1/",
        "/api/",
    ]

    headers_no_auth = {"Content-Type": "application/json"}
    headers_with_bearer = (
        {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        if API_KEY
        else headers_no_auth
    )
    headers_with_jwt = (
        {"Authorization": f"Bearer {JWT_TOKEN}", "Content-Type": "application/json"}
        if JWT_TOKEN
        else headers_no_auth
    )

    print("\n🔍 Testing API endpoints...")

    for endpoint in endpoints_to_try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\nTesting: {url}")

        # Try without authentication first
        try:
            response = requests.get(url, headers=headers_no_auth, timeout=5)
            print(f"   No auth - Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS! Valid JSON returned")
                    print(f"   Response preview: {str(data)[:200]}...")
                    return url, headers_no_auth, data
                except json.JSONDecodeError:
                    print(f"   ⚠️  Status 200 but invalid JSON")
                    print(f"   Response text: {response.text[:200]}...")
            elif response.status_code == 401:
                print(f"   🔐 Authentication required")
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found")
            else:
                print(f"   ❓ Other status: {response.text[:100]}")

        except Exception as e:
            print(f"   ❌ Connection error: {e}")

        # Try with API key
        if API_KEY and headers_with_bearer != headers_no_auth:
            try:
                response = requests.get(url, headers=headers_with_bearer, timeout=5)
                print(f"   API Key - Status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ SUCCESS with API key! Valid JSON returned")
                        print(f"   Response preview: {str(data)[:200]}...")
                        return url, headers_with_bearer, data
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Status 200 but invalid JSON with API key")

            except Exception as e:
                print(f"   ❌ API key connection error: {e}")

        # Try with JWT token
        if (
            JWT_TOKEN
            and headers_with_jwt != headers_no_auth
            and headers_with_jwt != headers_with_bearer
        ):
            try:
                response = requests.get(url, headers=headers_with_jwt, timeout=5)
                print(f"   JWT Token - Status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ SUCCESS with JWT! Valid JSON returned")
                        print(f"   Response preview: {str(data)[:200]}...")
                        return url, headers_with_jwt, data
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Status 200 but invalid JSON with JWT")

            except Exception as e:
                print(f"   ❌ JWT connection error: {e}")

    print("\n❌ No working endpoints found!")
    print("\n💡 Next steps:")
    print("1. Verify your Open WebUI is running and accessible")
    print("2. Check if you need authentication (API key)")
    print("3. Look at Open WebUI docs for the correct API endpoints")
    print("4. Try accessing the web interface to confirm it's working")

    return None, None, None


def check_webui_version():
    """Try to determine Open WebUI version/info"""
    print("\n🔍 Checking Open WebUI info...")

    info_endpoints = [
        "/api/version",
        "/api/v1/version",
        "/version",
        "/api/config",
        "/api/v1/config",
    ]

    for endpoint in info_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Found info at {endpoint}:")
                    print(f"   {json.dumps(data, indent=2)}")
                    return
                except:
                    print(f"✅ Found response at {endpoint}:")
                    print(f"   {response.text}")
                    return
        except:
            continue

    print("❌ Could not find version/config info")


if __name__ == "__main__":
    # Test the connection
    working_url, working_headers, sample_data = test_connection()

    if working_url:
        print(f"\n🎉 FOUND WORKING ENDPOINT: {working_url}")
        print("Update your main script with this URL and authentication setup")
    else:
        check_webui_version()
