
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

# Default base URL, can be overridden by config in the future if needed.
# For now, we are not making base_url configurable based on user feedback.
DRAWIO_BASE_URL = "https://app.diagrams.net/"

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

        # Retrieve URL parameters from config
        lightbox = config.get("drawio_lightbox", True)
        edit_mode = config.get("drawio_edit_mode", "_blank")
        layers = config.get("drawio_layers", True)
        nav = config.get("drawio_nav", True)
        appearance = config.get("drawio_appearance", "auto") # New
        border_color = config.get("drawio_border_color", "none") # New
        links_config = config.get("drawio_links", "auto") # New

        # Construct query parameters string
        params = []
        if lightbox: # Parameter is 'lightbox=1' or not present
            params.append("lightbox=1")
        # edit_mode: value directly used, e.g. 'edit=_blank'
        if edit_mode:
            params.append(f"edit={edit_mode}")
        if layers: # Parameter is 'layers=1' or not present
            params.append("layers=1")
        if nav: # Parameter is 'nav=1' or not present
            params.append("nav=1")

        # Appearance: 'ui=auto|light|dark'
        if appearance and appearance != "auto": # "auto" is often default, no need to send
            params.append(f"ui={appearance}")

        # Border Color: 'border=HEXCOLOR' (without #) or 'border=none'
        if border_color: # Could be "none" or a hex string
            # diagrams.net expects hex colors without '#' for the 'border' URL param.
            actual_border_color = border_color.lstrip('#')
            if actual_border_color: # Ensure it's not empty after stripping
                 params.append(f"border={actual_border_color}")

        # Links: 'links=auto|blank|self'
        if links_config and links_config != "auto": # "auto" is often default
            params.append(f"links={links_config}")

        param_string = "&".join(params)
        if not param_string: # Ensure param_string is not empty if all options are default/off
            full_url = f"{DRAWIO_BASE_URL}#R{url_fragment}"
        else:
            full_url = f"{DRAWIO_BASE_URL}?{param_string}#R{url_fragment}"

        # The line above correctly assigns full_url based on param_string.
        # The duplicated line below is removed:
        # full_url = f"{DRAWIO_BASE_URL}?{param_string}#R{url_fragment}"
        log_event(f"Constructed Draw.io URL: {full_url}", level="DEBUG")

        copy_code = config.get("drawio_copy_code", True)
        copy_url = config.get("drawio_copy_url", True)
        open_browser = config.get("drawio_open_in_browser", True)

        log_event(f"Config settings: copy_code={copy_code}, copy_url={copy_url}, open_browser={open_browser}", level="DEBUG")

        new_clipboard_content = None

        # Handle clipboard copying in the requested order: code first, then URL
        if copy_code and copy_url:
            # First copy the XML code
            if pyperclip:
                pyperclip.copy(clipboard_content)
                log_event("Copied Draw.io XML to clipboard", level="INFO")
                show_notification("Draw.io XML", "XML code copied to clipboard", "")

                # Then copy the URL
                pyperclip.copy(full_url)
                log_event("Copied Draw.io URL to clipboard", level="INFO")
                show_notification("Draw.io URL", "URL copied to clipboard", "")
            new_clipboard_content = full_url  # Return URL as final clipboard content
        elif copy_code:
            new_clipboard_content = clipboard_content
            show_notification("Draw.io XML", "XML code copied to clipboard", "")
        elif copy_url:
            new_clipboard_content = full_url
            show_notification("Draw.io URL", "URL copied to clipboard", "")

        # Open browser after clipboard operations
        if open_browser:
            webbrowser.open_new(full_url)
            log_event("Opened URL in browser.", level="DEBUG")
            show_notification("Draw.io Browser", "Opened in browser", "")

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
