Explanation of .plist Keys:

Label: A unique name for your agent.
ProgramArguments: An array where the first string is the executable (your Python interpreter) and subsequent strings are arguments passed to it (your script path).
RunAtLoad: If true, the agent starts when it's loaded by launchd (typically at login).
KeepAlive: If true, launchd will restart your script if it exits unexpectedly.
StandardOutPath: File where standard output (e.g., print() statements, rich logger output) will be redirected.
StandardErrorPath: File where standard error output will be redirected.
WorkingDirectory: Sets the current working directory for your script. This is important for your script to correctly find the modules subdirectory.
EnvironmentVariables:
PYTHONUNBUFFERED: Setting this to 1 is good practice for services, as it ensures that Python's output is not buffered and gets written to the log files more immediately.
3. Ensure Script Dependencies are Met

Your script depends on pyperclip, rich, and pyobjc-framework-Cocoa. The Python interpreter specified in the .plist file must have access to these libraries.

If you used a virtual environment, ensure the Python path in the .plist points to the Python executable inside that venv. The libraries installed in that venv will then be available.
If you installed these libraries globally for a specific Python interpreter, ensure that's the interpreter you're using.
4. Load and Start the LaunchAgent

Open Terminal and run the following commands:

Load the agent: This tells launchd to recognize your .plist file.

bash
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
If RunAtLoad is true, this command will also attempt to start the agent.

To manually start it (if needed, or for testing):

bash
launchctl start com.omairaslam.clipboardmonitor
Your script should now be running in the background. It will also start automatically the next time you log in.

5. Checking Logs and Status

Logs: You can check the output and error logs you defined:
bash
tail -f ~/Library/Logs/ClipboardMonitor.out.log
tail -f ~/Library/Logs/ClipboardMonitor.err.log
List loaded agents (to see if yours is listed):
bash
launchctl list | grep omairaslam
6. Stopping and Unloading the LaunchAgent

To stop the agent temporarily (it will restart if KeepAlive is true, or at next load):

bash
launchctl stop com.omairaslam.clipboardmonitor
To unload the agent (stops it and prevents it from loading at next login):

bash
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
If you make changes to your .plist file, you'll need to unload and then load it again for the changes to take effect.

By following these steps, your clipboard monitor will run reliably as a background service on your Mac. Remember to replace placeholder paths with your actual system paths!