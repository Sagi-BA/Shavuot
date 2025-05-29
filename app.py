# https://sagi-shavuot.streamlit.app/

import streamlit as st
import speech_recognition as sr
import os
from dotenv import load_dotenv
from pollinations_generator import PollinationsGenerator
from together_ai_generator import TogetherAIGenerator
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import arabic_reshaper
from bidi.algorithm import get_display
import textwrap
from imgur_uploader import ImgurUploader
import uuid

# Load environment variables
load_dotenv()

# Initialize generators
pollinations = PollinationsGenerator()
together_ai = TogetherAIGenerator()

# דוגמאות מוכנות
EXAMPLES = [
    "מנגו, גבינת עיזים, דבש, אהבה",
    "ענבים, תאנים, רימונים, שמחה",
    "עוגת גבינה, פרחים, חיטה, שוקולד",
    "תמרים, יין, גבינה צפתית, חיוך",
    "אבטיח, לחם, שמן זית, ברכה"
]

def get_user_id():
    if 'user_id' not in st.session_state:
        user_id = str(uuid.uuid4())
        st.session_state['user_id'] = user_id
    return st.session_state['user_id']

def register_user(user_id, users_file='users.txt'):
    if not os.path.exists(users_file):
        with open(users_file, 'w') as f:
            f.write('')
    with open(users_file, 'r+') as f:
        users = set(line.strip() for line in f)
        if user_id not in users:
            f.write(user_id + '\n')
            users.add(user_id)
    return len(users)

def compose_final_image(image_url, hebrew_text):
    """Compose a new image: top - blessing (wrapped), middle - basket, bottom center - tips text"""
    try:
        # Download the basket image
        response = requests.get(image_url)
        basket_img = Image.open(io.BytesIO(response.content)).convert("RGB")
        basket_width, basket_height = basket_img.size

        # Set up fonts
        try:
            font_bless = ImageFont.truetype("arial.ttf", 40)
        except:
            font_bless = ImageFont.load_default()
        try:
            font_tips = ImageFont.truetype("arial.ttf", 10)
        except:
            font_tips = ImageFont.load_default()

        # --- RTL Hebrew fix ---
        reshaped_text = arabic_reshaper.reshape(hebrew_text)
        bidi_text = get_display(reshaped_text)

        # Helper to get text size (bbox or size)
        def get_text_size(draw, text, font):
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0,0), text, font=font)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                return width, height
            else:
                return draw.textsize(text, font=font)

        # --- Word wrap blessing text ---
        dummy_img = Image.new("RGB", (basket_width, 100), "white")
        draw_dummy = ImageDraw.Draw(dummy_img)
        max_width = basket_width - 40  # 20px padding each side
        # Split text into lines that fit
        words = bidi_text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = (word if not current_line else current_line + " " + word)
            w, h = get_text_size(draw_dummy, test_line, font_bless)
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        # Reverse lines for correct Hebrew (RTL) order
        lines = lines[::-1]
        bless_h = h * len(lines) + 10 * (len(lines)-1)
        bless_pad = 30

        # Tips text
        tips_text = "AI TIPS & TRICKS with sagi bar on"
        tips_w, tips_h = get_text_size(draw_dummy, tips_text, font_tips)
        tips_pad = 10
        tips_area_h = tips_h + 2 * tips_pad

        # Final image size
        final_height = bless_h + bless_pad + basket_height + tips_area_h
        final_img = Image.new("RGB", (basket_width, final_height), "white")
        draw = ImageDraw.Draw(final_img)

        # Draw blessing (centered, top, RTL, wrapped)
        bless_y = bless_pad // 2
        for line in lines:
            w, h = get_text_size(draw, line, font=font_bless)
            bless_x = basket_width // 2
            draw.text((bless_x, bless_y), line, fill="black", font=font_bless, anchor="ma")
            bless_y += h + 10

        # Paste basket image
        final_img.paste(basket_img, (0, bless_h + bless_pad))

        # Draw tips text (bottom center)
        tips_x = basket_width // 2
        tips_y = final_height - tips_area_h + tips_pad // 2
        draw.text((tips_x, tips_y), tips_text, fill="gray", font=font_tips, anchor="ma")

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        final_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return img_byte_arr
    except Exception as e:
        st.error(f"שגיאה בהרכבת התמונה: {str(e)}")
        return None

def get_image_download_link(img_bytes, filename="bikkurim_basket.png"):
    """Generate a download link for the image"""
    b64 = base64.b64encode(img_bytes).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}" class="download-btn">⬇️ הורד את התמונה</a>'
    return href

def transcribe_audio():
    """Record and transcribe audio using speech_recognition"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 הקלטה מתחילה...")
        audio = r.listen(source)
        st.info("🎵 מעבד את ההקלטה...")
        
    try:
        text = r.recognize_google(audio, language="he-IL")
        return text
    except sr.UnknownValueError:
        st.error("לא הצלחתי להבין את ההקלטה")
        return None
    except sr.RequestError:
        st.error("שגיאה בשירות ההקלטה")
        return None

def generate_image(prompt):
    # פרומפט עשיר ומפורט
    basket_prompt = (
        f"A beautiful Shavuot basket on a festive table, containing: {prompt}. "
        "The basket is overflowing with fresh, colorful produce, cheeses, and flowers. "
        "Ultra-realistic, vibrant, joyful, high detail, 4k, cinematic lighting."
    )
    return pollinations.generate_image(basket_prompt)

def generate_hebrew_text(prompt):
    """Generate Hebrew text using Together AI"""
    return together_ai.generate_hebrew_text(prompt)


def hide_streamlit_header_footer():
    hide_st_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)

def main():    
    st.set_page_config(
        page_title="מה תביאו לביכורים? 🎉",
        page_icon="🎉",
        layout="centered"
    )

    hide_streamlit_header_footer()     

    # ספירת משתמשים ייחודיים
    user_id = get_user_id() 

    total_users = register_user(user_id)
    st.markdown(f'<div style="text-align:center;font-size:1.3em;margin:10px 0 0 0;"><b>סה"כ משתמשים: {total_users}</b></div>', unsafe_allow_html=True)

    # עיצוב וואו + RTL
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Varela+Round&display=swap');
        .stApp { 
            direction: rtl; 
            background: linear-gradient(135deg, #fffbe7 0%, #ffe5ec 100%); 
            font-family: 'Varela Round', sans-serif; 
        }
        .wow-box { 
            border-radius: 24px; 
            box-shadow: 0 4px 32px #ffb6b6; 
            border: 3px solid #ffb6b6; 
            padding: 24px; 
            background: #fff8;
            animation: fadeIn 0.5s ease-in;
        }
        .example-btn { 
            background: #fffbe7; 
            border: 2px solid #ffb6b6; 
            border-radius: 16px; 
            margin: 4px; 
            font-size: 1.1em; 
            transition: 0.2s; 
        }
        .example-btn:hover { 
            background: #ffe5ec; 
            color: #d72660; 
            transform: scale(1.05);
        }
        .result-img { 
            border-radius: 18px; 
            box-shadow: 0 2px 16px #d7266060; 
            border: 2px solid #d72660;
            animation: slideUp 0.5s ease-out;
        }
        .download-btn {
            display: inline-block;
            padding: 10px 20px;
            background: linear-gradient(135deg, #4fc3f7 0%, #1976d2 100%);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            margin: 10px 0;
            transition: 0.3s;
            animation: pulse 2s infinite;
        }
        .download-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .input-box { 
            width: 100%; 
            border-radius: 12px; 
            border: 2px solid #ffb6b6; 
            padding: 10px; 
            font-size: 1.1em; 
            margin-bottom: 10px; 
            direction: rtl;
            transition: 0.3s;
        }
        .input-box:focus {
            border-color: #d72660;
            box-shadow: 0 0 8px #d7266060;
        }
        .sticky-footer {
          position: fixed;
          bottom: 0;
          left: 0;
          width: 100vw;
          background: #fff;
          z-index: 999;
          border-top: 2px solid #eee;
          box-shadow: 0 -2px 12px #0001;
          padding: 8px 0 2px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center; color:#d72660; font-size:2.5em;'>מה תביא לביכורים? <span style='font-size:1.2em;'>🎉</span></h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-size:1.2em;'>ספרו לנו מה תרצו להביא לסל הביכורים שלכם</div>", unsafe_allow_html=True)

    # שלב 1: העלאת תמונה אישית
    user_image = st.file_uploader("העלו תמונה אישית (רשות)", type=["jpg", "jpeg", "png"], key="user_image")
    if user_image is not None:
        st.image(user_image, caption="התמונה האישית שלך", width=250)

    # כפתורי הקלטה בלבד (ללא הקלדה)
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🎤 מיקרופון", key="btn_mic"):
            st.session_state["input_type"] = "mic"
    with col2:
        if st.button("🔄 התחל מההתחלה", key="btn_reset"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    st.markdown("<div style='text-align:center; color:#888; font-size:1em;'>לחצו על המיקרופון לדיבור | לחצו על המעטפה להקלדה</div>", unsafe_allow_html=True)
    # קלט מהמשתמש
    user_items = ""
    input_type = st.session_state.get("input_type", None)
    mic_transcript = None
    if input_type == "mic":
        mic_transcript = transcribe_audio()
        if mic_transcript:
            st.info("הטקסט שזוהה מהמיקרופון. אפשר לערוך/להשלים/להפריד בפסיקים:")
            user_items = st.text_input("מה תרצו שיהיה בסל? (הפרד בפסיקים)", value=mic_transcript, key="items_input", help="לדוג' מגבת צבעונית, חטיפי שוקולד, ספר, ...")
        else:
            user_items = st.text_input("מה תרצו שיהיה בסל? (הפרד בפסיקים)", key="items_input", help="לדוג' מגבת צבעונית, חטיפי שוקולד, ספר, ...")
    else:
        user_items = st.text_input("מה תרצו שיהיה בסל? (הפרד בפסיקים)", key="items_input", help="לדוג' מגבת צבעונית, חטיפי שוקולד, ספר, ...")

    # דוגמאות לבחירה
    st.markdown("<div style='text-align:center; margin-top:18px;'>", unsafe_allow_html=True)
    cols = st.columns(len(EXAMPLES))
    example_clicked = None
    for i, example in enumerate(EXAMPLES):
        if cols[i].button(example, key=f"ex_{i}"):
            example_clicked = example
    st.markdown("</div>", unsafe_allow_html=True)
    if example_clicked:
        user_items = example_clicked

    if user_items:
        st.markdown(f"<div class='wow-box'><b>🎯 מה שבחרת/הקלטת:</b> {user_items}</div>", unsafe_allow_html=True)

        # 1. טקסט שירי
        with st.spinner("📝 יוצר טקסט שירי לסל שלך..."):
            hebrew_text = generate_hebrew_text(user_items)
        if hebrew_text:
            st.markdown(f"<div class='wow-box' style='border-color:#d72660;'><b>📝</b> {hebrew_text}</div>", unsafe_allow_html=True)

            # 2. תמונה עם progress bar
            progress_bar = st.progress(0, text="🎨 יוצר תמונה של הסל שלך...")
            import time
            for percent_complete in range(1, 101, 10):
                progress_bar.progress(percent_complete, text="🎨 יוצר תמונה של הסל שלך...")
                time.sleep(0.03)
            image_url = generate_image(user_items)
            progress_bar.progress(100, text="✅ התמונה מוכנה!")
            
            if image_url:
                # Add text to image
                img_with_text = compose_final_image(image_url, hebrew_text)
                # שילוב תמונה אישית אם הועלתה
                if img_with_text and user_image is not None:
                    try:
                        # Open base image
                        base_img = Image.open(io.BytesIO(img_with_text)).convert("RGBA")
                        # Open user image
                        user_img = Image.open(user_image).convert("RGBA")
                        # Remove polaroid frame: just use the user image with rounded corners and shadow
                        img_w = base_img.width // 5 - 24
                        img_h = int(img_w * 0.8)
                        user_img = user_img.resize((img_w, img_h))
                        # Add rounded corners to user image
                        mask = Image.new("L", (img_w, img_h), 0)
                        draw_mask = ImageDraw.Draw(mask)
                        draw_mask.rounded_rectangle([0,0,img_w,img_h], radius=28, fill=255)
                        user_img.putalpha(mask)
                        # Add shadow
                        shadow = Image.new("RGBA", (img_w+12, img_h+12), (0,0,0,0))
                        shadow_draw = ImageDraw.Draw(shadow)
                        shadow_draw.rounded_rectangle([6,6,img_w+6,img_h+6], radius=32, fill=(0,0,0,60))
                        # New position: bottom right
                        frame_x = base_img.width-img_w-40
                        frame_y = base_img.height-img_h-40
                        base_img.paste(shadow, (frame_x+6, frame_y+6), shadow)
                        base_img.paste(user_img, (frame_x, frame_y), user_img)
                        # Convert back to bytes
                        img_byte_arr = io.BytesIO()
                        base_img = base_img.convert("RGB")
                        base_img.save(img_byte_arr, format='PNG')
                        img_with_text = img_byte_arr.getvalue()
                    except Exception as e:
                        st.error(f"שגיאה בשילוב התמונה האישית: {str(e)}")
                if img_with_text:
                    # Display the image
                    st.image(img_with_text, caption="הסל שלך לביכורים", use_column_width=True)

                # כפתור שיתוף והורדה דרך imgur
                imgur_url = None
                try:
                    uploader = ImgurUploader()
                    img_b64 = base64.b64encode(img_with_text).decode()
                    imgur_url = uploader.upload_media_to_imgur(img_b64, "image", "Bikkurim Basket", "AI Generated Bikkurim Basket")
                except Exception as e:
                    st.error(f"שגיאה בהעלאת התמונה ל-Imgur: {str(e)}")

                # תקן את הלינק ל-imgur.com
                if imgur_url and imgur_url.startswith("https://i.imgur.com/"):
                    img_id = imgur_url.replace("https://i.imgur.com/", "").split(".")[0]
                    # Remove any extra text after the ID (e.g., 'הסל')
                    img_id = ''.join([c for c in img_id if c.isalnum()])
                    imgur_url = f"https://imgur.com/{img_id}"

                if imgur_url:
                    # כפתור הורדה
                    st.markdown(f'<a href="{imgur_url}" download class="download-btn">⬇️ הורדת התמונה</a>', unsafe_allow_html=True)
                    # כפתור שיתוף
                    share_text = f"{imgur_url}"
                    whatsapp_url = f"https://wa.me/?text={share_text}"
                    st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="font-size:1.3em; color:#25d366;">📱 שיתוף בוואטסאפ</a>', unsafe_allow_html=True)

    # FOOTER with links (sticky to bottom)
    st.markdown("""
    <div class="sticky-footer">
      <div style='text-align:center; font-size:1.1em; margin-bottom:2px;'>
        <a href="mailto:sagi.baron76@gmail.com" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="font-size:1.3em;vertical-align:middle;">📧</span> <b>EMAIL ME</b></a>
        <a href="https://www.youtube.com/@SagiBaron" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#FF0000;font-size:1.3em;vertical-align:middle;">▶️</span> <b>SUBSCRIBE TO MY YOUTUBE CHANNEL</b></a>
        <a href="https://api.whatsapp.com/send?phone=972549995050" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#25d366;font-size:1.3em;vertical-align:middle;">💬</span> <b>AI DISCUSSION GROUP</b></a>
        <a href="https://whatsapp.com/channel/0029Vaj33VkEawds11JP9o1c" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#25d366;font-size:1.3em;vertical-align:middle;">💬</span> <b>AI TIPS & TRICKS CHANNEL</b></a>
        <a href="https://api.whatsapp.com/send?phone=972549995050" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#25d366;font-size:1.3em;vertical-align:middle;">💬</span> <b>CONTACT ME</b></a>
        <a href="https://www.linkedin.com/in/sagi-bar-on" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#0077b5;font-size:1.3em;vertical-align:middle;">🔗</span> <b>LINKEDIN</b></a>
        <a href="https://www.facebook.com/sagi.baron" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#1877f2;font-size:1.3em;vertical-align:middle;">📘</span> <b>FACEBOOK</b></a>
        <a href="https://linktr.ee/sagib?lt_utm_source=lt_share_link#373198503" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#43e97b;font-size:1.3em;vertical-align:middle;">✳️</span> <b>LINKTREE</b></a>
        <a href="https://buymeacoffee.com/sagibar" target="_blank" rel="noopener noreferrer" style="margin:0 10px;text-decoration:none;"><span style="color:#ffdd00;font-size:1.3em;vertical-align:middle;">🍺</span> <b>BUY ME A BEER</b></a>
      </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 