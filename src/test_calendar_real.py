# src/test_calendar_real.py

"""
Test: Calendar Agent gerçekten çalışıyor mu?
"""

from calendar_agent import CalendarAgent
from datetime import datetime

def test_calendar_real():
    """
    Gerçek calendar testi
    """
    print("\n" + "="*70)
    print("  🧪 CALENDAR AGENT REAL TEST")
    print("="*70 + "\n")
    
    agent = CalendarAgent()
    
    if not agent.service:
        print("❌ Calendar service not available")
        return
    
    # Test 1: Bugünün etkinliklerini göster
    print("📋 Test 1: Bugünün etkinlikleri")
    print("-" * 70)
    
    try:
        now = datetime.now()
        time_min = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events_result = agent.service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("✅ Bugün için etkinlik yok")
        else:
            print(f"📅 Bugün {len(events)} etkinlik var:")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"   • {event['summary']} - {start}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: Yarının etkinliklerini göster
    print("📋 Test 2: Yarının etkinlikleri")
    print("-" * 70)
    
    try:
        from datetime import timedelta
        tomorrow = now + timedelta(days=1)
        time_min = tomorrow.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = tomorrow.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events_result = agent.service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("✅ Yarın için etkinlik yok")
        else:
            print(f"📅 Yarın {len(events)} etkinlik var:")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"   • {event['summary']} - {start}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 3: Gelecek 7 günü göster
    print("📋 Test 3: Gelecek 7 gün (bugünden itibaren)")
    print("-" * 70)
    
    try:
        from datetime import timedelta
        
        for day_offset in range(7):
            check_date = now + timedelta(days=day_offset)
            time_min = check_date.replace(hour=0, minute=0).isoformat() + 'Z'
            time_max = check_date.replace(hour=23, minute=59).isoformat() + 'Z'
            
            events_result = agent.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            
            day_name = check_date.strftime('%A')
            date_str = check_date.strftime('%Y-%m-%d')
            
            if events:
                print(f"📅 {date_str} ({day_name}): {len(events)} etkinlik")
            else:
                print(f"✅ {date_str} ({day_name}): Boş")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 4: TEST ETKİNLİĞİ EKLE (sonra silinecek)
    print("📋 Test 4: Test etkinliği ekleme (GERÇEKTEN EKLER!)")
    print("-" * 70)
    
    add_test = input("Test etkinliği eklemek ister misiniz? (yes/no): ")
    
    if add_test.lower() == 'yes':
        result = agent.add_event(
            play_title="TEST OYUN - StageAgent Test",
            venue="Test Sahne",
            show_date="1 Kasım Cuma",
            show_time="20:00",
            ticket_url="https://example.com"
        )
        
        if result.get('success'):
            print(f"✅ Test etkinliği eklendi!")
            print(f"   Event ID: {result['event_id']}")
            print(f"   Link: {result['event_link']}")
            print(f"\n🗑️  Bu test etkinliğini Google Calendar'dan manuel silebilirsiniz")
        else:
            print(f"❌ Hata: {result.get('error')}")
    else:
        print("⏭️  Test etkinliği eklenmedi")
    
    print("\n" + "="*70)
    print("  ✅ Test complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_calendar_real()