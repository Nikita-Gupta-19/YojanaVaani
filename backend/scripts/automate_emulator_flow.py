import subprocess
import time
import requests

def run_adb(cmd):
    full_cmd = f"/Users/nikita/Library/Android/sdk/platform-tools/adb {cmd}"
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

print("1. Scrolling down on Onboarding...")
run_adb("shell input swipe 540 1800 540 800 300")
time.sleep(0.5)

print("2. Tapping 'बातचीत शुरू करें'...")
run_adb("shell input tap 540 2010")
time.sleep(2.5)

# 9 Savitri Devi Answers
answers = [
    "Savitri%sDevi",
    "59%ssaal",
    "Mahila",
    "Uttar%sPradesh,%sSonbhadra",
    "45000%srupaye",
    "ST",
    "Kheti%saur%smazdoori",
    "45%spratishat%sdivyangta",
    "Pension,%smedical%saur%spakka%sghar%ssahayata"
]

for idx, ans in enumerate(answers, 1):
    print(f"Entering Q{idx}: {ans}")
    run_adb("shell input tap 350 1640")
    time.sleep(0.5)
    run_adb(f"shell input text '{ans}'")
    time.sleep(0.5)
    # Tap the orange 'भेजें' button
    run_adb("shell input tap 920 1640")
    if idx == 9:
        print("Waiting 6s for Stage 2 agentic reasoning & schemes matching...")
        time.sleep(6.0)
    else:
        time.sleep(2.0)

print("Taking final screenshot of Results screen...")
run_adb("exec-out screencap -p > /tmp/results_screen_live.png")
subprocess.run("cp /tmp/results_screen_live.png /Users/nikita/.gemini/antigravity/brain/41b5ff46-f9c1-4ea7-8c78-a708cad079cc/results_screen_live.png", shell=True)
print("Done!")

