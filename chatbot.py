import os
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader
 
# -----------------------------------
# LOAD API KEY
# -----------------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
 
# -----------------------------------
# READ PDF DATASET
# -----------------------------------
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
DIGIBANK_DATA = read_pdf(DATASET_PATH) if os.path.exists(DATASET_PATH) else ""
 
# -----------------------------------
# LLM MODEL
# -----------------------------------
model = genai.GenerativeModel("models/gemini-2.5-flash")
 
# -----------------------------------
# GLOBAL STATES
# -----------------------------------
USER_LANGUAGE = None
LANG_CODE = "en"
DISPUTE_MODE = False
POST_ACTION_MODE = False
END_CHAT = False
RESTART_MODE = False
 
# -----------------------------------
# LANGUAGE CONFIG
# -----------------------------------
LANGUAGES = {
    "1": {
        "name": "English",
        "code": "en",
        "welcome": "Welcome to DigiBank Virtual Assistant",
        "menu": {
            "1": "Check my Bank Balance",
            "2": "Check my Transaction History",
            "3": "Raise a Dispute/Grievance",
        }
    },
    "2": {
        "name": "Hindi",
        "code": "hi",
        "welcome": "डिजीबैंक वर्चुअल असिस्टेंट में आपका स्वागत है",
        "menu": {
            "1": "मेरा बैंक बैलेंस जांचें",
            "2": "मेरी ट्रांजैक्शन हिस्ट्री देखें",
            "3": "शिकायत दर्ज करें",
        }
    },
    "3": {
        "name": "Marathi",
        "code": "mr",
        "welcome": "डिजीबँक व्हर्च्युअल असिस्टंट मध्ये आपले स्वागत आहे",
        "menu": {
            "1": "माझा बँक बॅलन्स तपासा",
            "2": "माझी व्यवहार इतिहास पहा",
            "3": "तक्रार नोंदवा",
        }
    }
}
 
# -----------------------------------
# PREDEFINED ANSWERS
# -----------------------------------
PREDEFINED_ANSWERS = {
    "English": {
        "1": "Step-1: Login to DigiBank.\n"
             "Step-2: Go to User Dashboard.\n"
             "Step-3: View your available Bank Balance.",
 
        "2": "Step-1: Login to DigiBank.\n"
             "Step-2: Open User Dashboard.\n"
             "Step-3: Select Transaction History.",
 
        "3": "Please write your dispute below and click Send.\n\n"
             "After submitting, please contact or get in touch with us through:\n"
             "📧 customersupport@digibank.com\n"
             "📞 Toll-Free: 0001 1123 4567"
    },
    "Hindi": {},
    "Marathi": {}
}
 
# -----------------------------------
# RESET CHATBOT
# -----------------------------------
def reset_chatbot(restart=False):
    global DISPUTE_MODE, POST_ACTION_MODE, END_CHAT, RESTART_MODE, USER_LANGUAGE
 
    DISPUTE_MODE = False
    POST_ACTION_MODE = False
    END_CHAT = False
    RESTART_MODE = False
 
    if not restart:
        USER_LANGUAGE = None
 
# -----------------------------------
# START CHAT
# -----------------------------------
def start_chat():
    reset_chatbot()
    return (
        "Please select your preferred language:\n\n"
        "1. For English Press 1\n"
        "2. For Hindi Press 2\n"
        "3. For Marathi Press 3"
    )
 
# -----------------------------------
# POST ACTION MENU
# -----------------------------------
def post_action_menu():
    return (
        "\n\nWhat would you like to do next?\n"
        "1️⃣ Do you have any other query?\n"
        "2️⃣ End chat"
    )
 
# -----------------------------------
# RESTART MENU
# -----------------------------------
def restart_menu():
    return (
        "\n\nWould you like to restart the chat?\n"
        "1️⃣ Restart chat\n"
        "2️⃣ Exit"
    )
 
# -----------------------------------
# SHOW DEFAULT MENU
# -----------------------------------
def show_default_menu():
    for lang in LANGUAGES.values():
        if lang["name"] == USER_LANGUAGE:
            menu_text = "\n".join([f"{k}. {v}" for k, v in lang["menu"].items()])
            return f"{lang['welcome']}\n\nPlease choose:\n\n{menu_text}"
 
# -----------------------------------
# MAIN CHATBOT LOGIC
# -----------------------------------
def ask_gemini(user_input):
    global USER_LANGUAGE, DISPUTE_MODE, POST_ACTION_MODE, END_CHAT, RESTART_MODE
 
    user_input = user_input.strip()
 
    # Restart handling
    if RESTART_MODE:
        if user_input == "1":
            reset_chatbot(restart=True)
            return show_default_menu()
        elif user_input == "2":
            return "👋 Thank you for using DigiBank. Goodbye!"
        else:
            return "Please select 1 or 2."
 
    # Post-action handling
    if POST_ACTION_MODE:
        if user_input == "1":
            POST_ACTION_MODE = False
            return "Please ask your next query:"
        elif user_input == "2":
            END_CHAT = True
            RESTART_MODE = True
            POST_ACTION_MODE = False
            return (
                "Thank you for getting in touch with us and we genuinely hope "
                "your experience with our service has been a positive one."
                + restart_menu()
            )
        else:
            return "Please select 1 or 2."
 
    # Language selection (ONLY FIRST TIME)
    if USER_LANGUAGE is None:
        lang_data = LANGUAGES.get(user_input)
        if not lang_data:
            return start_chat()
        USER_LANGUAGE = lang_data["name"]
        menu_text = "\n".join([f"{k}. {v}" for k, v in lang_data["menu"].items()])
        return f"{lang_data['welcome']}\n\nPlease choose:\n\n{menu_text}"
 
    # Menu answers
    if user_input in PREDEFINED_ANSWERS.get(USER_LANGUAGE, {}):
        POST_ACTION_MODE = True
        return PREDEFINED_ANSWERS[USER_LANGUAGE][user_input] + post_action_menu()
 
    # Dataset-based Gemini response
    prompt = f"""
You are a DigiBank chatbot.
 
STRICT RULES:
1. Answer ONLY from the dataset below.
2. If answer is NOT present, say:
   "This information is not available in the provided dataset."
3. Always reply STEP-BY-STEP.
4. Reply only in {USER_LANGUAGE}.
5. Do NOT add extra information.
 
DATASET:
{DIGIBANK_DATA}
 
USER QUESTION:
{user_input}
"""
 
    response = model.generate_content(prompt)
    answer = response.text.strip()
 
    POST_ACTION_MODE = True
    return answer + post_action_menu()
 
# -----------------------------------
# TERMINAL RUN
# -----------------------------------
if __name__ == "__main__":
    print("🤖 DigiBank Chatbot Started\n")
    print(start_chat())
 
    while True:
        user_msg = input("\nYou: ")
        if user_msg.lower() in ["exit", "quit"]:
            print("👋 Chatbot closed.")
            break
        print("\nDigiBank AI:\n", ask_gemini(user_msg))
 
 