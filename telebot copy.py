from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import requests
import datefinder
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
from oauth2client import client
from oauth2client import tools
from google.auth.transport.requests import Request
import os.path
import random
import redis
import string
import telegram


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
redis_pickle_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=False)

INPUT_NAME = range(0)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

 
#create_event(start_time_str= '23 Jan 12.30pm', summary="Test Meeting using CreateFunction Method",
#description="Test Description",location="Mentone, VIC, Australia") #callfunction

### To Begin OAuth ###
#Utility function to begin OAuth process and gain access to the calendar
def get_service(bot, update, code=None):
    user_id = get_user_id(bot,update)
    creds = None
    service = None
    if redis_client.hexists(user_id, "credentials"):
        creds = pickle.loads(redis_pickle_client.hget(user_id, "credentials"))
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return service

    # If there are no (valid) credentials available, let the user log in.
    if (creds == None) or (not creds.valid):

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            return service

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES)

            # Setup authorization URL
            flow.redirect_uri = InstalledAppFlow._OOB_REDIRECT_URI
            auth_url, _ = flow.authorization_url()

            if not code:
                instructions = """Please follow the instructions to link your Google Account:
                    1. Click on the authorization URL
                    2. Copy the authentication code
                    3. Use '/permissions <authentication_code>' to finish!"""
                keyboard = [[telegram.InlineKeyboardButton("Open URL", url=auth_url)]]
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                update.message.reply_text(instructions, reply_markup=reply_markup)
            else:
                print("WITHIN GET SERVICE")
                print(code)
                # Fetch access token if args present
                flow.fetch_token(code=code)
                creds = flow.credentials
                print("Obtain credentials")
                # Save the credentials for the next run
                redis_pickle_client.hset(user_id, "client_secret", pickle.dumps(creds))
                service = build("calendar", "v3", credentials=creds, cache_discovery=False)
                return service
    return service

#Wrapper function that calls the function to create a new event 
def finish_oauth(bot, update, args): #start_time, end_time, summary, args):
    user_id = get_user_id(bot, update)
    try:
        print("WITHIN FINISH OAUTH")
        print(args[0])
        get_service(bot, update, code = args[0]) #If the code is present
        update.message.reply_text("Authorization Succesfully Granted")
    except Exception as e:
        print(e)
        update.message.reply_text("Authorization Failed")


#New event is the actual function that goes onto create the event.
#Summary is the same as the title for the event 
def new_event(bot, update): #start_time, end_time, summary, code=None):
    user_id = get_user_id(bot,update)
    if redis_client.hexists(user_id, "credentials"):
        print("AWESOME")
    creds = pickle.loads(redis_pickle_client.hget(user_id, "credentials"))
    print(creds)
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    ##Temporary code ##
    start_time_str = "23 Jan 12:30pm"
    title = "Test event"
    matches = list(datefinder.find_dates(start_time_str))
    if len(matches):
        start_time = matches[0]
        end_time = start_time + timedelta(hours=1)
    timezone = 'Asia/Singaapore'
    event = {
        'summary': title,
        'start': {
            'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
    }
             
    return service.events().insert(calendarId='primary', body=event).execute()

# Need to find a way to store the code which the user has provided -- Do so with user_id
def get_user_id(bot, update):
    user_id = update.message.from_user.username
    return user_id

def start(bot, update):

    message = """Heyy!! This is a simple bot that can add events to your calendar.
    To get started:
    /setup: Setup the google sign in to grant access to your calendar
    """
    update.message.reply_text(message)


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)



def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("713563116:AAFPVLQPr4W5qGhS8DTHLf7WwlH7A_jOUnk")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("setup", get_service))
    dp.add_handler(CommandHandler("permissions", finish_oauth, pass_args=True))
    dp.add_handler(CommandHandler("new_event", new_event))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()