import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from api_client import call_api, get_customer_org_id, get_user_id

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Slack app
app = App(token=SLACK_BOT_TOKEN)

@app.event("message")
def handle_message(event, say):
    try:
        user_id = event.get('user')
        channel_id = event.get('channel')
        text = event.get('text')
        team_id = event.get('team')

        if not user_id or not channel_id or not text or not team_id:
            say("Error: Incomplete message data.", thread_ts=event['ts'])
            return

        # Get the customer organization ID
        customer_org_id = get_customer_org_id(team_id)
        if not customer_org_id:
            say(f"Error: No customer organization found for team ID: {team_id}. Please use the /register_organization command.", thread_ts=event['ts'])
            return

        # Get the user ID
        api_user_id = get_user_id(user_id)
        if not api_user_id:
            say(f"Error: No user found for Slack ID: {user_id}. Please use the /register_user command.", thread_ts=event['ts'])
            return

        # Create the signal
        signal_response = call_api("/signal/create", method="POST", json={
            "signal": str(text),
            "user_id": int(api_user_id),
            "source": "Slack",
            "type": "Ask"
        })

        if signal_response and "report_id" in signal_response:
            say(f"Signal reported with ID: {signal_response['report_id']}", thread_ts=event['ts'])
        else:
            say(f"Error: Failed to create signal. Response: {signal_response}. Signal: {text}, User ID: {api_user_id}", thread_ts=event['ts'])

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        say(f"Error: An unexpected error occurred while processing the message. Please try again later.", thread_ts=event['ts'])

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()