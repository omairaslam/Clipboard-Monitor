
"""
Draw.io XML Clipboard Module - Detects draw.io XML, encodes for diagrams.net, copies URL, opens browser, notifies user.
"""

import xml.etree.ElementTree as ET
import zlib
import base64
import urllib.parse
import webbrowser

try:
    import pyperclip
except ImportError:
    pyperclip = None

import logging
from pathlib import Path
try:
    from ..utils import show_notification, log_event, log_error
    from ..config_manager import ConfigManager
except ImportError:
    # This is for standalone testing
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from utils import show_notification, log_event, log_error
    from config_manager import ConfigManager


DRAWIO_URL_TEMPLATE = "https://app.diagrams.net/?lightbox=1&edit=_blank&layers=1&nav=1#R{encoded}"

def is_drawio_xml(xml_str):
    """
    Check if a string is valid Draw.io XML.
    """
    if not isinstance(xml_str, str) or not xml_str.strip():
        return False
    try:
        root = ET.fromstring(xml_str)
        return root.tag == "mxfile" and root.find("diagram") is not None
    except ET.ParseError:
        return False


def encode_drawio_url(xml_str):
    """
    Encode Draw.io XML for use in a URL.
    """
    # Compress, base64, and url-encode as per diagrams.net spec
    compressed = zlib.compress(xml_str.encode("utf-8"), 9)[2:-4]  # strip zlib header/footer
    b64 = base64.b64encode(compressed).decode("utf-8")
    url_encoded = urllib.parse.quote(b64, safe='')
    return url_encoded


def process(clipboard_content, config=None):
    """
    Process clipboard content for draw.io XML.
    Returns the new clipboard content (the URL) if it was modified, otherwise None.
    """
    log_event("Draw.io module processing started.", level="DEBUG")
    if not is_drawio_xml(clipboard_content):
        log_event("Clipboard content is not Draw.io XML.", level="DEBUG")
        return None

    log_event("Draw.io XML detected.", level="DEBUG")
    if config is None:
        log_event("Config not provided, loading from ConfigManager.", level="DEBUG")
        config_manager = ConfigManager()
        config = config_manager.get_section('modules')

    if not config.get("drawio_module", True):
        log_event("Draw.io module is disabled in config.", level="DEBUG")
        return None
    log_event("Draw.io module is enabled.", level="DEBUG")

    try:
        log_event("Encoding Draw.io URL.", level="DEBUG")
        url_fragment = encode_drawio_url(clipboard_content)
        full_url = DRAWIO_URL_TEMPLATE.format(encoded=url_fragment)

        copy_url = config.get("drawio_copy_url", True)
        open_browser = config.get("drawio_open_in_browser", True)
        log_event(f"Config settings: copy_url={copy_url}, open_browser={open_browser}", level="DEBUG")
        
        notification_message = []
        new_clipboard_content = None

        if copy_url:
            if pyperclip:
                pyperclip.copy(full_url)
                new_clipboard_content = full_url
                notification_message.append("URL copied to clipboard")
                log_event("URL copied to clipboard.", level="DEBUG")
            else:
                log_error("pyperclip is not available, cannot copy URL.")

        if open_browser:
            webbrowser.open_new(full_url)
            notification_message.append("opened in browser")
            log_event("Opened URL in browser.", level="DEBUG")

        if notification_message:
            show_notification("Draw.io Diagram", "Draw.io XML detected! " + " and ".join(notification_message) + ".", "")
            log_event(f"Draw.io diagram processed: {' and '.join(notification_message)}.", level="INFO")
        
        return new_clipboard_content

    except (zlib.error, base64.binascii.Error, Exception) as e:
        log_error(f"Draw.io processing failed: {e}")
        show_notification("Draw.io Error", f"Draw.io processing failed: {e}", "")
        return None

if __name__ == '__main__':
    # Example usage for standalone testing
    test_xml = """<mxfile>
      <diagram id="C_kwDOLG5kMdo0ZWY4MWQ5ZC0z" name="Page-1">
        <mxGraphModel dx="1434" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
          <root>
            <mxCell id="0" />
            <mxCell id="1" parent="0" />
            <mxCell id="2" value="Hello" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="1">
              <mxGeometry x="380" y="250" width="60" height="30" as="geometry" />
            </mxCell>
          </root>
        </mxGraphModel>
      </diagram>
    </mxfile>"""

    print("Testing with valid Draw.io XML...")
    process(test_xml)

    print("\nTesting with invalid XML...")
    process("<invalid>xml</invalid>")

    print("\nTesting with non-XML string...")
    process("Just a regular string")

