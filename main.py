#!/usr/bin/env python3
"""
Main entry point for the Discord bot.
This script starts the bot with keep-alive functionality for 24/7 operation.
"""

import os
import asyncio
import logging
from threading import Thread
from flask import Flask
import time

# Import bot components
from bot import main as bot_main

# Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is running 24/7!"

@app.route('/status')
def status():
    return {
        "status": "online",
        "service": "Discord Bot",
        "timestamp": time.time()
    }

@app.route('/health')
def health():
    return {"health": "ok"}

def run_flask():
    """Run Flask server in a separate thread"""
    # Disable Flask logging to reduce spam
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Start Flask server
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def main():
    """Main function to start both Flask and Discord bot"""
    print("Starting Discord Bot with 24/7 keep-alive...")
    
    # Start Flask server in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Small delay to ensure Flask starts
    time.sleep(2)
    print("Keep-alive server started on port 8080")
    
    # Start Discord bot (this will block)
    try:
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("Bot shutdown requested")
    except Exception as e:
        print(f"Bot error: {e}")
        raise

if __name__ == "__main__":
    main()