from together import Together
import os
from dotenv import load_dotenv
import streamlit as st

class TogetherAIGenerator:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("TOGETHER_API_KEY")
        self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"  # or "meta-llama/Llama-3-8B-Instruct"
        self.client = Together(api_key=self.api_key)

    def generate_hebrew_text(self, prompt):
        """
        Generate Hebrew text using Together AI's Llama-3 model (chat endpoint)
        """
        try:
            system_prompt = (
                "אתה משורר עברי מודרני. כתוב משפט קצר, משעשע ומקורי על סל ביכורים. "
                "השתמש בשפה עברית יפה ומודרנית."
            )
            user_prompt = f"כתוב משפט על סל ביכורים שמכיל: {prompt}"
            # print(f"user_prompt: {user_prompt}")    
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.7,
                stream=False
            )
            # Extract the generated text
            generated_text = response.choices[0].message.content.strip()
            return generated_text

        except Exception as e:
            st.error(f"שגיאה ביצירת הטקסט: {str(e)}")
            return None

def test():
    generator = TogetherAIGenerator()
    test_prompt = "תפוחים, דבש, ואהבה"
    result = generator.generate_hebrew_text(test_prompt)
    print(f"Test result: {result}")
    return result

if __name__ == "__main__":
    test() 