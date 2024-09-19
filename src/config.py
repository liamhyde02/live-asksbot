import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Environment variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
API_KEY = os.environ.get("API_KEY")
API_BASE_URL = "https://live-db-kohl.vercel.app"

# Print environment variables for debugging
print(f"SLACK_BOT_TOKEN: {SLACK_BOT_TOKEN[:10]}...")
print(f"SLACK_APP_TOKEN: {SLACK_APP_TOKEN[:10]}...")

# Store conversation states
conversation_states = {}