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
