import pprint
import datefinder
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
 
scopes = ['https://www.googleapis.com/auth/calendar']
 
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=scopes)

#Runs user authentication flow giving the html link to begin authorisation
credentials = flow.run_console()
 
#Stores the user credentials here 
pickle.dump(credentials, open("token.pkl", "wb"))
credentials = pickle.load(open("token.pkl", "rb"))

#Uses the credentials to begin making python event
service = build("calendar", "v3", credentials=credentials)
 
result = service.calendarList().list().execute()
calendar_id = result['items'][0]['id']
 
pp = pprint.PrettyPrinter(indent=4) #use pprint for nicer view
timezone = 'Singapore' #enter your timezone

#Summary is the same as the title for the event 
def create_event(start_time_str, summary, duration=1,attendees=None, description=None, location=None):
    matches = list(datefinder.find_dates(start_time_str))
    if len(matches):
        start_time = matches[0]
        end_time = start_time + timedelta(hours=duration)
                 
    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
    }
    pp.pprint('''*** %r event added:
    With: %s
    Start: %s
    End:   %s''' % (summary.encode('utf-8'),
        attendees,start_time, end_time))
         
    return service.events().insert(calendarId='primary', body=event,sendNotifications=True).execute()
 
create_event(start_time_str= '23 Jan 12.30pm', summary="Test Meeting using CreateFunction Method",
description="Test Description",location="Mentone, VIC, Australia") #callfunction