import subprocess
import time
import requests

def adb(cmd):
    return subprocess.run(f"adb {cmd}", shell=True, capture_output=True, text=True).stdout.strip()

print("1. Starting fresh from Onboarding...")
# If currently in ConversationScreen, tap 'छोड़ें' (120, 160)
adb("shell input tap 120 160")
time.sleep(1.0)

# Tap the big glowing microphone on OnboardingScreen (540, 1480)
adb("shell input tap 540 1480")
time.sleep(3.0)

answers = [
    "Ramesh%sKumar",               # Q1: नाम
    "45%ssaal",                    # Q2: उम्र
    "purush",                      # Q3: लिंग
    "Uttar%sPradesh,%sBarabanki",   # Q4: राज्य और ज़िला
    "48000%srupaye",               # Q5: वार्षिक आय
    "OBC",                         # Q6: सामाजिक श्रेणी
    "Kheti%skisan",                # Q7: पेशा/व्यवसाय
    "Nahi",                        # Q8: दिव्यांगता
    "Kheti%saur%spension%ssahayata"# Q9: क्या सहायता चाहिए
]

for idx, ans in enumerate(answers, 1):
    print(f"Entering Q{idx}: {ans}")
    adb("shell input tap 400 1420")
    time.sleep(0.3)
    adb(f"shell input text '{ans}'")
    time.sleep(0.3)
    adb("shell input tap 870 1420")
    if idx == 9:
        print("Q9 submitted! Waiting up to 45s for Stage 2 LangGraph agentic reasoning...")
        # Poll backend logs or wait for the agent to finish
        for sec in range(45):
            time.sleep(1.0)
            if sec % 5 == 0:
                print(f"  Thinking... {sec}s")
    else:
        time.sleep(2.5)

print("Capturing live emulator screen...")
time.sleep(2.0)
adb("shell screencap -p /sdcard/screen_stage2_live.png")
adb("pull /sdcard/screen_stage2_live.png /Users/nikita/.gemini/antigravity/brain/08107605-3fe5-4261-914a-3ab249a1174d/screen_stage2_live.png")
print("Done!")
