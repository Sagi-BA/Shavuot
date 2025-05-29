import requests
from PIL import Image
import io
import sys, os
from urllib.parse import quote
import base64
import json
import time
import streamlit as st
from deep_translator import GoogleTranslator

# Add the parent directory of 'text_to_image' (which is 'utils') to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.imgur_uploader import ImgurUploader

# https://pollinations.ai/
## Parameters
# - prompt (required): The text description of the image you want to generate. Should be URL-encoded.
# - model (optional): The model to use for generation. Options: 'flux' or 'turbo'. Default: 'turbo'
# - seed (optional): Seed for reproducible results. Default: random
# - width (optional): Width of the generated image. Default: 1024
# - height (optional): Height of the generated image. Default: 1024
# - nologo (optional): Set to 'true' to turn off the rendering of the logo
# - nofeed (optional): Set to 'true' to prevent the image from appearing in the public feed
# - enhance (optional): Set to 'true' or 'false' to turn on or off prompt enhancing (passes prompts through an LLM to add detail)

## Example Usage
# https://image.pollinations.ai/prompt/A%20beautiful%20sunset%20over%20the%20ocean?model=flux&width=1280&height=720&seed=42&nologo=true&enhance=true

## Response
# The API returns a raw image file (typically JPEG or PNG) as the response body. You can directly embed the image in your HTML or Markdown.
class PollinationsGenerator:
    def __init__(self):
        self.api_url = "https://image.pollinations.ai/prompt/"
        
    def generate_image(self, prompt):
        """
        Generate an image using Pollinations API
        """
        try:
            # Translate each item to English and emphasize visibility
            items = [item.strip() for item in prompt.split(',') if item.strip()]
            items_en = []
            for item in items:
                try:
                    translated = GoogleTranslator(source='auto', target='en').translate(item)
                except Exception:
                    translated = item  # fallback
                items_en.append(f"{translated} (clearly visible, in the front)")
            items_english = ', '.join(items_en)
            
            # Build the improved prompt
            formatted_prompt = (
                f"A beautiful Shavuot basket on a festive table, containing: {items_english}. "
                "The basket is overflowing, ultra-realistic, vibrant, joyful, high detail, 4k, cinematic lighting."
            )
            # print(formatted_prompt)
            # Create the API URL with the prompt and extra params
            image_url = (
                f"{self.api_url}{formatted_prompt}"
                f"?model=flux&seed=99&nologo=true&enhance=true"
            )
            
            # Make the request
            response = requests.get(image_url)
            
            if response.status_code == 200:
                return image_url
            else:
                st.error(f"שגיאה ביצירת התמונה: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"שגיאה ביצירת התמונה: {str(e)}")
            return None

    @staticmethod
    def convert_image_url_to_base64(image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            buffered = io.BytesIO()
            img.save(buffered, format=img.format)
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return image_base64
        except Exception as e:
            print(f"Failed to convert image from URL: {image_url}")
            print(f"Error: {str(e)}")
            return None

def test(upload_dir="uploads", model_name="turbo", filename=None):    
    generator = PollinationsGenerator()
    prompt = "A fast red color car"
    negative_prompt = "low quality, worst quality"
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    image_url = generator.generate_image(prompt)
    return image_url

if __name__ == "__main__":
    test_result = test("uploads", "turbo", "pollinations_generator.png")
    print(f"Test {'passed' if test_result else 'failed'}")   