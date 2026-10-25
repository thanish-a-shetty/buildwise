from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()  # reads GEMINI_API_KEY from the environment

resp = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="In one sentence, what is a Bill of Quantities in construction?",
)
print(resp.text)
