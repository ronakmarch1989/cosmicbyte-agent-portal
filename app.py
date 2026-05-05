import streamlit as st
import anthropic
import json
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cosmic Byte — Agent Test Portal",
    page_icon="🎮",
    layout="centered"
)

# ─────────────────────────────────────────────
#  STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { max-width: 700px; margin: 0 auto; }
    .stTextArea textarea { font-size: 14px; }
    .score-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 14px;
        line-height: 1.6;
    }
    .score-good {
        background: rgba(74, 222, 128, 0.15);
        border-left: 3px solid #4ade80;
        color: inherit;
    }
    .score-ok {
        background: rgba(234, 179, 8, 0.15);
        border-left: 3px solid #eab308;
        color: inherit;
    }
    .score-weak {
        background: rgba(248, 113, 113, 0.15);
        border-left: 3px solid #f87171;
        color: inherit;
    }
    h1 { font-size: 2rem !important; }
    .stProgress > div > div { background-color: #c8410a; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ANTHROPIC CLIENT
# ─────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# ─────────────────────────────────────────────
#  PRODUCTS & QUESTIONS
#  To add a new product: copy one PRODUCTS entry
#  and fill in id, name, category, description,
#  and questions list. Set available=True when ready.
# ─────────────────────────────────────────────
PRODUCTS = [
    {
        "id": "lumora",
        "name": "Lumora",
        "category": "Controller",
        "description": "Tri-mode wireless controller with Hall Effect sensors, gyro and RGB.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity",
                "scenario": "A new customer just unboxed their Lumora and asks: 'What are the different ways I can connect this controller to my PC?'",
                "question": "Explain all connection options on the Lumora and when you would recommend each one.",
                "rubric": "Must mention: 2.4GHz wireless dongle (best for PC, lowest latency), Bluetooth (phones/tablets/Mac up to 8m range), Wired USB-C (1000Hz polling, charges while playing). Strong answers also mention software only works on 2.4GHz or wired, not Bluetooth."
            },
            {
                "tag": "Platform compatibility",
                "scenario": "A frustrated customer says: 'I bought this controller to use on my PS5 and Xbox. Neither detects it. What are the pairing steps?'",
                "question": "How do you respond to this customer?",
                "rubric": "Must clearly state Lumora is PC-only, NOT compatible with PS5, Xbox or Nintendo Switch. No warranty for console use. Should be polite but firm. Must NOT provide console pairing steps."
            },
            {
                "tag": "Auto button press",
                "scenario": "A customer calls: 'My X button keeps pressing itself super fast repeatedly. The controller is brand new. Is it broken?'",
                "question": "Walk through your diagnosis and how you resolve this for the customer.",
                "rubric": "Should identify Turbo mode as most likely cause, accidentally enabled via Turbo+X. Fix: press Turbo+X again to disable, or hold Turbo+Start for 2 seconds to clear all turbo. Must rule this out before suggesting a warranty claim."
            },
            {
                "tag": "Gyro setup",
                "scenario": "A customer says: 'I want to use gyro in my shooting game but it doesn't officially support gyro. Is there any way?'",
                "question": "Explain how to set up gyro and make it work in games that don't natively support it.",
                "rubric": "Should mention: connect via Wired or 2.4GHz, open Cosmic Byte software, assign gyro to a button, choose mode (Always On / Press to Activate / Toggle). Key point: gyro mimics joystick so works in ANY game even without native gyro support."
            },
            {
                "tag": "Firmware update",
                "scenario": "A customer says their controller is behaving oddly and asks how to update the firmware.",
                "question": "Walk the customer through the complete firmware update process step by step.",
                "rubric": "Steps: (1) Uninstall existing Cosmic Byte software first. (2) Download latest from thecosmicbyte.com. (3) Connect via USB-C wired mode. (4) Install — firmware flashes automatically. Must mention wired mode is required."
            },
            {
                "tag": "D-pad and joystick swapped",
                "scenario": "A customer says: 'My D-pad and joystick have swapped — joystick moves camera, D-pad moves character. I never changed anything.'",
                "question": "What is the likely cause and how do you fix it?",
                "rubric": "Correct cause: joystick/D-pad swap setting in Cosmic Byte software, toggled accidentally. Fix: open software, find swap setting, toggle back to default. Should NOT blame DInput/XInput for this symptom."
            },
            {
                "tag": "Dongle disconnections",
                "scenario": "Controller disconnects every few minutes. Dongle is at the back of the tower, next to a Wi-Fi router and USB 3.0 hard drive, about 4 meters away.",
                "question": "Diagnose what is causing the disconnections and tell the customer exactly what to do.",
                "rubric": "Should identify all three: (1) Dongle at back of tower — poor line of sight, move to front USB port. (2) USB 3.0 devices cause 2.4GHz interference. (3) Wi-Fi router shares 2.4GHz band. Range should stay under 7-10 meters."
            },
            {
                "tag": "Battery and charging",
                "scenario": "Customer asks: 'How do I check battery mid-game without stopping?' and 'My controller stopped charging — I am using a 65W fast charger.'",
                "question": "Answer both of the customer's questions completely.",
                "rubric": "Battery check: press Macro+RB — LED: Red=1-25%, Yellow=26-50%, Blue=51-75%, Green=76-100%. Charging: 65W fast chargers above 10W cause issues. Use PC USB port or 5V/1A adapter. Check cable supports data and power."
            },
            {
                "tag": "Software and input modes",
                "scenario": "Two issues: (1) Cosmic Byte software says no controller detected even though it works in games. (2) An old 2008 game does not detect the controller at all.",
                "question": "Solve both problems and explain why each is happening.",
                "rubric": "Issue 1: Software only works in Wired or 2.4GHz — NOT Bluetooth. Switch mode. Issue 2: Old games need DInput. Hold Back+Start 3 seconds to switch from XInput (Yellow LED) to DInput (Red LED), then relaunch the game."
            },
            {
                "tag": "Warranty and reset",
                "scenario": "Customer tried everything to fix erratic behavior. Asks if reset will delete macros. Also dropped controller cracking the shell and asks if that is covered under warranty.",
                "question": "Guide them through the reset, answer the macro question, and explain the warranty situation.",
                "rubric": "Reset: insert pin into RESET hole on back, hold 2 seconds, re-pair. Macros NOT deleted — only pairing data clears. Warranty: 1 year manufacturing defects only. Physical damage from dropping is NOT covered."
            }
        ]
    },
    # ── ADD NEW PRODUCTS BELOW ──────────────────
    {
        "id": "ares",
        "name": "Ares",
        "category": "Controller",
        "description": "Tri-mode wireless controller with 2.4GHz, Bluetooth 5.0 and Wired USB-C. Supports PC (Windows), Android (OTG) and iOS (MFI games). 2026 manufacturing batch features 1000Hz polling rate — older models cannot be upgraded to 1000Hz.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity modes and LED indicators",
                "scenario": "A new customer just unboxed their Ares and asks: 'How do I connect this to my PC with the dongle? Also how do I connect via Bluetooth to my Android phone and my iPhone? And how do I know which mode I am in?'",
                "question": "Explain all three connection methods on the Ares and what each LED colour means.",
                "rubric": "Four LED colours: Orange=XInput PC, Red=DirectInput PC, Green=Android, Blue=iOS. 2.4GHz wireless dongle (recommended for PC): plug dongle into PC, press and hold Home for 3 seconds to power on, controller vibrates once and LED blinks, when connected LED stays solid. Wired USB-C: connect cable to PC, Windows auto-detects and installs drivers, defaults to XInput. Bluetooth Android: hold A+Home for 3 seconds, Green LED confirms pairing, requires OTG support. Bluetooth iOS: hold B+Home for 3 seconds, Blue LED confirms pairing, supports MFI-enabled games only. Bluetooth PC XInput: hold X+Home for 3 seconds, Orange LED confirms pairing. Must mention clear line of sight between controller and dongle for best 2.4GHz performance."
            },
            {
                "tag": "Platform compatibility and console warning",
                "scenario": "A frustrated customer says: 'I bought the Ares to use on my PS5 and Xbox Series X. Neither detects the controller at all. What pairing steps do I follow?'",
                "question": "How do you respond to this customer?",
                "rubric": "Must clearly and politely state: the Ares is designed exclusively for Windows PC use. It is NOT compatible with PlayStation, Xbox, Nintendo Switch or any gaming console. No warranty or support is provided for console usage. Android support is limited and also not covered under warranty. Should NOT provide any console pairing steps. Must be polite but firm and honest. Can suggest the customer verify compatibility before purchasing in future."
            },
            {
                "tag": "XInput vs DirectInput — old game",
                "scenario": "A customer says: 'I connected the Ares via the 2.4GHz dongle on my PC. Windows sees it fine but my old 2004 game completely ignores the controller.'",
                "question": "Diagnose the issue and walk the customer through the fix on the Ares.",
                "rubric": "Old games only support DirectInput (DInput). The Ares defaults to XInput (Orange LED) in dongle or wired mode. To switch between XInput and DInput in dongle or wired mode: press Back+Start together for 3 seconds. Orange LED = XInput, Red LED = DirectInput. Customer must relaunch the game after switching. Pressing Back+Start again for 3 seconds toggles back to XInput."
            },
            {
                "tag": "Turbo and auto turbo setup",
                "scenario": "A customer says: 'My A button keeps pressing itself super fast on its own. Also how do I set up Auto Turbo so a button fires continuously without me holding it? And how do I cancel both?'",
                "question": "Diagnose the auto-press, explain how turbo and auto turbo work, and how to cancel each.",
                "rubric": "Auto-press cause: Turbo accidentally enabled on A button by holding A then pressing Turbo. Fix: repeat same procedure — hold A then press Turbo — to cancel. Turbo works on A, B, X, Y, L1, L2, R1, R2. Turbo (manual hold required): hold the desired button then press Turbo button. Cancel: repeat same procedure. Auto Turbo (fires continuously without holding): hold desired button then press Auto button. Cancel: repeat same procedure. Auto Turbo fires the button repeatedly without the customer needing to hold anything. Speed adjustment: press Turbo+Right Joystick Up to increase speed, Turbo+Right Joystick Down to decrease speed. Always rule out Turbo before suggesting hardware defect."
            },
            {
                "tag": "D-pad 4-way and 8-way modes",
                "scenario": "A customer who plays fighting games says: 'My D-pad keeps registering diagonal inputs when I only want to go left, right, up or down. Is there a setting to stop the diagonals?'",
                "question": "Explain the D-pad input modes on the Ares and how to switch between them.",
                "rubric": "The Ares supports two D-pad modes. 8-Way mode (default): allows all 8 directional inputs including diagonals. 4-Way mode: only registers pure directional inputs — up, down, left, right — eliminates accidental diagonals, best for fighting and platformer games. To toggle between 4-Way and 8-Way: hold the Up D-pad button then press the Back button. Repeat to toggle back. No software needed."
            },
            {
                "tag": "Joystick and D-pad swap",
                "scenario": "A customer says: 'In my game the left joystick controls the character movement but I want to use the D-pad for movement instead. Can I swap them on the Ares?'",
                "question": "Explain how to swap the joystick and D-pad functions on the Ares.",
                "rubric": "To toggle between left joystick and D-pad functions on the Ares: press L3+Back. This swaps the left joystick and D-pad roles. Pressing L3+Back again toggles them back. Simple toggle, no software needed, works in all connection modes."
            },
            {
                "tag": "LED controls and vibration",
                "scenario": "A customer says: 'The ABXY buttons on my Ares have stopped glowing. Also the vibration seems off — sometimes it works, sometimes it doesn't. How do I control both?'",
                "question": "Explain how to control the ABXY LED and vibration on the Ares.",
                "rubric": "ABXY LED toggle: press X+Back to turn ABXY LEDs on or off. Vibration LED toggle: press A+Back to turn vibration on or off. Vibration strength: press R3+Left Joystick Up to increase, R3+Left Joystick Down to decrease. Important: vibration is automatically disabled when battery is critically low to save power — if vibration suddenly stops, check battery first. Android and iOS do NOT support vibration functions. Game support is also required for vibration to work."
            },
            {
                "tag": "Battery, charging and low battery warnings",
                "scenario": "A customer says: 'How do I know when my Ares is low on battery? Also the LED is flashing slowly — what does that mean? And the vibration has stopped working completely.'",
                "question": "Explain all battery and charging indicators on the Ares and diagnose the vibration issue.",
                "rubric": "Low battery warning: LED flashes slowly — this is the low battery indicator. Charging: LED slowly blinks while charging. Fully charged: LED turns off completely. Critical battery behaviour: controller automatically disables vibration when battery is critically low to save power. This is why vibration has stopped — it is not a defect, just a power-saving feature. Customer needs to charge the controller. Use a standard 5V USB source. Recommend using the included USB-C cable."
            },
            {
                "tag": "Polling rate — 2026 batch",
                "scenario": "A customer says: 'I heard the Ares now has a 1000Hz polling rate. I have an older Ares from about a year ago. Can I update or upgrade mine to get 1000Hz? And what exactly does polling rate affect?'",
                "question": "Explain polling rate, clarify which Ares models have 1000Hz, and be honest about whether older models can be upgraded.",
                "rubric": "Polling rate explanation: polling rate is how often the controller reports its input state to the PC per second. 1000Hz means 1000 reports per second, resulting in 1ms input latency — more responsive and precise. Only the 2026 manufacturing batch of the Ares includes the 1000Hz polling rate upgrade. Older Ares models have a lower polling rate. CRITICAL: older models CANNOT be upgraded to 1000Hz — there is no firmware update, cable, software or any workaround that adds 1000Hz to older hardware. It is a hardware difference. Be honest and clear — do not suggest any workaround. If the customer wants 1000Hz they would need to purchase a new 2026 batch unit."
            },
            {
                "tag": "Controller won't turn on and won't connect",
                "scenario": "A customer says: 'My Ares won't turn on at all. I pressed Home but nothing happens. Also my friend's Ares connected fine to my PC before but mine won't connect via Bluetooth even after pairing.'",
                "question": "Walk the customer through diagnosing and fixing both issues.",
                "rubric": "Won't turn on: ensure battery is charged first — connect via USB-C and charge. To power on: press and hold Home button for 3 seconds. If still not turning on after charging, try reset pin-hole on back. Won't connect via Bluetooth: verify correct pairing mode for the platform — PC XInput=X+Home for 3 seconds (Orange LED), Android=A+Home (Green LED), iOS=B+Home (Blue LED). Ensure Bluetooth is active and visible on the receiving device. Restart the pairing process. Check that the LED is blinking during pairing — solid LED means already connected to another device, which will block new pairing. May need to clear existing Bluetooth pairing from both controller and device before re-pairing."
            },
            {
                "tag": "Reset and troubleshooting unresponsive buttons",
                "scenario": "A customer says: 'Some buttons on my Ares are not responding at all during gameplay. I have restarted the game and reconnected the controller but it still happens. What do I do?'",
                "question": "Walk the customer through diagnosing unresponsive buttons and how to perform a reset on the Ares.",
                "rubric": "Step 1: Check if Turbo or Auto Turbo may have caused unexpected behaviour — disable any turbo assignments. Step 2: check controller is connected properly — LED should be solid, not blinking. Step 3: try switching between XInput and DInput via Back+Start for 3 seconds to see if game responds differently. Step 4: hardware reset — insert a pin into the RESET pin-hole on the back of the controller, hold for 1-2 seconds. This resets the controller without deleting settings. Step 5: re-pair the controller after reset. If issue persists after reset contact Cosmic Byte support — warranty covers manufacturing defects for 1 year. Physical damage and water damage are not covered."
            },
            {
                "tag": "Warranty and what is covered",
                "scenario": "A customer says: 'My Ares stopped working after 8 months. I also accidentally dropped it and the shell has a crack. Will the warranty cover this? And I am also using it on my Android phone — is that covered?'",
                "question": "Explain the Ares warranty coverage honestly and completely.",
                "rubric": "Warranty: 1 year against manufacturing defects only. Physical damage from dropping — including cracked shell — is explicitly NOT covered under warranty. Water damage is also not covered. Tampered products are not covered. Android support: the Ares has limited Android support via OTG, but Android compatibility issues are explicitly not covered under warranty — the controller is classified as a PC-only device. If the controller stopped working due to a genuine manufacturing defect unrelated to the drop, the customer may have a valid claim, but the physical crack complicates matters. Advise customer to contact Cosmic Byte support: +91 7351615161 (Mon-Sat 10am-6pm), WhatsApp: +91 7351615161, email: cc@thecosmicbyte.com. Scan QR code in manual for warranty claim procedure."
            }
        ]
    },
    {
        "id": "nexus",
        "name": "Nexus",
        "category": "Controller",
        "description": "2.4GHz wireless controller powered by 2x AAA batteries. Supports XInput and DirectInput on PC (Windows) and Android (OTG). Dual vibration motors, sensitive triggers, up to 8m wireless range.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity and turning on",
                "scenario": "A customer just unboxed their Nexus and says: 'How do I get this working on my PC? I inserted the batteries but nothing is happening and I cannot see it in Windows.'",
                "question": "Walk the customer through the complete setup process to connect the Nexus to their PC for the first time.",
                "rubric": "Steps in order: (1) Open battery compartment, insert 2x AAA batteries with correct polarity, close securely. (2) Slide the power switch to ON — Green and Red LEDs will flash. (3) Plug the wireless dongle into a USB port on the PC. (4) Once connected successfully, LEDs will remain lit solid (not flashing). (5) Windows 10 is Plug and Play — no drivers needed. If connection fails: try a different USB port, ensure no obstructions between controller and dongle, reinsert dongle and restart PC. Must mention the physical power switch — not just inserting batteries."
            },
            {
                "tag": "LED indicators and mode status",
                "scenario": "A customer asks: 'The lights on my Nexus are confusing me. Sometimes I see green, sometimes red, sometimes both. What does each LED combination mean?'",
                "question": "Explain all LED indicator states on the Nexus and what each one means.",
                "rubric": "Four LED states: Green LED only = XInput mode (PC default). Red LED only = DirectInput mode. Green + Red LEDs both on = PC Analog Mode. LEDs flashing = controller is trying to connect / pairing in progress. LEDs solid = successfully connected. LEDs flashing slowly = low battery. No LEDs = controller is off or battery is dead. Agent must correctly identify all four mode states and the battery/connection states."
            },
            {
                "tag": "XInput vs DirectInput — old game",
                "scenario": "A customer says: 'I connected the Nexus via the wireless dongle. Windows detects it fine and I can see it in Game Controllers, but my old 2003 game completely ignores it. What is wrong?'",
                "question": "Diagnose why the old game is not detecting the Nexus and explain exactly how to fix it.",
                "rubric": "Old games only support DirectInput (Red LED). The Nexus connects to Windows in XInput mode automatically (Green LED). To switch: press and hold the Mode button for more than 5 seconds — this toggles between XInput and DirectInput. Red LED confirms DirectInput is active. Customer must relaunch the game after switching. If still not working, try switching back to XInput and testing again. Always relaunch the game after switching modes."
            },
            {
                "tag": "Platform compatibility and console warning",
                "scenario": "A customer says: 'I want to use my Nexus on my PS4 and Nintendo Switch. How do I pair it to each console?'",
                "question": "How do you respond to this customer?",
                "rubric": "Must clearly and politely state: the Nexus is designed exclusively for Windows PC use. It is NOT compatible with PlayStation, Xbox, Nintendo Switch or any gaming console. No warranty or support is provided for console usage. Android support is available but limited — requires OTG functionality and is not covered under warranty. Should NOT provide any console pairing steps. Be polite but firm. Recommend customer verify compatibility before purchasing in future."
            },
            {
                "tag": "Android connection",
                "scenario": "A customer asks: 'Can I use my Nexus on my Android phone? If yes, how do I connect it?'",
                "question": "Explain how to connect the Nexus to an Android device and what limitations apply.",
                "rubric": "Android connection steps: (1) Ensure Android device is running Android 4.0 or higher. (2) Verify device supports OTG functionality — contact device manufacturer if unsure. (3) Use a compatible OTG cable with the wireless dongle to connect. (4) No additional drivers needed. (5) No mode change required for Android — controller connects automatically. Important limitations: Android compatibility is not covered under warranty. Android support is limited. If connection fails: restart device, try reconnecting, confirm OTG is supported by the device."
            },
            {
                "tag": "Vibration not working",
                "scenario": "A customer says: 'The vibration on my Nexus has completely stopped working. I was playing fine earlier today and now there is no rumble at all.'",
                "question": "Diagnose why vibration has stopped and explain how to fix it.",
                "rubric": "Two most likely causes: (1) Low battery — when battery is low, vibration is automatically disabled to conserve power. Fix: replace both AAA batteries with fresh ones. This is the most common cause. (2) Game compatibility — the game being played may not support vibration feedback. Not all PC games support controller rumble. Fix: test in a game known to support vibration. Always check battery first before assuming hardware fault. The Nexus has dual vibration motors so if both motors stop simultaneously, battery is almost certainly the cause rather than hardware failure."
            },
            {
                "tag": "Controller disconnecting frequently",
                "scenario": "A customer says: 'My Nexus keeps disconnecting every few minutes during gameplay. The dongle is plugged into the back of my desktop tower. I am sitting about 5 meters away.'",
                "question": "Diagnose all possible causes of frequent disconnections and tell the customer exactly what to do.",
                "rubric": "Multiple causes to identify: (1) Signal obstruction — dongle at back of tower has poor line of sight through the case and desk. Move dongle to a front USB port or use a USB extension cable to bring it closer to open space. (2) Distance and interference — 5m is within range but physical barriers reduce effective range. Ensure clear line of sight between controller and dongle. (3) Low battery — replace AAA batteries with fresh ones even if LEDs appear lit. (4) USB port issues — try a different USB port. (5) Other 2.4GHz devices nearby (Wi-Fi routers, other wireless devices) can cause interference. Move dongle away from router. Maximum effective range is 8 meters in open conditions."
            },
            {
                "tag": "Buttons and analog sticks unresponsive",
                "scenario": "A customer says: 'Several buttons on my Nexus are not responding at all in my game. The analog sticks also feel sluggish. The controller is connected and the LED is solid.'",
                "question": "Walk the customer through diagnosing and fixing unresponsive buttons and analog sticks.",
                "rubric": "Diagnostic steps: (1) Check input mode — old games need DirectInput (Red LED), modern games need XInput (Green LED). Hold Mode button 5 seconds to switch. Relaunch game after switching. (2) Test the controller on another game or in Windows Game Controllers (joy.cpl) to rule out hardware issues vs game compatibility. (3) Check for dirt or debris around buttons and analog sticks — clean gently with a dry cloth. Do not use liquids. (4) Check battery — low battery can cause sluggish or intermittent response. Replace AAA batteries. (5) Try reconnecting the dongle to a different USB port. (6) Reinsert dongle and restart PC."
            },
            {
                "tag": "Controller not detected by Windows",
                "scenario": "A customer says: 'My Nexus is not showing up in Windows at all. The LED is solid green so it seems connected but Windows Game Controllers shows nothing.'",
                "question": "Walk the customer through all the steps to get Windows to detect the Nexus.",
                "rubric": "Steps: (1) Ensure Windows 10 is up to date — Nexus is Plug and Play on Windows 10. (2) Disconnect and reconnect the wireless dongle — try a different USB port. (3) Try switching between XInput and DirectInput by holding Mode button 5 seconds, then check again in both Windows Game Controllers and Device Manager. (4) Restart the computer with dongle plugged in. (5) Check Device Manager for any error flags on the controller entry. (6) If solid Green LED means XInput — check Windows Game Controllers (joy.cpl) under XInput devices. DirectInput devices show differently. Note: solid LED confirms wireless connection between controller and dongle but Windows still needs to recognise the USB device from the dongle."
            },
            {
                "tag": "Battery management and storage",
                "scenario": "A customer asks: 'How do I know when my batteries are running low? Also I am going on holiday for 3 weeks and won't use the controller — what should I do with it?'",
                "question": "Explain the low battery indicators and proper storage procedure for the Nexus.",
                "rubric": "Low battery indicators: LED will flash (instead of staying solid) — this is the primary low battery warning. Vibration will also be automatically disabled when battery is low. When either of these happen, replace both AAA batteries immediately with fresh ones for best performance. Storage procedure: (1) Turn off the power switch — slide to OFF. (2) Remove the AAA batteries from the compartment — do not leave batteries in during long periods of non-use as they can leak and damage the controller. (3) Store controller in a dry place within temperature range -10°C to +60°C, humidity 20-80%. Always use fresh batteries when returning to use."
            }
        ]
    },
    {
        "id": "ares_wired",
        "name": "Ares Wired",
        "category": "Controller",
        "description": "USB wired controller for PC. Supports XInput and DirectInput. LED-illuminated ABXY, Turbo/Auto-Turbo, Hall Effect joysticks (2026 batch). Compatible with Windows 7/8/10/11. Plug & Play on Windows 8 and above.",
        "available": True,
        "questions": [
            {
                "tag": "First-time setup and connection",
                "scenario": "A customer just bought the Ares Wired and says: 'I plugged it into my PC but nothing is happening. Windows is not detecting it at all. What do I do?'",
                "question": "Walk the customer through the complete setup process for the Ares Wired on PC.",
                "rubric": "Steps: (1) Plug the USB cable into a USB port — recommended: use the rear USB port on the desktop for more stable power. (2) No driver installation required for Windows 8, 10 and 11 — Plug and Play. Windows 7 may require manual configuration. (3) Controller auto-detects as XInput mode (Blue LED). (4) Check Device Manager under 'Game Controllers' if not detected. (5) If still not detected: try a different USB port, avoid USB hubs, restart PC. (6) Do not use low-quality USB extension cables. Must mention rear USB port recommendation and no drivers needed for Windows 8+."
            },
            {
                "tag": "LED indicators and input modes",
                "scenario": "A customer asks: 'My Ares Wired shows different coloured lights at different times. Blue, Red, Yellow, Green — what does each one mean?'",
                "question": "Explain all LED indicator states on the Ares Wired and what each colour means.",
                "rubric": "Four LED mode states: Blue = XInput mode (default, PC). Red = DirectInput mode. Yellow = PC Analog mode. Green = Android mode. These LEDs indicate the current input protocol the controller is using. Blue is the default when plugged into Windows. Red is needed for older/legacy games. Yellow is PC Analog. Green appears when connected to Android via OTG. Agent must correctly map all four colours to their modes."
            },
            {
                "tag": "XInput vs DirectInput — old game",
                "scenario": "A customer says: 'I plugged in my Ares Wired and Windows detects it fine. But my old 2002 game completely ignores it. I can see it in joy.cpl but the game does not respond to any inputs.'",
                "question": "Diagnose the issue and walk the customer through the fix on the Ares Wired.",
                "rubric": "Old games only support DirectInput (Red LED). The Ares Wired defaults to XInput (Blue LED) on Windows. To switch modes: press and hold the HOME button for 5 seconds — this cycles between XInput and DirectInput. Red LED confirms DirectInput is active. Customer must relaunch the game after switching. If the game still does not respond, switch back and try XInput — some games use XInput despite appearing old. Always relaunch the game after switching modes."
            },
            {
                "tag": "Hall Effect joysticks — 2026 batch",
                "scenario": "A customer says: 'I heard the Ares Wired now has Hall Effect joysticks. My controller is from last year. Does mine have Hall Effect? And what is the difference from normal joysticks?'",
                "question": "Explain Hall Effect joysticks, which Ares Wired models have them, and be honest about older models.",
                "rubric": "Hall Effect explanation: Hall Effect joysticks use magnetic sensors instead of physical contact potentiometers. This means they do not wear out from friction, are highly drift-resistant by design, have longer lifespan, and provide more precise input. The 2026 manufacturing batch of the Ares Wired has been upgraded to Hall Effect joysticks AND Hall Effect analog triggers. Older Ares Wired models have standard joysticks which are more prone to drift over time. IMPORTANT: There is no upgrade path — older hardware cannot be converted to Hall Effect. If a customer has an older model with drift issues, joystick drift from wear is not covered under warranty as it is considered wear and tear. If the customer wants Hall Effect they would need to purchase a 2026 batch unit."
            },
            {
                "tag": "Turbo and Auto Turbo",
                "scenario": "A customer says: 'My A button keeps firing super fast on its own. Also I want to set up Auto Turbo on my X button so it fires repeatedly without me holding it. How does this work and how do I stop the A button?'",
                "question": "Diagnose the auto-firing A button and explain how Turbo and Auto Turbo work on the Ares Wired.",
                "rubric": "Auto-firing A cause: Turbo accidentally enabled on A. Fix: press A then press the Turbo button again to cancel — same process used to enable is used to disable. Turbo (fires fast while held): press desired button (A/B/X/Y/L1/L2/R1/R2) then press Turbo button. To cancel: repeat same process. Auto Turbo (fires continuously without holding): press desired button then press the AUTO button. To cancel: repeat same process. Key distinction: Turbo requires the player to hold the button, Auto Turbo fires on its own without holding. Always rule out Turbo and Auto Turbo before suggesting hardware defect."
            },
            {
                "tag": "LED controls — ABXY and V LED",
                "scenario": "A customer says: 'The glowing ABXY buttons have turned off on my Ares Wired. Also the V-shaped light strip in the middle is also dark. How do I turn them back on?'",
                "question": "Explain how to control both LED groups on the Ares Wired.",
                "rubric": "The Ares Wired has two independent LED groups. ABXY LED: press X+Back to toggle on or off. V LED (the V-shaped centre light strip): press A+Back to toggle on or off. These are completely independent — ABXY can be on while V LED is off and vice versa. Customer simply needs to press the correct combination to toggle each one back on. Note: these are toggle functions so pressing once turns off, pressing again turns on."
            },
            {
                "tag": "Joystick and D-pad swap",
                "scenario": "A customer says: 'In my game I want the D-pad to control my character movement but the left joystick is currently controlling movement and I cannot change it in the game settings. Can I swap them on the controller itself?'",
                "question": "Explain how to swap joystick and D-pad functions on the Ares Wired.",
                "rubric": "To swap left joystick and D-pad functions: press L3+Back button. This switches the function between the left stick and D-pad. Pressing L3+Back again swaps them back. Simple toggle, works immediately, no software needed."
            },
            {
                "tag": "Console compatibility warning",
                "scenario": "A customer says: 'I bought the Ares Wired to use on my PS5. I plugged it in via USB but the PS5 does not detect it at all. Is there a special mode or adapter I can use?'",
                "question": "How do you respond to this customer?",
                "rubric": "Must clearly and politely state: the Ares Wired is strictly designed for PC use only. It is NOT compatible with PlayStation, Xbox, Nintendo Switch or any gaming console. No warranty or support is provided for console usage. Any attempt to use via adapters, converters or third-party tools is also not covered under warranty. Should NOT suggest any workaround or adapter. Be honest and polite — recommend the customer verify compatibility before future purchases. Android support is limited via OTG and also not covered under warranty."
            },
            {
                "tag": "Controller not detected or buttons unresponsive",
                "scenario": "A customer says: 'My Ares Wired was working fine yesterday. Today I plugged it in and Windows shows it in Device Manager but several buttons are not working in my game.'",
                "question": "Walk the customer through diagnosing and fixing both the detection and unresponsive button issues.",
                "rubric": "Step 1: check input mode — switch between XInput and DirectInput by holding HOME for 5 seconds. Blue=XInput for modern games, Red=DirectInput for older games. Relaunch game after switching. Step 2: test in Windows Game Controllers panel (Win+R → joy.cpl) to see if all buttons register outside the game — this isolates whether it is a hardware or game-compatibility issue. Step 3: enable controller in in-game settings — some games require manual controller activation. Step 4: reconnect the controller — unplug and replug. Step 5: try a different USB port (prefer rear port, avoid USB hubs). Step 6: restart PC. Step 7: if still unresponsive, use the reset pinhole on the rear with a pin."
            },
            {
                "tag": "Joystick drift and warranty",
                "scenario": "A customer says: 'My Ares Wired left joystick drifts to the right even when I am not touching it. I have had the controller for about 10 months. Is this a manufacturing defect covered under warranty?'",
                "question": "Explain what is causing the drift, what the customer can try to fix it, and be honest about warranty coverage.",
                "rubric": "Joystick drift diagnosis: (1) Reconnect the controller — sometimes helps with connection-related false drift. (2) Check calibration in Windows: Control Panel → Devices → Game Controller Settings. Recalibrate the joystick. (3) Ensure the stick is not physically damaged or dirty. 2026 batch Ares Wired has Hall Effect joysticks which are drift-resistant by design — if this is a 2026 unit, drift may indicate a genuine defect worth escalating. Older models with standard joysticks: drift after 10 months of use is considered normal wear and tear and is explicitly NOT covered under warranty. The manual states regular wear and tear is not covered. If the controller is within 1 year and the customer believes it is a manufacturing defect (not wear), advise them to contact support and mention the batch. Physical damage is also not covered."
            }
        ]
    },
    {
        "id": "ares_wireless",
        "name": "Ares Wireless",
        "category": "Controller",
        "description": "2.4GHz wireless controller with 700mAh rechargeable battery, Hall Effect joysticks and triggers (2026 batch), RGB LED, dual vibration, Turbo/Auto-Turbo. PC only via USB dongle. Up to 8m range.",
        "available": True,
        "questions": [
            {
                "tag": "First-time setup and connection",
                "scenario": "A customer just unboxed their Ares Wireless and says: 'How do I get this connected to my PC? There is a USB dongle in the box. What do I do?'",
                "question": "Walk the customer through the complete first-time setup process for the Ares Wireless on PC.",
                "rubric": "Steps: (1) Insert USB wireless receiver (dongle) into a USB port on the PC — for best performance use a USB extension cable to position it in open space, away from the back of a tower. (2) Press the Home button to power on the controller. (3) Controller connects automatically in XInput mode (Blue LED stays solid). (4) Plug and Play — no drivers needed. If connection does not establish automatically: check if both controller and dongle LEDs are blinking continuously — this means they need re-pairing. Re-pairing steps: plug receiver into PC, press Home button, then press Home button twice quickly — LEDs stop blinking and controller is paired. Must mention the dongle extension cable tip and the re-pairing procedure."
            },
            {
                "tag": "LED indicators and mode states",
                "scenario": "A customer asks: 'My Ares Wireless shows Blue sometimes, then Red, then Yellow. What do each of these mean? And how do I know if it is actually connected versus just trying to connect?'",
                "question": "Explain all LED indicator states on the Ares Wireless including connection status.",
                "rubric": "Five LED mode states: Blue = XInput mode (default, PC). Red = DirectInput mode. Yellow = PC Analog mode. Green = Android mode. Auto/others = automatic. Connection status: LEDs blinking = controller is trying to connect or needs pairing. LED solid = successfully connected. Low battery: LED flashes and vibration is disabled. Charging: LED blinks slowly. Fully charged: LED turns off. Agent must distinguish between mode LEDs and status LEDs — the same LED shows both mode colour and connection/charging state depending on context."
            },
            {
                "tag": "Re-pairing the dongle",
                "scenario": "A customer says: 'My Ares Wireless was working but now both the controller light and the dongle light are blinking constantly and it will not connect. I tried turning it off and on but nothing works.'",
                "question": "Explain what is happening and walk the customer through re-pairing the controller with the dongle.",
                "rubric": "Blinking on both controller and dongle simultaneously means the pairing between them has been lost — they need to be re-paired. Re-pairing steps: (1) Plug the USB receiver into the PC. (2) Press the Home button on the controller to power on. (3) Press the Home button twice quickly (double-press). (4) LEDs will stop blinking — controller is now paired and connected. This is different from simply turning on — the double-press of Home initiates the pairing handshake. If pairing still fails: try reset pinhole on rear, then repeat pairing steps."
            },
            {
                "tag": "XInput vs DirectInput — old game",
                "scenario": "A customer says: 'My old 2001 game does not detect my Ares Wireless at all via the dongle. Windows sees it fine with a Blue LED but the game ignores it completely.'",
                "question": "Diagnose the issue and explain how to fix it on the Ares Wireless.",
                "rubric": "Old games only support DirectInput (Red LED). The Ares Wireless defaults to XInput (Blue LED). To switch: press and hold the HOME button for 5 seconds — this cycles between XInput and DirectInput. Red LED confirms DirectInput is active. Customer must relaunch the game after switching. If game still does not detect: try switching back to XInput and testing — some older games actually use XInput. Always relaunch game after every mode switch."
            },
            {
                "tag": "Powering off the controller",
                "scenario": "A customer asks: 'How do I turn off the Ares Wireless when I am done gaming? I do not want it draining the battery when I am not using it.'",
                "question": "Explain how to power off the Ares Wireless and any other battery-saving tips.",
                "rubric": "To power off: press and hold B + Back button for 5 seconds. Controller will shut down. To power on: press Home button. Battery saving tips: always power off when not in use using B+Back. The controller may auto-sleep after extended inactivity but manually powering off is recommended. Low battery warning: LED flashes and vibration automatically disables — charge promptly when this happens. Use only 5V/1A charger or PC USB port — fast chargers are NOT supported and can damage the battery and void the warranty. This is a critical point agents must know."
            },
            {
                "tag": "Hall Effect joysticks and triggers — 2026 batch",
                "scenario": "A customer says: 'I saw that the Ares Wireless now has Hall Effect joysticks AND Hall Effect triggers. My controller is about a year old. Does mine have these? And why does it matter for triggers?'",
                "question": "Explain Hall Effect joysticks and triggers, confirm which batch has them, and be honest about older models.",
                "rubric": "Hall Effect joysticks: use magnetic sensors, no physical friction wear, drift-resistant by design, high precision. Hall Effect triggers: same magnetic sensor technology applied to analog triggers — provides consistent pressure sensitivity, no wear from repeated trigger pulls, longer lifespan and more accurate analog input. The 2026 manufacturing batch of the Ares Wireless has both Hall Effect joysticks AND Hall Effect analog triggers. Older models have standard joystick and trigger mechanisms which can wear and drift over time. CRITICAL: there is no upgrade path — older hardware cannot be retrofitted. Wear and tear on older joysticks/triggers is NOT covered under warranty. If a customer wants Hall Effect on both joysticks and triggers they need a 2026 batch unit."
            },
            {
                "tag": "Charging and fast charger warning",
                "scenario": "A customer says: 'My Ares Wireless is not charging. I am using a 65W USB-C fast charger. The LED is not showing any charging indicator. Did the controller break?'",
                "question": "Diagnose the charging issue and explain what charger the customer must use.",
                "rubric": "CRITICAL: Fast charging is NOT supported on the Ares Wireless. Using a fast charger (like a 65W charger) can damage the battery and void the warranty — this is explicitly stated in the manual. Customer must use only a 5V/1A charger or a standard PC USB port for charging. Charging indicators: LED blinks slowly while charging, LED turns OFF when fully charged. Fix: switch to a 5V/1A adapter or PC USB port, use a good quality USB-C cable, check the charging port for debris. If the battery was already exposed to fast charging repeatedly it may be damaged — in that case warranty would not cover it as it is user-caused damage. Agent must proactively warn customer never to use fast chargers again."
            },
            {
                "tag": "Turbo and Auto Turbo",
                "scenario": "A customer says: 'My B button fires super fast on its own. Also how do I set up Auto Turbo on the Y button so it keeps firing without me holding it?'",
                "question": "Diagnose the B button issue and explain Turbo and Auto Turbo setup on the Ares Wireless.",
                "rubric": "Auto-firing B: Turbo accidentally enabled. Fix: press B then Turbo button again to cancel — same enable process cancels it. Turbo (fast fire while button held): press desired button (A/B/X/Y/L1/L2/R1/R2) then press Turbo button. To cancel: repeat same process. Auto Turbo (fires continuously without holding): press desired button then press AUTO button. To cancel: repeat same process. Supported on: A, B, X, Y, L1, L2, R1, R2. Key distinction: Turbo requires holding the button, Auto Turbo fires independently. Always rule out Turbo/Auto before suggesting hardware fault."
            },
            {
                "tag": "LED controls and vibration",
                "scenario": "A customer says: 'The ABXY buttons stopped glowing and the V-shaped light is also off. Also the vibration has completely stopped during gameplay.'",
                "question": "Explain how to control the LEDs and diagnose the vibration issue on the Ares Wireless.",
                "rubric": "ABXY LED toggle: press X+Back to turn on or off. V LED (centre V-strip) toggle: press A+Back to turn on or off. These are independent toggles. Vibration issue: first check battery level — vibration is automatically disabled when battery is low to conserve power. Charge the controller first. If vibration still does not work after charging: ensure the game supports vibration feedback — not all PC games support rumble. Android does not support vibration. Also check the customer has not accidentally toggled vibration if the model supports that. If vibration is completely absent across all games with full battery it may be a hardware defect."
            },
            {
                "tag": "Disconnections and range issues",
                "scenario": "A customer says: 'My Ares Wireless keeps disconnecting every few minutes. The USB dongle is plugged into the back of my PC tower and I sit about 5-6 meters away. I also have a Wi-Fi router right next to my PC.'",
                "question": "Diagnose all causes of disconnection and tell the customer exactly what to do.",
                "rubric": "Multiple causes to identify and address: (1) Dongle position — at the back of a tower it has poor line of sight through the case. Move dongle to a front USB port or use a USB extension cable to bring it into open space. This is the most common fix. (2) Distance — 5-6m is within the 6-8m range but obstacles dramatically reduce effective range. Clear line of sight is critical. (3) Wi-Fi router interference — Wi-Fi routers operate on 2.4GHz, same band as the dongle. Move dongle away from router. (4) USB 3.0 ports can cause 2.4GHz interference — if dongle is near a USB 3.0 hard drive or port, move it. (5) Low battery — replace/charge even if LED appears lit. (6) Restart controller and re-pair if needed. Maximum effective range is 8m in open, interference-free conditions."
            },
            {
                "tag": "Warranty — battery, physical, and fast charger damage",
                "scenario": "A customer says: 'My Ares Wireless battery drains really fast after 9 months. I have been using a fast charger to charge it. Also I dropped it and cracked the shell. What is covered under warranty?'",
                "question": "Explain the warranty coverage honestly for all three issues the customer mentioned.",
                "rubric": "Three issues to address separately: (1) Battery drain after 9 months: regular wear and tear from battery usage is explicitly NOT covered under warranty. Battery degradation over time is normal. Additionally, if the customer used a fast charger, this can damage the battery — fast charging voids warranty coverage for battery issues. (2) Fast charger damage: using unsupported chargers is user-caused damage and not covered. Manual explicitly warns that fast charging is not supported and can damage battery and void warranty. (3) Physical damage from dropping: cracked shell from a drop is explicitly NOT covered under warranty. Water damage and tampered products are also not covered. Warranty covers only manufacturing defects for 1 year. Contact: +91 7351615161, cc@thecosmicbyte.com."
            }
        ]
    },
    {
        "id": "ares_pro",
        "name": "Ares Pro",
        "category": "Controller",
        "description": "Tri-mode wireless controller with Hall Effect joysticks, LED ABXY buttons, M1/M2 macro keys and software support (new models only).",
        "available": True,
        "questions": [
            {
                "tag": "Software support and firmware warning",
                "scenario": "A customer says: 'I downloaded the Cosmic Byte software but it is not detecting my Ares Pro. I also saw a firmware update file on the website — should I use that to fix it?' They bought their controller about a year ago.",
                "question": "How do you verify if this customer's Ares Pro supports the software, and what is the critical warning about firmware updates they must know?",
                "rubric": "Step 1 — Model check: ask customer to check the back label. If it says App Support in the top left corner, their model supports the software. If not present, their model does NOT support the software — no workaround, older models work fine as controllers only. Step 2 — CRITICAL firmware warning: two different firmware versions exist. Models WITH software support must ONLY update firmware through the software itself (connect wired, press firmware update button in software) — never use the standalone firmware file. Models WITHOUT software support use the separate standalone firmware file. Mixing these up can cause serious issues. Agents must always confirm which model type before advising any firmware update. Also note: software v1.2.11 added auto shutdown adjustment via software."
            },
            {
                "tag": "Connectivity and LED modes",
                "scenario": "A customer says: 'I am confused about how to connect my Ares Pro. I want to use it on my PC with the dongle, on my Android phone via Bluetooth, and on my iPhone. Also how do I know which mode I am in?'",
                "question": "Explain all connection methods and what each LED color means on the Ares Pro.",
                "rubric": "Four LED colors indicate mode: Orange=XInput PC, Red=DInput PC, Green=Android, Blue=iOS. Wireless dongle: plug dongle into PC, hold Home for 3 seconds when controller is off, motor vibrates once, LED flashes then stays solid. Wired: plug USB-C cable, automatically switches to XInput (Orange LED). Bluetooth PC XInput: hold X+Home for 3 seconds (Orange LED). Bluetooth Android: hold A+Home for 3 seconds (Green LED). Bluetooth iOS: hold B+Home for 3 seconds (Blue LED). Android support is limited and not covered under warranty. Controller is PC-only device — not compatible with any console."
            },
            {
                "tag": "XInput vs DInput switching",
                "scenario": "A customer says: 'I am using the dongle on PC and my old game from 2006 does not detect the Ares Pro at all. Windows sees it fine but the game ignores it completely.'",
                "question": "Diagnose the issue and explain how to fix it on the Ares Pro.",
                "rubric": "Old games only support DInput (Red LED). The Ares Pro defaults to XInput (Orange LED) when connected via dongle or wired. To switch between XInput and DInput in wireless dongle or wired mode: hold Back+Start for 3 seconds. Orange LED = XInput, Red LED = DInput. Customer must relaunch the game after switching. In Bluetooth mode the LED colors indicate the connected platform directly."
            },
            {
                "tag": "Turbo auto button press",
                "scenario": "A customer calls: 'My B button on the Ares Pro keeps pressing itself super fast repeatedly. The controller is new. Is it broken? Also how do I change how fast the turbo fires?'",
                "question": "Diagnose the issue, explain how to disable turbo, and how to adjust turbo speed.",
                "rubric": "Cause: Turbo accidentally enabled on B — activated by pressing B+Turbo. Fix: press B+Turbo again to cancel. Turbo works on A, B, X, Y, L1, L2, R1, R2. Speed adjustment: press Turbo+Right Joystick Up to increase speed (motor vibrates once to confirm), press Turbo+Right Joystick Down to decrease speed (motor vibrates once). Always rule out Turbo before suggesting hardware defect."
            },
            {
                "tag": "M1/M2 macro setup",
                "scenario": "A customer says: 'When I press the M1 button on the back of my Ares Pro it does nothing at all. I want to set it up to press A when I press M1. How do I do this? And later how do I cancel it?'",
                "question": "Walk the customer through recording a macro on M1 and how to cancel it.",
                "rubric": "To set up macro: hold M1+Turbo simultaneously for 3 seconds until purple LED starts flashing. Press the button to assign (e.g. A). Press M1 again to save — controller vibrates once and LED stops flashing confirming success. To use: press M1 during gameplay. Cannot assign macros to Back, Start, Turbo or Home buttons. To cancel: hold M1+Turbo for 3 seconds until purple LED flashes, then press M1 once — controller vibrates once and LED stops flashing confirming cancellation. Same process applies to M2."
            },
            {
                "tag": "LED controls",
                "scenario": "A customer says: 'The glowing ABXY buttons on my Ares Pro turned off and I cannot figure out how to turn them back on. Also the V-shaped light in the middle is also off.'",
                "question": "Explain how to control both LED groups on the Ares Pro.",
                "rubric": "The Ares Pro has two independent LED groups. ABXY LED: press X+Back to toggle on or off. V LED (the V-shaped light): press A+Back to toggle on or off. These are independent so ABXY can be on while V LED is off or vice versa. If both are off, customer simply needs to press the respective combinations to turn them back on. LEDs not lighting up can also indicate low battery — advise customer to charge if toggling does not work."
            },
            {
                "tag": "Joystick and D-pad toggle",
                "scenario": "A customer says: 'In my game I want to use the D-pad to move my character but it is currently controlled by the left joystick. Can I swap them on the Ares Pro?'",
                "question": "Explain how to swap the joystick and D-pad functions on the Ares Pro.",
                "rubric": "To toggle between left joystick and D-pad functions: press L3+Back. This swaps the left joystick and D-pad roles. Pressing L3+Back again swaps them back. This is a simple toggle — no software needed. The function works in all connection modes."
            },
            {
                "tag": "D-pad 4-way and 8-way mode",
                "scenario": "A customer who plays fighting games says: 'My D-pad sometimes registers diagonal inputs when I only want pure left, right, up or down. Is there a way to lock it to only 4 directions?'",
                "question": "Explain the D-pad input modes on the Ares Pro and how to switch between them.",
                "rubric": "The Ares Pro supports 4-Way and 8-Way D-pad input modes. 4-Way mode only allows pure directional inputs (up, down, left, right) — best for fighting and platformer games where accidental diagonals cause problems. 8-Way mode (default) allows all 8 directions including diagonals. To toggle between them: hold D-pad Up, then press Back button. Repeat to toggle back. 4-Way mode eliminates accidental diagonal inputs."
            },
            {
                "tag": "Joystick range modes",
                "scenario": "A customer who plays precision games asks: 'Is there any way to adjust how sensitive or how far the joystick moves on the Ares Pro? I want more control for aiming.'",
                "question": "Explain the joystick range modes on the Ares Pro and how to cycle through them.",
                "rubric": "The Ares Pro has three joystick range modes activated with R3/L3+Turbo. Full Circle (default) = full joystick movement enabled, medium vibration confirms. Small Circle = reduced joystick range for precision control — better for aiming and fine movement, small vibration confirms. Square Mode = square-style input mapping for tight angles, strong vibration confirms. The vibration intensity when switching tells the agent which mode was selected. Customer can cycle through all three by repeating R3/L3+Turbo."
            },
            {
                "tag": "Joystick calibration",
                "scenario": "A customer says: 'My left joystick on the Ares Pro keeps drifting slightly even when I am not touching it. How do I fix this?'",
                "question": "Walk the customer through the joystick calibration process on the Ares Pro.",
                "rubric": "Calibration steps: (1) Power off the controller completely. (2) Hold Back+X+Home for 1 second — LEDs flash green and blue, controller vibrates once confirming calibration mode. (3) Rotate both joysticks clockwise 3 times. (4) Press both triggers fully 3 times. (5) Press Start to finish — green LED lights up and controller vibrates once to confirm. The Ares Pro uses Hall Effect joysticks which are drift-resistant by design but calibration may be needed after extended use or physical impact."
            },
            {
                "tag": "Headset jack and audio",
                "scenario": "A customer says: 'I plugged my headset into the 3.5mm jack on the Ares Pro but I cannot hear any game audio. I am currently connected via Bluetooth to my PC.'",
                "question": "Explain why audio is not working and what the customer needs to do.",
                "rubric": "The 3.5mm headset jack only works in wireless dongle mode and wired USB mode. It is NOT supported in Bluetooth mode. Customer needs to switch from Bluetooth to either wireless dongle or wired connection to use the headset jack. Once switched, the jack supports both audio output and microphone input. Also remind customer that Bluetooth mode does not support the headset jack regardless of platform."
            },
            {
                "tag": "Battery and warranty",
                "scenario": "A customer says: 'My Ares Pro vibration stopped working completely and the LED is flashing. Also the battery seems to drain much faster than before after 8 months of use. Is this covered under warranty?'",
                "question": "Diagnose the vibration and LED issue, and explain what the warranty covers for both the battery and vibration concerns.",
                "rubric": "Flashing LED = low battery — vibration is automatically disabled when battery is low to save power. Customer needs to charge first. Vibration adjustment (updated in software v1.2.11): HOLD R3+Left Joystick Up for 3 seconds to increase (not just a tap — must hold 3 seconds). HOLD R3+Left Joystick Down for 3 seconds to decrease. This was updated to prevent accidental changes during gameplay. Auto shutdown time can also be adjusted via the software on supported models. Warranty: 1 year against manufacturing defects only. Important: regular wear and tear from battery usage is explicitly NOT covered — battery degradation over months is normal wear and tear. Physical damage and water damage also not covered."
            }
        ]
    },
    {
        "id": "drakon",
        "name": "Drakon",
        "category": "Controller",
        "description": "Wireless controller with TMR joysticks, 3-level trigger lock, magnetic covers, charging dock, macro buttons and RGB.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity modes",
                "scenario": "A new customer asks: 'I want to use the Drakon on my PC via the dongle, but also sometimes on my Android phone via Bluetooth. How do I connect for each and how do I know which mode is active?'",
                "question": "Explain how to connect the Drakon in 2.4GHz and Bluetooth modes for PC and Android, including how LED indicators confirm the mode.",
                "rubric": "2.4GHz PC: press X+HOME for 3 seconds, LED2=XInput, LED3=DInput. To switch between X/D in 2.4GHz: hold FNR+HOME for 3 seconds. Bluetooth PC: B+HOME=XInput(LED2), A+HOME=DInput(LED3), Y+HOME=Gyro(LED4). Bluetooth Android: A+HOME=DInput(LED3), B+HOME=XInput(LED2), Y+HOME=Gyro(LED4). All Bluetooth pairings require 3-second long press. iOS supported for XInput(B+HOME) and Gyro(Y+HOME) only, support is limited. LED staying solid confirms connection."
            },
            {
                "tag": "XInput vs DInput — old game",
                "scenario": "A customer says: 'I connected the Drakon via 2.4GHz dongle on PC. Windows detects it fine but my old 2005 game does not detect the controller at all.'",
                "question": "Explain why the game is not detecting the controller and how to fix it.",
                "rubric": "Old games only support DInput. In 2.4GHz mode the controller defaults to XInput (LED2). To switch to DInput: hold FNR+HOME for 3 seconds (LED3 confirms DInput). Customer must relaunch the game after switching. LED2=XInput, LED3=DInput. Switching back to XInput uses the same FNR+HOME combo."
            },
            {
                "tag": "Gyro and on-the-fly gyro",
                "scenario": "A customer asks: 'I want to use gyro motion control on my PC. I tried the 2.4GHz dongle but gyro does not seem to work. Also can I use gyro in games that do not officially support it?'",
                "question": "Explain how to use gyro on PC including how to make it work in games without native gyro support.",
                "rubric": "Native Gyro Mode: only available in Bluetooth mode. Switch from 2.4GHz to Bluetooth, then hold Y+HOME for 3 seconds, LED4 confirms Gyro mode active. On-the-fly gyro via software: connect via Wired or 2.4GHz, open Cosmic Byte software, assign gyro to any button, set activation mode (Always On / Press to Activate / Toggle), map gyro output to mimic Left or Right joystick — this makes gyro work in ANY game even without native support. Both methods must be explained."
            },
            {
                "tag": "3-level trigger lock system",
                "scenario": "A customer who plays both racing and FPS games says: 'For racing I want gradual trigger pressure. For FPS I want the trigger to fire instantly like a button. But sometimes I want something in between. The Drakon has some kind of trigger switch — how does it work?'",
                "question": "Explain the 3-level trigger lock system on the Drakon and which setting is best for which type of game.",
                "rubric": "The Drakon has an independent 3-position physical travel limit switch for each trigger (LT and RT). Position 1 (shortest travel) = Digital signal, ON/OFF like a button, best for FPS and fast-action games. Position 2 (medium travel) = Analog signal, approximately 50% travel, middle ground for mixed gaming. Position 3 (longest travel) = Analog signal, 100% full travel, best for racing and simulation games requiring precise gradual input. Each trigger has its own independent switch so LT and RT can be set differently."
            },
            {
                "tag": "Mouse mode",
                "scenario": "A customer asks: 'I heard the Drakon has a mouse mode where the joystick works like a mouse cursor. How do I turn this on and use it?'",
                "question": "Explain how to activate and use Mouse Mode on the Drakon.",
                "rubric": "Mouse Mode is available in 2.4GHz wireless mode only. To activate: press CAPTURE+R3 for 5 seconds. LED3 and LED4 stay on together to confirm Mouse Mode is active. In this mode: A button = Left Click, B button = Right Click. The right joystick controls cursor movement. To exit Mouse Mode disconnect and reconnect normally. This is a PC-only feature via 2.4GHz."
            },
            {
                "tag": "Turbo auto button press",
                "scenario": "A customer calls: 'My A button keeps firing super fast repeatedly on its own. The Drakon is brand new. Also how do I change the turbo speed and clear all turbo settings?'",
                "question": "Diagnose the auto-press issue and explain turbo speed adjustment and how to clear all turbo settings.",
                "rubric": "Cause: Turbo accidentally enabled on A button (press TURBO then A). Fix: repeat TURBO+A to disable. Three speed levels: Slow=5 shots/sec, Medium=15 shots/sec, Fast=25 shots/sec. To change speed: press FNL+Turbo then move Right Joystick Left (decrease) or Right (increase). To clear ALL turbo settings at once: hold FNR+Turbo for 5 seconds until vibration confirms reset. Always rule out Turbo before suggesting hardware fault."
            },
            {
                "tag": "Macro buttons FNL FNR",
                "scenario": "A customer says: 'When I press the MR button on the back of the Drakon it fires a sequence of random inputs I never set up. Also what is the difference between FNL and FNR buttons and how do I record a new macro?'",
                "question": "Explain what FNL and FNR are, why MR is misfiring, and how to record and clear macros.",
                "rubric": "FNL and FNR are function modifier buttons on the back used to activate secondary functions — they work like shift keys. MR is firing because a macro was accidentally recorded on it. To record new macro on MR: press FNR+MR to enter recording mode, press your sequence (up to 22 inputs including delays), press MR again to save — vibration confirms. To clear: enter macro mode via FNR+MR, press MR immediately with no inputs — vibration confirms deletion. ML uses FNL+ML. Factory reset (L1+R1+L2+R2+L3+R3 simultaneously) clears all macros."
            },
            {
                "tag": "Charging — dock and cable",
                "scenario": "A customer asks: 'How do I charge the Drakon? I have the charging dock but I am not sure if it is charging properly. Also the RGB lights turned off suddenly while I was playing — did something break?'",
                "question": "Explain how to charge using both the dock and USB cable, how to confirm charging is working, and why the RGB turned off.",
                "rubric": "Dock charging: connect dock to USB power, place controller onto magnetic contacts — Dock LED On=Charging, Dock LED Off=Fully charged. Cable charging: connect USB-C to controller and any 5V USB source — LED Blinking=Charging, LED Steady=Fully charged. Use 5V adapters only, avoid fast chargers. RGB turning off automatically is normal behavior — RGB lights turn off automatically when battery is low to preserve battery life. Vibration may also reduce automatically at low battery. Battery life is 8-20 hours depending on usage."
            },
            {
                "tag": "Joystick drift and calibration",
                "scenario": "A customer says: 'My Drakon left joystick is drifting slightly to the right even when I am not touching it. It started after I dropped the controller.'",
                "question": "Explain what is likely causing the drift and walk the customer through the calibration process step by step.",
                "rubric": "Physical impact can cause joystick calibration offset. Calibration steps: (1) Turn OFF controller. (2) Hold CAPTURE then press HOME to power on — LED1 blinks confirming calibration mode. (3) Press A to begin — LED2 blinks. (4) Rotate both joysticks three full circles. (5) Press LT and RT three times each. (6) Press A again to save and exit — LED returns to normal. If drift persists after calibration it may indicate physical damage. Drakon uses TMR joystick system which is drift-resistant under normal use."
            },
            {
                "tag": "Magnetic covers and dongle storage",
                "scenario": "A customer asks: 'How do I change the top cover on the Drakon? Also I keep losing the 2.4GHz dongle when travelling — is there a way to store it safely with the controller?'",
                "question": "Explain how to remove and install the magnetic top covers, and where to store the dongle.",
                "rubric": "Removing cover: locate the lift point near the front edge, insert finger and gently pull upward — magnets release smoothly. Installing cover: align new cover with frame, lower gently, magnetic locks secure automatically. Do not force the magnets. Under the top cover there is a dedicated dongle storage slot — insert the 2.4GHz dongle into this slot when travelling, it clicks into place and will not fall out. The Drakon also comes with 3 magnetic top covers, 2 extra D-pads (Precision and Disc), and 2 extra joystick tops in the package."
            },
            {
                "tag": "Button mapping and customisation",
                "scenario": "A customer says: 'I want to swap A and B buttons on my Drakon. I also want the D-pad to control character movement instead of the left joystick. And my inputs feel like they are going diagonally wrong — is there a fix for that?'",
                "question": "Explain how to perform each of these three customisations on the Drakon.",
                "rubric": "ABXY swap: hold TURBO+R3 for 2 seconds — vibration confirms, A swaps with B and X with Y simultaneously. D-pad and Left Stick swap: hold L3+CAPTURE for 2 seconds — vibration confirms swap. Joystick circle/square angle mode (for diagonal accuracy): hold L3+TURBO for 2 seconds — toggles between Round mode (default) and Square 45-degree mode which improves diagonal accuracy and reduces circle error percentage. All are toggle functions — repeat to swap back. Factory reset restores all to default."
            },
            {
                "tag": "Reset and warranty",
                "scenario": "A customer has tried everything. The controller is frozen and unresponsive. They also ask about factory reset and whether water damage after a spill is covered under warranty.",
                "question": "Explain the reset option, what factory reset clears, and the warranty situation for water damage.",
                "rubric": "Emergency reset (controller frozen/unresponsive): insert pin into RESET hole on back, hold for 1 second — controller restarts normally, no settings deleted. Factory reset (clears all custom settings): hold L1+R1+L2+R2+L3+R3 simultaneously — vibrates 1 second to confirm, restores all Turbo, Vibration and Macro settings to factory defaults. Re-pairing may be required after factory reset. Warranty: 1 year for manufacturing defects only. Water damage is explicitly NOT covered under warranty. Physical damage is also not covered. Be honest but polite."
            }
        ]
    },
    {
        "id": "stellaris",
        "name": "Stellaris",
        "category": "Controller",
        "description": "Tri-mode wireless controller with TMR joysticks, gyro, macro buttons and RGB lighting.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity modes",
                "scenario": "A customer just bought the Stellaris and asks: 'How do I connect this to my PC? And can I also use it on my Android phone and iPhone?'",
                "question": "Explain all connectivity options on the Stellaris and how to connect on each platform.",
                "rubric": "Should mention three modes: Wired USB-C (plug in and press HOME, LED2=XInput/LED3=DInput), 2.4GHz wireless (press X+HOME for 3 seconds to pair), and Bluetooth (different button combos per platform). For PC Bluetooth: XInput=B+HOME, DInput=A+HOME, Gyro=Y+HOME. For Android: XInput=B+HOME, DInput=A+HOME, Gyro=Y+HOME. For iOS: DInput=A+HOME, XInput=B+HOME, Gyro=Y+HOME. Gyro is ONLY available in Bluetooth mode. iOS support is limited."
            },
            {
                "tag": "XInput vs DInput",
                "scenario": "A customer says: 'I connected the Stellaris via the 2.4GHz dongle but my 2007 game is not detecting it at all. I can see it in Windows joy.cpl but the game completely ignores it.'",
                "question": "Diagnose why the game is not detecting the controller and walk the customer through the fix.",
                "rubric": "Old games only support DInput. In 2.4GHz mode, XInput shows LED2 and DInput shows LED3. To switch to DInput in 2.4GHz mode: long-press SELECT+HOME. To switch back to XInput: long-press HOME. Customer must relaunch the game after switching. LED3 staying on confirms DInput is active."
            },
            {
                "tag": "Gyro on PC",
                "scenario": "A customer says: 'I want to use gyro/motion control on my PC in a game that does not officially support it. I connected via the 2.4GHz dongle but cannot find any gyro option anywhere.'",
                "question": "Explain the two ways the customer can use gyro on their PC with the Stellaris, including how to make it work in games that do not natively support it.",
                "rubric": "Two methods: (1) Native Bluetooth Gyro Mode — disconnect dongle, pair via Bluetooth, hold Y+HOME for 3 seconds, LED4 stays on. Works for games with native gyro support. (2) Software on-the-fly gyro — connect via Wired or 2.4GHz, open Cosmic Byte software, assign gyro to any button, choose activation mode (Always On / Press to Activate / Toggle), map gyro output to mimic Left or Right joystick. This method makes gyro work as motion-based joystick input in ANY game even without native gyro support. Key point: gyro via 2.4GHz dongle requires the software configuration — raw gyro is Bluetooth only."
            },
            {
                "tag": "Trigger modes",
                "scenario": "A customer who plays both racing games and FPS games says: 'The triggers feel too gradual for my shooting game. I want instant button-like triggers. But for my racing game I want the gradual feel back. How do I switch between them?'",
                "question": "Explain the trigger modes on the Stellaris and how to switch between them.",
                "rubric": "The Stellaris has a physical trigger mode switch on the controller body. Analog mode (switch flipped inward) = longer travel, pressure-sensitive gradual input, best for racing and simulation. Digital mode (switch flipped outward) = shorter travel, instant response like a button, best for FPS and competitive games. Customer physically flips the switch — no software or button combo needed."
            },
            {
                "tag": "Turbo auto button press",
                "scenario": "A customer calls: 'My B button keeps pressing itself super fast and repeatedly on its own. The controller is brand new. Is it defective?'",
                "question": "Diagnose the most likely cause and explain how to resolve it step by step.",
                "rubric": "Most likely cause is Turbo mode accidentally enabled via TURBO+B. Fix: hold TURBO+B again to disable it for that button. To clear ALL turbo assignments at once: hold TURBO button for 5 seconds. Three speed levels exist: 5, 12 (default), 20 presses per second. Always rule out Turbo before suggesting hardware defect."
            },
            {
                "tag": "Macro buttons",
                "scenario": "A customer says: 'When I press the MR button on the back of my Stellaris it fires off a sequence of random button presses I never set up. How do I stop this?'",
                "question": "Explain what is happening and how to fix it.",
                "rubric": "A macro was recorded on MR, possibly accidentally. To record/overwrite with empty: hold TURBO then hold MR for 2 seconds (recording mode), then press MR to save. Or perform factory reset to clear all macros. Macros can store up to 22 inputs. ML and MR are the two back macro buttons. Factory reset clears all macro definitions completely."
            },
            {
                "tag": "Hardware reset vs factory reset",
                "scenario": "A customer is confused: 'I see a Reset button on the controller and also heard about a factory reset. What is the difference? My controller is acting strange with random inputs.'",
                "question": "Explain the difference between hardware reset and factory reset, and advise which one the customer should use for their situation.",
                "rubric": "Hardware reset (press RESET button next to USB port for 1 second): fixes unresponsive behavior and connection issues only, does NOT delete any user settings, controller goes to sleep after. Factory reset (hold SELECT+L3+R3 simultaneously for 5 seconds while ON): clears ALL custom settings including turbo, macros, RGB, vibration, button swaps, stick modes — re-pairing required. For random inputs recommend factory reset. For connection issues or unresponsive, try hardware reset first."
            },
            {
                "tag": "Battery check and audio jack",
                "scenario": "A customer asks two things: 'How do I check battery level on the Stellaris?' and 'I plugged my headset into the 3.5mm jack but I cannot hear anything — I am connected via Bluetooth on my phone.'",
                "question": "Answer both questions completely.",
                "rubric": "Battery check: press CAPTURE+START — LEDs show level for 3 seconds: LED1=1-25%, LED2=26-50%, LED3=51-75%, LED4=76-100%. Audio jack: 3.5mm only works in PC mode via 2.4GHz wireless or wired USB — NOT in Bluetooth mode, NOT on mobile devices. Customer needs to switch to wired or 2.4GHz on PC to use the headset."
            },
            {
                "tag": "D-pad and button swaps",
                "scenario": "A customer says: 'In my game I want the D-pad to control movement instead of the left joystick. Also the A and B buttons feel reversed for me — can they be swapped?'",
                "question": "Explain how to swap D-pad with left stick and how to swap ABXY buttons on the Stellaris.",
                "rubric": "D-pad and Left Stick swap (PC mode only): hold START+L3 for 3 seconds, motor vibration confirms swap. ABXY swap: hold TURBO+R3 for 3 seconds, motor vibration confirms — A swaps with B and X swaps with Y simultaneously. Both are toggles — repeat the same combo to swap back. Factory reset restores both to default."
            },
            {
                "tag": "Console compatibility and warranty",
                "scenario": "A customer says: 'I bought the Stellaris to use on my PS5 and it is not working at all. Also I spilled water on it and some buttons are sticky. Will either of these be covered under warranty?'",
                "question": "Address the console issue and explain the warranty situation for both problems clearly.",
                "rubric": "Console: Stellaris is NOT supported on any gaming console including PS5. No warranty, service or support for console use. Customer should have verified compatibility before purchasing. Warranty: 1 year for manufacturing defects only. Water damage is explicitly NOT covered. Physical damage is NOT covered. Be clear and honest but polite — neither issue qualifies for warranty support."
            }
        ]
    },
    {
        "id": "blitz_tri",
        "name": "Blitz Tri-Mode",
        "category": "Controller",
        "description": "Tri-mode controller (USB Wired / 2.4GHz / Bluetooth) with TMR joysticks, Hall Effect triggers, 1000Hz polling rate, macro programming, gyro, Dualshock mode (iOS), Steam mode, charging dock support. 600mAh battery. PC primary platform.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity modes and LED indicators",
                "scenario": "A new customer asks: 'I want to use my Blitz Tri-Mode on my PC via the dongle, on my Android phone, and on my iPhone. How do I connect for each and how do I know which mode I am in from the LEDs?'",
                "question": "Explain all connection methods and LED indicator meanings on the Blitz Tri-Mode.",
                "rubric": "Wired PC: plug USB-C cable, press HOME — LED2 stays on (XInput). To switch to DInput wired: long-press HOME — LED3 stays on. 2.4GHz PC: press X+HOME for 3 seconds — LED2 (XInput) or LED3 (DInput). Switch DInput in 2.4GHz: long-press SELECT+HOME. Mouse mode (wired or 2.4GHz): hold CAPTURE+R3 for 5 seconds — LED3+LED4 stay on; A=left click, B=right click, right stick=cursor. Repeat CAPTURE+R3 to exit. Bluetooth PC XInput: B+HOME — LED2. Bluetooth PC DInput: A+HOME — LED3. Bluetooth Gyro: Y+HOME — LED4. Bluetooth Android XInput: B+HOME — LED2. Bluetooth Android DInput: A+HOME — LED3. Bluetooth Android Gyro: Y+HOME — LED4. Bluetooth iOS XInput: B+HOME — LED2. Bluetooth iOS Dualshock: TURBO+HOME — LED1. Bluetooth iOS Gyro: Y+HOME — LED4. iOS requires Bluetooth-only pairing and app must support external controllers. Consoles NOT supported."
            },
            {
                "tag": "XInput vs DInput — old game",
                "scenario": "A customer says: 'I connected the Blitz Tri-Mode via the 2.4GHz dongle on PC. Windows detects it fine but my old 2003 game completely ignores it.'",
                "question": "Diagnose and fix the issue for the Blitz Tri-Mode.",
                "rubric": "Old games only support DInput (LED3). Blitz Tri-Mode defaults to XInput (LED2) in 2.4GHz mode. To switch to DInput in 2.4GHz: long-press SELECT+HOME — LED3 stays on confirming DInput. Customer must relaunch the game after switching. In wired mode: long-press HOME to toggle between XInput (LED2) and DInput (LED3). Always relaunch game after switching modes."
            },
            {
                "tag": "Steam mode",
                "scenario": "A customer says: 'I play most of my games on Steam and the Blitz Tri-Mode is not being detected properly in Steam even though Windows sees it. Is there a special Steam mode?'",
                "question": "Explain Steam Mode on the Blitz Tri-Mode — what it is, when to use it, and exactly how to activate it.",
                "rubric": "Steam Mode is a special wired-only boot mode for Steam compatibility. Steps: (1) Ensure controller is fully powered OFF. (2) Press and hold R3 (right stick click down). (3) While holding R3, plug the USB-C cable into the PC. (4) Controller boots directly into Steam-compatible mode. CRITICAL: Steam Mode is wired only — it cannot be activated wirelessly. After activating, restart Steam if it was already open. This mode is specifically for Steam game detection issues."
            },
            {
                "tag": "Gyro setup and Bluetooth-only limitation",
                "scenario": "A customer says: 'I want to use gyro motion control on my PC with the Blitz Tri-Mode. I am using the 2.4GHz dongle but I cannot find any gyro option. Also can I use gyro in games that do not natively support it?'",
                "question": "Explain how gyro works on the Blitz Tri-Mode and why it is not working via the dongle.",
                "rubric": "Native Gyro Mode is ONLY available in Bluetooth mode — it does NOT work in 2.4GHz or wired modes. Customer must disconnect dongle and pair via Bluetooth: press Y+HOME for 3 seconds, LED4 stays on confirming gyro mode. For games without native gyro support: connect via wired or 2.4GHz, open Cosmic Byte software (downloadable from thecosmicbyte.com), assign gyro to a button, set activation mode (Always On / Press to Activate / Toggle), map gyro output to mimic left or right joystick — this makes gyro work as joystick input in any game. Software method works over wired/2.4GHz. Both methods should be explained."
            },
            {
                "tag": "Turbo, Auto Fire and speed adjustment",
                "scenario": "A customer says: 'My A button keeps firing super fast on its own. Also how do I set Auto Fire on X? And how do I change the turbo speed and clear all turbo assignments at once?'",
                "question": "Diagnose the auto-firing A button, explain Auto Fire setup, speed adjustment and clearing all turbo on the Blitz Tri-Mode.",
                "rubric": "Auto-firing A: Turbo enabled on A. Enable Turbo: hold TURBO + desired button. To toggle to Auto Fire on same button: press TURBO + same button again. Cancel individual: hold CLEAR + button. Clear ALL turbo: hold TURBO for 5 seconds. Three speed levels: Level 1=5 presses/sec, Level 2=12 presses/sec (default), Level 3=20 presses/sec. Adjust speed: hold TURBO, push right stick Right to increase one level, Left to decrease one level. Turbo works on A, B, X, Y, LB, RB, LT, RT."
            },
            {
                "tag": "Macro programming",
                "scenario": "A customer says: 'I want to record a macro on my Blitz Tri-Mode — a sequence of button presses that fires with one press. How do I record, execute and clear a macro?'",
                "question": "Walk the customer through recording, executing, and clearing a macro on the Blitz Tri-Mode.",
                "rubric": "Record macro: hold TURBO for 3 seconds (enter macro recording mode), perform the button sequence (up to 22 inputs), press TURBO to save. Execute macro: double-press TURBO during gameplay. Clear macro: enter macro mode (hold TURBO 3 seconds), then press TURBO immediately without recording any buttons — this clears the stored macro. Supports up to 22 inputs per macro. Agent must correctly distinguish between the Turbo function and the Macro function — macros are separate from turbo assignments."
            },
            {
                "tag": "Vibration adjustment and battery check",
                "scenario": "A customer asks: 'How do I reduce the vibration on my Blitz Tri-Mode? It is too strong. Also how do I check the battery level without stopping my game?'",
                "question": "Explain vibration adjustment and the battery level check on the Blitz Tri-Mode.",
                "rubric": "Vibration adjustment: hold TURBO, push right stick Up to increase, Down to decrease. Four levels: 100%, 70% (default), 40%, 0% (off). Battery level check: press TURBO+START simultaneously — LEDs show level: LED1 only = 1-25%, LED1+2 = 26-50%, LED1+2+3 = 51-75%, all four LEDs = 76-100%. Charging: use 5V/1A charger or PC USB port only. Fast chargers damage battery and void warranty. Charging time: 2.5-3 hours. Battery life: 7-15 hours depending on mode and usage."
            },
            {
                "tag": "Stick calibration and D-pad modes",
                "scenario": "A customer says: 'My left joystick on the Blitz Tri-Mode drifts slightly even when I am not touching it. Also I play fighting games and my D-pad keeps registering diagonals — can I lock it to 4 directions?'",
                "question": "Walk the customer through stick calibration and explain the D-pad direction modes on the Blitz Tri-Mode.",
                "rubric": "Stick calibration: (1) Power off controller. (2) Hold CAPTURE+HOME. (3) Press A — LED2 turns on. (4) Rotate both joysticks in full circles 3 times reaching maximum range. (5) Press each trigger fully 3 times. (6) Press A again to save and exit — calibration complete. D-pad 4-way vs 8-way: default is 8 directions. To switch between 4-way and 8-way: press SELECT+D-pad Right for 3 seconds. Short vibration = 4-way mode, Long vibration = 8-way mode. 4-way eliminates diagonal inputs — best for fighting games."
            },
            {
                "tag": "Power functions and controller lock",
                "scenario": "A customer asks: 'How do I properly turn off the Blitz Tri-Mode? Also I put it in my bag and it kept turning on by itself and draining the battery. Is there a way to prevent this?'",
                "question": "Explain all power functions and the controller lock feature on the Blitz Tri-Mode.",
                "rubric": "Power ON: press HOME for 0.5-1 second. Power OFF manually: hold HOME for 5 seconds. Auto sleep: 5 minutes of inactivity while connected. Controller reset (if frozen): hold HOME for 8 seconds. Factory reset (clears all settings): hold SELECT+L3+R3 for 5 seconds. Controller lock (prevents accidental button wake-up in bag): hold SELECT+R3 (right stick click) for 5 seconds until all four LEDs light up — this locks the button wake-up feature. To unlock: plug in a USB charger. This is the critical feature for the bag issue. Must distinguish between reset (HOME 8s) and factory reset (SELECT+L3+R3 5s)."
            },
            {
                "tag": "ABXY swap, stick shape mode and D-pad swap",
                "scenario": "A customer says: 'I want to swap A and B buttons, also swap the D-pad with the left joystick. And I heard there is a square mode for the joystick — what does that do?'",
                "question": "Explain all three customisation options on the Blitz Tri-Mode.",
                "rubric": "ABXY swap: hold TURBO+R3 for 3 seconds — A and B swap, X and Y swap simultaneously. Toggle — repeat to restore. D-pad and Left Stick swap: hold START+L3 for 3 seconds — swaps D-pad and left joystick functions. Toggle — repeat to restore. Stick shape mode (L3+TURBO): toggles between Circle Mode (default — full circular range) and 45-Degree Square Mode (constrains movement to square grid, improving diagonal accuracy for competitive games). Factory reset restores all to default."
            },
            {
                "tag": "Charging dock, reset types and warranty",
                "scenario": "A customer says: 'I bought a charging dock separately for my Blitz Tri-Mode. Also the controller is behaving strangely — should I do a reset or factory reset? And I dropped it cracking the shell — is that covered?'",
                "question": "Explain charging dock usage, the difference between reset and factory reset, and warranty coverage.",
                "rubric": "Charging dock: the Blitz Tri-Mode supports charging dock (sold separately) — place controller onto dock contacts, dock charges via USB power source. Standard cable charging: USB-C to 5V/1A adapter or PC USB port. Fast chargers NOT supported — damages battery and voids warranty. Controller reset (HOME 8 seconds): fixes freezes and input issues without deleting settings. Factory reset (SELECT+L3+R3 for 5 seconds): clears ALL custom settings — turbo, macros, button swaps, vibration levels, D-pad modes. Use factory reset for strange button behaviour first. Warranty: 1 year manufacturing defects only. Physical damage from dropping (cracked shell) is NOT covered. Water damage not covered. Tampered products not covered."
            }
        ]
    },
    {
        "id": "blitz_wireless",
        "name": "Blitz Wireless",
        "category": "Controller",
        "description": "DISCONTINUED — 2.4GHz wireless + USB wired dual-mode controller. Hall Effect joystick and trigger. 600mAh battery. No Bluetooth, no gyro, no macro. Simpler feature set. Agents should know this model is discontinued when customers ask about buying.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity and first-time setup",
                "scenario": "A customer says: 'I just got a Blitz Wireless controller. How do I connect it to my PC via the dongle for the first time? The LED is flashing and nothing is connecting.'",
                "question": "Walk the customer through first-time setup and connection on the Blitz Wireless.",
                "rubric": "First-time dongle pairing: press HOME button for 3-5 seconds to enter pairing mode — LED flashes and controller pairs with dongle for the first time. Once connected: LED1 and LED2 stay on (XInput mode). To connect after first pairing: press HOME for 1 second. Wired mode: connect USB-C cable, press HOME to start using — without pressing HOME the controller only charges, it will NOT function as a controller. Default connection priority: if both dongle and cable are connected simultaneously, controller uses dongle for input and cable for charging. Auto power off: if LED blinks and no dongle found within 1 minute, controller turns off automatically. Connected idle: auto power off after 5 minutes of inactivity."
            },
            {
                "tag": "XInput and DInput modes",
                "scenario": "A customer says: 'My Blitz Wireless is connected via the dongle but my old 2004 game does not detect it. I can see it in Windows but the game ignores it.'",
                "question": "Diagnose the issue and explain how to switch to DInput on the Blitz Wireless.",
                "rubric": "Old games require DInput (LED3+LED4 stay on). Blitz Wireless defaults to XInput when connected (LED1+LED2). To switch to DInput in wireless dongle mode: press HOME button for 2 seconds — LED3 and LED4 will stay on confirming DInput mode. Customer must relaunch the game after switching. To switch back to XInput: press HOME for 2 seconds again to toggle. Note: this controller is 2.4GHz + wired only — there is no Bluetooth mode on the Blitz Wireless."
            },
            {
                "tag": "Android connection and mouse mode",
                "scenario": "A customer asks: 'Can I connect my Blitz Wireless to my Android phone? And I heard there is a mouse mode — how does that work?'",
                "question": "Explain Android connection and mouse mode on the Blitz Wireless.",
                "rubric": "Android connection: plug the USB dongle into Android device using an OTG converter (not included — customer needs a Type-C OTG converter). Press HOME for 1 second. LED flashes then LED3 stays on when connected to Android. Device must support OTG. Mouse mode (Android and PC, wired or 2.4GHz only): press CAPTURE+R3 simultaneously — LED3 and LED4 remain on confirming mouse mode. In mouse mode: right stick controls cursor, A=left click, B=right click. Mouse mode does NOT work in Bluetooth mode — but the Blitz Wireless has no Bluetooth anyway. To exit mouse mode: press CAPTURE+R3 again."
            },
            {
                "tag": "Turbo — enable, auto-turbo and clear all",
                "scenario": "A customer says: 'My B button keeps auto-firing. Also I want to set up turbo on A so it fires fast while I hold it. How do I clear all turbo settings at once? And how do I change turbo speed?'",
                "question": "Diagnose the B button issue, explain Turbo and Auto-Turbo setup, clearing all, and speed adjustment on the Blitz Wireless.",
                "rubric": "Auto-firing B: Turbo enabled on B. To activate Turbo (fires fast while held): press and hold TURBO button + desired button (A/B/X/Y/LB/RB/LT/RT). To activate Auto-Turbo (fires continuously without holding): press and hold TURBO + the same button that already has Turbo assigned — this upgrades it to Auto-Turbo. Cancel individual: press and hold TURBO + the assigned button again to toggle off. Clear ALL turbo assignments: hold TURBO+SELECT for 5 seconds — controller vibrates confirming all cleared. Three speed levels: Slow=5 shots/sec (LEDs flash slowly), Medium=12 shots/sec (default, LEDs flash medium), Fast=20 shots/sec (LEDs flash fast). Increase speed: press TURBO + pull right stick Right. Decrease speed: press TURBO + pull right stick Left."
            },
            {
                "tag": "Vibration adjustment",
                "scenario": "A customer says: 'The vibration on my Blitz Wireless is too strong and distracting. How do I reduce it or turn it off completely?'",
                "question": "Explain how to adjust vibration on the Blitz Wireless.",
                "rubric": "Four vibration levels: None (off), Weak, Medium, Strong. To adjust: controller must be connected to PC. Press TURBO + pull right stick Up to increase one level. Press TURBO + pull right stick Down to decrease one level. To turn off completely: decrease until None/off level is reached. Adjustment must be done while connected — no software needed."
            },
            {
                "tag": "D-pad 4-way and 8-way and battery check",
                "scenario": "A customer who plays fighting games says: 'My D-pad keeps registering diagonals. Also how do I check how much battery is left without stopping my game?'",
                "question": "Explain the D-pad direction modes and battery check on the Blitz Wireless.",
                "rubric": "D-pad default is 8 directions. To switch between 4-way and 8-way: press SELECT+D-pad Right for 3 seconds. Short vibration = 4-way mode (only up/down/left/right, no diagonals). Long vibration = 8-way mode. Repeat to toggle back. 4-way mode eliminates accidental diagonal inputs — best for fighting and platformer games. Battery level check: press TURBO+START simultaneously. LEDs show level: LED1=1-25%, LED1+2=26-50%, LED1+2+3=51-75%, all four LEDs=76-100%."
            },
            {
                "tag": "Joystick calibration and drift",
                "scenario": "A customer says: 'My left joystick on the Blitz Wireless drifts slightly upward even when I am not touching it. How do I fix this?'",
                "question": "Walk the customer through the joystick calibration process on the Blitz Wireless.",
                "rubric": "Calibration steps (note: different from Blitz Tri-Mode): (1) With controller powered off, press the UP D-pad button then press HOME button. (2) LED1 illuminates. (3) Press A to enter calibration mode — LED2 turns on. (4) Rotate each joystick in full circles three times, reaching maximum range. (5) Press each trigger fully with normal pressure three times. (6) Press A again to confirm and exit — calibration complete. The Blitz Wireless has Hall Effect joysticks which are drift-resistant by design — drift may indicate calibration offset rather than physical wear. If drift persists after calibration, contact support."
            },
            {
                "tag": "Controller lock and power management",
                "scenario": "A customer says: 'I put my Blitz Wireless in my bag and it kept turning on by itself draining the battery. Also how do I properly turn it off and what happens if it freezes?'",
                "question": "Explain power off, auto-sleep, the lock feature and reset on the Blitz Wireless.",
                "rubric": "Manual power off: hold HOME button for 5 seconds. Auto sleep: 5 minutes of inactivity while connected. If searching for dongle with no success: auto powers off after 1 minute. Controller lock (prevents accidental button wake-up in bag): hold SELECT+R3 (right stick click down) for 5 seconds until all four LEDs light up — locks button wake-up feature. To unlock: plug in a USB charger. Reset (if frozen or not functioning correctly): hold HOME for 8 seconds to force reset. Must distinguish: power off (HOME 5s) vs reset (HOME 8s) vs lock (SELECT+R3 5s)."
            },
            {
                "tag": "Charging and discontinued status",
                "scenario": "A customer says: 'My Blitz Wireless is not charging properly. I am using a fast charger. Also a friend wants to buy one — where can they get it?'",
                "question": "Diagnose the charging issue and be honest about the discontinued status of the Blitz Wireless.",
                "rubric": "Charging: use the included USB-A to USB-C cable with a PC USB port or standard 5V/1A charger. Fast chargers and mobile chargers WILL damage the battery and void the warranty — this is the cause of the charging issue. Charging indicators: while charging in connected mode, the mode LEDs blink slowly. Fully charged in connected mode: LEDs stay steady. While charging in disconnected mode: all four LEDs blink slowly. Fully charged in disconnected mode: all four LEDs stay steady. Charging time: 2-3 hours. Battery life: 7-15 hours depending on usage. Discontinued status: the Blitz Wireless is a discontinued model and is no longer sold new by Cosmic Byte. Agent should be honest — if a friend wants to buy a Blitz controller, they should look at the current Blitz Tri-Mode which is the active model with more features. Warranty: 1 year manufacturing defects only. Physical and water damage not covered."
            },
            {
                "tag": "Blitz Wireless vs Blitz Tri-Mode — key differences",
                "scenario": "A customer says: 'I have a Blitz Wireless and my colleague has a Blitz Tri-Mode. He says his has features mine does not. What is the difference and why do some troubleshooting steps not work on mine?'",
                "question": "Clearly explain the key differences between the Blitz Wireless and Blitz Tri-Mode so the agent can set correct expectations.",
                "rubric": "Key differences agents must know: Connectivity: Blitz Wireless = 2.4GHz dongle + USB wired only. Blitz Tri-Mode = 2.4GHz + USB Wired + Bluetooth (three modes). Gyro: Blitz Wireless = NO gyro. Blitz Tri-Mode = gyro via Bluetooth. Macro: Blitz Wireless = NO macro programming. Blitz Tri-Mode = full macro support (hold TURBO 3s to record). iOS Dualshock mode: Blitz Wireless = NOT available. Blitz Tri-Mode = TURBO+HOME for Dualshock mode. Steam Mode: Blitz Wireless = NOT available. Blitz Tri-Mode = hold R3 while plugging USB. Charging dock: Blitz Wireless = NOT supported. Blitz Tri-Mode = supported (sold separately). Joystick tech: Blitz Wireless = Hall Effect joystick + Hall Effect trigger. Blitz Tri-Mode = TMR joystick + Hall Effect trigger. Availability: Blitz Wireless = DISCONTINUED. Blitz Tri-Mode = current active model. Agents should use the correct manual for each — steps from Tri-Mode manual will NOT work on Wireless model."
            }
        ]
    },
    {
        "id": "eclipse",
        "name": "Eclipse",
        "category": "Controller",
        "description": "Tri-mode controller (2.4GHz / Bluetooth 5.3 / Wired USB-C). Compatible with PC, Android, iOS 13+. 1200mAh battery (11-13hrs). Adjustable joystick resistance roller, trigger travel switch, ABXY layout switch, gyro, macro M1/M2 buttons, KeyLinker app, wireless charging contacts, replaceable D-pad, ~10m range.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity modes and first-time setup",
                "scenario": "A new customer just unboxed their Eclipse and asks: 'How do I connect this to my PC via 2.4GHz? And how do I connect via Bluetooth to my Android phone and iPhone? What does the logo light colour tell me?'",
                "question": "Explain all connection methods on the Eclipse and what the logo indicator light colours mean.",
                "rubric": "Logo light colours: Blue = iOS or Android (Bluetooth). Orange = 2.4G mode. Logo breathes green = charging. Logo flashes red once every 10 minutes = low battery. Logo turns off = fully charged. 2.4GHz first-time setup: set the physical mode switch to 2.4G (middle position), plug USB receiver into device, with controller powered OFF press and hold Pairing button for 3 seconds — logo flashes rapidly, then turns solid and controller vibrates to confirm connection. Bluetooth setup: set mode switch to Bluetooth (left position), with controller powered OFF press and hold Pairing button for 3 seconds — logo flashes rapidly, on device enable Bluetooth and select 'Xbox Wireless Controller', solid logo + vibration confirms pairing. Wired: connect USB-C cable — wired mode activates automatically. Reconnection to last paired device: short-press Home button. Physical mode switch positions: Left=Bluetooth, Middle=2.4G, Right=NS (Switch/XInput Bluetooth)."
            },
            {
                "tag": "ABXY layout switch and button mapping issues",
                "scenario": "A customer says: 'My A and B buttons seem reversed compared to what my game expects. In some games the confirm button fires the wrong action. How do I fix this?'",
                "question": "Explain the ABXY layout switch on the Eclipse and how to fix incorrect button mapping.",
                "rubric": "The Eclipse has a physical ABXY Layout Switch on the front of the controller (noted on the product layout). This toggles between XBOX-style layout and Alternate-style layout. Customer should flip this physical switch to change between the two layouts. This is a hardware switch — no software needed. Additionally, turbo or macro may be causing unexpected button behaviour — check by cancelling turbo (press M + A a third time to cycle through and cancel) or clearing macros (hold M + M1/M2 for 3 seconds then exit without assigning). ABXY LED brightness is separate — adjusted with M + Right Stick Left/Right (4 levels: 0%, 30%, 70%, 100%). Important: gyro calibration must always be performed in XBOX (ABXY) layout mode."
            },
            {
                "tag": "Joystick resistance adjustment and dead zone",
                "scenario": "A customer says: 'My joystick feels too loose for FPS games — I want it stiffer. Also sometimes there is a slight drift even when I barely touch the stick at the centre.'",
                "question": "Explain the joystick resistance roller and dead zone adjustment on the Eclipse.",
                "rubric": "Joystick resistance (tension) adjustment: the Eclipse has a physical resistance adjustment roller/knob at the base of each analog stick — this is a unique hardware feature. To increase stiffness: rotate the roller clockwise. To decrease stiffness (looser): rotate counter-clockwise. Make adjustments gradually and test after each rotation. Stiffer = better for precision FPS aiming. Looser = better for quick flick responses. Dead zone toggle: press and hold both Left Stick (LS) and Right Stick (RS) simultaneously for 5 seconds — controller vibrates to confirm change — toggles between 5% deadzone (default, reduces accidental drift) and 0% deadzone (maximum precision, no filtering). Active zone shape toggle: hold M + LS or RS for 5 seconds to toggle between 10% square zone and 0% circle zone."
            },
            {
                "tag": "Turbo, Auto Turbo and clearing all",
                "scenario": "A customer says: 'My A button keeps firing super fast on its own. Also how do I set Auto Turbo on X so it fires without holding? How do I adjust speed and clear everything?'",
                "question": "Diagnose the auto-firing A button, explain Turbo and Auto Turbo setup, speed adjustment and clearing all turbo on the Eclipse.",
                "rubric": "Turbo cycling on any button works as follows — each press of M + that button cycles through states: Press 1 = Manual Turbo (fires rapidly while held, logo flashes red rapidly). Press 2 = Auto Turbo (fires continuously on single press). Press 3 = Cancel Turbo. Auto-firing A = Auto Turbo is active. Fix: press M + A once more (third press) to cancel. Turbo can be assigned to: A, B, X, Y, LB, LT, RT, D-pad only — RB is NOT in the supported list. Speed adjustment: hold M + Right Stick Up to increase speed, hold M + Right Stick Down to decrease — vibration confirms change. Clear ALL turbo: press M button twice, then hold M for 5 seconds — controller vibrates to confirm all turbo cleared."
            },
            {
                "tag": "Macro M1/M2 programming",
                "scenario": "A customer says: 'When I press M1 on my Eclipse nothing happens. I want to assign the A button to M1. How do I set it up, and how do I clear it later?'",
                "question": "Walk the customer through macro programming on the M1/M2 buttons of the Eclipse.",
                "rubric": "To assign macro to M1 or M2: (1) While controller is connected, hold M + M1 (or M2) for 3 seconds to enter programming mode. (2) Press the desired button to assign — up to 21 programmable buttons available: A/B/X/Y/D-pad/LB/RB/LT/RT/L3/R3/Menu/View/Joysticks. (3) Press M1 (or M2) again to save and exit. If no button is selected during programming, M1/M2 will be blank (cleared). To clear existing macro: hold M + M1 for 3 seconds, then exit without pressing any assignment button — macro is erased. M1 does nothing if no macro has been assigned yet."
            },
            {
                "tag": "Stick and trigger calibration",
                "scenario": "A customer says: 'My left joystick drifts slightly and my triggers feel like they are not registering at the right point. How do I calibrate them on the Eclipse?'",
                "question": "Walk the customer through the complete stick and trigger calibration process on the Eclipse.",
                "rubric": "Stick and Trigger Calibration steps: (1) Power on the controller. (2) Hold View + M + Menu simultaneously for 3 seconds to enter calibration — LED1 and LED3 will flash. (3) Rotate both joysticks clockwise 3 full turns. (4) Fully press both triggers 3 times. (5) Switch triggers to short travel mode using the trigger travel switch on the back, then press them fully 3 more times. (6) Press View button to exit — LED1 and LED3 will stay solid for 5 seconds then power off. This is the only calibration that covers both sticks AND the trigger short/long travel modes — both travel modes must be calibrated. Note: different from gyro calibration. Calibration must be done in XBOX layout mode."
            },
            {
                "tag": "Gyro calibration",
                "scenario": "A customer says: 'The gyro on my Eclipse is not responding correctly — it drifts when the controller is still on a table. How do I calibrate it?'",
                "question": "Walk the customer through gyro calibration on the Eclipse, including any important conditions.",
                "rubric": "Gyro calibration steps: (1) Power off the controller completely. (2) Place the controller flat on a stable, level surface — this is critical for accurate calibration. (3) Hold View + A + B + Home simultaneously to enter gyro calibration — LED1 and LED2 will flash. (4) After 1 second, press Menu to complete calibration — LEDs will turn off confirming success. IMPORTANT conditions: calibration MUST be performed in XBOX (ABXY) layout mode — if the layout switch is set to Alternate, gyro calibration will not work correctly. Controller must be completely still and on a flat surface during calibration. This is separate from stick/trigger calibration."
            },
            {
                "tag": "Trigger travel switch and trigger issues",
                "scenario": "A customer says: 'For FPS games I want the triggers to fire almost instantly with a light press. But for racing games I want the full gradual pull back. How does the trigger switch work on the Eclipse?'",
                "question": "Explain the trigger travel switch on the Eclipse and when to use each mode.",
                "rubric": "The Eclipse has a physical Trigger Travel Switch on the back of the controller — one for LT and one for RT, they can be set independently. Two positions: Long travel mode = full analog range, gradual pressure-sensitive input, best for racing and simulation games requiring precise throttle/brake control. Short travel mode = reduced travel distance, triggers respond almost instantly like a button, best for FPS and competitive games where fast trigger response matters. Customer physically flips the switch — no software needed. During calibration: both long and short travel modes must be calibrated separately — the calibration process specifically requires pressing triggers in long mode first, then switching to short mode and pressing again."
            },
            {
                "tag": "Battery, charging and KeyLinker app",
                "scenario": "A customer asks: 'How do I know when my Eclipse battery is low? Also what is the KeyLinker app and do I need it?'",
                "question": "Explain the battery indicators and the KeyLinker app on the Eclipse.",
                "rubric": "Battery indicators: Low battery = logo light flashes red once every 10 minutes (subtle — agent must know this is the low battery signal). Charging = logo light breathes green (pulsing). Fully charged = logo light turns off completely. Battery: 1200mAh, 11-13 hours playtime. Charging time: 3-4 hours. Input voltage: 5V 500mA. The Eclipse also has wireless charging contacts on the back — it can be charged wirelessly without plugging in a cable (requires compatible wireless charging dock). KeyLinker app: available on Google Play Store and Apple App Store — provides advanced customization and controller adjustments beyond what the hardware buttons allow. Not mandatory for basic use but recommended for users who want deeper configuration. Customer should download it for features like sensitivity curves, button remapping beyond hardware capabilities, etc."
            },
            {
                "tag": "Controller reset, power off and disconnection issues",
                "scenario": "A customer says: 'My Eclipse is behaving very strangely — LEDs flashing erratically and buttons not responding. Also it keeps disconnecting from Bluetooth. What do I do?'",
                "question": "Explain the reset process, power off, and how to resolve Bluetooth disconnection issues on the Eclipse.",
                "rubric": "Power off: hold Home button for 5 seconds. Auto power-off: 10 minutes of inactivity. Factory reset (clears all settings): use a small pin to press the Reset hole on the back of the controller — restores all factory defaults including clearing all macros, turbo, and pairing data. For erratic LED behaviour: hold Home 5 seconds to power off, then press Reset hole with pin, then reconnect. Bluetooth disconnection issues: (1) Delete old pairing entries from the device's Bluetooth list. (2) Set mode switch to Bluetooth (left). (3) Hold Pairing button 3 seconds — logo flashes rapidly. (4) Select 'Xbox Wireless Controller' on device. (5) If still failing, press Reset hole and retry full pairing. 2.4GHz disconnection: ensure dongle is directly in USB port (avoid USB hubs), check for interference, re-hold Pairing button 3 seconds. Vibration at 0% will not indicate anything — check M+Right Stick Up to increase vibration first if customer says vibration stopped."
            },
            {
                "tag": "Warranty and physical features",
                "scenario": "A customer says: 'I dropped my Eclipse and the D-pad broke off. Also I want to know if the wireless charging feature means I can use any Qi charger. Is my broken D-pad covered under warranty?'",
                "question": "Address the D-pad question, clarify the wireless charging contacts feature, and explain warranty coverage.",
                "rubric": "D-pad: the Eclipse comes with a replaceable D-pad in the box (package contents include Replaceable D-Pad x1). The customer may be able to swap in the spare D-pad if it is the same part. However, physical damage from dropping is NOT covered under warranty. Wireless charging contacts: the Eclipse has wireless charging contacts on the back — these are for use with a compatible charging dock/wireless charging surface, not necessarily standard Qi chargers. Customers should check compatibility with their specific charging solution. This is a premium feature not common on most controllers. Warranty: 1 year against manufacturing defects only. Physical damage from dropping is NOT covered. Water damage not covered. Tampered products not covered. Support: +91 7351615161 (Mon-Sat 10am-6pm), cc@thecosmicbyte.com."
            }
        ]
    },
    {
        "id": "starforge",
        "name": "Starforge",
        "category": "Controller",
        "description": "Tri-mode controller (2.4GHz / Bluetooth 5.3 / Wired USB-C). PC (XInput/DInput), Android 8.0+, iOS 13+, Smart TVs, Tesla vehicles. 1200mAh (10-12hrs). Swappable modular joystick modules (4 resistance levels), 4x back macro buttons (M1-M4), RGB light strips, trigger motor vibration, ABXY layout screw switch, gyro, KeyLinker app, Back+Start for XInput/DInput toggle, LS+RS+Home reset.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity modes, mode switch and LED indicators",
                "scenario": "A new customer asks: 'How do I connect my Starforge to my PC via 2.4GHz dongle, and also via Bluetooth to my Android phone and iPhone? The mode switch has multiple positions — what do they do? And what do the indicator lights mean?'",
                "question": "Explain all connectivity modes, the physical mode switch positions, and LED indicator states on the Starforge.",
                "rubric": "Physical mode switch positions (bottom of controller): Mobile Mode = Android and iOS wireless. NS Mode = Gyro controller mode. PC Mode = PC Bluetooth wireless. 2.4GHz Mode = PC wireless XInput. 2.4GHz first-time setup: set switch to 2.4G, insert USB receiver, with controller powered OFF hold Pairing button for 3 seconds — LED flashes rapidly, solid LED + vibration = connected. Bluetooth (PC or Mobile): set switch to PC Mode or Mobile Mode, with controller OFF hold Pairing button 3 seconds, on device open Bluetooth and connect to 'Xbox Wireless Controller', solid LED + vibration = paired. Wired: set switch to corresponding device position, connect USB-C cable, hold Back+Start for 3 seconds to toggle XInput/DInput in wired mode. Reconnection: short-press Home. LED status: solid red = low battery. Red slow breathing 0-30% = charging. Ice blue slow breathing 30-100% = charging. Solid ice blue = fully charged. Blinking blue = pairing/searching. Compatible with PC, Android 8.0+, iOS 13+ MFi games, Smart TVs, Tesla vehicles (via 2.4GHz)."
            },
            {
                "tag": "XInput vs DInput switching",
                "scenario": "A customer says: 'I connected my Starforge via the 2.4GHz dongle but my old 2002 game completely ignores it. Windows detects it fine. How do I switch input modes?'",
                "question": "Explain how to switch between XInput and DInput on the Starforge and when each is needed.",
                "rubric": "Old games only support DInput. In wired mode: hold Back + Start for 3 seconds to toggle between XInput and DInput. In 2.4GHz mode: the mode switch must be set to 2.4G — this mode operates as XInput by default on PC. If DInput is needed in 2.4GHz, customer should try the wired connection and use Back+Start to switch. In Bluetooth mode: the mode switch position (PC Mode vs Mobile Mode) determines the platform. Always relaunch the game after switching. Also verify the mode switch is correctly set to PC/2.4G and not accidentally on Mobile or NS mode."
            },
            {
                "tag": "Modular joystick replacement",
                "scenario": "A customer says: 'I want to swap the joystick modules on my Starforge to a stiffer resistance. How do I do this and what do I need to do afterwards?'",
                "question": "Walk the customer through the complete joystick module replacement process and post-replacement steps on the Starforge.",
                "rubric": "Steps: (1) Hold Home for 5 seconds to power off. Disconnect all cables and remove dongle. (2) Gently lift and remove the magnetic top cover on the joystick side — no tools needed, secured with magnets. (3) Use the included puller tool to carefully pull the joystick module upward to detach from socket — plug-and-play, no screws. (4) Take new joystick module (available in 60gf, 70gf, 120gf, 150gf resistance options). Align connector pins with socket, ensure flat edge of joystick base faces inward. (5) Press firmly and evenly until it clicks — firm pressure critical, if not fully seated causes drift. (6) Reattach magnetic cover, ensure it snaps securely. (7) Power on. MANDATORY after replacement: perform full stick and trigger calibration (Back+X+Home 1 second method). Calibration is required every time joystick modules are replaced. Package includes 3 extra joystick sets, 1 puller tool."
            },
            {
                "tag": "Stick and trigger calibration",
                "scenario": "A customer says: 'After swapping joystick modules my Starforge left stick drifts and the range feels wrong. How do I calibrate it?'",
                "question": "Walk the customer through the stick and trigger calibration process on the Starforge.",
                "rubric": "Stick and Trigger Calibration steps (note: different from Eclipse): (1) Power OFF the controller. (2) Press and hold Back + X + Home for 1 second — LED light strips start flashing. (3) Rotate BOTH joysticks clockwise 5 full rotations (more than Eclipse which is 3 rotations). (4) Fully press BOTH triggers 5 times — trigger lock must be at FULL range (long travel) only when doing this step. (5) Press Start button — light strips turn off, confirming successful calibration. Important: calibration must be performed in XBOX (ABXY) layout mode. Calibration required after: joystick module replacement, drift, inconsistent response, incorrect range, or any button registering automatically without being pressed. Unlike Eclipse, the Starforge calibration does NOT require switching to short trigger mode."
            },
            {
                "tag": "Gyro calibration and NS mode",
                "scenario": "A customer says: 'The gyro on my Starforge keeps drifting when the controller is flat on a table. Also what is NS mode on the mode switch?'",
                "question": "Explain gyro calibration and NS mode on the Starforge.",
                "rubric": "Gyro calibration: (1) Power off controller and place flat on a stable surface. (2) Hold Back + A + Home for 3 seconds to enter gyro calibration — left and right indicator lights flash. (3) Press Start — light strips turn off confirming calibration. Controller must be completely still on a flat surface. Calibration must be in XBOX ABXY layout mode. NS mode: the mode switch position labelled NS = Gyro Controller Mode — this is a specific gyro-enabled Bluetooth mode, not Nintendo Switch mode despite the NS label. It enables motion control features when connected to compatible devices via Bluetooth. It is separate from standard PC Bluetooth and Mobile modes."
            },
            {
                "tag": "M1/M2/M3/M4 macro buttons",
                "scenario": "A customer says: 'My Starforge has four back buttons M1, M2, M3, M4. When I press M2 it fires a random sequence I never set. How do I fix it, set up a new macro, and cancel one?'",
                "question": "Explain how macros work on all four M buttons of the Starforge and how to fix, set and cancel them.",
                "rubric": "The Starforge has 4 back macro buttons: M1, M2, M3, M4 — more than most controllers. M2 firing randomly = macro was accidentally recorded on it. To record/replace macro on any M button: (1) While connected, press and hold Fn + M1/M2/M3/M4 for 3 seconds — light strip flashes. (2) Press the button to assign (A/B/X/Y, D-Pad, LB/RB/LT/RT, L3/R3, joystick clicks, +/-). Up to 32 programmable buttons allowed. (3) Press the M button again to save. To cancel/clear macro: press Fn + M1/M2/M3/M4 again — this cancels/clears the macro on that button. Each M button is programmed and cancelled independently using Fn as the modifier. Up to 32 programmable buttons supported (more than Eclipse's 21)."
            },
            {
                "tag": "Turbo, Auto Turbo and turbo speed",
                "scenario": "A customer says: 'My B button keeps auto-firing rapidly by itself. Also how do I set up turbo on Y, adjust the speed, and clear all turbo?'",
                "question": "Diagnose the auto-firing B button, explain Turbo/Auto Turbo setup, speed adjustment and clearing all on the Starforge.",
                "rubric": "The Starforge turbo system cycles with each press of the same combo: Press 1 = Manual Turbo (rapid fire while held). Press 2 = Auto Turbo (fires on single press continuously). Press 3 = Cancel. Auto-firing B = Auto Turbo active. Fix: press Turbo + B one more time to cancel. To enable turbo on Y: press Turbo + Y = Manual Turbo. Press Turbo + Y again = Auto Turbo. Press Turbo + Y once more = cancel. Turbo works on: A, B, X, Y, LB, RB, LT, RT. Speed adjustment: Turbo button + Right Stick Right = increase one level. Turbo button + Right Stick Left = decrease one level. Three levels: 5 presses/sec (slow), 12 presses/sec (default), 20 presses/sec (fast). Clear ALL turbo: hold Turbo button for 5 seconds — vibration confirms all cleared."
            },
            {
                "tag": "RGB lighting, ABXY LED and vibration",
                "scenario": "A customer says: 'How do I change the RGB colours on my Starforge? Also the ABXY buttons have gone dark. And my vibration seems very weak. How do I adjust all three?'",
                "question": "Explain RGB strip adjustment, ABXY LED toggle, and vibration adjustment on the Starforge.",
                "rubric": "RGB light strip: Brightness = press Fn + Left D-pad. Lighting effects/patterns = press Fn + Right D-pad. These control the decorative RGB strips. ABXY LED: to toggle ABXY button lighting on or off — press and HOLD Fn + D-pad Left for 5 seconds — lights switch state (ON to OFF or OFF to ON) after the hold duration. This is different from RGB brightness (which is a short press). Vibration adjustment: five levels — 0% (off), 25%, 50%, 75%, 100%. Increase: hold Fn + Up D-pad. Decrease: hold Fn + Down D-pad. Also ensure vibration is enabled in the game settings. Also check trigger motor vibration mode (separate) — press both triggers + Fn simultaneously for 1 second to cycle through 4 trigger vibration modes."
            },
            {
                "tag": "Trigger motor vibration and ABXY layout switch",
                "scenario": "A customer says: 'My triggers have a slight buzz/vibration that I never set up. Also my A and B buttons seem swapped compared to other controllers. How do I fix both?'",
                "question": "Explain trigger motor vibration modes and the ABXY layout switch on the Starforge.",
                "rubric": "Trigger motor vibration: the Starforge has independent trigger vibration motors — separate from the main controller vibration. To cycle through modes: press BOTH triggers + Fn button simultaneously for 1 second. Four modes indicated by RGB light strip: Mode 1 = Linear vibration (strength increases with trigger depth), RGB1 ice blue 3 seconds. Mode 2 (DEFAULT) = Bluetooth game-native vibration signals, RGB2 ice blue 3 seconds. Mode 3 = Synchronized with large motor vibration, RGB3 ice blue 3 seconds. Mode 4 = Trigger vibration OFF, RGB4 ice blue 3 seconds. The buzz the customer experiences is Mode 1 or 2 active — set to Mode 4 to disable. ABXY layout switch: locate the small screw in the centre of the ABXY buttons on the front. Use the included screwdriver (in package) to rotate the screw clockwise or counterclockwise to switch between layouts — vibration confirms layout change. Restart controller after changing layout."
            },
            {
                "tag": "Controller reset, power functions and connectivity troubleshooting",
                "scenario": "A customer says: 'My Starforge is completely frozen — no buttons respond, LEDs are stuck. Also Bluetooth keeps dropping. What do I do?'",
                "question": "Walk the customer through the reset process and Bluetooth troubleshooting on the Starforge.",
                "rubric": "Controller reset (factory soft reset): (1) Ensure controller is powered OFF. (2) Press and hold LS + RS + Home for 1 second — red light turns on for 1 second then controller auto powers off confirming successful reset. Use reset when: buttons/joysticks stop responding completely, controller fails to connect via Bluetooth or 2.4GHz even after re-pairing, controller stuck in pairing or update mode, RGB/LEDs freeze. After reset: reconnect or re-pair, recalibrate joysticks if needed. Power off manually: hold Home for 5 seconds. Auto power-off: 10 minutes inactivity. Bluetooth dropping: remove previous connection from device Bluetooth list, ensure mode switch on correct position (PC Mode for PC Bluetooth, Mobile Mode for phone), hold Pairing button 3 seconds, select 'Xbox Wireless Controller'. 2.4GHz not connecting: ensure dongle inserted, set switch to 2.4G, hold Pairing button 3 seconds, check for USB hub (avoid) or interference. Firmware: check for latest firmware via Cosmic Byte Starforge Firmware Tool on website — do not disconnect during update."
            },
            {
                "tag": "Warranty, package contents and unique features",
                "scenario": "A customer asks: 'What is included in the Starforge box? Also I spilled water on it — is it covered? And I heard it works with Tesla cars?'",
                "question": "List package contents, explain warranty coverage, and confirm the Tesla/Smart TV compatibility claim.",
                "rubric": "Package contents: Starforge Gaming Controller x1, Magnetic Cover x1, 2.4G USB Receiver x1, Type-C USB Cable (1.5m) x1, User Manual x1, Extra Joystick Sets x3, Puller x1, Screwdriver x1. The screwdriver is for the ABXY layout screw switch. The 3 extra joystick sets cover different resistance levels (60gf, 70gf, 120gf, 150gf available). Puller is for removing joystick modules. Tesla vehicles: yes, the Starforge officially supports Tesla vehicle connectivity via 2.4GHz mode — this is a documented feature. Smart TVs are also supported. Warranty: 1 year against manufacturing defects only. Water damage is explicitly NOT covered. Physical damage not covered. Tampered products not covered. KeyLinker app available for advanced customisation. Wireless range: approximately 10 metres. Battery: 1200mAh, 10-12 hours playtime, 3-4 hours charging time."
            }
        ]
    },
]

PASS_MARK = 70

# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": "home",
        "agent_name": "",
        "active_product": None,
        "current_q": 0,
        "scores": [],
        "feedbacks": [],
        "answers": [],
        "earned": 0,
        "possible": 0,
        "all_results": [],
        "grading": False,
        "current_grade": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────
#  GRADE ANSWER
# ─────────────────────────────────────────────
def grade_answer(answer, question, scenario, rubric, product_name):
    prompt = f"""You are grading a customer support agent for the Cosmic Byte {product_name}.

QUESTION: {question}
SCENARIO: {scenario}

RUBRIC (what a complete answer must include):
{rubric}

AGENT ANSWER:
"{answer}"

Grade out of 10:
- 9-10: All key points correct, genuinely helpful to a customer
- 7-8: Most key points covered, minor gaps
- 5-6: Partially correct, missing some important points
- 3-4: Some relevant content but significant gaps
- 0-2: Incorrect or too vague

Reply with ONLY raw JSON, no markdown, starting with {{ and ending with }}:
{{"score":7,"feedback":"What was good and what was missing from their answer."}}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        import re
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            result = json.loads(match.group())
            return {
                "score": max(0, min(10, round(float(result.get("score", 5))))),
                "feedback": result.get("feedback", "No feedback provided.")
            }
        return {"score": 5, "feedback": raw}
    except Exception as e:
        return {"score": 0, "feedback": f"Grading error: {str(e)}"}

# ─────────────────────────────────────────────
#  HOME SCREEN
# ─────────────────────────────────────────────
def show_home():
    st.markdown("## 🎮 Cosmic Byte — Agent Test Portal")
    st.markdown("Type your answers in plain language, just like responding to a real customer. Claude grades each answer instantly.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Questions", "10–12")
    col2.metric("To pass", "70%")
    col3.metric("Grading", "AI")
    col4.metric("Duration", "~15 min")

    st.divider()

    name = st.text_input("Your full name", placeholder="e.g. Priya Sharma", key="name_input")
    if name:
        st.session_state.agent_name = name.strip()

    st.divider()
    st.markdown("### Available tests")

    for product in PRODUCTS:
        with st.container():
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"**{product['name']}** `{product['category']}`")
                st.markdown(f"<small>{product['description']}</small>", unsafe_allow_html=True)
                st.markdown(f"<small>{len(product['questions'])} questions &nbsp;·&nbsp; 70% to pass</small>", unsafe_allow_html=True)
            with col_btn:
                if product["available"]:
                    if st.button("Start →", key=f"btn_{product['id']}", type="primary", disabled=not st.session_state.agent_name):
                        shuffled = product.copy()
                        shuffled["questions"] = random.sample(product["questions"], len(product["questions"]))
                        st.session_state.active_product = shuffled
                        st.session_state.current_q = 0
                        st.session_state.scores = []
                        st.session_state.feedbacks = []
                        st.session_state.answers = []
                        st.session_state.earned = 0
                        st.session_state.possible = 0
                        st.session_state.current_grade = None
                        st.session_state.screen = "quiz"
                        st.rerun()
                else:
                    st.button("Coming soon", key=f"btn_{product['id']}", disabled=True)
            st.divider()

    if not st.session_state.agent_name:
        st.info("Enter your name above to start a test.")

    # Leaderboard
    if st.session_state.all_results:
        st.markdown("### Leaderboard")
        sorted_results = sorted(st.session_state.all_results, key=lambda x: x["pct"], reverse=True)
        for i, r in enumerate(sorted_results[:20]):
            badge = "✅ Pass" if r["pct"] >= PASS_MARK else "❌ Fail"
            col1, col2, col3, col4, col5 = st.columns([0.5, 2.5, 1.5, 1, 1])
            col1.markdown(f"**{i+1}**")
            col2.markdown(r["name"])
            col3.markdown(f"<small>{r['product']}</small>", unsafe_allow_html=True)
            col4.markdown(f"**{r['pct']}%**")
            col5.markdown(badge)

# ─────────────────────────────────────────────
#  QUIZ SCREEN
# ─────────────────────────────────────────────
def show_quiz():
    product = st.session_state.active_product
    qs = product["questions"]
    cur = st.session_state.current_q
    q = qs[cur]
    total_qs = len(qs)

    # Header
    col1, col2 = st.columns([3, 1])
    col1.markdown(f"**{st.session_state.agent_name}** — {product['name']} test")
    col2.markdown(f"Points: **{st.session_state.earned}** / {st.session_state.possible}")

    # Progress
    progress_val = cur / total_qs
    st.progress(progress_val)
    st.markdown(f"<small>Question {cur+1} of {total_qs}</small>", unsafe_allow_html=True)

    st.divider()

    # Question
    st.markdown(f"`{q['tag']}`")
    st.markdown(f"**{q['question']}**")

    if q.get("scenario"):
        st.info(f"📋 {q['scenario']}")

    # Answer input — disabled if already graded
    already_answered = cur < len(st.session_state.answers)
    answer_val = st.session_state.answers[cur] if already_answered else ""

    answer = st.text_area(
        "Your answer",
        value=answer_val,
        placeholder="Write your answer here as you would explain it to a real customer...",
        height=150,
        disabled=already_answered,
        key=f"ans_{cur}"
    )

    if not already_answered:
        st.caption(f"{len(answer)} characters")

    # Show existing grade if already answered
    if already_answered and cur < len(st.session_state.scores):
        sc = st.session_state.scores[cur]
        fb = st.session_state.feedbacks[cur]
        level = "score-good" if sc >= 8 else "score-ok" if sc >= 5 else "score-weak"
        lbl = "Strong answer" if sc >= 8 else "Partial credit" if sc >= 5 else "Needs improvement"
        st.markdown(f"""<div class="score-box {level}">
            <strong>{sc}/10 — {lbl}</strong><br>{fb}
        </div>""", unsafe_allow_html=True)

    st.divider()

    col_back, col_space, col_next = st.columns([1, 2, 1])

    with col_back:
        if cur > 0:
            if st.button("← Back"):
                st.session_state.current_q -= 1
                st.rerun()

    with col_next:
        if already_answered:
            if cur < total_qs - 1:
                if st.button("Next →", type="primary"):
                    st.session_state.current_q += 1
                    st.rerun()
            else:
                if st.button("See results →", type="primary"):
                    st.session_state.screen = "result"
                    st.rerun()
        else:
            if st.button("Check answer →", type="primary"):
                if len(answer.strip()) < 15:
                    st.warning("Please write a more complete answer before submitting.")
                else:
                    with st.spinner("Grading your answer..."):
                        result = grade_answer(
                            answer.strip(),
                            q["question"],
                            q.get("scenario", ""),
                            q["rubric"],
                            product["name"]
                        )

                    st.session_state.answers.append(answer.strip())
                    st.session_state.scores.append(result["score"])
                    st.session_state.feedbacks.append(result["feedback"])
                    st.session_state.earned += result["score"]
                    st.session_state.possible += 10
                    st.rerun()

# ─────────────────────────────────────────────
#  RESULT SCREEN
# ─────────────────────────────────────────────
def show_result():
    product = st.session_state.active_product
    qs = product["questions"]
    earned = st.session_state.earned
    max_score = len(qs) * 10
    pct = round((earned / max_score) * 100)
    passed = pct >= PASS_MARK

    # Save result
    result_entry = {
        "name": st.session_state.agent_name,
        "product": product["name"],
        "earned": earned,
        "max": max_score,
        "pct": pct,
        "pass": passed,
        "date": datetime.now().strftime("%d %b %Y %H:%M")
    }
    existing = [r for r in st.session_state.all_results
                if not (r["name"] == result_entry["name"] and r["product"] == result_entry["product"] and r["date"] == result_entry["date"])]
    existing.append(result_entry)
    st.session_state.all_results = existing

    # Send email (only once per result)
    email_key = f"email_sent_{result_entry['name']}_{result_entry['product']}_{result_entry['date']}"
    if email_key not in st.session_state:
        st.session_state[email_key] = True
        with st.spinner("Sending results to manager..."):
            sent = send_result_email(
                st.session_state.agent_name,
                product["name"],
                earned, max_score, pct, passed,
                qs,
                st.session_state.scores,
                st.session_state.feedbacks,
                st.session_state.answers
            )

    # Hero
    st.markdown(f"## Results — {st.session_state.agent_name}")
    st.markdown(f"### {product['name']} Knowledge Test")

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{earned}/{max_score}")
    col2.metric("Percentage", f"{pct}%")
    col3.metric("Result", "PASS ✅" if passed else "FAIL ❌")

    if passed:
        st.success(f"Well done, {st.session_state.agent_name}! You demonstrated strong knowledge of the {product['name']}.")
    else:
        st.error(f"{st.session_state.agent_name}, a score of {PASS_MARK}% or above is required. Review the feedback below and retake when ready.")

    # Stats
    strong = len([s for s in st.session_state.scores if s >= 8])
    partial = len([s for s in st.session_state.scores if 5 <= s < 8])
    weak = len([s for s in st.session_state.scores if s < 5])

    col1, col2, col3 = st.columns(3)
    col1.metric("Strong (8-10)", strong)
    col2.metric("Partial (5-7)", partial)
    col3.metric("Weak (0-4)", weak)

    st.divider()

    # Review
    st.markdown("### Question by question review")
    for i, q in enumerate(qs):
        sc = st.session_state.scores[i] if i < len(st.session_state.scores) else 0
        fb = st.session_state.feedbacks[i] if i < len(st.session_state.feedbacks) else ""
        ans = st.session_state.answers[i] if i < len(st.session_state.answers) else ""
        level = "score-good" if sc >= 8 else "score-ok" if sc >= 5 else "score-weak"
        lbl = "Strong" if sc >= 8 else "Partial" if sc >= 5 else "Weak"
        with st.expander(f"Q{i+1}: {q['tag']} — {sc}/10 ({lbl})"):
            st.markdown(f"**{q['question']}**")
            st.markdown(f"*Your answer:* {ans}")
            st.markdown(f"""<div class="score-box {level}">{fb}</div>""", unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to portal"):
            st.session_state.screen = "home"
            st.rerun()
    with col2:
        if st.button("Retake test", type="primary"):
            original = next(p for p in PRODUCTS if p["id"] == st.session_state.active_product["id"])
            shuffled = original.copy()
            shuffled["questions"] = random.sample(original["questions"], len(original["questions"]))
            st.session_state.active_product = shuffled
            st.session_state.current_q = 0
            st.session_state.scores = []
            st.session_state.feedbacks = []
            st.session_state.answers = []
            st.session_state.earned = 0
            st.session_state.possible = 0
            st.session_state.current_grade = None
            st.session_state.screen = "quiz"
            st.rerun()


# ─────────────────────────────────────────────
#  SEND RESULT EMAIL
# ─────────────────────────────────────────────
def send_result_email(agent_name, product_name, earned, max_score, pct, passed, qs, scores, feedbacks, answers):
    try:
        gmail = st.secrets["GMAIL_ADDRESS"]
        app_password = st.secrets["GMAIL_APP_PASSWORD"]

        subject = f"[Cosmic Byte] {agent_name} — {product_name} Test — {'PASSED ✅' if passed else 'FAILED ❌'} ({pct}%)"

        body = f"""
COSMIC BYTE — AGENT TEST RESULT
================================
Agent:    {agent_name}
Product:  {product_name}
Date:     {datetime.now().strftime("%d %b %Y %H:%M")}
Score:    {earned} / {max_score}
Result:   {pct}% — {"PASSED ✅" if passed else "FAILED ❌"}
================================

QUESTION BY QUESTION BREAKDOWN:
"""
        for i, q in enumerate(qs):
            sc = scores[i] if i < len(scores) else 0
            fb = feedbacks[i] if i < len(feedbacks) else ""
            ans = answers[i] if i < len(answers) else ""
            lbl = "Strong" if sc >= 8 else "Partial" if sc >= 5 else "Weak"
            body += f"""
Q{i+1}: {q['tag']} — {sc}/10 ({lbl})
Question: {q['question']}
Agent answer: {ans}
Feedback: {fb}
{"─" * 50}"""

        body += f"""

{"Well done! Strong knowledge demonstrated." if passed else "Score below 70%. Recommend reviewing the manual before retaking."}

— Cosmic Byte Agent Training Portal
"""

        msg = MIMEMultipart()
        msg['From'] = gmail
        msg['To'] = gmail
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail, app_password)
            server.send_message(msg)

        return True
    except Exception as e:
        return False

# ─────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────
if st.session_state.screen == "home":
    show_home()
elif st.session_state.screen == "quiz":
    show_quiz()
elif st.session_state.screen == "result":
    show_result()
