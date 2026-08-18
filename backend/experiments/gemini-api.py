import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

client = genai.Client()

print(os.getenv("GEMINI_API_KEY"))

interaction = client.interactions.create(
    model="gemini-3.7-flash",
    input="Explain how AI works in a few words"
)

print(interaction.output_text)