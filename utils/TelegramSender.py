import os
from dotenv import load_dotenv
import asyncio
import aiohttp
from typing import Optional
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.MAX_CAPTION_LENGTH = 1024  # Telegram's limit
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment variables")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = None

    async def ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _truncate_caption(self, caption: str) -> str:
        """Truncate caption to comply with Telegram's limits"""
        if not caption:
            return ""
        if len(caption) > self.MAX_CAPTION_LENGTH:
            return caption[:self.MAX_CAPTION_LENGTH - 3] + "..."
        return caption

    async def _make_request(self, method: str, endpoint: str, **kwargs):
        await self.ensure_session()
        url = f"{self.base_url}/{endpoint}"
        try:
            async with getattr(self.session, method)(url, **kwargs) as response:
                if response.status != 200:
                    response_text = await response.text()
                    print(f"Failed to {endpoint}. Status: {response.status}")
                    print(f"Response: {response_text}")
                    return None
                return await response.json()
        except Exception as e:
            print(f"Error making request: {str(e)}")
            return None

    async def verify_bot_token(self):
        result = await self._make_request('get', 'getMe')
        if result:
            return True
        return False

    async def send_photo_bytes(self, photo_bytes: BytesIO, caption: Optional[str] = None) -> None:
        try:
            data = aiohttp.FormData()
            data.add_field("chat_id", self.chat_id)
            data.add_field("photo", photo_bytes, filename="generated_image.png", content_type="image/png")
            
            if caption:
                truncated_caption = self._truncate_caption(caption)
                data.add_field("caption", truncated_caption)

            result = await self._make_request('post', 'sendPhoto', data=data)
            if result:
                print("Photo sent successfully to Telegram")
            return result
        except Exception as e:
            print(f"Error sending photo: {str(e)}")
            return None

    async def send_message(self, text: str, title: Optional[str] = None) -> None:
        try:
            message_text = text
            if title:
                message_text = f"<b>{title}</b>\n\n{text}"
                
            # Truncate if needed
            message_text = self._truncate_caption(message_text)
            
            params = {
                "chat_id": self.chat_id,
                "text": message_text,
                "parse_mode": "HTML"
            }
            
            result = await self._make_request('post', 'sendMessage', params=params)
            if result:
                print("Message sent successfully")
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    async def send_document(self, document: BytesIO, caption: Optional[str] = None) -> None:
        try:
            data = aiohttp.FormData()
            data.add_field("chat_id", self.chat_id)
            data.add_field("document", document, filename="comparison_results.html", content_type="text/html")
            
            if caption:
                truncated_caption = self._truncate_caption(caption)
                data.add_field("caption", truncated_caption)

            result = await self._make_request('post', 'sendDocument', data=data)
            if result:
                print("Document sent successfully")
        except Exception as e:
            print(f"Error sending document: {str(e)}")

# Example usage
async def main():
    sender = TelegramSender()
    try:
        if await sender.verify_bot_token():
            await sender.send_message("Test message", "Test")
        else:
            print("Bot token verification failed")
    finally:
        await sender.close_session()

if __name__ == "__main__":
    asyncio.run(main())