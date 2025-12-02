import os
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------------------
# READ PDF FILE CORRECTLY
# ---------------------------
def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "chatbotfile.pdf")
DIGIBANK_DATA = read_pdf(DATASET_PATH)

model = genai.GenerativeModel("models/gemini-2.5-flash")

# ---------------------------
# CHATBOT ANSWER FUNCTION
# ---------------------------
def ask_gemini(question):

    prompt = f"""
You are DigiBank's AI assistant.

Format rules (IMPORTANT):
- ALWAYS answer in VERTICAL bullet points.
- Each bullet point must be on a NEW line.
- Add a BLANK LINE between bullet points.
- Do NOT write paragraphs.
- Do NOT merge multiple points in one line.
- Do NOT write inline explanations.
- Keep answers simple, clean, and vertical.

Use this exact format:

• Point 1

• Point 2

• Point 3

Dataset:
{DIGIBANK_DATA}

User question: {question}
"""

    response = model.generate_content(prompt)
    return response.text
