# whatsapp.py
import re
import time
from neonize.client import NewClient
from neonize.events import MessageEv, HistorySyncEv
from neonize.utils.enum import ReceiptType
from neonize.utils import log
from database import save_message, get_messages, delete_messages, get_recent_messages_formatted
from scraping import scrape_text
import os
from llm import (
    generate_wait_message,
    generate_final_response,
    generate_first_time_greeting
)
from config import ADMIN_NUMBER

# A simple in-memory dictionary to store scraped link content per user
#   { user_id: "accumulated scraped text" }
USER_SCRAPED_CONTENT = {}

# --- Helper functions ---

def handle_greeting(client, chat, sender_id, sender_name, text):
    """Handles first-time greeting for a new conversation."""
    greeting = generate_first_time_greeting(sender_name, text)
    client.send_message(chat, greeting)
    log.info(f"Sent greeting to {sender_name} ({sender_id}).")
    save_message(sender_id, greeting, int(time.time()), True)

def handle_link(client, message, sender_id, sender_name, text):
    """Handles link detection and scraping."""
    url_pattern = r'(https?://\S+)'
    links_found = re.findall(url_pattern, text)
    if not links_found:
        return

    link = links_found[0]
    log.info(f"Link detected: {link}")

    # Send wait message
    wait_message = generate_wait_message(text)
    client.reply_message(wait_message, message)
    save_message(sender_id, wait_message, int(time.time()), True)
    log.info(f"Sent wait message to {sender_name} for link processing: {wait_message}")

    # Scrape the link and store the content
    scraped_content = scrape_text(link)
    log.debug(f"Scraped content (first 200 chars): {scraped_content[:200]}...")
    USER_SCRAPED_CONTENT[sender_id] = f"\n[Scraped from {link}]\n{scraped_content}"
    log.info(f"Updated scraped content for {sender_id}.")

def handle_file(client, message):
    """Handles file attachments (downloads the file)."""
    file_name = (message.Message.documentMessage.fileName or
                 message.Message.imageMessage.fileName or "file")
    client.download_any(message=message.Message, path=f"./downloads/{file_name}")
    log.info(f"Downloaded file: {file_name}")

def handle_commands(client, chat, sender_id, text):
    """
    Checks for special commands. If one of the commands is detected and the sender's number
    matches a specific number, it sends back pre-formatted info and returns True.
    """
    # Example: Only allow commands from a specific sender.
    if sender_id != ADMIN_NUMBER:
        log.debug(f"Command {text} from {sender_id} not allowed.")
        return False
    
    log.debug(f"Command {text} from {sender_id} is allowed.")

    if text.startswith("!files"):
        # Get list of files in the downloads folder
        downloads_folder = "./downloads"
        files = os.listdir(downloads_folder)
        files_list = "\n".join(files)
        client.send_message(chat, f"[COMMAND] File info: \n{files_list}")
        log.info(f"Processed !files command for {sender_id}.")
        return True
    elif text.startswith("!commands"):
        client.send_message(chat, "[COMMAND] Available commands: !files, !commands, !prompts")
        log.info(f"Processed !commands command for {sender_id}.")
        return True
    elif text.startswith("!prompts"):
        client.send_message(chat, "[COMMAND] Prompt info: [list of prompt templates...]")
        log.info(f"Processed !prompts command for {sender_id}.")
        return True
    # Check if the user wants to clear the conversation history
    elif text.startswith("!reset"):
        client.send_message(chat, "[SYSTEM] Cleared conversation history!")
        delete_messages(sender_id)
        log.info(f"Cleared conversation history for {sender_id} due to '!reset' command.")
        USER_SCRAPED_CONTENT[sender_id] = ""
        log.debug(f"Cleared scraped content for {sender_id}.")
        return True
    elif text.startswith("!"):
        client.send_message(chat, "[COMMAND] Unknown command.")
        log.info(f"Processed unknown command for {sender_id}.")
        return True
    
    return False

def handle_final_response(client, chat, sender_id, text, conversation_history):
    """Generates and sends the final response using the LLM."""
    final_answer = generate_final_response(
        previous_messages=conversation_history,
        scraped_text=USER_SCRAPED_CONTENT.get(sender_id, ""),
        user_text=text
    )
    log.debug(f"Final answer generated: {final_answer}")
    client.send_message(chat, final_answer)
    save_message(sender_id, final_answer, int(time.time()), True)
    log.info(f"Sent final response to {sender_id}.")

# --- Main event handlers ---

def on_history_sync(client, history: HistorySyncEv):
    """
    Processes historical messages from the sync data, storing them in the DB.
    The data structure is at `history.Data.conversations[...]`.
    """
    sync_type = getattr(history.Data, "syncType", None)
    log.info(f"Received history sync event with syncType: {sync_type}")
    log.debug(f"Full history sync data: {history}")

    if not hasattr(history.Data, "conversations"):
        log.info("No conversations found in HistorySyncEv.")
        return

    for conversation in history.Data.conversations:
        user_id = conversation.ID.split('@')[0]  # e.g. phone number
        log.debug(f"Processing conversation for user {user_id}")
        for message_obj in conversation.messages:
            message_data = message_obj.message
            msg = message_data.message
            from_me = getattr(message_data.key, "fromMe", False)
            log.debug(f"Processing message (from_me={from_me}): {msg}")

            # Extract text from different possible fields
            if hasattr(msg, "conversation") and msg.conversation:
                message_content = msg.conversation
            elif (hasattr(msg, "extendedTextMessage") and msg.extendedTextMessage.text):
                message_content = msg.extendedTextMessage.text
            else:
                log.debug("Message is not a text message; skipping.")
                continue

            timestamp = message_obj.message.messageTimestamp
            log.debug(f"Saving message with timestamp {timestamp} for user {user_id}")
            save_message(user_id, message_content, timestamp, from_me)

def on_message(client: NewClient, message: MessageEv):
    """
    Real-time incoming messages.
    Uses one big try/except to capture any errors and separates out key functionality
    into helper functions.
    """
    try:
        chat = message.Info.MessageSource.Chat
        sender_id = message.Info.MessageSource.Chat.User
        text = (message.Message.conversation or
                message.Message.extendedTextMessage.text or
                message.Message.imageMessage.caption or
                message.Message.documentMessage.caption or
                "")
        from_me = message.Info.MessageSource.IsFromMe
        timestamp = message.Info.Timestamp // 1000  # Convert ms to s if needed
        sender_name = message.Info.Pushname or "User"

        log.info(f"Message from {sender_name} ({sender_id}): {text}")
        log.debug(f"Raw message info: {message}")

        # Save raw message object to a file
        message_filename = f"messages/{int(time.time())}.txt"
        with open(message_filename, "w", encoding="utf-8") as file:
            file.write(str(message))
        log.debug(f"Saved raw message to {message_filename}")

        # Check if the message is older than one minute
        if time.time() - timestamp > 60:
            log.info(f"Message from {sender_name} ({sender_id}) is older than one minute; skipping further processing.")
            return

        # Mark as read
        client.mark_read(
            message.Info.ID,
            chat=chat,
            sender=message.Info.MessageSource.Sender,
            receipt=ReceiptType.READ
        )
        log.debug(f"Marked message {message.Info.ID} as read.")

        # Check for a command and process it if present.
        if handle_commands(client, chat, sender_id, text):
            # If a command was processed, do not process further.
            return
        
        # Determine if this is the first message from the user
        previous_messages = get_messages(sender_id)
        is_first_message = len(previous_messages) == 0
        log.debug(f"User {sender_id} has {len(previous_messages)} previous messages; is_first_message={is_first_message}")

        # Save the incoming message to the DB
        save_message(sender_id, text, timestamp, from_me)
        log.debug(f"Saved incoming message for user {sender_id} at timestamp {timestamp}.")

        # Process greeting for a first-time message
        if is_first_message:
            handle_greeting(client, chat, sender_id, sender_name, text)

        # Process links (if any)
        handle_link(client, message, sender_id, sender_name, text)

        # Process file attachments if present
        if message.Info.Type == "media" and not message.Info.MediaType == "url":
            handle_file(client, message)

        # Retrieve a formatted conversation history for context
        conversation_history = get_recent_messages_formatted(sender_id)
        log.debug(f"Retrieved conversation history for {sender_id}: {conversation_history}")

        log.info(f"Generating final response for {sender_id}...")
        handle_final_response(client, chat, sender_id, text, conversation_history)

    except Exception as e:
        log.error(f"Error in on_message handler: {e}")
