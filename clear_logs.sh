#!/bin/bash
# Clear All Clipboard Monitor Log Files

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo -e "${YELLOW}${ICON_TRASH} Clearing all log files...${NC}"

all_cleared=true
for log_file in "${LOG_FILES[@]}"; do
    full_path="$LOG_DIR/$log_file"
    if [ -f "$full_path" ]; then
        truncate -s 0 "$full_path" &> /dev/null
        echo -e "  ${GREEN}${ICON_SUCCESS} Cleared: $log_file${NC}"
    else
        # This is not an error, just informational
        echo -e "  ${YELLOW}Skipped (not found): $log_file${NC}"
    fi
done

echo ""
echo -e "${GREEN}${ICON_SUCCESS} All log files have been cleared.${NC}"