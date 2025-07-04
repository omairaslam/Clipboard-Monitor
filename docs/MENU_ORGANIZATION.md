# Menu Bar Organization

This document outlines the new, reorganized menu structure for the Clipboard Monitor menu bar application. The goal of this reorganization is to improve usability and provide a more logical grouping of settings and actions.

## Main Menu Structure

The main menu is organized into the following sections, separated by horizontal lines:

1.  **Status & Service Control**: At-a-glance status and core service controls.
2.  **History & Modules**: Access to clipboard history and module management.
3.  **Preferences**: All user-configurable settings.
4.  **Application**: Logs and quit option.

---

### 1. Status & Service Control

-   **Status**: Displays the current status of the monitoring service (e.g., "Running (Enhanced)", "Paused", "Stopped").
-   **Pause/Resume Monitoring**: Toggles clipboard monitoring without stopping the service.
-   **Service Control**:
    -   Start Service
    -   Stop Service
    -   Restart Service

### 2. History & Modules

-   **Recent Clipboard Items**: A dynamic list of the most recent clipboard entries for quick access.
-   **View Clipboard History**:
    -   Open in Browser
    -   Open in Terminal
    -   Clear History
-   **Modules**:
    -   Enable/disable individual processing modules (e.g., Markdown, Mermaid, Draw.io).

### 3. Preferences

The "Preferences" menu is now organized into logical sub-menus:

-   **General Settings**:
    -   Debug Mode
    -   Set Notification Title...
    -   Polling Interval
    -   Enhanced Check Interval
-   **History Settings**:
    -   Set Max History Items...
    -   Set Max Content Length...
    -   Set History Location...
-   **Module Settings**:
    -   **Draw.io Settings**:
        -   Copy URL
        -   Open in Browser
        -   **URL Parameters** (Submenu):
            -   Lightbox (Toggle)
            -   Edit Mode (Submenu: e.g., New Tab (_blank))
            -   Layers Enabled (Toggle)
            -   Navigation Enabled (Toggle)
            -   Appearance (Submenu: Auto/Light/Dark)
            -   Link Behavior (Submenu: Auto/New Tab/Same Tab)
            -   Set Border Color... (Text Input)
    -   **Mermaid Settings**:
        -   Copy URL
        -   Open in Browser
        -   **Editor Theme** (Submenu: Default/Dark/Forest/Neutral)
-   **Advanced Settings**:
    -   **Performance Settings**:
        -   Lazy Module Loading
        -   Adaptive Checking
        -   Memory Optimization
        -   Process Large Content
        -   Set Max Execution Time...
    -   **Security Settings**:
        -   Sanitize Clipboard
        -   Set Max Clipboard Size...
        -   **Clipboard Modification** (Submenu - MOVED HERE):
            -   Markdown Modify Clipboard
            -   Code Formatter Modify Clipboard
    -   **Configuration**:
        -   Reset to Defaults
        -   Export Configuration...
        -   Import Configuration...
        -   View Current Configuration

### 4. Application

-   **Logs**:
    -   View Output Log
    -   View Error Log
    -   Clear Logs
-   **Quit**: Exits the menu bar application.

---

This new structure groups related items together, making it easier for users to find the settings and actions they need. The "Preferences" menu, in particular, is now much cleaner and more intuitive.