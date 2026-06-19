import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
URL = os.getenv("SPACE_URL", "https://huggingface.co/spaces/Qalam/Nuclear-Intelligence")

def ping_space():
    try:
        response = requests.get(URL)
        if response.status_code == 200:
            logger.info(f"Successfully pinged {URL}")
        else:
            logger.warning(f"Failed to ping {URL}. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error pinging {URL}: {e}")

if __name__ == "__main__":
    logger.info("Starting Keep-Alive script...")
    while True:
        ping_space()
        time.sleep(20 * 60)  # Ping every 20 minutes
