import os
import requests
from dotenv import load_dotenv

class TelegramSender:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        load_dotenv()
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            raise ValueError("Telegram Bot Token not found. Please provide it or set it in the environment variables.")
        if not self.chat_id:
            raise ValueError("Telegram Chat ID not found. Please provide it or set it in the environment variables.")
            
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_photo_bytes(self, photo_bytes: bytes, caption: str = "Bikkurim Basket") -> bool:
        """
        Sends photo bytes to Telegram using the bot API.
        
        :param photo_bytes: The photo data in bytes
        :param caption: Optional caption for the photo
        :return: True if successful, False otherwise
        """
        try:
            url = f"{self.api_url}/sendPhoto"
            files = {
                'photo': ('bikkurim_basket.png', photo_bytes, 'image/png')
            }
            data = {
                'chat_id': self.chat_id,
                'caption': caption
            }
            
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Failed to send photo to Telegram: {str(e)}")
            return False

    def send_image(self, image_bytes: bytes, caption: str = "Bikkurim Basket") -> bool:
        """
        Legacy method - use send_photo_bytes instead.
        Sends an image to Telegram using the bot API.
        
        :param image_bytes: The image data in bytes
        :param caption: Optional caption for the image
        :return: True if successful, False otherwise
        """
        return self.send_photo_bytes(image_bytes, caption)

    def send_message(self, message: str) -> bool:
        """
        Sends a text message to Telegram using the bot API.
        
        :param message: The message text to send
        :return: True if successful, False otherwise
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Failed to send message to Telegram: {str(e)}")
            return False 