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

def main():
    st.set_page_config(
        page_title="מה תביא לביכורים? 🎉",
        page_icon="🎉",
        layout="centered"
    )

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
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center; color:#d72660; font-size:2.5em;'>מה תביא לביכורים? <span style='font-size:1.2em;'>🎉</span></h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-size:1.2em;'>ספרו לנו מה תרצו להביא לסל הביכורים שלכם</div>", unsafe_allow_html=True)

    # כפתורי הקלטה והקלדה (Streamlit buttons instead of HTML)
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("✉️ הקלדה", key="btn_text"):
            st.session_state["input_type"] = "text"
    with col2:
        if st.button("🎤 מיקרופון", key="btn_mic"):
            st.session_state["input_type"] = "mic"
    with col3:
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
            user_items = st.text_input("מה תרצה שיהיה בסל? (הפרד בפסיקים)", value=mic_transcript, key="items_input", help="לדוג' מגבת צבעונית, חטיפי שוקולד, ספר, ...")
        else:
            user_items = st.text_input("מה תרצה שיהיה בסל? (הפרד בפסיקים)", key="items_input", help="לדוג' מגבת צבעונית, חטיפי שוקולד, ספר, ...")
    else:
        user_items = st.text_input("מה תרצה שיהיה בסל? (הפרד בפסיקים)", key="items_input", help="לדוג' מגבת צבעונית, חטיפי שוקולד, ספר, ...")

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
                if img_with_text:
                    # Display the image
                    st.image(img_with_text, caption="הסל שלך לביכורים", use_column_width=True)
                    
                    # Add download button
                    st.markdown(get_image_download_link(img_with_text), unsafe_allow_html=True)

                # כפתור שיתוף
                share_text = f"הנה הסל שלי לביכורים! {hebrew_text}"
                whatsapp_url = f"https://wa.me/?text={share_text}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="font-size:1.3em; color:#25d366;">📱 שתף בוואטסאפ</a>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 