import logging
import os

def configure_logging():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the overall logging level to DEBUG

    # Define a common log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create and configure a file handler (logs everything)
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Log all messages (DEBUG and above)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create and configure a console handler (logs only INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only log INFO and above to the console
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# In your main() function, call configure_logging() early on
def main():
    configure_logging()

    # (Optional) If you are using a custom log from neonize.utils, set its level as well.
    # For example:
    from neonize.utils import log
    log.setLevel(logging.DEBUG)

    # The rest of your main() function remains the same...
    import signal
    from neonize.client import NewClient
    from neonize.events import (
        MessageEv,
        ConnectedEv,
        HistorySyncEv,
        PairStatusEv,
        event
    )
    from neonize.utils.enum import Presence
    from database import init_db
    from whatsapp import on_message, on_history_sync, on_message
    from config import CONV_DB_PATH, NEO_DB_PATH

    # A global event to handle interrupts
    stop_event = event

    def interrupted(*_):
        """Signal handler for Ctrl+C."""
        stop_event.set()

    signal.signal(signal.SIGINT, interrupted)

    # Create the DB directory if it doesn't exist
    os.makedirs(os.path.dirname(CONV_DB_PATH), exist_ok=True)
    os.makedirs("messages", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)

    # Initialize DB
    init_db()

    # Create the client
    client = NewClient(NEO_DB_PATH)

    @client.event(ConnectedEv)
    def on_connected(client: NewClient, connected: ConnectedEv):
        client.send_presence(presence=Presence.AVAILABLE)
        logging.info("✓ Connected")

    @client.event(HistorySyncEv)
    def handle_history_sync(client: NewClient, history: HistorySyncEv):
        on_history_sync(client, history)

    @client.event(PairStatusEv)
    def PairStatusMessage(_: NewClient, message: PairStatusEv):
        logging.info(f"logged as {message.ID.User}")

    @client.event(MessageEv)
    def PairStatusMessage(client: NewClient, message: MessageEv):
        on_message(client, message)

    # Connect the client
    client.connect()

    # Keep the program running until a signal is received
    stop_event.wait()
    logging.info("Exiting...")

if __name__ == "__main__":
    main()
