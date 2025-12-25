"""
Google API Key Tester
Tests if your Google Calendar, Maps, and YouTube API keys work
Run this BEFORE building the integration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_calendar_api():
    """Test Google Calendar API"""
    print("\n📅 Testing Google Calendar API...")
    
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle
        
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        
        creds = None
        
        # Check if we have saved credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # You need credentials.json from Google Cloud Console
                if not os.path.exists('credentials.json'):
                    print("❌ credentials.json not found!")
                    print("\n📝 HOW TO GET credentials.json:")
                    print("1. Go to: https://console.cloud.google.com/")
                    print("2. Create/Select project")
                    print("3. Enable Google Calendar API")
                    print("4. Create OAuth 2.0 credentials")
                    print("5. Download as credentials.json")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        # Try to use the API
        service = build('calendar', 'v3', credentials=creds)
        
        # Get list of calendars
        calendar_list = service.calendarList().list().execute()
        
        print("✅ Google Calendar API works!")
        print(f"   Found {len(calendar_list.get('items', []))} calendars")
        
        return True
        
    except ImportError:
        print("❌ Google Calendar libraries not installed")
        print("\n📦 Install with:")
        print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_google_maps_api():
    """Test Google Maps Distance Matrix API"""
    print("\n🗺️  Testing Google Maps API...")
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY not found in .env")
        print("\n📝 Add to .env file:")
        print("   GOOGLE_MAPS_API_KEY=your_key_here")
        return False
    
    try:
        import requests
        
        # Simple test: Distance from Taksim to Kadıköy
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': 'Taksim, Istanbul',
            'destinations': 'Kadıköy, Istanbul',
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'OK':
            distance = data['rows'][0]['elements'][0]['distance']['text']
            duration = data['rows'][0]['elements'][0]['duration']['text']
            
            print("✅ Google Maps API works!")
            print(f"   Example: Taksim → Kadıköy = {distance} ({duration})")
            return True
        else:
            print(f"❌ API Error: {data['status']}")
            if 'error_message' in data:
                print(f"   {data['error_message']}")
            return False
            
    except ImportError:
        print("❌ requests library not installed")
        print("   pip install requests")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_youtube_api():
    """Test YouTube Data API"""
    print("\n📺 Testing YouTube API...")
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found in .env")
        print("\n📝 Add to .env file:")
        print("   YOUTUBE_API_KEY=your_key_here")
        return False
    
    try:
        import requests
        
        # Simple test: Search for a theater-related video
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': 'Hamlet tiyatro',
            'maxResults': 1,
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            video_title = data['items'][0]['snippet']['title']
            
            print("✅ YouTube API works!")
            print(f"   Example search result: {video_title}")
            return True
        else:
            print(f"❌ API Error: {data.get('error', {}).get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_env_file():
    """Check if .env file exists"""
    print("\n📄 Checking .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("\n📝 Create .env file with:")
        print("""
# Google APIs
GOOGLE_MAPS_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here

# LLM APIs (already have these)
GEMINI_API_KEY=your_existing_key
ANTHROPIC_API_KEY=your_existing_key
        """)
        return False
    else:
        print("✅ .env file found")
        return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  GOOGLE API KEY TESTER")
    print("="*70)
    
    results = {
        'env_file': check_env_file(),
        'calendar': test_google_calendar_api(),
        'maps': test_google_maps_api(),
        'youtube': test_youtube_api()
    }
    
    print("\n" + "="*70)
    print("  TEST RESULTS")
    print("="*70)
    
    for test, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test.upper()}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Ready for integration!")
    else:
        print("\n⚠️  Some tests failed. Fix issues above before continuing.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()