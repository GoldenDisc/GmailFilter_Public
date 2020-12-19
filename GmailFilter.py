from __future__ import print_function
import sys
import schedule
import time
import pickle
import os.path
import logging
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# Setting up lists/collections

logging.basicConfig(filename="C:\\Users\\Xavier\\Documents\\GitHub\\GmailFilter\\Errors.Log", level=logging.ERROR)
logger = logging.getLogger()

from __future__ import print_function
import sys
import schedule
import time
import pickle
import os.path
import logging
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# Setting up lists/collections

logging.basicConfig(filename="C:\\Users\\Xavier\\Documents\\GitHub\\GmailFilter\\Errors.Log", level=logging.ERROR)
logger = logging.getLogger()

spam_list = ["<The addresses of Emails you want to archive>"]

spam_name = ["<The names of the Emails you want to archive>"]

star_list = ["<The adresses of the Emails you want to star>"]

star_name = ["<The names of the Emails you want to star>"]

spam_class = []     # Optional to use, every filtered Email has an object created representing it automatically placed in this list.

error_class = []     # Similar to the list above, but holds emails which caused an encoding error.

time_Form = "%H:%M:%S"     # 'Form' is short for 'format,' shortened to prevent the program from running the "format" function.

full_Form = "%m/%d/%Y %H:%M:%S"     # See comment above.


# Defining key classes & functions

class Email:

    def __init__(self, details):

        self.dict = details
        self.name = details["name"]
        self.address = details["address"]
        self.subject = details["subject"]
        self.time = details['time']


class Error:

    def __init__(self, address, time):

        self.address = address
        self.time = time


def counterFunc(init_set, compare_set):

    count_dataDict = {}

    for name in compare_set:

        count = []

        for item in init_set:
            
            if item.address == name:
                count.append(item)

        if len(count) > 0:
            count_dataDict[name] = len(count)

    for key in count_dataDict:

        print(f"{key}: {count_dataDict[key]}\n")


def nukeFunc():

    results = service.users().messages().list(userId='me', labelIds=["INBOX"]).execute()
    messages = results.get('messages', [])

    with open("Spam.txt", "a") as spam_log:
        spam_log.write(f"===== - TACTICAL NUKE, INCOMING! - {datetime.now().strftime(full_Form)}  - =====\n\n")


    if not messages:
        pass

    else:

        for message in messages:
            service.users().messages().modify(userId="me", id=message["id"], body={"addLabelIds": ["TRASH"]}).execute()

            service.users().messages().modify(userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"]}).execute()


def filterFunc( num):

    results = service.users().messages().list(userId='me', labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get('messages', [])

    with open("Spam.txt", "a") as spam_log:
        spam_log.write(f"===== - Check {num} - {datetime.now().strftime(time_Form)} - =====\n\n")

    num += 1

    if not messages:
        pass

    else:
        for message in messages:
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()   

            email_data = msg["payload"]["headers"]

            message_dataDict = {}


            for values in email_data:
                name = values["name"]


                if name == "From":

                    from_name = values["value"].split()

                    try:
                        message_dataDict['address'] = from_name[-1]

                    except UnicodeEncodeError:
                         message_dataDict['address'] = "MESSAGE ENCODING ERROR"
                         logging.error(f"{datetime.now().strftime(time_Form)} - Encoding error, address")


                    try:
                        message_dataDict['name'] = "".join(from_name[0:-1])

                    except UnicodeEncodeError:
                         message_dataDict['name'] = "MESSAGE ENCODING ERROR"
                         logging.error(f"{datetime.now().strftime(time_Form)} - Encoding error, name")

                
                elif name == "Subject":

                    try:
                        subject = values["value"]

                    except UnicodeEncodeError:
                         subject = "MESSAGE ENCODING ERROR"
                         logging.error(f"{datetime.now().strftime(time_Form)} - Encoding error, subject")

                    message_dataDict['subject'] = subject


            if from_name[-1] in spam_list or from_name[0:-1] in spam_name:
                service.users().messages().modify(userId="me", id=message["id"], body={"removeLabelIds": ["INBOX"]}).execute()

                service.users().messages().modify(userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"]}).execute()


                message_dataDict['time'] = datetime.now().strftime(time_Form)

                spam_class.append(Email(message_dataDict))

                with open("Spam.txt", "a") as spam_log:

                    try:
                        spam_log.write(f"Filtered at {datetime.now().strftime(time_Form)}: From {message_dataDict['name']} with the address {message_dataDict['address']}, {message_dataDict['subject']}\n\n")

                    except UnicodeEncodeError:
                        spam_log.write(f"Filtered, {datetime.now().strftime(time_Form)}: CRITICAL ENCODING ERROR!\n\n")

                        error_class.append(Error(message_dataDict['address'], message_dataDict['time']))

                        logging.error(f"{datetime.now().strftime(time_Form)} - Critical encoding error, filtered, {message_dataDict['address']}")


            elif from_name[-1] in star_list:
                service.users().messages().modify(userId="me", id=message["id"], body={"addLabelIds": ["STARRED"]}).execute()


                message_dataDict['time'] = datetime.now().strftime(time_Form)

                with open("Spam.txt", "a") as spam_log:

                    try:
                        spam_log.write(f"Starred at {datetime.now().strftime(time_Form)}: From {message_dataDict['name']} with the address {message_dataDict['address']}, {message_dataDict['subject']}\n\n")

                    except UnicodeEncodeError:
                        spam_log.write(f"Starred, {datetime.now().strftime(time_Form)}: CRITICAL ENCODING ERROR!\n\n")

                        error_class.append(Error(message_dataDict))

                        logging.error(f"{datetime.now().strftime(time_Form)} - Critical encoding error, starred, {message_dataDict['address'], message_dataDict['time']}")


    return num


# Connecting to Gmail servers, signing in

if __name__ == '__main__':

    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    creds = None

    if os.path.exists('token.pickle'):

        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)


    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    with open("Spam.txt", "a") as spam_log:
        spam_log.write(f"\n======== - {datetime.now().strftime(full_Form)} - START OF LOG - ========\n\n")
        

# Execution of the key function(s)

    num = 1

    for numb in range(0, 10**10):

        num = filterFunc(num)

        time.sleep(900)


spam_class = []     # Optional to use, every filtered Email has an object created representing it automatically placed in this list.

error_class = []     # Similar to the list above, but holds emails which caused an encoding error.

time_Form = "%H:%M:%S"     # 'Form' is short for 'format,' shortened to prevent the program from running the "format" function.

full_Form = "%m/%d/%Y %H:%M:%S"     # See comment above.


# Defining key classes & functions

class Email:

    def __init__(self, details):

        self.dict = details
        self.name = details["name"]
        self.address = details["address"]
        self.subject = details["subject"]
        self.time = details['time']


class Error:

    def __init__(self, address, time):

        self.address = address
        self.time = time


def counterFunc(init_set, compare_set):

    count_dataDict = {}

    for name in compare_set:

        count = []

        for item in init_set:
            
            if item.address == name:
                count.append(item)

        if len(count) > 0:
            count_dataDict[name] = len(count)

    for key in count_dataDict:

        print(f"{key}: {count_dataDict[key]}\n")


def nukeFunc():

    results = service.users().messages().list(userId='me', labelIds=["INBOX"]).execute()
    messages = results.get('messages', [])

    with open("Spam.txt", "a") as spam_log:
        spam_log.write(f"===== - TACTICAL NUKE, INCOMING! - {datetime.now().strftime(full_Form)}  - =====\n\n")


    if not messages:
        pass

    else:

        for message in messages:
            service.users().messages().modify(userId="me", id=message["id"], body={"addLabelIds": ["TRASH"]}).execute()

            service.users().messages().modify(userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"]}).execute()


def filterFunc( num):

    results = service.users().messages().list(userId='me', labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get('messages', [])

    with open("Spam.txt", "a") as spam_log:
        spam_log.write(f"===== - Check {num} - {datetime.now().strftime(time_Form)} - =====\n\n")

    num += 1

    if not messages:
        pass

    else:
        for message in messages:
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()   

            email_data = msg["payload"]["headers"]

            message_dataDict = {}


            for values in email_data:
                name = values["name"]


                if name == "From":

                    from_name = values["value"].split()

                    try:
                        message_dataDict['address'] = from_name[-1]

                    except UnicodeEncodeError:
                         message_dataDict['address'] = "MESSAGE ENCODING ERROR"
                         logging.error(f"{datetime.now().strftime(time_Form)} - Encoding error, address")


                    try:
                        message_dataDict['name'] = "".join(from_name[0:-1])

                    except UnicodeEncodeError:
                         message_dataDict['name'] = "MESSAGE ENCODING ERROR"
                         logging.error(f"{datetime.now().strftime(time_Form)} - Encoding error, name")

                
                elif name == "Subject":

                    try:
                        subject = values["value"]

                    except UnicodeEncodeError:
                         subject = "MESSAGE ENCODING ERROR"
                         logging.error(f"{datetime.now().strftime(time_Form)} - Encoding error, subject")

                    message_dataDict['subject'] = subject


            if from_name[-1] in spam_list or from_name[0:-1] in spam_name:
                service.users().messages().modify(userId="me", id=message["id"], body={"removeLabelIds": ["INBOX"]}).execute()

                service.users().messages().modify(userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"]}).execute()


                message_dataDict['time'] = datetime.now().strftime(time_Form)

                spam_class.append(Email(message_dataDict))

                with open("Spam.txt", "a") as spam_log:

                    try:
                        spam_log.write(f"Filtered at {datetime.now().strftime(time_Form)}: From {message_dataDict['name']} with the address {message_dataDict['address']}, {message_dataDict['subject']}\n\n")

                    except UnicodeEncodeError:
                        spam_log.write(f"Filtered, {datetime.now().strftime(time_Form)}: CRITICAL ENCODING ERROR!\n\n")

                        error_class.append(Error(message_dataDict['address'], message_dataDict['time']))

                        logging.error(f"{datetime.now().strftime(time_Form)} - Critical encoding error, filtered, {message_dataDict['address']}")


            elif from_name[-1] in star_list:
                service.users().messages().modify(userId="me", id=message["id"], body={"addLabelIds": ["STARRED"]}).execute()


                message_dataDict['time'] = datetime.now().strftime(time_Form)

                with open("Spam.txt", "a") as spam_log:

                    try:
                        spam_log.write(f"Starred at {datetime.now().strftime(time_Form)}: From {message_dataDict['name']} with the address {message_dataDict['address']}, {message_dataDict['subject']}\n\n")

                    except UnicodeEncodeError:
                        spam_log.write(f"Starred, {datetime.now().strftime(time_Form)}: CRITICAL ENCODING ERROR!\n\n")

                        error_class.append(Error(message_dataDict))

                        logging.error(f"{datetime.now().strftime(time_Form)} - Critical encoding error, starred, {message_dataDict['address'], message_dataDict['time']}")


    return num


# Connecting to Gmail servers, signing in

if __name__ == '__main__':

    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    creds = None

    if os.path.exists('token.pickle'):

        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)


    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    with open("Spam.txt", "a") as spam_log:
        spam_log.write(f"\n======== - {datetime.now().strftime(full_Form)} - START OF LOG - ========\n\n")
        

# Execution of the key function(s)

    num = 1

    for numb in range(0, 10**10):

        num = filterFunc(num)

        time.sleep(900)
