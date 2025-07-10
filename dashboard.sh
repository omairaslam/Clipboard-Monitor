#!/bin/bash
# Interactive Dashboard for Clipboard Monitor

# Source the shared configuration and other scripts
source "$(dirname "$0")/_config.sh"

# Function to display the main menu
display_menu() {
    clear
    echo -e "${YELLOW}📋 Clipboard Monitor Dashboard${NC}"
    echo "--------------------------------------------------"
    # Display current service status by running the status script
    bash "$(dirname "$0")/status_services.sh"
    
    echo -e "${YELLOW}Log Files:${NC}"
    echo "  1. Tail Main Output Log (${LOG_DIR}/${LOG_FILES[0]})"
    echo "  2. Tail Main Error Log  (${LOG_DIR}/${LOG_FILES[1]})"
    echo "  3. Tail Menu Bar Output Log (${LOG_DIR}/${LOG_FILES[2]})"
    echo "  4. Tail Menu Bar Error Log  (${LOG_DIR}/${LOG_FILES[3]})"
    echo ""
    echo -e "${YELLOW}Service Controls:${NC}"
    echo "  [s] Start All   [t] Stop All   [r] Restart All"
    echo ""
    echo -e "${YELLOW}Management:${NC}"
    echo "  [c] Clear All Logs"
    echo "  [q] Quit"
    echo "--------------------------------------------------"
}

# Main loop
while true; do
    display_menu
    read -p "Enter your choice: " choice

    case $choice in
        1)
            clear
            echo "Tailing Main Output Log... (Press Ctrl+C to return to dashboard)"
            trap 'echo "Returning to dashboard..."; sleep 1' INT
            tail -f "${LOG_DIR}/${LOG_FILES[0]}"
            trap - INT # Reset trap
            ;;
        2)
            clear
            echo "Tailing Main Error Log... (Press Ctrl+C to return to dashboard)"
            trap 'echo "Returning to dashboard..."; sleep 1' INT
            tail -f "${LOG_DIR}/${LOG_FILES[1]}"
            trap - INT
            ;;
        3)
            clear
            echo "Tailing Menu Bar Output Log... (Press Ctrl+C to return to dashboard)"
            trap 'echo "Returning to dashboard..."; sleep 1' INT
            tail -f "${LOG_DIR}/${LOG_FILES[2]}"
            trap - INT
            ;;
        4)
            clear
            echo "Tailing Menu Bar Error Log... (Press Ctrl+C to return to dashboard)"
            trap 'echo "Returning to dashboard..."; sleep 1' INT
            tail -f "${LOG_DIR}/${LOG_FILES[3]}"
            trap - INT
            ;;
        s|S)
            clear
            bash "$(dirname "$0")/start_services.sh"
            read -p "Press Enter to continue..."
            ;;
        t|T)
            clear
            bash "$(dirname "$0")/stop_services.sh"
            read -p "Press Enter to continue..."
            ;;
        r|R)
            clear
            bash "$(dirname "$0")/restart_services.sh"
            read -p "Press Enter to continue..."
            ;;
        c|C)
            clear
            bash "$(dirname "$0")/clear_logs.sh"
            read -p "Press Enter to continue..."
            ;;
        q|Q)
            echo "Exiting dashboard."
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            sleep 1
            ;;
    esac
done