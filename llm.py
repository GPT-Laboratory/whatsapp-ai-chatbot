# llm.py
import requests
import logging
from config import (
    LLM_PROVIDER, OPENAI_API_KEY,
    OLLAMA_API_URL, OLLAMA_MODEL_NAME, 
    OPENAI_API_URL, OPENAI_MODEL_NAME,
    SUMMARIZE_PROMPT_EN, SUMMARIZE_PROMPT_FI,
    FINAL_RESPONSE_PROMPT_EN, FINAL_RESPONSE_PROMPT_FI,
    LANG_SELECTED, AI_ASSISTANT_NAME
)
from database import get_recent_messages_formatted

def _call_llm_api(prompt_text):
    print(f"Calling LLM with prompt: {prompt_text}")
    if LLM_PROVIDER == "openai":
        return _call_openai_api(prompt_text)
    return _call_local_llm_api(prompt_text)

def _call_local_llm_api(prompt_text):
    payload = {"model": OLLAMA_MODEL_NAME, "prompt": prompt_text, "stream": False}
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "No response from local model.").strip()
        logging.error(f"Local LLM Error {response.status_code}: {response.text}")
        return f"Error: {response.status_code}."
    except requests.RequestException as e:
        logging.error(f"Local LLM Request Failed: {e}")
        return "Error with local LLM request."

def _call_openai_api(prompt_text):
    payload = {
        "model": OPENAI_MODEL_NAME,
        "messages": [{"role": "system", "content": prompt_text}],
        "stream": False,
    }
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        response = requests.post(OPENAI_API_URL, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        logging.error(f"OpenAI API Error {response.status_code}: {response.text}")
        return f"Error: {response.status_code}."
    except requests.RequestException as e:
        logging.error(f"OpenAI API Request Failed: {e}")
        return "Error with OpenAI API request."

def generate_first_time_greeting(user_name, user_message):
    # Instruct the LLM to include the placeholder "USER_NAME_HERE" instead of the actual name.
    greeting_prompt = f"""\ 
You are {AI_ASSISTANT_NAME}, a friendly artificial intelligence assistant.
This is your first interaction with the user.
The user has just sent the following message:
"{user_message}"

Please greet the user using the placeholder "USER_NAME_HERE" in place of their actual name.
Respond in the same language as the user's message.
Keep the greeting short and welcoming.
Introduce yourself and clearly state that you are an AI assistant.
Also, mention that you can open links and answer questions about their content.
IMPORTANT:
- Use "USER_NAME_HERE" as a placeholder for the user's name.
- Do not include the actual user name in your response.
"""
    # Call the LLM API with the prompt containing the placeholder.
    raw_response = _call_llm_api(greeting_prompt).strip()

    # Replace the placeholder with the actual user name before sending the message.
    final_response = raw_response.replace("USER_NAME_HERE", user_name)
    return final_response

def summarize_conversation(user_id):
    """
    Summarize the most recent messages for the user into a concise format.
    """
    # Retrieve the most recent messages
    conversation_history = get_recent_messages_formatted

    # Choose prompt template based on language
    if LANG_SELECTED == "FI":
        prompt_template = SUMMARIZE_PROMPT_FI
    else:
        prompt_template = SUMMARIZE_PROMPT_EN

    # Format the prompt
    prompt = prompt_template.format(conversation=conversation_history)

    return _call_llm_api(prompt).strip()

def generate_final_response(previous_messages, scraped_text, user_text):
    """
    Generate the final response for the user.
    """
    # Choose prompt template based on language
    if LANG_SELECTED == "FI":
        prompt_template = FINAL_RESPONSE_PROMPT_FI
    else:
        prompt_template = FINAL_RESPONSE_PROMPT_EN

    # Format the prompt
    final_prompt = prompt_template.format(
        ai_assistant_name=AI_ASSISTANT_NAME,
        previous_messages=previous_messages,
        scraped_text=scraped_text or "No additional content provided.",
        user_message=user_text
    )

    logging.debug(f"Final prompt generated: {final_prompt}")
    return _call_llm_api(final_prompt).strip()

def generate_wait_message(user_text):
    prompt = f"""\
You are a language expert. The user has just sent the following message:
\"{user_text}\"

Please produce exactly one short sentence that says something along the lines of:
"Please wait while I check the link..."
but in the same language the user wrote in. Keep it very short.
"""

    result = _call_llm_api(prompt)
    return result.strip()
