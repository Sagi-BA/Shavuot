import streamlit as st
import openai
from PIL import Image
import requests
from io import BytesIO

st.set_page_config(page_title="מה הייתי מביא לביכורים?", layout="centered")

st.title("🎤 מה הייתי מביא לביכורים?")
st.write("הקליטו את עצמכם אומרים מה הייתם מביאים לסל הביכורים, ואנחנו נהפוך את זה לגלויה חגיגית עם סל מותאם אישית!")

# Step 1: Record (simulate for now)
user_input = st.text_input("מה היית אומר?", "הייתי מביא ענבים, לב וניגון ישן")

# Step 2: Generate poetic text (placeholder)
if st.button("צור את סל הביכורים שלי"):
    with st.spinner("יוצר סל אישי..."):
        poetic_text = f"סל הביכורים שלך כולל: {user_input} – שילוב של טעם, רגש וזיכרון 🌾"
        image_url = "https://images.unsplash.com/photo-1590080876213-7a9180b8b68a"  # placeholder

        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        st.image(image, caption="הסל שלך מוכן!", use_column_width=True)
        st.markdown(f"**{poetic_text}**")

        st.success("אפשר לשתף את הגלויה עם חברים או לנסות שוב!")

