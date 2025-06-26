#!/usr/bin/env python3
"""
Web-based clipboard history viewer that opens in browser
"""

import os
import json
import datetime
import webbrowser
import tempfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
from utils import load_clipboard_history

def create_html_viewer():
    """Create HTML file for clipboard history"""
    
    history = load_clipboard_history()
    
    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clipboard History Viewer ({len(history)} items)</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: #007AFF;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .stats {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 20px;
        }}
        .history-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 15px;
            background: #fafafa;
            overflow: hidden;
        }}
        .item-header {{
            background: #f0f0f0;
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .item-number {{
            font-weight: bold;
            color: #007AFF;
        }}
        .item-timestamp {{
            color: #666;
            font-size: 14px;
        }}
        .item-content {{
            padding: 15px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            background: white;
            max-height: 200px;
            overflow-y: auto;
        }}
        .copy-btn {{
            background: #007AFF;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-right: 8px;
        }}
        .copy-btn:hover {{
            background: #0056CC;
        }}
        .select-btn {{
            background: #34C759;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        .select-btn:hover {{
            background: #28A745;
        }}
        .no-history {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .action-buttons {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        }}
        .refresh-btn, .clear-btn {{
            background: #007AFF;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }}
        .refresh-btn:hover, .clear-btn:hover {{
            background: #0056CC;
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}
        .clear-btn {{
            background: #dc3545;
        }}
        .clear-btn:hover {{
            background: #c82333;
        }}
        .instructions {{
            background: #E3F2FD;
            border: 1px solid #BBDEFB;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .instructions h4 {{
            margin: 0 0 10px 0;
            color: #1976D2;
        }}
        .rtf-content {{
            background: #FFF3E0;
            border: 1px solid #FFB74D;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
        }}
        .rtf-content strong {{
            color: #E65100;
        }}
        .rtf-content code {{
            background: #F5F5F5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            display: block;
            margin: 8px 0;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .rtf-content em {{
            color: #FF6F00;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Clipboard History Viewer</h1>
            <div class="stats">{len(history)} items in history</div>
        </div>
        <div class="content">
            <div class="instructions">
                <h4>📋 How to Copy Items:</h4>
                <p><strong>Method 1:</strong> Click the "Copy" button (may not work in all browsers due to security restrictions)</p>
                <p><strong>Method 2:</strong> Click "Select All" then press <kbd>Cmd+C</kbd> (Mac) or <kbd>Ctrl+C</kbd> (Windows)</p>
                <p><strong>Method 3:</strong> Manually select the text and copy with <kbd>Cmd+C</kbd> or <kbd>Ctrl+C</kbd></p>
            </div>
"""

    if not history:
        html_content += """
            <div class="no-history">
                <h3>No clipboard history found</h3>
                <p>Copy something to start tracking your clipboard history!</p>
            </div>
"""
    else:
        for i, item in enumerate(history):
            try:
                timestamp = datetime.datetime.fromtimestamp(item.get('timestamp', 0))
                content = item.get('content', '').strip()

                # Detect content type
                content_type = "text"
                content_icon = "📄"
                if content.startswith('{\\rtf') or (content.startswith('{') and 'deff0' in content and 'ttbl' in content):
                    content_type = "rtf"
                    content_icon = "🎨"
                elif content.startswith(('http://', 'https://')):
                    content_type = "url"
                    content_icon = "🔗"

                # Escape HTML characters
                content_html = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                # Special handling for RTF content
                if content_type == "rtf":
                    content_html = f'<div class="rtf-content"><strong>🎨 RTF Content (converted from Markdown)</strong><br><code>{content_html}</code><br><em>💡 This RTF content will appear formatted when pasted into compatible applications.</em></div>'
                else:
                    # Truncate very long content for display
                    if len(content_html) > 2000:
                        content_html = content_html[:2000] + "... (truncated)"
                
                time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                html_content += f"""
            <div class="history-item">
                <div class="item-header">
                    <span class="item-number">Item #{i+1}</span>
                    <span class="item-timestamp">{time_str}</span>
                    <button class="copy-btn" onclick="copyToClipboard('{i}')">Copy</button>
                    <button class="select-btn" onclick="selectText('{i}')">Select All</button>
                </div>
                <div class="item-content" id="content-{i}">{content_html}</div>
            </div>
"""
            except Exception as e:
                html_content += f"""
            <div class="history-item">
                <div class="item-header">
                    <span class="item-number">Item #{i+1}</span>
                    <span class="item-timestamp">Error</span>
                </div>
                <div class="item-content">Error displaying item: {e}</div>
            </div>
"""
    
    html_content += """
        </div>
    </div>

    <div class="action-buttons">
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
        <button class="clear-btn" onclick="clearHistory()">🗑️ Clear History</button>
    </div>
    
    <script>
        function copyToClipboard(itemIndex) {
            const contentElement = document.getElementById('content-' + itemIndex);
            const content = contentElement.textContent;
            const btn = event.target;
            const originalText = btn.textContent;

            // Try modern clipboard API first
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(content).then(function() {
                    showCopySuccess(btn, originalText);
                }).catch(function(err) {
                    fallbackCopy(content, btn, originalText);
                });
            } else {
                fallbackCopy(content, btn, originalText);
            }
        }

        function fallbackCopy(content, btn, originalText) {
            // Fallback method using textarea
            const textarea = document.createElement('textarea');
            textarea.value = content;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();

            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    showCopySuccess(btn, originalText);
                } else {
                    showCopyError(btn, originalText, 'Copy command failed');
                }
            } catch (err) {
                showCopyError(btn, originalText, err.toString());
            }

            document.body.removeChild(textarea);
        }

        function showCopySuccess(btn, originalText) {
            btn.textContent = '✓ Copied!';
            btn.style.background = '#28a745';

            setTimeout(function() {
                btn.textContent = originalText;
                btn.style.background = '#007AFF';
            }, 2000);
        }

        function showCopyError(btn, originalText, error) {
            btn.textContent = '✗ Failed';
            btn.style.background = '#dc3545';

            // Show detailed error in console
            console.error('Copy failed:', error);

            // Show user-friendly message
            alert('Copy failed. Please use the "Select All" button and manually copy (Cmd+C).\\n\\nError: ' + error);

            setTimeout(function() {
                btn.textContent = originalText;
                btn.style.background = '#007AFF';
            }, 3000);
        }

        function selectText(itemIndex) {
            const contentElement = document.getElementById('content-' + itemIndex);

            // Create a range and select the text
            if (window.getSelection && document.createRange) {
                const range = document.createRange();
                range.selectNodeContents(contentElement);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);

                // Show instruction
                alert('Text selected! Now press Cmd+C (Mac) or Ctrl+C (Windows) to copy.');
            } else {
                alert('Text selection not supported. Please manually select the text and copy.');
            }
        }

        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);

        function clearHistory() {
            if (confirm('Are you sure you want to clear all clipboard history? This action cannot be undone.')) {
                // Note: This is a web interface, so we can't directly clear the history file
                // Instead, we'll show instructions to the user
                alert('To clear history:\\n\\n1. Use the menu bar app: Click the clipboard icon → View Clipboard History → Clear History\\n2. Or use the terminal: Run "python3 cli_history_viewer.py clear"\\n\\nThen refresh this page.');
            }
        }

        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.key === 'r' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                location.reload();
            }
        });
    </script>
</body>
</html>
"""
    
    return html_content

def open_web_viewer():
    """Create and open web-based history viewer"""
    try:
        # Create HTML content
        html_content = create_html_viewer()
        
        # Create temporary HTML file
        temp_dir = tempfile.mkdtemp()
        html_file = os.path.join(temp_dir, 'clipboard_history.html')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Open in browser
        webbrowser.open(f'file://{html_file}')
        
        print(f"Opened clipboard history viewer in browser")
        print(f"HTML file: {html_file}")
        
        return True
        
    except Exception as e:
        print(f"Error creating web viewer: {e}")
        return False

if __name__ == "__main__":
    open_web_viewer()
