import os
import django
import logging
from messages_app.views import find_misused_sender_ids  

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/app/daily_task.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Main function to process and email misused sender IDs.
    """
    try:
        # Set up Django environment
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "message_classification.settings")
        django.setup()

        logger.info("Django environment set up successfully.")

        # Directly invoke the logic without requiring an HTTP request
        response = find_misused_sender_ids(None) 
        logger.info(f"Task completed: {response.content.decode()}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

