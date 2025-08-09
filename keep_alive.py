from flask import Flask
from threading import Thread
import logging
import time

app = Flask('')

@app.route('/')
def home():
    return "Discord Bot is running!"

@app.route('/status')
def status():
    return {"status": "online", "service": "Discord Bot"}

@app.route('/health')
def health():
    return {"health": "ok", "timestamp": time.time()}

def run():
    # Disable Flask's default logging to avoid spam
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        logging.error(f"Flask server error: {e}")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    
    # Give the server a moment to start
    time.sleep(2)
    
    # Verify server is running
    try:
        import requests
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code == 200:
            logging.info("Keep-alive server verified running on port 8080")
        else:
            logging.warning("Keep-alive server may not be responding properly")
    except:
        logging.warning("Could not verify keep-alive server status")