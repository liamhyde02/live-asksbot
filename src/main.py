import uvicorn
from asksbot import app as slack_app, fastapi_app
from slack_bolt.adapter.fastapi import SlackRequestHandler

handler = SlackRequestHandler(slack_app)

@fastapi_app.post("/slack/events")
async def slack_events(request):
    return await handler.handle(request)

if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)