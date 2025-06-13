#!/usr/bin/env python3
import time
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from AppKit import NSPasteboard, NSStringPboardType

# Configure logging
log_format = '%(asctime)s - %(levelname)s - %(message)s'
log_file = '/tmp/mdtortf.log'

logger = logging.getLogger('MDtoRTF')
logger.setLevel(logging.INFO)

# Rotating file handler (1MB max, 3 backups)
file_handler = RotatingFileHandler(
    log_file, maxBytes=1048576, backupCount=3, encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(log_format))

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_clipboard():
    try:
        pb = NSPasteboard.generalPasteboard()
        content = pb.stringForType_(NSStringPboardType) or ""
        logger.debug(f"Clipboard content: {content[:50]}...")
        return content
    except Exception as e:
        logger.error(f"Clipboard access error: {str(e)}")
        return ""

def set_clipboard_rtf(rtf_data):
    try:
        subprocess.run(
            ['pbcopy', '-Prefer', 'rtf'],
            input=rtf_data,
            check=True,
            timeout=2
        )
        logger.info("RTF copied to clipboard successfully")
    except subprocess.TimeoutExpired:
        logger.error("pbcopy operation timed out")
    except Exception as e:
        logger.error(f"Clipboard set error: {str(e)}")

def is_markdown(text):
    if not text:
        return False
    markers = ['#', '*', '-', '`', '![']
    return any(m in text for m in markers) and '\n' in text

def convert_md_to_rtf(md_text):
    try:
        logger.debug("Starting Markdown conversion")
        with subprocess.Popen(
            ['/opt/homebrew/bin/pandoc', '-f', 'markdown', '-t', 'html'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        ) as p1, subprocess.Popen(
            ['textutil', '-convert', 'rtf', '-stdin', '-stdout', '-format', 'html'],
            stdin=p1.stdout,
            stdout=subprocess.PIPE
        ) as p2:
            html, _ = p1.communicate(input=md_text.encode('utf-8'), timeout=5)
            rtf, _ = p2.communicate(timeout=5)
            logger.info(f"Converted {len(md_text)} characters")
            return rtf
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        return None

def main():
    logger.info("Starting MDtoRTF service")
    last_content = ""
    try:
        while True:
            current_content = get_clipboard()
            if current_content and current_content != last_content:
                if is_markdown(current_content):
                    logger.info("Detected Markdown content")
                    rtf_data = convert_md_to_rtf(current_content)
                    if rtf_data:
                        set_clipboard_rtf(rtf_data)
                last_content = current_content
            time.sleep(0.8)
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
