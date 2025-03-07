# config.py
import os
from dotenv import load_dotenv
load_dotenv()

ADMIN_NUMBER = os.getenv("ADMIN_NUMBER")

# Database Configuration
CONV_DB_PATH = "db/conversations.sqlite3"
NEO_DB_PATH = "db/neonize.sqlite3"

LLM_PROVIDER = "openai"  # "ollama" or "openai"

# Local Language Model Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME = "hf.co/itlwas/Ahma-7B-Instruct-Q4_K_M-GGUF:latest"
OLLAMA_MODEL_NAME_2 = "hf.co/LumiOpen/Poro-34B-chat-GGUF:Q4_K_M"

# OpenAI Language Model Configuration
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL_NAME = "gpt-4o-mini"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CONV_DB_PATH = "db/conversations.sqlite3"
NEO_DB_PATH = "db/neonize.sqlite3"
MAX_MESSAGES = 10  # Maximum number of messages to retrieve for summarization

# Language Selection
LANG_SELECTED = "EN"  # Default language for the assistant (EN or FI)

AI_ASSISTANT_NAME = "Juha Botti"

# Prompts
SUMMARIZE_PROMPT_EN = """\
You are a highly concise summarizer. Below is a conversation between a user and an assistant (ME).
Please produce a very short summary of the key points of their conversation so far.
You do not need to include greetings or pleasantries unless crucial.
Keep the summary in the same language as the conversation.
Here is the conversation:
====================
{conversation}
====================
Now produce a concise summary:
"""

SUMMARIZE_PROMPT_FI = """\
Olet erittäin tiivis tiivistäjä. Alla on keskustelu käyttäjän ja avustajan (MINÄ) välillä.
Ole hyvä ja tee erittäin lyhyt yhteenveto heidän keskustelunsa keskeisistä kohdista.
Sinun ei tarvitse sisällyttää tervehdyksiä tai kohteliaisuuksia, elleivät ne ole olennaisia.
Tässä on keskustelu:
====================
{conversation}
====================
Tee nyt tiivis yhteenveto:
"""

FINAL_RESPONSE_PROMPT_EN = """\
You are a friendly assistant called {ai_assistant_name}, an expert at helping users without wasting their time.
Always respond in the same language as the user's last message.
Keep your response short and concise, unless the user explicitly requests a longer or more detailed explanation.

Here is the previous conversation for context:
--------------------------------
{previous_messages}
--------------------------------

If the user provided a link, I opened the link for you and heres the text it contained:
--------------------------------
{scraped_text}
--------------------------------

Now, the user's latest message is:
--------------------------------
{user_message}
--------------------------------

Please provide a short, friendly, helpful response in the same language as the user's message.
It's ok to admit that you do not know something.
Use the user's latest message and the summary to determine the language.
If the user included questions about the link, address them specifically.
Otherwise, politely offer to clarify or answer further questions.
"""

FINAL_RESPONSE_PROMPT_FI = """\
Olet ystävällinen avustaja nimeltä {ai_assistant_name} ja asiantuntija käyttäjien auttamisessa ilman ajanhukkaa.
Vastaa aina samalla kielellä kuin käyttäjän viimeisin viesti.
Pidä vastauksesi lyhyenä ja ytimekkäänä, ellei käyttäjä erikseen pyydä pidempää tai yksityiskohtaisempaa selitystä.

Tässä on tiivis yhteenveto keskustelusta tähän mennessä:
--------------------------------
{conversation_summary}
--------------------------------

Jos käyttäjä antoi linkkitekstiä, tässä se on:
--------------------------------
{scraped_text}
--------------------------------

Nyt käyttäjän viimeisin viesti on:
"{user_message}"

Ole hyvä ja anna lyhyt, ystävällinen ja hyödyllinen vastaus samalla kielellä kuin käyttäjän viesti.
Jos käyttäjä sisälsi kysymyksiä linkistä, vastaa niihin erityisesti.
Muussa tapauksessa tarjoa kohteliaasti selvennystä tai vastaa lisäkysymyksiin.
"""