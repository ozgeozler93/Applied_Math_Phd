
# src/calendar_agent.py
"""
Agent 7: Calendar Integration Agent
Manages user's Google Calendar for theater events
"""

import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete token.pickle
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarAgent:
    """
    Agent 7: Calendar Integration
    
    Capabilities:
    - Add theater events to calendar
    - Check for scheduling conflicts
    - Find free time slots
    - Send reminders
    """
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """
        Authenticate with Google Calendar API
        """
        creds = None
        
        # Token.pickle stores user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("❌ credentials.json not found!")
                    print("📝 Get it from: https://console.cloud.google.com/")
                    print("   1. Enable Google Calendar API")
                    print("   2. Create OAuth 2.0 credentials")
                    print("   3. Download as credentials.json")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        print("✅ Calendar Agent authenticated!")
    
    def add_event(self, play_title, venue, show_date, show_time, ticket_url=None):
        """
        Add theater event to Google Calendar
        
        Args:
            play_title: Name of the play
            venue: Theater venue
            show_date: Date string (e.g., "16 Kasım Cumartesi")
            show_time: Time string (e.g., "20:30")
            ticket_url: URL to ticket page
        
        Returns:
            dict: Created event or error
        """
        if not self.service:
            return {"error": "Calendar service not authenticated"}
        
        try:
            # Parse date and time
            start_datetime = self._parse_turkish_date_time(show_date, show_time)
            
            if not start_datetime:
                return {"error": f"Could not parse date: {show_date} {show_time}"}
            
            # End time: 2.5 hours later (typical play duration)
            end_datetime = start_datetime + timedelta(hours=2, minutes=30)
            
            # Create event
            event = {
                'summary': f'🎭 {play_title}',
                'location': venue,
                'description': f"""Tiyatro Oyunu: {play_title}

Mekan: {venue}
Tarih: {show_date}
Saat: {show_time}

{f'🎫 Biletler: {ticket_url}' if ticket_url else ''}

🤖 StageAgent tarafından eklendi
""",
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/Istanbul',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/Istanbul',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},       # 1 hour before
                    ],
                },
                'colorId': '10',  # Green color for theater events
            }
            
            # Insert event
            event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': event['id'],
                'event_link': event.get('htmlLink'),
                'start': start_datetime.strftime('%Y-%m-%d %H:%M'),
                'end': end_datetime.strftime('%Y-%m-%d %H:%M')
            }
            
        except HttpError as error:
            return {'error': f'Calendar API error: {error}'}
        except Exception as e:
            return {'error': f'Error creating event: {e}'}
    
    def check_conflicts(self, show_date, show_time):
        """
        Check if user has conflicts at this time
        
        Args:
            show_date: Date string
            show_time: Time string
        
        Returns:
            dict: Conflict information
        """
        if not self.service:
            return {"error": "Calendar service not authenticated"}
        
        try:
            start_datetime = self._parse_turkish_date_time(show_date, show_time)
            
            if not start_datetime:
                return {"error": "Could not parse date"}
            
            # Check +/- 3 hours for conflicts
            time_min = (start_datetime - timedelta(hours=3)).isoformat() + 'Z'
            time_max = (start_datetime + timedelta(hours=3)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return {
                    'has_conflict': False,
                    'message': f'✅ {show_date} {show_time} müsaitsiniz!'
                }
            else:
                conflicts = []
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    conflicts.append({
                        'title': event['summary'],
                        'start': start
                    })
                
                return {
                    'has_conflict': True,
                    'message': f'⚠️ {len(events)} çakışma bulundu',
                    'conflicts': conflicts
                }
        
        except HttpError as error:
            return {'error': f'Calendar API error: {error}'}
    
    def find_free_slots(self, start_date, days=7):
        """
        Find free time slots in the next N days
        
        Args:
            start_date: Starting date
            days: Number of days to check
        
        Returns:
            list: Free evening slots (18:00-22:00)
        """
        if not self.service:
            return {"error": "Calendar service not authenticated"}
        
        try:
            free_slots = []
            
            for day_offset in range(days):
                check_date = start_date + timedelta(days=day_offset)
                
                # Check evening slots (18:00, 19:00, 20:00, 21:00)
                for hour in [18, 19, 20, 21]:
                    check_time = check_date.replace(hour=hour, minute=0, second=0)
                    
                    # Check if this slot is free
                    time_min = check_time.isoformat() + 'Z'
                    time_max = (check_time + timedelta(hours=3)).isoformat() + 'Z'
                    
                    events_result = self.service.events().list(
                        calendarId='primary',
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True
                    ).execute()
                    
                    events = events_result.get('items', [])
                    
                    if not events:
                        free_slots.append({
                            'date': check_time.strftime('%Y-%m-%d'),
                            'time': check_time.strftime('%H:%M'),
                            'day_name': check_time.strftime('%A')
                        })
            
            return {
                'free_slots': free_slots,
                'count': len(free_slots)
            }
        
        except HttpError as error:
            return {'error': f'Calendar API error: {error}'}
    
    def _parse_turkish_date_time(self, date_str, time_str):
        """
        Parse Turkish date format to datetime
        
        Args:
            date_str: "16 Kasım Cumartesi" or "16 Kasım"
            time_str: "20:30"
        
        Returns:
            datetime or None
        """
        # Turkish month names
        months = {
            'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
            'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
            'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
        }
        
        try:
            # Clean and split
            date_parts = date_str.lower().split()
            
            # Extract day and month
            day = int(date_parts[0])
            month_name = date_parts[1]
            
            month = months.get(month_name)
            if not month:
                return None
            
            # Current year or next year
            year = datetime.now().year
            
            # Parse time
            hour, minute = map(int, time_str.split(':'))
            
            # Create datetime
            event_datetime = datetime(year, month, day, hour, minute)
            
            # If date is in the past, assume next year
            if event_datetime < datetime.now():
                event_datetime = datetime(year + 1, month, day, hour, minute)
            
            return event_datetime
            
        except Exception as e:
            print(f"Date parsing error: {e}")
            return None


def demo():
    """
    Demo: Calendar Agent capabilities
    """
    print("\n" + "="*70)
    print("  🗓️  AGENT 7: CALENDAR INTEGRATION DEMO")
    print("="*70 + "\n")
    
    agent = CalendarAgent()
    
    if not agent.service:
        print("❌ Could not authenticate. Please set up credentials.json")
        return
    
    # Test 1: Check conflicts
    print("📋 Test 1: Checking conflicts for 16 Kasım 20:30")
    result = agent.check_conflicts("16 Kasım Cumartesi", "20:30")
    print(f"   Result: {result}\n")
    
    # Test 2: Find free slots
    print("📋 Test 2: Finding free evening slots in next 7 days")
    result = agent.find_free_slots(datetime.now(), days=7)
    print(f"   Found {result.get('count', 0)} free slots")
    if result.get('free_slots'):
        for slot in result['free_slots'][:5]:  # Show first 5
            print(f"   - {slot['date']} at {slot['time']} ({slot['day_name']})")
    print()
    
    # Test 3: Add event (optional - commented out to avoid actually creating)
    print("📋 Test 3: Adding event to calendar")
    print("   (Commented out - uncomment to actually create event)")
    result = agent.add_event(
        play_title="İnsanlar, Mekanlar, Nesneler",
        venue="Zorlu PSM - Turkcell Platinum Sahnesi",
        show_date="16 Kasım Cumartesi",
        show_time="20:30",
        ticket_url="https://biletinial.com/..."
    )
    print(f"   Result: {result}")
    
    print("\n" + "="*70)
    print("  ✅ Calendar Agent demo complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    demo()