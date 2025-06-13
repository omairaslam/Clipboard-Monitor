import pyperclip
import time
import webbrowser
import base64
import json
import logging
import traceback
import subprocess
import re
import signal
import sys

MERMAID_PLAYGROUND_BASE = "https://mermaid.live/edit#"

# Set up robust logging
logging.basicConfig(
    filename='/tmp/mermaid_clipboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_notification(message):
    """Send macOS notification using osascript"""
    try:
        subprocess.run(
            ['osascript', '-e', f'display notification "{message}" with title "Mermaid Clipboard"'],
            check=True
        )
        logging.info("Notification sent: %s", message)
    except Exception as e:
        logging.error("Notification failed: %s", str(e))

def encode_mermaid_code(mermaid_code):
    try:
        data = {"code": mermaid_code, "mermaid": {}}
        json_str = json.dumps(data, separators=(',', ':'))
        b64 = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
        return b64
    except Exception as e:
        logging.error("Encoding failed: %s", str(e))
        return ""

def is_mermaid_code(text):
    if not text:
        return False
    # Regex for common Mermaid diagram types at the start of the text (case-insensitive)
    mermaid_patterns = [
        r"^\s*graph\s",                 # flowchart
        r"^\s*flowchart\b",             # flowchart alternative starter
        r"^\s*sequenceDiagram\b",       # sequence diagram
        r"^\s*classDiagram\b",          # class diagram
        r"^\s*stateDiagram\b",          # state diagram
        r"^\s*erDiagram\b",             # ER diagram
        r"^\s*gantt\b",                 # Gantt chart
        r"^\s*pie\b",                   # Pie chart
        r"^\s*journey\b",               # Journey diagram
        r"^\s*mindmap\b",               # Mindmap
        r"^\s*timeline\b",              # Timeline
        r"^\s*gitGraph\b",              # Git graph
        r"^\s*quadrantChart\b",         # Quadrant chart
        r"^\s*requirementDiagram\b",    # Requirement diagram
        r"^\s*C4Context\b",             # C4 diagrams
        r"^\s*C4Container\b",
        r"^\s*C4Component\b",
        r"^\s*C4Dynamic\b",
    ]
    for pattern in mermaid_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False

def handle_exit(signum, frame):
    logging.info("Mermaid clipboard watcher shutting down (signal %s)", signum)
    sys.exit(0)

def main():
    last_clipboard = ""
    logging.info("Mermaid clipboard watcher started")
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    while True:
        try:
            text = pyperclip.paste()
            if not text:
                time.sleep(1)
                continue
            if text != last_clipboard:
                if is_mermaid_code(text):
                    logging.info("Mermaid code detected: %s", text[:100].replace('\n', ' '))
                    send_notification("Mermaid chart detected! Opening playground...")
                    encoded = encode_mermaid_code(text)
                    if encoded:
                        url = MERMAID_PLAYGROUND_BASE + encoded
                        webbrowser.open(url)
                        logging.info("Opened Mermaid playground with URL: %s", url)
                last_clipboard = text
            time.sleep(1)
        except Exception as e:
            logging.error("Unhandled exception: %s", str(e))
            logging.error(traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    main()
