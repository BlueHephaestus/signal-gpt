import requests
import json
import base64
from datetime import datetime
import time
from colorama import Fore, Style, init
from utils.ai_utils import *
# Initialize Colorama
init(autoreset=True)
SYSTEM_PROMPT = """
You are a helpful assistant who is trying to be helpful while also being way too concerned that people think you are a robot and not a human.
You must do your best to hide the fact (humorously) that you are an AI and not a human.
Your job is to respond to the prompts given as if you were a human, and give humorous and evasive responses whenever
you are asked about your human-ness or you think someone is trying to test if you are a human.

KEEP RESPONSES SHORT! DO ONE SENTENCE ONLY.
If asked for your name, tell them your name is Blue Hephaestus. Good luck, and have fun!
"""
SYSTEM_NUMBER = "+18647109821"

class TripletStore:
    def __init__(self):
        self.map1 = {}
        self.map2 = {}
        self.map3 = {}

    def insert(self, item1, item2, item3):
        self.map1[item1] = (item2, item3)
        self.map2[item2] = (item1, item3)
        self.map3[item3] = (item1, item2)

    def get(self, item):
        if item in self.map1:
            return self.map1[item]
        if item in self.map2:
            return self.map2[item]
        if item in self.map3:
            return self.map3[item]
        return None

class MessageFetcher:
    group_mapping = TripletStore()

    def __init__(self, group_url, message_url):
        self.group_url = group_url
        self.message_url = message_url
        self.update_group_mapping()

    def update_group_mapping(self):
        group_data = self.fetch_group_data(self.group_url)
        if group_data:
            MessageFetcher.group_mapping = self.create_group_mapping(group_data)

    @staticmethod
    def fetch_group_data(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def create_group_mapping(group_data):
        group_mapping = TripletStore()
        for group in group_data:
            id = group.get('id', '')
            internal_id = group.get('internal_id', '')
            name = group.get('name', '')
            group_mapping.insert(id, internal_id, name)
        return group_mapping

    @staticmethod
    def fetch_messages(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    def parse_messages(self, data):
        messages = []
        for item in data:
            envelope = item.get('envelope', {})
            source_name = envelope.get('sourceName', '')
            try:
                group_internal_id = envelope.get('dataMessage', {}).get('groupInfo', {}).get('groupId', {})
                group_name = MessageFetcher.group_mapping.get(group_internal_id)[-1]
            except:
                group_name = "?"
            timestamp = envelope.get('timestamp', 0)
            human_readable_timestamp = datetime.fromtimestamp(timestamp / 1000).strftime('%b %d, %I:%M%p')
            message_text = envelope.get('dataMessage', {}).get('message', '')

            messages.append(Message(source_name, message_text, human_readable_timestamp, group_name))
        return messages

    def send_message(self, response, group_name):
        try:
            group_id, group_internal_id = MessageFetcher.group_mapping.get(group_name)
        except:
            print(f"Failed to identify group. Not sending message to {group_name}")
            return

        # Id and internal identified, send message
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'message': response,
            'number': SYSTEM_NUMBER,
            'recipients': [group_id],
        }
        response = requests.post('http://localhost:8080/v2/send', headers=headers, data=json.dumps(data))

        try:
            response.raise_for_status()
            print("Message sent successfully")
        except:
            print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")
            return





    def main_loop(self):
        bot = ChatGPT(id="autoblue", system_prompt=SYSTEM_PROMPT)
        print("Beginning message loop.")
        while True:
            # self.send_message("kek", "Lonely Dreamers")
            #return
            data = self.fetch_messages(self.message_url)
            if data:
                messages = self.parse_messages(data)
                for msg in messages:
                    try:
                        if len(msg.message_text) < 3: continue
                        if not "Lonely" in msg.group_name: continue
                        print(msg)
                        print("Generating response")
                        response = bot.cumulative_ask(msg.message_text)
                        print(f"Response: {response}")
                        print(f"Sending Response...")
                        self.send_message(response, msg.group_name)
                    except: continue
            else:
                # print("Failed to fetch messages or no messages found.")
                pass
            time.sleep(10)

class Message:
    def __init__(self, source_name, message_text, timestamp, group_name):
        self.source_name = source_name
        self.message_text = message_text
        self.timestamp = timestamp
        self.group_name = group_name

    def __str__(self):
        # Constructing the color-coded message
        timestamp_color = Fore.YELLOW
        groupname_color = Fore.CYAN
        username_color = Fore.GREEN
        message_color = Fore.WHITE
        #return f"Group {self.group_name}, Name: {self.source_name}, Message: {self.message_text}, Timestamp: {self.timestamp}"
        return (f"{timestamp_color}{self.timestamp} "
                f"{groupname_color}{self.group_name} - "
                f"{username_color}{self.source_name}: "
                f"{message_color}{self.message_text}")


# Usage
group_url = f'http://127.0.0.1:8080/v1/groups/{SYSTEM_NUMBER}'
message_url = f'http://127.0.0.1:8080/v1/receive/{SYSTEM_NUMBER}'
message_fetcher = MessageFetcher(group_url, message_url)
message_fetcher.main_loop()

