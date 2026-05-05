import streamlit as st
import anthropic
import json
import time
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
    col1.metric("Questions", "10")
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
                        st.session_state.active_product = product
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
