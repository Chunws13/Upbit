from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os, ssl, certifi

load_dotenv()
ssl_context = ssl.create_default_context(cafile=certifi.where())

token = os.getenv("SLACK_TOKEN")
channel = os.getenv("SLACK_CHANNEL")

class Message_Bot:
    def __init__(self, token: str, channel: str, ssl):
        self.bot = WebClient(token=token, ssl=ssl)
        self.channel = channel
        print(token, channel)
        
    def send_message(self, message: str):
        try:
            response = self.bot.chat_postMessage(
                channel = self.channel,
                text= message
            )

        except SlackApiError as error:
            print(error.response["error"])

if __name__ == "__main__":
    bot = Message_Bot(token=token, channel=channel, ssl=ssl_context)
    bot.send_message("message_bot 에서 직접 실행되었습니다.")