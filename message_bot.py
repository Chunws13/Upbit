from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv("SLACK_TOKEN")
channel = os.getenv("SLACK_CHANNEL")

class Message_Bot:
    def __init__(self, token: str, channel: str):
        self.bot = WebClient(token=token)
        self.channel = channel

    def send_message(self, message: str):
        try:
            response = self.bot.chat_postMessage(
                channel = self.channel,
                text= message
            )

        except SlackApiError as error:
            assert error.response["error"]

if __name__ == "__main__":
    Message_Bot(token=token, channel=channel).send_message("message_bot.py 에서 직접 실행되었습니다.")