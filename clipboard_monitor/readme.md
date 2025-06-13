# Clipboard Monitor for macOS

A Python script that monitors the macOS clipboard for changes and logs them. This script is designed to run as a background service using `launchd`.

## Prerequisites

*   macOS
*   Python 3.x
*   pip (Python package installer)

## Installation

1.  **Clone the Repository (Optional)**
    If you've cloned this project from a Git repository:
    ```bash
    git clone <repository-url>
    cd clipboard-monitor # Or your project directory
    ```

2.  **Install Dependencies**
    This script requires the following Python libraries:
    *   `pyperclip`
    *   `rich`
    *   `pyobjc-framework-Cocoa`

    It's highly recommended to use a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install pyperclip rich pyobjc-framework-Cocoa
    ```
    Alternatively, you can create a `requirements.txt` file with the dependencies:
    ```
    pyperclip
    rich
    pyobjc-framework-Cocoa
    ```
    And then install them using:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration: Setting up the LaunchAgent

To run the clipboard monitor script as a background service, you need to create a `.plist` file in `~/Library/LaunchAgents/`.

1.  **Create the `.plist` file:**
    Create a file named `com.omairaslam.clipboardmonitor.plist` (you can customize the label, but ensure it's unique) in `~/Library/LaunchAgents/` with the following content.

    **Important:** You **must** replace the placeholder paths in the XML below with the correct absolute paths for your system.
    *   Update `/path/to/your/venv/bin/python` to the absolute path of your Python interpreter. If you're using a virtual environment (recommended), this will be something like `/Users/your_username/path/to/your/project/venv/bin/python`. If using a system Python, it might be `/usr/bin/python3` or `/usr/local/bin/python3`.
    *   Update `/path/to/your/project/clipboard_monitor_script.py` to the absolute path of your main Python script.
    *   Update `/path/to/your/project/` for `WorkingDirectory` to the absolute path of the directory containing your script.
    *   The log file paths `~/Library/Logs/ClipboardMonitor.out.log` and `~/Library/Logs/ClipboardMonitor.err.log` use `~` to refer to the current user's home directory. `launchd` typically resolves this correctly. Ensure the `~/Library/Logs` directory exists and is writable by your user.

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.omairaslam.clipboardmonitor</string> <!-- Must be unique. Convention: reverse domain name. -->

        <key>ProgramArguments</key>
        <array>
            <!-- IMPORTANT: Replace with the ABSOLUTE path to your Python interpreter -->
            <string>/path/to/your/venv/bin/python</string>
            <!-- IMPORTANT: Replace with the ABSOLUTE path to your script -->
            <string>/path/to/your/project/clipboard_monitor_script.py</string>
        </array>

        <key>RunAtLoad</key>
        <true/> <!-- Start the agent when it's loaded (e.g., at login) -->

        <key>KeepAlive</key>
        <true/> <!-- Restart the agent if it exits unexpectedly -->

        <!-- Log paths. Ensure ~/Library/Logs is writable. -->
        <key>StandardOutPath</key>
        <string>~/Library/Logs/ClipboardMonitor.out.log</string>

        <key>StandardErrorPath</key>
        <string>~/Library/Logs/ClipboardMonitor.err.log</string>

        <!-- IMPORTANT: Replace with the ABSOLUTE path to your script's working directory -->
        <key>WorkingDirectory</key>
        <string>/path/to/your/project/</string>

        <key>EnvironmentVariables</key>
        <dict>
            <key>PYTHONUNBUFFERED</key>
            <string>1</string> <!-- Ensures Python output is not buffered -->
        </dict>
    </dict>
    </plist>
    ```

2.  **Explanation of `.plist` Keys:**
    *   `Label`: A unique name for your agent (e.g., `com.yourusername.clipboardmonitor`).
    *   `ProgramArguments`: An array where the first string is the executable (your Python interpreter) and subsequent strings are arguments passed to it (your script path).
    *   `RunAtLoad`: If `true`, the agent starts when it's loaded by `launchd` (typically at login).
    *   `KeepAlive`: If `true`, `launchd` will restart your script if it exits unexpectedly.
    *   `StandardOutPath`: File where standard output (e.g., `print()` statements, `rich` logger output) will be redirected.
    *   `StandardErrorPath`: File where standard error output will be redirected.
    *   `WorkingDirectory`: Sets the current working directory for your script. This is important for your script to correctly find relative paths, like a `modules` subdirectory if you have one.
    *   `EnvironmentVariables`:
        *   `PYTHONUNBUFFERED`: Setting this to `1` is good practice for services, as it ensures that Python's output is not buffered and gets written to the log files more immediately.

3.  **Ensure Script Dependencies are Met by the Interpreter:**
    The Python interpreter specified in the `.plist` file (`ProgramArguments`) must have access to the required libraries (`pyperclip`, `rich`, `pyobjc-framework-Cocoa`).
    *   **Virtual Environment:** If you used a virtual environment for installing dependencies (recommended), ensure the `ProgramArguments` path points to the Python executable *inside* that `venv` (e.g., `/path/to/your/project_directory/venv/bin/python`). The libraries installed in that `venv` will then be available.
    *   **Global/System Python:** If you installed these libraries globally for a specific Python interpreter, ensure that's the interpreter you're using in the `.plist`.

## Running the Service

Once the `.plist` file is configured and saved in `~/Library/LaunchAgents/`:

1.  **Load the Agent:**
    Open Terminal and run:
    ```bash
    launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
    ```
    If `RunAtLoad` is `true` in your `.plist`, this command will also attempt to start the agent.

2.  **Manually Start (if needed):**
    To manually start it for testing or if `RunAtLoad` was initially `false`:
    ```bash
    launchctl start com.omairaslam.clipboardmonitor
    ```
    Your script should now be running in the background and will start automatically on login (if `RunAtLoad` is `true`).

## Checking Logs and Status

*   **View Logs:**
    You can monitor the output and error logs defined in your `.plist` file:
    ```bash
    tail -f ~/Library/Logs/ClipboardMonitor.out.log
    tail -f ~/Library/Logs/ClipboardMonitor.err.log
    ```
    (Adjust paths if you changed them from the defaults in the `.plist`.)

*   **Check Agent Status:**
    To see if your agent is loaded and its status (e.g., PID if running):
    ```bash
    launchctl list | grep com.omairaslam.clipboardmonitor # Replace with your Label or part of it
    ```

## Managing the Service

*   **Stop the Agent Temporarily:**
    (If `KeepAlive` is `true`, `launchd` might try to restart it. If `RunAtLoad` is `true`, it will start on next login.)
    ```bash
    launchctl stop com.omairaslam.clipboardmonitor
    ```

*   **Unload the Agent (Stop and Prevent Autostart):**
    This stops the agent and prevents it from loading at the next login.
    ```bash
    launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
    ```

*   **Applying Changes:**
    If you make changes to your `.plist` file or the Python script itself, you'll generally need to unload and then load the agent again for the changes to take effect:
    ```bash
    launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
    launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
    # You might need to manually start it again if RunAtLoad was false or for immediate effect
    # launchctl start com.omairaslam.clipboardmonitor
    ```

## Troubleshooting Tips

*   **Check Paths:** The most common issue. Double-check all absolute paths in your `.plist` file: Python interpreter, script path, and working directory.
*   **Permissions:** Ensure your Python script is executable (`chmod +x /path/to/your/script.py`). Also, ensure the directory for log files (`~/Library/Logs/`) is writable by your user.
*   **Python Environment:** Verify that the Python interpreter specified in the `.plist` can run your script and import all required modules. Test this directly from the terminal:
    ```bash
    /path/to/your/venv/bin/python /path/to/your/project/clipboard_monitor_script.py
    ```
    (Replace with your actual paths). Check for any import errors.
*   **System Logs:** For more in-depth `launchd` issues, open the Console app (Applications > Utilities > Console) and search for messages related to your agent's label.
*   **Typos in `.plist`:** XML is picky. Ensure your `.plist` file is well-formed.

By following these steps, your clipboard monitor should run reliably as a background service on your Mac.

---
*Remember to replace all placeholder paths and `com.omairaslam.clipboardmonitor` (if you chose a different label) with your actual values.*

```

This `README.md` should provide a much better experience for anyone (including your future self!) looking to understand, set up, and run your clipboard monitor project, especially if it's hosted on GitHub.
