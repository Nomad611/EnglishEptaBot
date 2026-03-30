import os
import asyncio
from flask import Flask
from aiogram import Bot, Dispatcher
import threading

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is running", 200

def run_bot():
    import bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot.main())

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
