import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from api_client import call_api, get_customer_org_id, get_user_id
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Slack app
app = App(token=SLACK_BOT_TOKEN)

# Initialize FastAPI app
fastapi_app = FastAPI()

class CommentCommand(BaseModel):
    report_ids: List[int]
    opportunity: str

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

@fastapi_app.post("/comment_opportunities")
async def handle_opportunity_comments(command: CommentCommand):
    try:
        results = []
        channels = await get_bot_channels()

        for channel in channels:
            channel_results = await process_channel(channel, command.report_ids, command.opportunity)
            results.extend(channel_results)

        return {"results": results}

    except Exception as e:
        logger.error(f"Error handling opportunity comments: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def get_bot_channels():
    try:
        response = app.client.conversations_list(types="public_channel,private_channel")
        return [channel["id"] for channel in response["channels"] if channel["is_member"]]
    except Exception as e:
        logger.error(f"Error getting bot channels: {e}", exc_info=True)
        return []

async def process_channel(channel_id, report_ids, opportunity):
    results = []
    try:
        conversation_history = app.client.conversations_history(channel=channel_id)
        for message in conversation_history["messages"]:
            report_id = find_report_id_in_replies(message)
            if report_id in report_ids:
                result = await process_message(channel_id, message, report_id, opportunity)
                results.append(result)
    except Exception as e:
        logger.error(f"Error processing channel {channel_id}: {str(e)}", exc_info=True)
    return results

async def process_message(channel_id, message, report_id, opportunity):
    try:
        bot_user_id = get_user_id("bot_user_id")  # Replace with actual bot user ID
        comment_id = call_api("/signal/comment", method="POST", json={
            "report_id": report_id,
            "comment": opportunity,
            "user_id": bot_user_id
        })

        if not comment_id:
            return {"report_id": report_id, "status": "failed", "error": "Failed to create comment"}

        response = app.client.chat_postMessage(
            channel=channel_id,
            text=f"New opportunity for report {report_id}: {opportunity}",
            thread_ts=message['ts']
        )
        return {"report_id": report_id, "status": "success", "comment_id": comment_id, "slack_ts": response['ts'], "channel": channel_id}
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return {"report_id": report_id, "status": "failed", "error": str(e)}

def find_report_id_in_replies(message):
    if "reply_count" not in message or message["reply_count"] == 0:
        return None

    for reply in message.get("replies", []):
        if "Signal reported with ID:" in reply.get("text", ""):
            try:
                return int(reply["text"].split("Signal reported with ID:")[-1].strip())
            except ValueError:
                continue
    return None

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()