#!/bin/bash

# Code Signing Script for Clipboard Monitor
# This will sign the app to avoid macOS security detection

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_BUNDLE="Clipboard Monitor.app"
DEVELOPER_ID="Developer ID Application: YOUR_NAME (TEAM_ID)"

print_status() {
    echo -e "${BLUE}📝 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🔐 Code Signing Clipboard Monitor"
echo "================================="
echo ""

# Check if app exists
if [ ! -d "$APP_BUNDLE" ]; then
    print_error "App bundle not found: $APP_BUNDLE"
    exit 1
fi

# Check for Developer ID
print_status "Checking for Developer ID certificates..."
AVAILABLE_CERTS=$(security find-identity -v -p codesigning | grep "Developer ID Application" || true)

if [ -z "$AVAILABLE_CERTS" ]; then
    print_error "No Developer ID Application certificates found"
    echo ""
    echo "To fix this:"
    echo "1. Join Apple Developer Program ($99/year)"
    echo "2. Create certificates in Apple Developer portal"
    echo "3. Download and install certificates in Keychain"
    echo ""
    echo "Alternative: Create a self-signed certificate for testing:"
    echo "1. Open Keychain Access"
    echo "2. Certificate Assistant > Create a Certificate"
    echo "3. Name: 'Developer ID Application: Your Name'"
    echo "4. Identity Type: Self Signed Root"
    echo "5. Certificate Type: Code Signing"
    echo ""
    exit 1
else
    echo "Available certificates:"
    echo "$AVAILABLE_CERTS"
    echo ""
fi

# Get the first available certificate
CERT_NAME=$(echo "$AVAILABLE_CERTS" | head -1 | sed 's/.*") \(.*\)/\1/')
print_status "Using certificate: $CERT_NAME"

# Sign all executables in the app bundle
print_status "Signing executables..."

# Find and sign all executables
find "$APP_BUNDLE" -type f -perm +111 -exec file {} \; | grep -E "(Mach-O|executable)" | cut -d: -f1 | while read executable; do
    echo "Signing: $executable"
    codesign --force --sign "$CERT_NAME" --timestamp --options runtime "$executable"
done

# Sign the main app bundle
print_status "Signing main app bundle..."
codesign --force --sign "$CERT_NAME" --timestamp --options runtime "$APP_BUNDLE"

# Verify signature
print_status "Verifying signature..."
codesign --verify --verbose "$APP_BUNDLE"
spctl --assess --verbose "$APP_BUNDLE"

print_success "Code signing completed!"

echo ""
echo "🚀 NEXT STEPS:"
echo "=============="
echo ""
echo "1. 📦 For distribution, you should also notarize:"
echo "   - Create a DMG with the signed app"
echo "   - Submit to Apple for notarization"
echo "   - Staple the notarization ticket"
echo ""
echo "2. 🧪 Test the signed app:"
echo "   - Try installing with the original install script"
echo "   - Should no longer trigger security warnings"
echo ""
echo "3. 🔄 If still having issues:"
echo "   - Use the manual installation method"
echo "   - Consider renaming the app to avoid suspicious keywords"
echo ""

echo "Press any key to continue..."
read -n 1 -s
