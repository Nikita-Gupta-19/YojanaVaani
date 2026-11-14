#!/usr/bin/env bash
set -e

echo "=== YojanaVaani Phone Installer ==="

# Check ADB
if ! command -v adb &> /dev/null; then
  export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"
fi

# List connected devices
DEVICES=$(adb devices | grep -v "List" | grep "device$" | awk '{print $1}')
PHYSICAL_DEVICE=""

for dev in $DEVICES; do
  if [[ "$dev" != emulator* ]]; then
    PHYSICAL_DEVICE="$dev"
    break
  fi
done

if [ -z "$PHYSICAL_DEVICE" ]; then
  echo ""
  echo "⚠️ No physical Android phone detected!"
  echo "Please connect your Android phone via USB cable and ensure:"
  echo "  1. Developer Options is enabled (Settings > About Phone > tap 'Build Number' 7 times)."
  echo "  2. 'USB Debugging' is switched ON."
  echo "  3. Accept the 'Allow USB Debugging?' prompt on your phone screen."
  echo ""
  echo "Currently connected devices:"
  adb devices
  exit 1
fi

echo "✓ Found physical Android phone: $PHYSICAL_DEVICE"

echo "1. Forwarding backend port 8000 over USB..."
adb -s "$PHYSICAL_DEVICE" reverse tcp:8000 tcp:8000
adb -s "$PHYSICAL_DEVICE" reverse tcp:8081 tcp:8081

APK_PATH="mobile/android/app/build/outputs/apk/debug/app-debug.apk"
if [ ! -f "$APK_PATH" ]; then
  echo "Building APK..."
  (cd mobile/android && ./gradlew assembleDebug)
fi

echo "2. Installing YojanaVaani APK onto phone..."
adb -s "$PHYSICAL_DEVICE" install -r "$APK_PATH"

echo "3. Granting Microphone & Camera permissions..."
adb -s "$PHYSICAL_DEVICE" shell pm grant com.mobile android.permission.RECORD_AUDIO || true
adb -s "$PHYSICAL_DEVICE" shell pm grant com.mobile android.permission.CAMERA || true

echo "4. Launching YojanaVaani on phone..."
adb -s "$PHYSICAL_DEVICE" shell am force-stop com.mobile
adb -s "$PHYSICAL_DEVICE" shell am start -n com.mobile/.MainActivity

echo "=== Success! App is running on your phone! ==="

