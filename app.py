"""
==============================================================================
COSMIC BYTE — AGENT TEST PORTAL  —  app version: 1.1.0
==============================================================================

What this file is:
  - Streamlit quiz UI for testing customer support agents on product knowledge
  - Claude Haiku 4.5 grades each free-form answer against a per-question rubric
  - Per-product question banks for each Cosmic Byte controller / mouse line
  - Email digest of results to the manager, including per-question timing
    flags and the test-taker's IP for cross-referencing against the support
    portal CSV log

Key dicts and constants (search for these to navigate):
  - PRODUCTS               -> list of products with id, name, category,
                              description, available, questions list
  - PASS_MARK              -> percent score required to pass (currently 70)
  - FAST_THRESHOLD_S       -> seconds under which an answer is flagged ⚡fast
                              in the result email; lives inline in
                              show_result and send_result_email

Companion file:
  - support_portal_v2.py   -> the customer-facing Claude-powered support
                              portal. From v2.10.0 it logs a "Client IP"
                              column on every conversation row, which is
                              what the cross-reference workflow joins
                              against the "Test IP" line in the email
                              digest produced by this file.

------------------------------------------------------------------------------
EDIT PROTOCOL  (READ THIS BEFORE EDITING THE FILE)
------------------------------------------------------------------------------
Every edit should follow the same versioning discipline used in
support_portal_v2.py so changes are traceable in the changelog below.

PRE-EDIT CHECKLIST:
  [ ] 1. Confirm you can ast.parse the file as-is (input is valid Python).
  [ ] 2. Read the latest 1-2 changelog entries to see what was just done.
  [ ] 3. Decide your version bump:
            X (major)  - rewrite, breaking change, restructure
            Y (minor)  - new section, new product, new feature
            Z (patch)  - bug fix, wording tweak, small addition

POST-EDIT CHECKLIST:
  [ ] 1. Bump __version__ on the line below this docstring to the new vX.Y.Z.
  [ ] 2. Update "app version: X.Y.Z" on the title line of this docstring.
  [ ] 3. Add a new entry at the TOP of the changelog with today's actual date
         (not a placeholder), the new version, "-- Author", and 1-N bullets
         describing what changed and why.
  [ ] 4. Run ast.parse again. If it fails, fix and re-run. Do not deliver a
         file that doesn't parse.

NOTES ON THE FORMAT:
  - The docstring uses triple-double-quotes. Do NOT type a literal sequence
    of three double-quote characters anywhere inside this docstring -- it
    will close the docstring early and break the file. If you need to refer
    to triple-quoted strings, use the words "triple-quote" or "the closing
    quotes" in prose.

CHANGELOG FORMAT:
  vX.Y.Z (YYYY-MM-DD) -- author
       - bullet describing change

------------------------------------------------------------------------------
CHANGELOG (newest entry first)
------------------------------------------------------------------------------

v1.1.0 (2026-05-07) -- Claude
  - Y-bump: replace per-question timing with grader-side AI-style
    detection. User correction: agents are allowed to consult and
    paste from the product manual during the test; what is NOT
    allowed is using an AI tool to generate the answer. Timing
    flagged anyone using the manual at all, which punishes the
    behavior we want to permit. Removed.

  Removed (relative to v1.0.0):

  1. session_state.question_starts and session_state.question_times.
     Reset blocks in the Start and Retake handlers no longer touch
     these keys.

  2. The timer-start block in show_quiz (set the start ts the first
     time an unanswered question rendered).

  3. The elapsed-capture and append in the submit handler.

  4. The "-- 32s" / "-- 14s ⚡fast" suffix on each question's
     expander header in show_result, plus the FAST_THRESHOLD_S
     constant and the secs / time_lbl plumbing.

  5. The Timing line and ⚡FAST per-question markers in
     send_result_email; the question_times kwarg removed from the
     signature.

  Added:

  6. grade_answer now asks Claude Haiku to ALSO judge whether the
     answer reads as AI-generated rather than written or
     manual-pasted by the agent. The prompt explicitly tells the
     grader that manual-paste is allowed (clipped technical tone,
     wording matching the rubric, no customer-facing softening) and
     AI-generation is not (conversational framing, em-dashes,
     parallel bullets, generic warmth, polished prose covering
     every rubric point at once). Returns ai_likely: bool alongside
     score and feedback.

  7. session_state.ai_flags: list[bool], parallel to scores /
     answers / feedbacks. Reset in Start and Retake handlers.

  8. Result page: each question's expander shows "🤖 AI-style"
     after the score label when the grader flagged the answer.

  9. send_result_email: new ai_flags kwarg. Top of the body has an
     AI-style summary line (count of flagged questions) when any
     are flagged; per-question lines append "🤖 AI-STYLE" to the
     header for flagged questions.

  Caveats (please read before acting on a flag):
     - Grader flags are advisory, not verdicts. Haiku grading
       Haiku output gets the easy cases but will produce false
       positives on agents who write fluent paragraph answers and
       false negatives on agents who post-process AI output to
       sound less polished.
     - The right move is to combine the flag with the support-
       portal IP cross-reference from v1.0.0. A flagged answer
       AND a portal query from the same IP within the test window
       is the strong signal.

v1.0.0 (2026-05-07) -- Claude
  - Initial versioned release. The file existed before this in unversioned
    form; this entry codifies its state at v1.0.0 and starts the changelog
    so future changes are traceable on the same protocol as
    support_portal_v2.py. No code behavior changes in this bump -- only
    the docstring header, __version__ constant, and startup print were
    added.

  Scope at v1.0.0 (the cheat-detection work that landed in this file
  before versioning was introduced):

  1. Per-question timing tracking. session_state has question_starts
     (idx -> unix timestamp, set when each unanswered question first
     renders -- not on back/forward navigation) and question_times (list
     of seconds, parallel to scores / answers / feedbacks). On submit,
     elapsed seconds since first render are captured. The result page
     shows "-- 32s" or "-- 14s ⚡fast" (under FAST_THRESHOLD_S = 20s)
     in each question's expander header. The email digest carries a
     Timing line with the average and a list of any sub-threshold
     questions, plus per-question seconds in the per-question breakdown.

  2. Client IP capture. Helper _get_client_ip() reads X-Forwarded-For
     from st.context.headers (set by Streamlit Cloud and most managed
     proxies) with a fallback to X-Real-IP, degrading to "" on bare-
     metal deployments without a proxy or on Streamlit < 1.36. The IP
     is captured once into session_state during init_state and emitted
     in the email body as a "Test IP:" line. When unavailable the email
     shows an explicit "(unavailable -- check Streamlit deployment proxy
     config)" so the gap is loud, not silent.

  Operational:
     The Test IP plus per-question submission times in the result email
     are the join key against the support-portal CSV (which has a
     "Client IP" column as of support_portal_v2.py v2.10.0). Workflow:
     agent submits the test, the email tells you their IP and the
     timestamp of each answer, you filter the portal CSV for that IP in
     the surrounding window. Any portal query within ~60 seconds before
     a fast-flagged answer is the evidence trail.

==============================================================================
"""

__version__ = "1.1.0"

import streamlit as st
import anthropic
import json
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Print version on startup so it appears in deployment logs (Streamlit Cloud,
# Render, etc.). Helps confirm which version is actually live after a deploy.
print(f"[agent_test_portal] starting up — app version {__version__}", flush=True)

# ─────────────────────────────────────────────
#  CLIENT IP HELPER
#  Reads X-Forwarded-For from st.context.headers (set by Streamlit Cloud and
#  most managed proxies). First entry in the comma-separated list is the
#  original client. Returns "" on bare-metal deployments without a proxy or
#  on Streamlit versions older than 1.36 — degrades gracefully.
# ─────────────────────────────────────────────
def _get_client_ip():
    try:
        ctx = getattr(st, "context", None)
        if ctx is None:
            return ""
        headers = getattr(ctx, "headers", None)
        if headers is None:
            return ""
        for key in ("X-Forwarded-For", "x-forwarded-for"):
            v = headers.get(key)
            if v:
                return v.split(",")[0].strip()
        for key in ("X-Real-IP", "x-real-ip"):
            v = headers.get(key)
            if v:
                return v.strip()
        return ""
    except Exception:
        return ""

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
    {
        "id": "quantum",
        "name": "Quantum",
        "category": "Controller",
        "description": "Dual-mode (Wired + Wireless Bluetooth) PS4-style controller. Compatible with PS4, PS5 (PS4 games only), Nintendo Switch (wired), PC (PS4/Steam mode wired + XInput wired + BT), iOS 13+, Android. Magnetic drift-free joysticks, magnetic pressure-sensitive triggers, 6-axis gyro, RGB LED, 3.5mm audio jack, touchpad, ML/MR macro buttons, travel switch triggers, speakers, 1000mAh battery.",
        "available": True,
        "questions": [
            {
                "tag": "PS4 connection — first time and reconnect",
                "scenario": "A customer just unboxed their Quantum and asks: 'How do I connect this to my PS4 for the first time? And once it is paired, how do I reconnect it next time without repeating the whole process?'",
                "question": "Walk the customer through first-time PS4 connection and how to reconnect on subsequent sessions.",
                "rubric": "First-time PS4 connection: (1) Connect the USB cable from the Quantum controller to the PS4 console. (2) Press the Home/PS button — LED turns solid indicating successful connection. (3) Disconnect the cable — the controller will now work wirelessly via Bluetooth. The controller can also be used in wired mode while charging simultaneously. Reconnection (subsequent sessions): press and hold the Home/PS button for about 1 second — the controller will automatically connect to the console. Auto-sleep: if the controller cannot establish communication with PS4 within 15 seconds it enters sleep mode. In connected mode, 10 minutes of inactivity triggers sleep. Press PS button to wake up. Power off: hold PS button for 8-10 seconds until light turns off."
            },
            {
                "tag": "PS5 compatibility — what works and what does not",
                "scenario": "A customer says: 'I bought the Quantum to use on my PS5 as my main controller. Some games work but others do not detect it at all. Is it fully compatible with PS5?'",
                "question": "Explain the PS5 compatibility situation for the Quantum clearly and set correct expectations.",
                "rubric": "The Quantum has VERY LIMITED PS5 compatibility — agents must be honest and clear about this. It behaves like a PS4 controller on PS5. Only PS4 games running on PS5 will support the Quantum. PS5 native games will NOT support the Quantum. The controller cannot be used to start up or navigate the PS5 system menu the same way as an original PS5 controller. Recommended use: use an original PS5 DualSense controller to start up the PS5, then use the Quantum as a backup/second controller for PS4 games on PS5. Agents must NOT promise full PS5 compatibility — this would be misleading. The Quantum is primarily designed for PS4."
            },
            {
                "tag": "PC connection — PS4 mode vs XInput mode",
                "scenario": "A customer says: 'I connected my Quantum to my PC via USB but some games do not detect it. Also I want to use it on Steam. What modes are available and how do I switch?'",
                "question": "Explain the PC connection modes on the Quantum — PS4 Controller mode vs XInput mode — and how to switch between them.",
                "rubric": "PC Wired default mode: connect USB cable — controller defaults to PS4 Controller mode, recognised by PC as 'Wireless Controller' with blue LED. This mode supports PC Steam platform and the headphone/audio jack function. To switch to XInput mode (wired only): long-press Share + Options buttons together for 3 seconds — switches to XInput mode. XInput mode works better with most modern PC games that expect an Xbox-style controller. PC Bluetooth mode: press Share + Home/PS button when controller is off until LED blinks — search for 'Dualshock 4 controller' in Bluetooth settings and pair. IMPORTANT: Bluetooth on PC only works as PS4 Controller mode — XInput mode is NOT available via Bluetooth on PC. Bluetooth PC mode is detected as 'Wireless Controller' with blue light. For Steam games, the default PS4 wired mode is recommended as Steam natively supports DualShock 4."
            },
            {
                "tag": "Nintendo Switch connection",
                "scenario": "A customer says: 'I want to use the Quantum on my Nintendo Switch. How do I connect it and are there any limitations?'",
                "question": "Explain Nintendo Switch connectivity on the Quantum and any limitations.",
                "rubric": "Nintendo Switch — Wired connection: connect USB-C cable from Quantum to the Switch console (or dock), press the Home/PS button — LED turns solid confirming successful connection. Wired connection supports the headphone jack function. Bluetooth on Switch (via Change Grip/Order): Method 1 — first complete wired connection, then disconnect cable — controller works wirelessly. Method 2 — go to Switch Controllers menu > Change Grip/Order, with controller powered off hold Options + PS button until 4 LEDs flash quickly, release and wait for connection. Reconnect on Switch: press and hold Home/PS button for 1 second to auto-reconnect. Up to 2 players supported simultaneously. Limitation: the Quantum does not have all Switch-native features — it works as a compatible generic controller."
            },
            {
                "tag": "iOS and Android Bluetooth connection",
                "scenario": "A customer asks: 'How do I connect my Quantum to my iPhone and my Android phone? And I heard the lights are different colours for each — what do the colours mean?'",
                "question": "Explain iOS and Android Bluetooth connection and LED colour indicators for each.",
                "rubric": "iOS connection: supports iOS 13.0 and above. With controller powered off, press Share + PS/Home button until LED flashes white. Open iOS Bluetooth settings, find 'DUALSHOCK 4 Wireless Controller' and connect. LED turns PINK when connected to iOS. If the phone cannot find the controller within 60 seconds, it enters sleep mode. Limited functionality note: some iOS games may not support external controllers — Bluetooth devices work with limited functionality on iOS and some games may not work as expected. Android connection: with controller powered off, press Share + PS/Home button until LED flashes white. Open Android Bluetooth settings, find 'Wireless controller' and connect. LED turns WHITE when connected to Android. If cannot connect within 60 seconds, enters sleep mode. Power off when connected to Android: press and hold PS button for 10 seconds. LED colour summary: Blue = PS4/PC mode. Pink = iOS connected. White = Android connected or pairing mode."
            },
            {
                "tag": "Turbo function — enable, auto, speed and clear all",
                "scenario": "A customer says: 'My Cross button keeps auto-firing rapidly on its own. How do I stop it? Also how do I set up Turbo on Triangle and adjust the speed? And how do I clear all turbo at once?'",
                "question": "Diagnose the auto-firing Cross button and explain all turbo controls on the Quantum.",
                "rubric": "Auto-firing Cross = Turbo or Auto Turbo is active. The Quantum turbo cycles with each press of Turbo + button: Press 1 = Manual Turbo (fires fast while button held). Press 2 = Auto Turbo (fires on single press continuously). Press 3 = Disabled. Fix: press Turbo + Cross once more to cycle to disabled. Supported buttons: Triangle, Square, Circle, Cross, L1, L2, R1, R2, L3, R3. Setup Turbo on Triangle: press Turbo + Triangle simultaneously = Manual Turbo. Press Turbo + Triangle again = Auto Turbo. Press again = cancel. Three speed levels: 5 shots/sec (slow, LED flashes slowly), 15 shots/sec (medium, LED flashes at moderate rate), 25 shots/sec (fast, LED flashes quickly). Increase speed: when turbo is on, hold Turbo + right joystick Up. Decrease speed: hold Turbo + right joystick Down. Clear ALL turbo: press and hold Share + Turbo for 1 second until controller vibrates — all turbo functions cleared."
            },
            {
                "tag": "ML/MR macro buttons",
                "scenario": "A customer says: 'I pressed ML on the back of my Quantum and it fired a sequence of buttons I never set up. How do I clear it? And how do I record a new macro with a timed sequence?'",
                "question": "Explain macro recording, execution, timing and clearing on the ML/MR buttons of the Quantum.",
                "rubric": "The Quantum has two back macro buttons: ML and MR. Each can store 1-12 function button presses. Programmable buttons: Cross, Triangle, Square, Circle, R1, R2, L1, L2, D-pad Up/Down/Left/Right. Record macro: (1) While controller is on, press and hold Turbo button for 3 seconds — LED flashes slowly and controller vibrates (entered macro programming mode). (2) Press the buttons in the desired sequence — the macro RECORDS the time interval between presses (e.g. press B, wait 1 second, press A, wait 3 seconds, press X = macro fires with those exact delays). (3) Press ML or MR to save — LED stays steady and controller vibrates to confirm. Execute: press ML or MR during gameplay. Macro persists after disconnect — controller remembers last macro setting automatically. Clear macro: enter macro mode (hold Turbo 3s, LED flashes), then press ML or MR immediately — LED turns steady = macro cleared for that button."
            },
            {
                "tag": "RGB LED adjustment and travel switch triggers",
                "scenario": "A customer asks: 'How do I change the RGB colours and brightness on my Quantum? Also there are two switch buttons on the back — what do they do for the triggers?'",
                "question": "Explain RGB LED controls and the travel switch trigger buttons on the Quantum.",
                "rubric": "RGB Brightness: 6 levels — 0%, 20%, 40%, 60%, 80%, 100%. Increase brightness: hold Options button + press D-pad Up. Decrease brightness: hold Options + press D-pad Down. RGB Mode/Effects: hold Options button + press D-pad Left or Right to cycle through different RGB LED effects. The controller always remembers the last RGB effect selected. Travel Switch Buttons: the Quantum has two physical Travel Switch buttons on the back — one for LT (L2) and one for RT (R2). These toggle trigger travel distance between long and short mode. Long travel = full analog pressure-sensitive input, best for racing/simulation. Short travel = instant response, best for FPS. Each trigger can be set independently. This is the same trigger lock concept as other premium controllers — no software needed, physical switch."
            },
            {
                "tag": "Charging, battery indicators and power off",
                "scenario": "A customer says: 'How do I charge my Quantum? What do the different light colours and patterns mean during charging? And the controller suddenly turned off mid-game — why?'",
                "question": "Explain charging, all battery indicator states, and why the controller may auto power off on the Quantum.",
                "rubric": "Charging: use the included USB-A to USB-C cable. Connect to a computer USB-A port or standard USB power source. Do NOT use wall adapters/chargers — the manual explicitly states adapters can damage the battery. Charging in OFF state: light breathes orange. Fully charged: light turns off completely. Low battery warning (connected mode): when battery voltage drops below 3.5V the LED flashes three times rapidly. When voltage drops below 3.4V the controller automatically turns off — this is why it turned off mid-game. Customer must charge immediately. Power off manually: hold PS/Home button for 8-10 seconds until controller light turns off. Auto sleep/power off: 15 seconds without PS4 connection in search mode = sleep. 10 minutes of inactivity in connected mode = sleep. Goes beyond 10 metres connection distance = auto power off. Battery: 1000mAh."
            },
            {
                "tag": "Unique hardware features — touchpad, gyro, speakers, audio jack",
                "scenario": "A customer asks: 'Does the Quantum have a touchpad like a real PS4 controller? Also I heard it has speakers and gyro — how do these work? And does the 3.5mm jack work on PC?'",
                "question": "Explain the touchpad, gyro, speaker, and audio jack functionality on the Quantum.",
                "rubric": "Touchpad: yes, the Quantum has a functioning touchpad — it works as a clickable touchpad in PS4 games that use it. This is a differentiating feature not found on most third-party controllers. 6-axis gyro sensor: the Quantum has a built-in 6-axis gyro/motion sensor — works in PS4 games that support motion control (e.g. aiming, steering). This is hardware-level and works automatically when the game requests it. Speakers: the Quantum has built-in speakers — works in PS4 games that output audio through the controller speaker (e.g. in-game sounds, notifications). This is another genuine PS4 feature replicated. 3.5mm audio jack: the 3.5mm jack for headphones works in PS4 Controller mode (default wired or Bluetooth). In wired mode on PC it works in PS4/Steam mode. In XInput mode on PC the audio jack is NOT guaranteed to work. On Nintendo Switch wired mode the jack also functions. Magnetic joysticks and magnetic triggers: the Quantum uses magnetic (Hall Effect equivalent) technology for both joysticks and triggers — drift-free by design."
            },
            {
                "tag": "Warranty, reset and when to contact support",
                "scenario": "A customer says: 'My Quantum is behaving strangely with random button presses. Also I spilled some water on it and now it sometimes does not connect. What do I do and is any of this covered under warranty?'",
                "question": "Walk the customer through the reset process and explain warranty coverage honestly for both issues.",
                "rubric": "Reset: for abnormal behaviour press the reset button on the FRONT of the controller (small reset button/hole). This performs a factory reset and clears all saved configurations. After reset the customer will need to re-pair the controller to their device. Random button presses: first check if Turbo or Macro is accidentally active — clear all turbo (Share+Turbo 1 second) and check ML/MR macros. If still random, perform factory reset. Water damage: the Quantum is not waterproof. Water damage is explicitly NOT covered under warranty. Agent must be honest — if the connectivity issue is caused by water damage, the customer cannot claim warranty for it. Warranty: 1 year against manufacturing defects only. Physical damage not covered. Water damage not covered. Regular wear and tear from battery usage not covered. Support phone: 07969273222 (different from most other Cosmic Byte products which use 7351615161 — agent must note this). Email: cc@thecosmicbyte.com. FAQ: support.thecosmicbyte.com."
            }
        ]
    },
    {
        "id": "stratos_xenon",
        "name": "Stratos Xenon",
        "category": "Controller",
        "description": "PS4-style wireless controller. Wireless on PS4 (Bluetooth), wired on PC (optional wireless dongle sold separately), PS5 (limited), Android, iOS. Upgraded Hall Effect joystick, touchpad, 3.5mm audio jack, mic on/off switch, programmable back buttons (PS4 only), turbo, 1300mAh battery, 8m wireless range.",
        "available": True,
        "questions": [
            {
                "tag": "PS4 pairing — first time and reconnecting",
                "scenario": "A customer says: 'I just got my Stratos Xenon. How do I pair it with my PS4 for the first time? And once it is paired, how do I reconnect it the next time I want to play?'",
                "question": "Walk the customer through first-time PS4 pairing and subsequent reconnection on the Stratos Xenon.",
                "rubric": "First-time PS4 pairing: connect the controller to the PS4 console using the included USB cable. The controller pairs via USB — once connected it is registered with the PS4. After pairing the controller works wirelessly via Bluetooth on PS4 (up to 8 metres range). Disconnect the cable after pairing to go wireless. Reconnection on subsequent sessions: short-press the Home button — the controller will reconnect automatically to the paired PS4. Auto-sleep: if the controller cannot communicate with PS4 within approximately 15 seconds it enters sleep mode. If no button input for extended inactivity in connected mode it also sleeps. Press Home to wake. The Stratos Xenon is designed primarily for PS4 wireless use — this is its main intended platform."
            },
            {
                "tag": "PC connection — wired and wireless dongle",
                "scenario": "A customer says: 'I want to use my Stratos Xenon on my PC. I connected the USB cable but some games do not detect it. Also I heard I can use it wirelessly on PC — is that true?'",
                "question": "Explain PC connectivity on the Stratos Xenon including the wired mode limitations and the wireless dongle option.",
                "rubric": "PC wired connection: connect the USB cable to the PC. Windows will automatically detect the controller and install drivers — this may take up to 30 seconds. IMPORTANT limitation: the controller works as a PS4-style controller on PC, NOT as an XInput controller by default. Only Windows games that are compatible with PS4 controllers will work directly. For Steam: go to Steam Settings, select Controller, choose PS4 controller type — Steam will automatically convert PS4 inputs to support all Windows games. For non-Steam games: third-party software like DS4Windows is required to use the controller with all Windows games. PC wireless: the controller works wirelessly ONLY on PS4 by default. To use it wirelessly on PC the customer must purchase the Stratos Xenon Wireless Dongle separately from the Cosmic Byte website — with the dongle no extra steps are needed. Agents must be honest that the dongle is a separate purchase and is not included in the box."
            },
            {
                "tag": "PS5 compatibility and connection",
                "scenario": "A customer says: 'I bought the Stratos Xenon to use on my PS5. I connected it via USB and pressed the Home button and some things work. But some PS5 games ignore it. What is going on?'",
                "question": "Explain PS5 compatibility and connection process for the Stratos Xenon and set honest expectations.",
                "rubric": "PS5 connection steps: (1) Connect controller to PS5 via USB cable. (2) Press and hold Home button for over 2 seconds — LED indicator flashes white light indicating the controller has entered connection mode. (3) Wait over 5 seconds — LED changes colour indicating successful connection. After pairing via USB it can be used wirelessly. PS5 compatibility is LIMITED — the Stratos Xenon behaves like a PS4 controller on PS5. PS4 games running on PS5 will generally work. PS5 native games will NOT support this controller as PS5 requires the official DualSense. Cannot be used to start up PS5 or navigate the PS5 system menu fully. Recommend using an official DualSense to boot up PS5 then switching to the Stratos Xenon as a second controller for PS4 games. Agents must NOT promise full PS5 compatibility."
            },
            {
                "tag": "Android and iOS Bluetooth connection",
                "scenario": "A customer says: 'How do I connect my Stratos Xenon to my Android phone and my iPhone? The light on the controller is flashing — what do I do next?'",
                "question": "Explain Android and iOS Bluetooth pairing on the Stratos Xenon.",
                "rubric": "Android and iOS pairing: (1) Press and hold the PS button and Share button simultaneously on the controller to enter pairing mode — the light on the back will start flashing. (2) On the phone/tablet open Bluetooth settings and scan for nearby devices. (3) The controller appears as 'Wireless Controller' in the Available Devices list. (4) Tap 'Wireless Controller' — a confirmation prompt appears. Tap OK. Controller is now connected. If device does not detect controller automatically: go to Bluetooth settings manually and search. If controller cannot connect within the search window it will enter sleep mode after 60 seconds — repeat the pairing process. iOS note: iOS 13+ is required. Only games that support external controllers will work — some iOS games may not. Flashing light = pairing mode. Solid light = connected successfully."
            },
            {
                "tag": "Turbo function setup and cancel",
                "scenario": "A customer says: 'My A button keeps firing super fast on its own. Also how do I set up Turbo on the Y button and how do I cancel it?'",
                "question": "Diagnose the auto-firing A button and explain how Turbo works on the Stratos Xenon.",
                "rubric": "Auto-firing A button: Turbo is already active on A. The Stratos Xenon Turbo is a hold-to-fire type. To cancel: repeat the same steps used to enable — long press Turbo button + A simultaneously for 2 seconds then release. Set Turbo on Y: long press the Turbo button and Y button simultaneously for 2 seconds, then release the Turbo button — Turbo is now active on Y. While Turbo is active, holding Y will fire it rapidly. Cancel Turbo on Y: repeat the same steps — long press Turbo + Y for 2 seconds then release. Turbo works on: A, B, X, Y, L1, L2, R1, R2. Note: the Stratos Xenon Turbo requires a 2-second simultaneous hold to toggle — this is different from single-press turbo systems on other controllers."
            },
            {
                "tag": "Programmable back buttons",
                "scenario": "A customer says: 'I want to set up the back button on my Stratos Xenon to act as the A button. How do I do it? And I am trying it on my PC but it is not working at all.'",
                "question": "Explain programmable back button setup and the important platform limitation on the Stratos Xenon.",
                "rubric": "CRITICAL platform limitation: programmable back buttons ONLY work on PS4 console. They do NOT work on PC, PS5, Android, or iOS — this is the most likely reason the customer's setup on PC is failing. Agents must state this clearly. Setup on PS4: (1) Long press the Turbo button for 5 seconds — LED turns green. (2) Press the back button to program — LED flashes. (3) Press the desired action button (e.g. A) — LED turns off confirming the back button is now mapped to that action. Cancel a programmable back button: (1) Long press Turbo for 5 seconds — LED turns green. (2) Press the target action button TWICE — LED turns off confirming cancellation. Each back button is programmed independently using this process."
            },
            {
                "tag": "Mic switch and audio jack",
                "scenario": "A customer says: 'There is a switch on the back of my Stratos Xenon labelled Mic. My headset mic is not working. Also I want to use the 3.5mm jack on PC — will it work?'",
                "question": "Explain the mic switch and 3.5mm audio jack functionality and limitations on the Stratos Xenon.",
                "rubric": "Mic switch: the Stratos Xenon has a physical mic on/off switch on the back of the controller. Slide left = microphone ON. Slide right = microphone OFF. IMPORTANT limitation: the mic function only works on PS4. If the customer is on PC, PS5, Android, or iOS the mic switch will have no effect. The mic passes audio from a headset connected to the 3.5mm jack. 3.5mm audio jack: supports headsets with a 3.5mm connector. Works on PS4 for both audio output and mic input. On PC (wired): audio output through the jack may work as the controller is detected as a USB audio device in PS4 controller mode — however this is not guaranteed for all PC configurations and mic function is PS4 only. On PS5, Android, iOS: audio jack support varies and mic is PS4 only. If mic is not working: check the physical switch position, ensure headset is fully plugged in, confirm they are on PS4."
            },
            {
                "tag": "Hall Effect joystick and drift",
                "scenario": "A customer says: 'My Stratos Xenon left joystick is drifting slightly even when I am not touching it. I thought Hall Effect joysticks do not drift. Is mine broken?'",
                "question": "Explain Hall Effect joysticks on the Stratos Xenon and how to address drift.",
                "rubric": "The Stratos Xenon features upgraded Hall Effect joysticks — these use magnetic sensors instead of physical contact potentiometers. Hall Effect joysticks are drift-resistant by design because there is no physical wear from contact. However 'drift-resistant' does not mean 'drift-proof forever' — calibration offset can still occur after physical impact, extended use, or if the controller is tilted when powered on. Steps to address drift: (1) Ensure the controller is on a flat, stable surface when powered on — the joystick position at startup is used as the centre reference. (2) Check the game's controller settings for deadzone adjustment — increasing deadzone slightly can eliminate minor drift in-game. (3) If drift is severe and persistent across all games and all connection modes it may indicate a manufacturing defect and the customer can contact support within the 1-year warranty period. Physical damage from dropping is not covered. The Stratos Xenon manual does not include a formal calibration procedure — if drift persists after the above steps, escalate to support."
            },
            {
                "tag": "Battery, charging and care",
                "scenario": "A customer asks: 'How do I charge my Stratos Xenon? How do I know when it is low on battery? Also I have had it for 6 months and the battery life seems much shorter now — is that covered under warranty?'",
                "question": "Explain charging, battery indicators, and the warranty position on battery degradation for the Stratos Xenon.",
                "rubric": "Charging: use the included USB cable to charge. Connect to a USB power source such as a PC USB port. Charging voltage: 4.5-5.5V. Charging current: under 260mA. Charging time: 2.5-3.5 hours for a full charge. Battery: 1300mAh built-in rechargeable lithium-ion (larger than many controllers). Charging indicator: light breathing/glowing indicates charging in progress. Charge in environments between 10°C-30°C for best results — extreme temperatures reduce charging efficiency. Low battery: LED will flash to indicate low battery. When battery is critically low the controller will auto power off. Battery lifespan: battery life naturally decreases with repeated usage and age — this is normal and expected. The manual explicitly states this. Battery degradation over 6 months is considered regular wear and tear and is NOT covered under warranty. Recommend charging fully at least once a year if storing for extended periods. If not using for a long time, turn off the controller to preserve battery."
            },
            {
                "tag": "Wireless range, sleep and power off",
                "scenario": "A customer says: 'My Stratos Xenon keeps disconnecting when I move around my room. Also I am not sure how to properly turn it off. And sometimes it turns on by itself in my bag.'",
                "question": "Explain wireless range, auto-sleep, manual power off, and how to prevent accidental power-on on the Stratos Xenon.",
                "rubric": "Wireless range: maximum 8 metres. If the customer moves beyond 8 metres the connection will drop and the controller may auto power off. Walls, furniture, and other 2.4GHz devices can reduce effective range. Ensure clear line of sight where possible. Keep away from Wi-Fi routers and other wireless devices that may cause interference. Sleep mode: controller enters sleep if it cannot communicate with PS4 within ~15 seconds of searching. In connected mode, significant inactivity triggers sleep. Press Home to wake. Power off: to properly turn off the controller press and hold the PS/Home button for several seconds until the light turns off. Always power off when not in use to preserve battery. Accidental power-on in bag: there is no dedicated lock mode on the Stratos Xenon. To prevent accidental wake-up: power the controller off completely using the Home button hold before placing in a bag. The controller will not turn on unless the Home button is pressed."
            },
            {
                "tag": "Warranty coverage and support",
                "scenario": "A customer says: 'I dropped my Stratos Xenon and now one of the back buttons does not work. Also I spilled juice on it and it started behaving strangely. I have had it 8 months. What is covered under warranty?'",
                "question": "Explain warranty coverage honestly for both issues on the Stratos Xenon.",
                "rubric": "Warranty: 1 year against manufacturing defects only. Two issues to address separately: (1) Dropped controller — back button stopped working: physical damage from dropping is explicitly NOT covered under warranty. The damage is user-caused. (2) Liquid spill — strange behaviour: water/liquid damage is explicitly NOT covered under warranty. Neither issue qualifies for warranty support. Agents should be honest but polite. If the customer believes the back button issue was a pre-existing manufacturing defect unrelated to the drop they could attempt to make a case — but physical impact damage complicates any such claim significantly. Battery wear and tear is also not covered. What IS covered: genuine manufacturing defects within 1 year — e.g. a button that never worked from the box, a joystick that drifted from day one with no physical cause. Support contact: 07969273222 (Mon-Sat 10am-6pm — note this is the same number as Quantum, different from most other CB products which use 7351615161). Email: cc@thecosmicbyte.com. Scan QR code in manual for warranty claim procedure."
            }
        ]
    },
    {
        "id": "velox",
        "name": "Velox",
        "category": "Mouse",
        "description": "Tri-mode gaming mouse (2.4GHz / Bluetooth 5.3 / Wired USB-C). PixArt PAW3395 sensor, 26000 DPI, 1000Hz polling rate, 650 IPS, 50G acceleration. 39g ultralight, PTFE feet, 230mAh battery, Huano switches (100M clicks). Windows & macOS.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity — all three modes",
                "scenario": "A new customer asks: 'How do I connect the Velox to my PC via 2.4GHz dongle? And how do I connect it via Bluetooth? Also what happens if I just plug in the USB-C cable?'",
                "question": "Explain all three connection modes on the Velox and how to set each one up.",
                "rubric": "Physical mode switch on the bottom of the mouse: Up = 2.4GHz mode. Middle = OFF (wired mode when cable connected). Down = Bluetooth mode. Wired mode: connect USB-C cable to mouse and PC — Green LED stays ON confirming wired mode. No setup required, works immediately. 2.4GHz mode: switch to Up position, plug in USB receiver — auto-connects. If manual pairing needed: switch to 2.4GHz, hold Left Click + Right Click + Scroll Wheel for 3 seconds — Red LED flashes confirming pairing mode, insert receiver — Green LED solid briefly then off = connected. Bluetooth mode: switch to Down position, hold Left Click + Right Click + Scroll Wheel for 3 seconds — Blue LED flashes = pairing mode. On device open Bluetooth, select 'CB Velox' (also may appear as 'blemouse5.3' depending on device — both refer to the Velox). Blue LED turns solid briefly then off = connected. Wireless range: greater than 10 metres. Supported systems: Windows and macOS."
            },
            {
                "tag": "DPI levels and LED colour codes",
                "scenario": "A customer asks: 'How do I change the DPI on my Velox? And how do I know which DPI level I am on? The light turned pink and I do not know what that means.'",
                "question": "Explain DPI switching and the complete LED colour map for DPI levels on the Velox.",
                "rubric": "DPI button is on the top of the mouse. Each press of the DPI button cycles to the next level. Six DPI levels: 800 DPI = Blue LED. 1600 DPI = Green LED. 2400 DPI = Pink LED (DEFAULT — this is why the customer sees pink). 3200 DPI = Yellow LED. 5800 DPI = Cyan LED. 7200 DPI = White LED. When DPI button is pressed the colour-coded LED illuminates for 3 seconds then turns off. Default is 2400 DPI (pink). Sensor: PixArt PAW3395. Max DPI: 26000 (achievable via software — 6 hardware DPI steps shown above). Software downloadable from thecosmicbyte.com allows custom DPI configuration beyond the 6 hardware steps."
            },
            {
                "tag": "LED indicators — mode and battery status",
                "scenario": "A customer says: 'The light on my Velox is flashing red rapidly. Also sometimes I see a slow blue flash and sometimes a fast blue flash. What do all these lights mean?'",
                "question": "Explain all LED indicator states on the Velox — mode indicators and battery/charging indicators.",
                "rubric": "Mode LEDs: Wired mode = Green LED steady ON always. 2.4GHz mode = Red LED (slow flash = trying to reconnect to receiver; fast flash = manual pairing mode active). Bluetooth mode = Blue LED (slow flash = trying to reconnect to last device; fast flash = pairing mode active). DPI levels: flash colour for 3 seconds when DPI button pressed (Blue=800, Green=1600, Pink=2400, Yellow=3200, Cyan=5800, White=7200). Battery/charging LEDs: Red LED flashing rapidly = low battery (below 3.2V) — charge immediately. Green flashing = charging in progress. Green steady = fully charged. Mouse shuts down automatically below 3.1V to protect battery."
            },
            {
                "tag": "Sleep modes and battery life",
                "scenario": "A customer says: 'My Velox mouse seems to go unresponsive after I stop using it for a while. There is a slight delay when I start moving it again. Also the battery drains faster than I expected — what can I do?'",
                "question": "Explain the sleep modes and give practical battery life tips for the Velox.",
                "rubric": "Two sleep modes: Light Sleep = after 1 minute of inactivity — wakes instantly on movement or button press. Deep Sleep = after 20 minutes of inactivity — slight delay on wake-up (this explains the customer's experience). To wake from deep sleep: move the mouse or press any button — the slight delay is normal and expected, not a defect. Battery: 230mAh rechargeable. Low power: below 3.2V = red LED flashes rapidly. Below 3.1V = auto shutdown to protect battery. Tips to extend battery life: ensure mouse enters sleep when not in use (do not disable sleep). Avoid frequently switching between modes. Lower DPI setting reduces sensor power draw. Use a good quality USB-C cable for charging. Do not use while charging with a faulty cable. Charging: 4.0V trickle to 4.2V full charge. Over-voltage protection at 6V. Surge protection at 24V."
            },
            {
                "tag": "2.4GHz not connecting or disconnecting",
                "scenario": "A customer says: 'My Velox is not being detected by my PC in 2.4GHz mode. I inserted the USB receiver but nothing happens. Also it keeps disconnecting during use.'",
                "question": "Walk the customer through diagnosing and fixing 2.4GHz connection issues on the Velox.",
                "rubric": "Step 1: check the bottom mode switch is set to Up (2.4GHz position) — not Middle (off/wired) or Down (Bluetooth). Step 2: ensure USB receiver is fully inserted into a working USB port — try a different port to rule out port issues. Step 3: check for interference — move receiver away from other USB devices, USB 3.0 drives, and Wi-Fi routers which can cause 2.4GHz interference. Step 4: if still not connecting, perform manual re-pair: with mouse in 2.4GHz mode (switch up), hold Left Click + Right Click + Scroll Wheel for 3 seconds until Red LED flashes (pairing mode), then insert the receiver — Green LED solid briefly then off = connected. Step 5: try the receiver in a USB 2.0 port (USB 3.0 ports can cause 2.4GHz interference). Reconnection: Red LED slow flash in 2.4GHz mode = mouse is searching for receiver — it will auto-reconnect when receiver is detected."
            },
            {
                "tag": "Bluetooth pairing not working",
                "scenario": "A customer says: 'I cannot get my Velox to pair via Bluetooth. I held the buttons and the blue light blinked but I cannot find it in my device's Bluetooth list. Also what is the device name I should look for?'",
                "question": "Walk the customer through Bluetooth troubleshooting on the Velox and clarify the Bluetooth device name.",
                "rubric": "Step 1: confirm bottom switch is set to Down (Bluetooth position). Step 2: press any button to wake the mouse if it is in sleep mode — the blue LED should be visible. Step 3: hold Left Click + Right Click + Scroll Wheel for 3 seconds until Blue LED flashes rapidly = pairing mode active. Step 4: on the device open Bluetooth settings and scan. Device name: the mouse may appear as 'CB Velox' OR 'blemouse5.3' — both refer to the same mouse, different pages of the manual reference both names. If customer cannot find it, look for both names. Step 5: if previously paired, remove the old pairing entry from the device's Bluetooth list first, then re-pair. Step 6: ensure the device supports Bluetooth 5.3. Blue LED solid briefly then off = successfully connected. Bluetooth mode slow flash = searching for last paired device (not in pairing mode — must do the 3-button hold to enter active pairing)."
            },
            {
                "tag": "Cursor lagging, skipping or inaccurate tracking",
                "scenario": "A customer says: 'My Velox cursor is skipping and lagging during gaming. It was smooth before. I am using the 2.4GHz dongle.'",
                "question": "Diagnose and fix cursor tracking issues on the Velox.",
                "rubric": "Step 1: check the surface — the PixArt PAW3395 sensor does not work well on glass or highly reflective surfaces. Use a mouse pad or non-reflective flat surface. Step 2: check DPI setting — if DPI is very high (5800 or 7200) and the surface is not ideal, tracking can appear erratic. Try a lower DPI setting using the DPI button. Step 3: check for wireless interference — in 2.4GHz mode, nearby USB 3.0 devices, Wi-Fi routers, and other 2.4GHz devices can cause lag. Move USB receiver closer to mouse or into a USB 2.0 port. Step 4: switch to wired mode temporarily to isolate whether the issue is hardware or wireless — if wired is smooth the problem is wireless interference. Step 5: check receiver is fully inserted. Step 6: try re-pairing (Left+Right+Scroll 3 seconds). Step 7: check if the mouse is in deep sleep wake-up — slight lag immediately after inactivity is normal deep sleep behaviour, not a tracking defect. Sensor specs: PAW3395, 650 IPS tracking speed, 50G acceleration, 26000 DPI max."
            },
            {
                "tag": "Buttons not responding",
                "scenario": "A customer says: 'The scroll wheel click and one of the side buttons on my Velox are not responding at all. The mouse moves fine.'",
                "question": "Walk the customer through diagnosing unresponsive buttons on the Velox.",
                "rubric": "Step 1: test in wired mode first — connect USB-C cable, set switch to Middle position — this isolates whether the issue is hardware or connection-related. If buttons work in wired mode, the problem is wireless. If buttons do not work even in wired mode, it is likely a hardware issue. Step 2: restart the computer and test again — driver or OS issues can occasionally cause specific buttons to stop registering. Step 3: check if any software (game or system) is remapping or blocking those buttons. Step 4: test in a different application — some games may not support all mouse buttons natively. Button specifications: Left Click and Right Click use Huano switches rated for 100 million clicks. Scroll Wheel: scroll + click function. Side Button 1 = Forward. Side Button 2 = Backward. If buttons are genuinely unresponsive in wired mode across multiple applications after restart, this may be a manufacturing defect — advise customer to contact Cosmic Byte support (+91 7351615161)."
            },
            {
                "tag": "Software, DPI customisation and macOS support",
                "scenario": "A customer asks: 'Is there software for the Velox? I want to set a custom DPI that is not one of the 6 preset levels. Also does it work on Mac?'",
                "question": "Explain the software availability, custom DPI capabilities, and macOS support on the Velox.",
                "rubric": "Software: yes, Cosmic Byte Velox software is available for download from thecosmicbyte.com — this is required for advanced customisation. The software allows custom DPI settings beyond the 6 hardware presets (which go up to 7200 DPI via button). Maximum DPI via software: 26000 DPI (the sensor's full capability). macOS support: yes, the Velox officially supports both Windows and macOS. The mouse works as a plug-and-play device on both operating systems for basic use. The software may have Windows-primary support — customer should check the website for macOS software availability. The 6 DPI hardware presets and all three connection modes work on macOS without software. For advanced features the software is recommended. Software also allows button remapping, polling rate adjustment, and other sensor settings."
            },
            {
                "tag": "Charging, warranty and care",
                "scenario": "A customer says: 'I dropped my Velox and it cracked slightly but still works. Also I have been charging it with my phone's fast charger. And the battery life has gone down a lot in 7 months — is any of this covered under warranty?'",
                "question": "Address the fast charger issue, physical damage, and battery degradation warranty position for the Velox.",
                "rubric": "Fast charger: CRITICAL — the Velox has specific charging voltage specs (4.0V trickle, 4.2V full, 6V over-voltage cutoff). Fast chargers can exceed these limits and damage the battery. The mouse has surge protection at 24V but fast chargers may still cause damage outside safe parameters. Recommend immediately switching to a standard 5V USB source or PC USB port. Do not continue using fast charger. Physical damage from dropping: cracked shell from dropping is explicitly NOT covered under warranty. Physical damage voids warranty coverage for that damage. Battery degradation after 7 months: regular wear and tear from usage is NOT covered (though the Velox manual specifically only mentions physical and water damage — agents should note this but cannot guarantee battery wear is covered). Fast charger-induced battery damage would also not be covered as it is user-caused. Warranty: 1 year against manufacturing defects only. Physical damage not covered. Water damage not covered. Tampered products not covered. Support: +91 7351615161 (Mon-Sat 10am-6pm), WhatsApp: +91 7351615161, cc@thecosmicbyte.com."
            }
        ]
    },
    {
        "id": "atlas_mouse",
        "name": "Atlas Mouse",
        "category": "Mouse",
        "description": "Tri-mode gaming mouse (Type-C Wired / 2.4G / Bluetooth). PixArt PAW3311 sensor, up to 12000 DPI, 1000Hz polling rate (133Hz in Bluetooth), 5 programmable buttons, Huano switches (20M clicks), 500mAh built-in battery, 57g, PTFE feet. Windows only for software.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity and mode switching",
                "scenario": "A new customer asks: 'How do I switch between wireless and Bluetooth on my Atlas mouse? And how do I know which mode I am in?'",
                "question": "Explain how to switch between connection modes and what the LED indicators mean on the Atlas Mouse.",
                "rubric": "Mode switching: press the M button briefly to toggle between 2.4G and Bluetooth modes. L2 indicator: Green = 2.4G Mode, Blue = Bluetooth Mode. For Bluetooth pairing mode: press and hold the M button for about 2 seconds — L2 indicator will flash blue rapidly. Wired mode: connect the Type-C cable — wired takes priority over all other modes automatically. Agent must mention all three modes and the connection priority rule."
            },
            {
                "tag": "DPI adjustment",
                "scenario": "A customer says: 'I want to lower the sensitivity on my Atlas Mouse. How do I change the DPI and how do I know which level I am on?'",
                "question": "Explain DPI adjustment and the DPI indicator colours on the Atlas Mouse.",
                "rubric": "Press the D button briefly to cycle through 5 DPI levels. L2 indicator colour shows current DPI: 800 DPI = Red. 1600 DPI (default) = Green. 2400 DPI = Blue. 5000 DPI = Purple. 12000 DPI = Yellow. Agent should list all 5 levels and their corresponding colours. Default is 1600 DPI (Green)."
            },
            {
                "tag": "Battery and charging indicators",
                "scenario": "A customer says: 'My Atlas Mouse light is flashing red. Is that normal? Also how do I know when it is done charging?'",
                "question": "Explain all L1 indicator states for battery and charging on the Atlas Mouse.",
                "rubric": "L1 indicator status: Flashing Red = Low Battery — connect to charge. Steady Blue = Charging in progress. Steady Green = Charging Complete. Use the ON/OFF switch to toggle battery power. The mouse has a 500mAh built-in lithium polymer battery. Agent must correctly map each LED state."
            },
            {
                "tag": "Polling rate and Bluetooth limitation",
                "scenario": "A customer says: 'I read the Atlas Mouse has 1000Hz polling rate but when I use it on Bluetooth it feels less responsive. Why?'",
                "question": "Explain the polling rate difference between modes on the Atlas Mouse.",
                "rubric": "The Atlas Mouse supports 1000Hz polling rate maximum — but only in 2.4G or wired mode. In Bluetooth mode the polling rate drops to 133Hz, which is significantly lower and results in less responsive cursor movement. This is a hardware limitation of Bluetooth, not a defect. For competitive gaming, 2.4G wireless or wired mode is strongly recommended for the full 1000Hz experience."
            },
            {
                "tag": "Software and programmable buttons",
                "scenario": "A customer asks: 'Can I remap the buttons on my Atlas Mouse? Where do I get the software and does it work on Mac?'",
                "question": "Explain software support and button customisation on the Atlas Mouse.",
                "rubric": "The 5 mouse keys can be personalised using the Cosmic Byte software. Software is Windows only — macOS is NOT supported for software. Download from www.thecosmicbyte.com. While the mouse itself is compatible with Windows XP+, Android 9.0+, Linux, and macOS for basic use, the software for customisation is Windows exclusive. Agent must clearly state the software limitation for Mac users."
            },
            {
                "tag": "Mouse not responding — troubleshooting",
                "scenario": "A customer says: 'My Atlas Mouse is completely unresponsive — cursor is not moving and buttons do nothing. I am on 2.4G mode.'",
                "question": "Walk the customer through diagnosing an unresponsive Atlas Mouse in 2.4G mode.",
                "rubric": "Step 1: check the ON/OFF switch is in the ON position. Step 2: confirm battery is charged — if L1 flashes red, charge the mouse first. Step 3: for 2.4G mode, confirm the USB receiver is properly connected to the device — try a different USB port. Step 4: re-pair if needed: switch from 2.4G to Bluetooth mode using M button and back to 2.4G. Step 5: if still unresponsive, reset — turn mouse off and disconnect from all connections, wait 10 seconds, reconnect and power back on. Wired mode check: for wired, verify the Type-C cable connection."
            },
            {
                "tag": "Bluetooth connection issues",
                "scenario": "A customer says: 'I cannot get my Atlas Mouse to pair via Bluetooth. The L2 light is blue but my PC cannot find the mouse.'",
                "question": "Walk the customer through fixing Bluetooth connection issues on the Atlas Mouse.",
                "rubric": "Step 1: ensure mouse is in Bluetooth mode — L2 indicator should show Blue (solid = Bluetooth mode). Step 2: to enter pairing mode, press and hold the M button for about 2 seconds until L2 flashes blue rapidly. Step 3: ensure Bluetooth is enabled on the device. Step 4: check if the mouse is already listed in paired devices on the PC — remove the old pairing and reconnect. Step 5: restart both mouse and device, then attempt to pair again. Note: Bluetooth polling rate is limited to 133Hz on the Atlas Mouse."
            },
            {
                "tag": "Cursor movement erratic",
                "scenario": "A customer says: 'The cursor on my Atlas Mouse is jumping around and not moving smoothly. It is very inconsistent.'",
                "question": "Diagnose and fix erratic cursor movement on the Atlas Mouse.",
                "rubric": "Step 1: adjust DPI — if DPI is set too high (5000 or 12000) it can feel erratic. Press D button to cycle to a lower DPI level like 1600 (Green). Step 2: clean the mouse sensor and the surface beneath it to remove dust or debris. Step 3: use the mouse on a suitable non-reflective surface — glass or reflective surfaces cause erratic tracking with the PAW3311 sensor. Step 4: if on 2.4G, check for wireless interference. Step 5: try a different USB port for the receiver."
            },
            {
                "tag": "Warranty and compatibility",
                "scenario": "A customer asks: 'Does the Atlas Mouse work on Linux? Also what is covered under warranty?'",
                "question": "Confirm compatibility and explain the Atlas Mouse warranty.",
                "rubric": "Compatibility: Windows XP and later, Android 9.0 and later, Linux, and macOS — all supported for basic use. Software (for customisation) is Windows only. Warranty: 1 year against manufacturing defects only. Physical damage, water damage, and tampered products are NOT covered. Regular wear and tear from battery usage is also NOT covered. Support: +91 73 5161 5161 (Mon-Sat 10am-6pm), Email: cc@thecosmicbyte.com."
            },
            {
                "tag": "Wired mode and cable",
                "scenario": "A customer asks: 'If I plug in the USB cable on my Atlas Mouse, does it automatically switch to wired mode? And what cable does it use?'",
                "question": "Explain wired mode behaviour and cable details on the Atlas Mouse.",
                "rubric": "Yes — when the USB-C cable is connected, the Atlas Mouse automatically switches to wired mode and wired takes priority over all other modes (Bluetooth and 2.4G). The cable is a 1.8m Paracord Cable with USB extension. While charging via the cable in wired mode, the mouse functions simultaneously — it can be used while charging. The ON/OFF switch controls battery power for wireless modes — in wired mode the cable powers the mouse regardless."
            }
        ]
    },
    {
        "id": "aether_mouse",
        "name": "Aether Mouse",
        "category": "Mouse",
        "description": "Tri-mode gaming mouse (2.4G / Bluetooth BLE / Wired USB). PixArt PAW3311 sensor, up to 12000 DPI (6-step), 1000Hz polling, TTC Optical Switches (100M clicks), replaceable 400mAh Li-Ion battery (2 included), 44g without battery / 55g with battery, dual PTFE skates, PD fast charging, 1.8m paracord cable.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity — all three modes",
                "scenario": "A new customer asks: 'How do I connect the Aether Mouse via 2.4G dongle? And how do I pair it via Bluetooth? Where is the USB dongle stored?'",
                "question": "Explain all three connection modes and dongle storage on the Aether Mouse.",
                "rubric": "Wired mode: connect the 1.8m paracord USB cable — automatically switches to wired, plug and play, no drivers required. 2.4G wireless: slide mode switch to 2.4G, plug USB receiver into PC. First-time pairing: press and hold Left + Middle + Right buttons for 3 seconds — green LED flashes indicating pairing mode, insert receiver to complete. Bluetooth mode: slide mode switch to BT — blue LED flashes slowly indicating Bluetooth standby. First-time pairing: press and hold Left + Middle + Right buttons for 3 seconds — blue light flashes rapidly indicating pairing mode, on device search for 'CB Aether'. USB receiver storage: the 2.4G USB dongle is stored inside the battery compartment — remove the battery cover to access it. Bluetooth requires BLE (Bluetooth Low Energy) support on the connecting device."
            },
            {
                "tag": "DPI levels and indicator colours",
                "scenario": "A customer asks: 'How do I change DPI on the Aether Mouse and what do the LED colours mean for each level?'",
                "question": "Explain DPI cycling and all DPI LED colour codes on the Aether Mouse.",
                "rubric": "Press the DPI button to cycle through 6 preset DPI levels. DPI levels and LED colours: 800 DPI = Red. 1600 DPI = Blue. 2400 DPI = Purple. 4800 DPI = Green. 6400 DPI = Yellow. 12000 DPI = Cyan. Agent should note the Aether has 6 DPI steps (more than the Atlas's 5) and list all colours correctly. The DPI range is configurable via software (downloadable from thecosmicbyte.com)."
            },
            {
                "tag": "Replaceable battery and charging",
                "scenario": "A customer asks: 'The Aether came with two batteries. How do I change the battery and how do I charge it? Does it support fast charging?'",
                "question": "Explain the replaceable battery system and charging on the Aether Mouse.",
                "rubric": "The Aether Mouse has a replaceable 400mAh lithium-ion battery system — two 400mAh batteries are included in the box. To replace: open the battery compartment cover (also where the USB dongle is stored), swap the battery. Charging indicator: Red LED blinks slowly when battery is low. Charging: supports PD Fast Charging via USB cable. This is a key differentiator — the Aether is the only mouse in this range with PD fast charging support. Weight: 44g without battery, 55g with battery installed. Note the battery compartment also houses the 2.4G USB dongle."
            },
            {
                "tag": "TTC Optical Switches — benefit and durability",
                "scenario": "A customer asks: 'What are TTC Optical Switches and why does the Aether use them instead of regular switches? How long do they last?'",
                "question": "Explain TTC Optical Switches on the Aether Mouse — what they are, their benefits, and rated lifespan.",
                "rubric": "TTC Optical Switches use light (infrared beam) to register clicks instead of physical metal contact. Benefits: faster actuation (no physical debounce delay), more reliable (no contact wear), resistant to double-click issues common with mechanical switches. Lifespan: rated for 100 million clicks — significantly longer than the Huano switches used in most other models (which are 10-20 million). The Aether's optical switches are a premium feature. Sensor: PixArt PAW3311. The switch type is a key selling point for customers concerned about longevity."
            },
            {
                "tag": "Bluetooth not connecting",
                "scenario": "A customer says: 'I cannot connect my Aether Mouse via Bluetooth. My device says it does not support BLE. What does that mean?'",
                "question": "Explain the Bluetooth BLE requirement and troubleshoot connection on the Aether Mouse.",
                "rubric": "BLE stands for Bluetooth Low Energy. The Aether Mouse requires BLE support on the connecting device — standard Bluetooth devices that do not support BLE will NOT be able to pair. Most modern smartphones, tablets, and laptops manufactured after 2012 support BLE. Older devices may not. Troubleshooting steps: ensure mode switch is set to BT. Press and hold Left + Middle + Right buttons for 3 seconds — blue LED flashes rapidly confirming pairing mode. On the device, search and select 'CB Aether'. If already paired with another device: remove that pairing first then reconnect. Ensure device Bluetooth supports BLE — if not, the customer must use wired or 2.4G mode instead."
            },
            {
                "tag": "2.4G not connecting",
                "scenario": "A customer says: 'My Aether Mouse is not working in 2.4G mode even though the dongle is plugged in.'",
                "question": "Walk the customer through 2.4G troubleshooting on the Aether Mouse.",
                "rubric": "Step 1: confirm USB receiver is plugged into a working USB port on the PC. Step 2: confirm mode switch is set to 2.4G. Step 3: re-pair — press and hold Left + Middle + Right buttons for 3 seconds (green LED flashes), then insert the receiver. Step 4: try a different USB port — USB 3.0 can cause 2.4GHz interference; try USB 2.0. Step 5: check battery level — if red LED blinks slowly, charge the mouse first. Step 6: check if the USB dongle stored in the battery compartment is the correct one for this mouse."
            },
            {
                "tag": "Sleep and wake function",
                "scenario": "A customer says: 'My Aether Mouse stops responding after I leave it idle. I have to click multiple times to wake it. Is this normal?'",
                "question": "Explain the sleep and wake function on the Aether Mouse.",
                "rubric": "The Aether Mouse enters sleep mode automatically after a period of inactivity to conserve battery. This is normal behaviour — not a defect. To wake: move the mouse or click any button. A slight delay on wake-up is normal and expected. The sleep function is especially important given the replaceable battery design — it preserves battery life between swaps. There is no way to disable sleep mode. If the mouse takes more than 2-3 seconds to wake consistently or does not wake at all, that could indicate a low battery issue — check the charge level."
            },
            {
                "tag": "Cursor erratic or unresponsive",
                "scenario": "A customer says: 'The cursor on my Aether Mouse skips and lags. I cleaned the sensor but it is still happening in 2.4G mode.'",
                "question": "Diagnose cursor tracking issues on the Aether Mouse beyond just sensor cleaning.",
                "rubric": "After sensor cleaning: Step 1 — check PTFE feet (dual skates) — if worn or dirty they can affect smooth movement and indirectly tracking feel. Clean PTFE feet. Step 2 — check surface: use a proper mouse pad or smooth non-reflective surface. PAW3311 sensor does not perform well on glass or reflective surfaces. Step 3 — adjust DPI: very high DPI settings can appear erratic. Try cycling to a lower level. Step 4 — check for wireless interference in 2.4G mode: move receiver away from USB 3.0 devices and Wi-Fi routers. Step 5 — check battery: low battery can cause erratic wireless behaviour — charge or swap battery. Step 6 — try re-pairing in 2.4G mode."
            },
            {
                "tag": "Programmable buttons and software",
                "scenario": "A customer asks: 'Can I remap all 6 buttons on the Aether Mouse? Is there macOS software?'",
                "question": "Explain programmable buttons and software support on the Aether Mouse.",
                "rubric": "All 6 buttons (including the DPI switch) are fully programmable using the Cosmic Byte software. Software supports: button remapping, macro configuration, performance profiles. Software compatible with: Windows 2000 / XP / Vista / 7 / 8 / 10. macOS support: Bluetooth mode requires BLE support, but the dedicated configuration software is Windows-primary. Customers should check thecosmicbyte.com for macOS software availability. Basic use (movement, clicks) works on macOS without software; full customisation requires Windows software."
            },
            {
                "tag": "Warranty and specifications",
                "scenario": "A customer asks: 'What are the dimensions of the Aether Mouse? Also I dropped it and the cover cracked — is that covered under warranty?'",
                "question": "Confirm key specs and explain warranty on the Aether Mouse.",
                "rubric": "Dimensions: 125mm (L) × 63mm (W) × 38mm (H). Weight: 44g without battery, 55g with battery. Sensor: PixArt PAW3311. Warranty: 1 year against manufacturing defects only. Physical damage from dropping (cracked cover) is NOT covered. Water damage not covered. Tampered products not covered. The Aether has a replaceable top/bottom cover made of ABS plastic — the cracked cover is physical damage from dropping and is the customer's responsibility. Support: +91 7351615161 (Mon-Sat 10am-6pm), WhatsApp: +91 7351615161, cc@thecosmicbyte.com."
            }
        ]
    },
    {
        "id": "umbra_mouse",
        "name": "Umbra Mouse",
        "category": "Mouse",
        "description": "Tri-mode gaming mouse (USB Type-C wired / 2.4GHz dongle / Bluetooth 5.0). PixArt A3104 sensor, DPI levels 400/800/1200/1600/2400/4000, up to 1000Hz polling (125Hz on Bluetooth), Huano switches (10M clicks), 300mAh rechargeable Li-ion battery, 53g, honeycomb body, PTFE feet, 1.8m paracord cable with magnetic ring.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity — all three modes",
                "scenario": "A new customer asks: 'How do I connect the Umbra Mouse to my PC using the dongle? How do I pair via Bluetooth? And what happens when I plug in the cable?'",
                "question": "Walk the customer through all three connection modes on the Umbra Mouse.",
                "rubric": "Wired mode (USB Type-C): plug the 1.8m paracord cable into mouse and PC — automatically switches to wired mode. Power switch on mouse does not need to be on for wired mode. 2.4GHz wireless: unplug USB cable, slide power switch to top position (2.4G symbol) — indicator flashes green then turns off once connected. First-time / re-pair: press and hold Left Click + Right Click + Scroll Wheel for 3 seconds — green LED blinks rapidly, once paired light turns off. Insert USB dongle to complete. Bluetooth mode: slide power switch to bottom position (Bluetooth symbol) — on device search for and connect to 'CB Umbra'. Re-pair: press and hold Left Click + Right Click + Scroll Wheel for 3 seconds — blue LED blinks rapidly. Once paired, blue light turns off."
            },
            {
                "tag": "DPI levels",
                "scenario": "A customer asks: 'How many DPI levels does the Umbra Mouse have and how do I switch between them?'",
                "question": "Explain DPI levels and switching on the Umbra Mouse.",
                "rubric": "The Umbra Mouse has 6 DPI levels: 400 / 800 / 1200 / 1600 / 2400 / 4000 DPI. Press the DPI Switch button to cycle through them. The Umbra uses the PixArt A3104 sensor — different from the PAW3311 in the Atlas and Aether. The sensor has a tracking speed of 45 IPS and 15G acceleration. Agent should note the maximum DPI is 4000 — lower than some other models in the range."
            },
            {
                "tag": "Indicator lights — what each means",
                "scenario": "A customer says: 'My Umbra Mouse has different coloured lights and I am confused about what they all mean. The red light is blinking slowly right now.'",
                "question": "Explain all indicator light states on the Umbra Mouse.",
                "rubric": "Indicator light states: Low Battery = Red light flashes slowly. Charging = Solid blue light (stays on while charging). Fully Charged = Blue light turns off. 2.4GHz Pairing Mode = Green light blinks fast. Bluetooth Pairing Mode = Blue light blinks fast. When connected in either wireless mode the light turns off — absence of light after pairing is confirmation of connection, not a problem. Red light flashing slowly currently = low battery, customer should charge immediately."
            },
            {
                "tag": "Polling rate and Bluetooth limitation",
                "scenario": "A customer says: 'I heard the Umbra Mouse has 1000Hz polling but it feels slower when I use Bluetooth. Is something wrong?'",
                "question": "Explain polling rate differences across modes on the Umbra Mouse.",
                "rubric": "The Umbra Mouse supports different polling rates per mode: Wired and 2.4GHz modes: 125Hz / 250Hz / 500Hz / 1000Hz (adjustable). Bluetooth mode: 125Hz only — this is fixed and cannot be increased in Bluetooth mode. The reduced responsiveness in Bluetooth mode is expected and not a defect. For competitive gaming requiring 1000Hz, wired or 2.4GHz mode is strongly recommended. The polling rate adjustment for wired/2.4GHz modes can be done via software."
            },
            {
                "tag": "Wired mode not working",
                "scenario": "A customer says: 'My Umbra Mouse is not working in wired mode. The cable is plugged in but nothing happens.'",
                "question": "Troubleshoot wired mode on the Umbra Mouse.",
                "rubric": "Key point for wired mode: the power switch does NOT need to be in ON position for wired mode — wired mode works regardless of power switch position. Step 1: ensure the USB Type-C cable is properly connected to both the mouse and computer. Step 2: check the power switch — for wired mode it should actually be off (or in any position), as wired mode works independently. Step 3: try a different USB port. Step 4: try a different USB Type-C cable if available. Step 5: restart the computer and reconnect. The 1.8m paracord cable has a magnetic ring — ensure the ring is not interfering with the connection near the port."
            },
            {
                "tag": "Mouse not waking from sleep",
                "scenario": "A customer says: 'My Umbra Mouse went idle and now it will not wake up even when I move it.'",
                "question": "Explain sleep/wake behaviour and how to troubleshoot it on the Umbra Mouse.",
                "rubric": "The Umbra Mouse enters sleep mode after a period of inactivity to save power. To wake: move the mouse or press any button. If it still does not respond: check the battery level — if low (red LED flashing slowly) the mouse may not have enough charge to wake. Charge the mouse. In wireless mode, check the power switch position — ensure it is in 2.4G or BT position (not off). In wired mode, disconnect and reconnect the cable. If mouse still does not wake after charging, perform a connection reset by switching power modes."
            },
            {
                "tag": "Bluetooth connection problems",
                "scenario": "A customer says: 'I cannot connect my Umbra Mouse via Bluetooth. I set the switch to Bluetooth but cannot find it on my device.'",
                "question": "Walk the customer through Bluetooth troubleshooting on the Umbra Mouse.",
                "rubric": "Step 1: slide power switch to the bottom position (Bluetooth symbol). Step 2: wake the mouse if in sleep mode — press any button. Step 3: on the device search for 'CB Umbra' in Bluetooth settings. Step 4: if not finding it, press and hold Left Click + Right Click + Scroll Wheel for 3 seconds to enter active pairing mode — blue LED blinks rapidly. Step 5: if already paired with another device, the mouse may be trying to reconnect to that device first — remove the old pairing from the device's Bluetooth list and re-pair. Step 6: ensure device Bluetooth supports Bluetooth 5.0. Once paired, blue light turns off confirming connection."
            },
            {
                "tag": "Cursor lagging",
                "scenario": "A customer says: 'The Umbra Mouse cursor keeps lagging and skipping. I am on 2.4GHz mode.'",
                "question": "Diagnose cursor lag on the Umbra Mouse in 2.4GHz mode.",
                "rubric": "Step 1: check surface — use mouse on a smooth non-reflective surface or mouse pad. PixArt A3104 does not track well on glass or reflective surfaces. Step 2: check for wireless interference — USB 3.0 drives, Wi-Fi routers near receiver cause 2.4GHz lag. Move receiver to a USB 2.0 port. Step 3: check battery — low battery causes erratic wireless behaviour. Red LED flashing = low battery, charge first. Step 4: check DPI setting — if set very low (400) or if DPI is mismatched to surface, it can feel laggy. Try 1600 or 2400 DPI. Step 5: if cursor only lags after being idle, that may be the sleep wake-up delay — normal behaviour. Step 6: re-pair the 2.4GHz connection if issues persist."
            },
            {
                "tag": "Buttons not responding",
                "scenario": "A customer says: 'Some buttons on my Umbra Mouse are not working at all.'",
                "question": "Walk the customer through diagnosing unresponsive buttons on the Umbra Mouse.",
                "rubric": "Step 1: test in wired mode first — this isolates hardware from connection issues. Step 2: restart the PC and reconnect the mouse. Step 3: if using Bluetooth or 2.4GHz, ensure it is properly paired. Step 4: check if software has remapped buttons — open configuration software and reset to default settings. Step 5: test on another computer to rule out software conflicts. Step 6: if a button is unresponsive across all modes and on multiple computers, it may be a hardware issue — Huano switches rated 10 million clicks could be a hardware defect if the mouse is relatively new. Contact support. Support: +91 7351615161 (Mon-Sat 10am-6pm), WhatsApp: +91 7351615161, cc@thecosmicbyte.com."
            },
            {
                "tag": "Warranty and physical design",
                "scenario": "A customer asks: 'Why does the Umbra Mouse have holes in the body? Also I spilled water on it — is that covered under warranty?'",
                "question": "Explain the honeycomb design and warranty on the Umbra Mouse.",
                "rubric": "Honeycomb design: the holes in the Umbra's body are a deliberate lightweight design choice. The honeycomb shell significantly reduces weight (53g) while maintaining structural integrity — it allows for faster mouse movements during gaming and reduces hand fatigue in long sessions. The ABS plastic shell with honeycomb pattern is the defining aesthetic of the Umbra. Warranty: 1 year against manufacturing defects only. Water/liquid damage is NOT covered under warranty — the honeycomb holes make the Umbra particularly susceptible to liquid ingress. Physical damage not covered. Tampered products not covered. The water spill incident is not covered. Contact: +91 7351615161."
            }
        ]
    },
    {
        "id": "firestorm_mouse",
        "name": "Firestorm Mouse",
        "category": "Mouse",
        "description": "RGB wired gaming mouse. Sensor: 3327, DPI 200–12400, 1000Hz polling, 220 IPS, 30G acceleration, Huano switches (10M clicks), 67g without cable, 1.5m paracord cable with cable management loop, honeycomb body with replaceable top cover, 11 RGB effects, 7 programmable buttons, Windows software only.",
        "available": True,
        "questions": [
            {
                "tag": "Setup and first connection",
                "scenario": "A new customer asks: 'How do I set up my Firestorm Mouse for the first time? I just unboxed it.'",
                "question": "Walk the customer through first-time setup of the Firestorm Mouse.",
                "rubric": "Steps: (1) Unpack and remove any plastic film from the mouse feet. (2) Connect mouse to PC using the USB cable. (3) Windows will detect the mouse within 5-30 seconds automatically. (4) Download software from www.thecosmicbyte.com for full customisation. (5) When installing software: disable antivirus temporarily — antivirus may block installation as the software may not be in their database yet. (6) Once software is installed, restart the PC. (7) Mouse is now ready. Customise functions, macros, RGB, and DPI via the software. Wired only — the Firestorm is not wireless."
            },
            {
                "tag": "DPI settings and RGB indicator",
                "scenario": "A customer asks: 'What DPI levels does the Firestorm Mouse support? How do I know which DPI I am on? And what is the default?'",
                "question": "Explain DPI range, adjustment, and the DPI LED indicator on the Firestorm Mouse.",
                "rubric": "DPI range: 200 to 12400 DPI. The DPI button cycles through preset levels and the LED colour changes with each DPI level. Each DPI level changes the indicator LED colour — if the colour does not change when pressing the DPI button, the button may be unresponsive. Custom DPI levels between 200 and 12400 can be set via the Cosmic Byte Firestorm software. Default DPI levels and their LED colours are configured in the software. Agent should note the sensor is model 3327 (different from PAW3311 in other mice). Polling rate is 1000Hz."
            },
            {
                "tag": "RGB lighting — customisation and troubleshooting",
                "scenario": "A customer says: 'The RGB on my Firestorm Mouse is not lighting up. Also how do I change the lighting effects?'",
                "question": "Explain RGB customisation and troubleshoot RGB issues on the Firestorm Mouse.",
                "rubric": "The Firestorm Mouse has 11 RGB effects. To customise: use the Cosmic Byte Firestorm software (Windows only) — downloadable from thecosmicbyte.com. If RGB is not working: Step 1 — cycle through RGB effects using mode button if available, or check software settings. Step 2 — ensure RGB is not set to 'Off' or 'Static Black' in software. Step 3 — reinstall or update the Firestorm software/driver. If software is not detecting the mouse: ensure correct software version for the Firestorm model. Run as Administrator (right-click > Run as Administrator). Reinstall — download latest from cosmicbyte.com. The 11 RGB modes are a key feature — honeycomb body allows light to shine through."
            },
            {
                "tag": "Replaceable top cover",
                "scenario": "A customer asks: 'What is the replaceable top cover on the Firestorm Mouse? How does it work?'",
                "question": "Explain the replaceable top cover feature on the Firestorm Mouse.",
                "rubric": "The Firestorm Mouse has a honeycomb design shell that is removable and replaceable. A plain solid cover is included as an alternative to the honeycomb top. To change the look: the top cover can be swapped between honeycomb (default) and plain cover. The honeycomb design makes the mouse very lightweight and allows RGB to shine through. The plain cover gives a cleaner aesthetic without holes. This is a unique feature of the Firestorm — it offers two distinct visual styles in one mouse. Weight with any cover: 67g without cable."
            },
            {
                "tag": "Software not detecting mouse",
                "scenario": "A customer says: 'I installed the Firestorm software but it says the mouse is not detected. The mouse itself works fine in games.'",
                "question": "Troubleshoot the Firestorm software not detecting the mouse.",
                "rubric": "The mouse working in games but not being detected by software is a common issue. Steps: Step 1 — confirm correct software version for the Firestorm model (not a different Cosmic Byte mouse software). Step 2 — run the software as Administrator: right-click the software icon and select 'Run as Administrator'. Step 3 — try a different USB port. Step 4 — uninstall and download the latest version from www.cosmicbyte.com. Step 5 — check if antivirus is blocking the software — disable antivirus temporarily and reopen. Step 6 — restart PC after reinstalling. Note: software is Windows only — it will not work on macOS or Linux."
            },
            {
                "tag": "Cursor not moving or mouse freezing",
                "scenario": "A customer says: 'My Firestorm Mouse cursor freezes and sometimes does not move at all.'",
                "question": "Diagnose cursor freezing on the Firestorm Mouse.",
                "rubric": "Step 1: surface — use a proper mousepad or non-reflective clean surface. Sensor 3327 tracks poorly on glass or reflective surfaces. Step 2: check for dust or debris on the sensor lens — clean gently. Step 3: try a different USB port (preferably USB 3.0 or 2.0 direct on motherboard, not a hub). Step 4: use software to adjust the polling rate (1000Hz recommended) and test responsiveness. Step 5: restart PC — sometimes a reboot resolves device recognition issues. Step 6: test on another PC to isolate hardware vs software issues. The Firestorm is wired only, so wireless interference is not a factor."
            },
            {
                "tag": "Buttons not responding or remapped unexpectedly",
                "scenario": "A customer says: 'Some buttons on my Firestorm Mouse are not doing what they should. The side buttons seem to do random things.'",
                "question": "Diagnose and fix button issues on the Firestorm Mouse.",
                "rubric": "Most likely cause: buttons have been remapped via the Firestorm configuration software. Step 1: open the Firestorm configuration software. Step 2: check if buttons are remapped to unexpected functions. Step 3: restore default settings in the software. Step 4: reassign buttons as needed. If software-level reset does not fix it: Step 5 — uninstall and reinstall software. Step 6 — test mouse buttons on another computer to rule out hardware issues. Step 7 — if a button is physically stuck or feels different from the others, this could be a mechanical issue — contact support. The Firestorm has 7 programmable buttons total."
            },
            {
                "tag": "Mouse lag or input delay",
                "scenario": "A customer says: 'My Firestorm Mouse feels laggy during gaming. There is a noticeable delay between my movements and the cursor.'",
                "question": "Diagnose and fix mouse lag on the Firestorm Mouse.",
                "rubric": "Step 1: set polling rate to 1000Hz via the Cosmic Byte software — this gives the minimum possible latency (1ms). Step 2: close background applications that may be causing high CPU usage — high system load increases input processing time. Step 3: check the USB cable for damage or fraying — a damaged cable can cause intermittent lag. Step 4: try a different USB port (preferably a direct motherboard USB port, not a hub). Step 5: check the surface and sensor — debris on sensor or reflective surface causes tracking issues that can appear as lag. The Firestorm is wired only so wireless interference is not a factor — lag in wired mice is almost always USB, surface, or software related."
            },
            {
                "tag": "Cable and paracord design",
                "scenario": "A customer asks: 'What is special about the paracord cable on the Firestorm Mouse? Can I use an extension?'",
                "question": "Explain the cable design and cable management loop on the Firestorm Mouse.",
                "rubric": "The Firestorm Mouse uses a 1.5m paracord cable. Paracord cable properties: extremely lightweight compared to standard rubber cables, very flexible with minimal drag — this makes the mouse feel similar to a wireless mouse. The cable has a cable management loop for routing the cable cleanly on a desk. The lightweight cable is a key feature — it reduces the resistance and drag felt when moving the mouse quickly. No wireless option exists — the Firestorm is wired only. USB extension cables can be used if 1.5m is too short, but additional cable weight/drag may reduce the wireless-like feel benefit of the paracord."
            },
            {
                "tag": "Warranty and compatibility",
                "scenario": "A customer asks: 'Does the Firestorm Mouse work on Mac? Also I spilled water on it — is that covered?'",
                "question": "Explain compatibility and warranty on the Firestorm Mouse.",
                "rubric": "Compatibility: the Firestorm Mouse is plug-and-play on Windows for basic use. Software is Windows only — macOS users can use the mouse but cannot access software customisation features (RGB, DPI presets, button remapping). There is no macOS software listed. Warranty: 1 year against manufacturing defects only. Water/liquid damage is NOT covered. Physical damage is NOT covered. Tampered products not covered. The water spill incident is user-caused and not covered. Support: +91 7351615161 (Mon-Sat 10am-6pm), WhatsApp: +91 7351615161, cc@thecosmicbyte.com."
            }
        ]
    },
    {
        "id": "ignis_mouse",
        "name": "Ignis Mouse",
        "category": "Mouse",
        "description": "Tri-mode gaming mouse (2.4GHz / Bluetooth / Wired USB-C). PixArt 3311 sensor, DPI 400–12000 hardware (up to 24000 via software), 1000Hz polling, Huano switches (20M clicks), 400mAh built-in rechargeable battery, ~52 hour battery life, 53.6g, F-Switch encoder, stealth design (no RGB), 1.5m ultralight paracord cable. Mode toggle on bottom.",
        "available": True,
        "questions": [
            {
                "tag": "Mode switching",
                "scenario": "A new customer asks: 'How do I switch between 2.4GHz, Bluetooth, and wired on my Ignis Mouse? There is a switch on the bottom.'",
                "question": "Explain the mode toggle and all three connection modes on the Ignis Mouse.",
                "rubric": "Bottom switch positions: Left = 2.4GHz Wireless Mode. Centre = Power OFF. Right = Bluetooth Mode. Wired mode: connect the USB-C paracord cable — wired mode activates automatically when cable is connected and battery begins charging simultaneously. 2.4GHz: slide switch left, plug in USB receiver. If mouse does not respond: press and hold Left + Right + Scroll for 3 seconds to re-sync. Bluetooth: slide switch right. Press and hold Left + Right + Scroll for 3 seconds to enter pairing mode — indicator blinks. Pair with device — appears as 'CB Ignis'. Agent must mention all three mode positions and the re-sync procedure."
            },
            {
                "tag": "DPI cycling",
                "scenario": "A customer asks: 'How do I change the DPI on my Ignis Mouse? I cannot find a DPI button on top.'",
                "question": "Explain DPI adjustment on the Ignis Mouse — noting the button location.",
                "rubric": "The DPI button on the Ignis Mouse is located on the bottom of the mouse — not on top like most mice. Press it to cycle through 6 DPI preset levels: 400 / 800 / 1600 / 3200 / 6400 / 12000 DPI. Via software: DPI can go up to 24000 DPI. The bottom placement of the DPI button is a deliberate design choice to maintain the stealth/clean look on top. Agent must clarify the DPI button location — this is commonly confusing for customers. Software available from thecosmicbyte.com for advanced DPI settings."
            },
            {
                "tag": "Battery life and charging",
                "scenario": "A customer asks: 'How long does the Ignis Mouse battery last? And how do I know when it is charging vs fully charged?'",
                "question": "Explain battery life and charging indicators on the Ignis Mouse.",
                "rubric": "Battery life: approximately 52 hours on a full charge — one of the longest battery lives in the Cosmic Byte mouse range. Battery capacity: 400mAh built-in rechargeable. Charging time: 2–3 hours. LED charging indicator: Steady Red = Charging in progress. Steady Green = Fully charged. To charge: connect the USB-C cable — wired mode activates and battery charges simultaneously. The 52-hour battery life is a key selling point. Mode switch centre position = OFF (to conserve battery when not in use)."
            },
            {
                "tag": "Stealth design — no RGB",
                "scenario": "A customer says: 'I cannot find any RGB settings on my Ignis Mouse and there is no light on it. Is it broken?'",
                "question": "Explain the Ignis Mouse design philosophy regarding RGB.",
                "rubric": "The Ignis Mouse is a deliberate stealth/zero RGB design. It has NO LED lighting on top during use — this is intentional, not a defect. The only LEDs are the charging indicator (Red/Green). The design is described as 'Zero RGB for a stealth professional look' — it prioritises clean aesthetics without lights. There is no RGB setting to find or adjust. This is a key differentiator for customers who want a minimalist gaming mouse without lighting distractions. Agent must clearly reassure the customer this is by design."
            },
            {
                "tag": "2.4GHz not working",
                "scenario": "A customer says: 'My Ignis Mouse is not responding in 2.4G mode. The receiver is plugged in.'",
                "question": "Troubleshoot 2.4GHz connection on the Ignis Mouse.",
                "rubric": "Step 1: confirm bottom switch is in the left position (2.4GHz). Centre position = OFF, right = Bluetooth. Step 2: ensure USB receiver is firmly plugged into a working USB port. Step 3: re-sync — press and hold Left + Right + Scroll buttons for 3 seconds — this re-syncs the mouse to the receiver. Step 4: try a different USB port — avoid USB 3.0 if possible as it can cause 2.4GHz interference. Step 5: check battery level — steady red light means charging is needed. Step 6: try another computer with the same receiver to test if the issue is PC or mouse specific."
            },
            {
                "tag": "Bluetooth not pairing",
                "scenario": "A customer says: 'I cannot pair my Ignis Mouse via Bluetooth. I slid the switch to the right but nothing shows up on my phone.'",
                "question": "Walk the customer through Bluetooth pairing on the Ignis Mouse.",
                "rubric": "Step 1: slide bottom switch to the RIGHT position (Bluetooth mode). Step 2: press and hold Left + Right + Scroll buttons for 3 seconds — mouse enters pairing mode (indicator blinks). Step 3: on your device, open Bluetooth settings and scan. Step 4: select 'CB Ignis' from the list. Step 5: if previously paired with another device, remove that pairing from both devices first. Step 6: if indicator is not blinking, mouse may be in sleep mode — press any button first to wake, then repeat pairing steps. Note: Bluetooth is not recommended for low-latency gaming — for gaming use 2.4GHz or wired mode."
            },
            {
                "tag": "Cursor lagging",
                "scenario": "A customer says: 'My Ignis Mouse cursor keeps skipping and lagging. I use it on 2.4GHz.'",
                "question": "Diagnose cursor lag on the Ignis Mouse.",
                "rubric": "Step 1: check the surface — use the mouse on a smooth non-reflective surface or a mouse pad. PixArt 3311 sensor performs poorly on glass or reflective surfaces. Step 2: check battery level — low battery causes erratic wireless performance. Charge if needed (red LED when charging). Step 3: check for interference — move receiver away from USB 3.0 devices and Wi-Fi routers. Use a USB 2.0 port for the receiver. Step 4: re-sync in 2.4GHz mode (hold Left + Right + Scroll for 3 seconds). Step 5: turn off the mouse when not in use (centre switch position) to avoid background reconnection drain. Step 6: avoid leaving mouse in pairing mode unnecessarily — drains battery."
            },
            {
                "tag": "Battery draining too fast",
                "scenario": "A customer says: 'My Ignis Mouse battery drains within a day. I thought it was supposed to last 52 hours.'",
                "question": "Diagnose battery drain and give tips on the Ignis Mouse.",
                "rubric": "52-hour battery life is measured under typical usage conditions. Possible causes for faster drain: (1) Mouse is left on when not in use — always switch to centre (OFF) position when not in use. (2) Mouse is being left in Bluetooth pairing mode — pairing mode drains battery faster than connected mode. (3) Heavy continuous use — 52 hours is an estimate, actual varies with usage intensity. (4) Battery is degrading due to age or repeated full discharge cycles — this is normal wear. Tips: turn off the mouse (centre switch) when not in use. Avoid complete discharge regularly. Charge with USB-C cable — wired mode charges simultaneously with use. Do not leave in pairing mode longer than needed."
            },
            {
                "tag": "Software and customisation",
                "scenario": "A customer asks: 'Can I customise the Ignis Mouse? What does the software let me do?'",
                "question": "Explain software support and customisation on the Ignis Mouse.",
                "rubric": "Yes, the Ignis Mouse has software support. Software allows: DPI customisation (including access to up to 24000 DPI beyond the 6 hardware presets), macro recording, button function customisation. Software is available for download from thecosmicbyte.com. Compatible with Windows XP, Vista, 7/8/10/11. macOS is not listed as a supported OS for the software — basic use works on any OS but full customisation is Windows. The mouse has no RGB to customise by design (stealth). The DPI button on the bottom cycles 6 hardware preset levels without software."
            },
            {
                "tag": "Warranty and compatibility",
                "scenario": "A customer asks: 'I accidentally dropped my Ignis Mouse in water. Is that covered under warranty? Also what operating systems does it work on?'",
                "question": "Explain warranty and OS compatibility on the Ignis Mouse.",
                "rubric": "Compatibility: Windows XP, Vista, 7/8/10/11 — basic plug-and-play on all. Software is Windows specific. Warranty: 1 year against manufacturing defects only. Water/liquid damage is NOT covered — the Ignis dropped in water is a user-caused incident and is not covered. Physical damage not covered. Tampered products not covered. The customer's incident is unfortunately not covered under warranty. Recommend checking if the mouse still functions after drying thoroughly for 24-48 hours in a dry environment. Support: +91 7351615161 (Mon-Sat 10am-6pm), WhatsApp: +91 7351615161, cc@thecosmicbyte.com."
            }
        ]
    },
    {
        "id": "raptor_mouse",
        "name": "Raptor Mouse",
        "category": "Mouse",
        "description": "Dual-mode gaming mouse (2.4G wireless + USB wired). PixArt 3212 sensor, DPI 800–4800, 500Hz polling, 30 IPS tracking, Huano switches (10M clicks), 96g without cable, 1.6m braided cable, PTFE feet (0.58mm), 11 RGB effects, 6 buttons, ABS surface. No Bluetooth.",
        "available": True,
        "questions": [
            {
                "tag": "Connectivity — dual mode setup",
                "scenario": "A new customer asks: 'How do I connect my Raptor Mouse to my PC? Does it have Bluetooth?'",
                "question": "Explain the connection modes on the Raptor Mouse and clarify what modes are available.",
                "rubric": "The Raptor Mouse is DUAL mode only — NOT tri-mode. It does NOT have Bluetooth. Two modes available: Wired (USB cable) and 2.4GHz wireless (USB dongle). Wired setup: unpack, connect the 1.6m braided USB cable to PC — Windows detects within 5-30 seconds. Wireless 2.4GHz setup: plug the USB dongle securely into PC/laptop, switch the mouse to '2.4G' mode using the slider switch on the bottom. If not detected, try a different USB port. Agent must clearly state there is no Bluetooth option on the Raptor — customers expecting tri-mode connectivity need to be informed of this key difference."
            },
            {
                "tag": "DPI range and adjustment",
                "scenario": "A customer asks: 'What DPI levels does the Raptor Mouse support? How do I change them?'",
                "question": "Explain DPI range and adjustment on the Raptor Mouse.",
                "rubric": "DPI range: 800 to 4800 DPI. The DPI is adjustable using a button near the scroll wheel — press to cycle through DPI levels. The Raptor has a lower maximum DPI (4800) compared to other models in the range — it uses the PixArt 3212 sensor. Polling rate is 500Hz (lower than the 1000Hz of most other models). Maximum tracking speed is 30 IPS. The Raptor is positioned as an entry-level wireless gaming mouse. Agent should note the 500Hz polling rate is the maximum — not adjustable to 1000Hz."
            },
            {
                "tag": "RGB lighting",
                "scenario": "A customer asks: 'How do I change the RGB on my Raptor Mouse? It has different colours when I received it.'",
                "question": "Explain RGB functionality on the Raptor Mouse.",
                "rubric": "The Raptor Mouse features 11 RGB effects on the mouse back and logo. The RGB creates a fashionable modern appearance. RGB mode can be cycled through the available effects. The mouse has RGB on both the back body and the logo — these can display different colours and patterns depending on the selected mode. There is no dedicated software listed for the Raptor Mouse for RGB customisation on the thecosmicbyte.com website (unlike the Firestorm which has dedicated software). Customers should check the Cosmic Byte website for any available Raptor software updates."
            },
            {
                "tag": "Mouse not connecting in 2.4G",
                "scenario": "A customer says: 'My Raptor Mouse is not being detected by my PC in 2.4G mode.'",
                "question": "Troubleshoot 2.4G connection on the Raptor Mouse.",
                "rubric": "Step 1: ensure USB dongle is firmly plugged into a working USB port — try a different port. Step 2: switch the mouse slider to '2.4G' mode (not wired/off position). Step 3: power on the mouse — check the power switch on the bottom is in the ON position. Step 4: if still not detected, try the dongle in a different USB port. Step 5: restart the PC with the dongle connected. Step 6: ensure the mouse is charged — charge for at least 30 minutes if battery is low. A red LED may indicate charging status. Step 7: avoid using the dongle through a USB hub — connect directly to PC USB port for best results."
            },
            {
                "tag": "Mouse not powering on",
                "scenario": "A customer says: 'My Raptor Mouse will not turn on at all. Nothing happens when I try to use it.'",
                "question": "Walk the customer through diagnosing a Raptor Mouse that won't power on.",
                "rubric": "Step 1: check battery/charge — connect the USB cable and charge for at least 30 minutes. Step 2: ensure the power switch (located on the bottom) is in the ON position. Step 3: for wireless mode, ensure the slider switch is set to '2.4G' (not the off position). Step 4: for wired mode, connect the USB cable — wired mode should work regardless of power switch position. Step 5: try a different USB cable or port. Step 6: after charging, attempt to power on again. If nothing works after full charge attempt, it may indicate a battery or hardware issue — contact support."
            },
            {
                "tag": "Cursor not moving or lagging",
                "scenario": "A customer says: 'My Raptor Mouse cursor moves but it is very jerky and inconsistent.'",
                "question": "Diagnose jerky cursor movement on the Raptor Mouse.",
                "rubric": "Step 1: ensure the mouse is on a clean, flat, non-reflective surface or mouse pad. Avoid glass or transparent surfaces. Step 2: check for dust or dirt on the sensor — clean the sensor lens gently. Step 3: increase the DPI setting using the DPI button — low DPI on a large screen can feel jerky. Step 4: if on 2.4G wireless, check for signal interference — USB 3.0 hard drives and Wi-Fi routers interfere with 2.4GHz. Move dongle or switch USB port. Step 5: try changing USB port for the dongle. Step 6: in wired mode, try a different cable or port. Note: Raptor's polling rate is 500Hz (not 1000Hz) — this is lower than other models which is inherent to this mouse."
            },
            {
                "tag": "Mouse disconnecting randomly",
                "scenario": "A customer says: 'My Raptor Mouse keeps disconnecting during gaming on wireless mode.'",
                "question": "Diagnose random disconnections on the Raptor Mouse.",
                "rubric": "Step 1: check battery level — low battery is the most common cause of random disconnections. Charge the mouse fully. Step 2: ensure the USB dongle is not obstructed or blocked by other devices. Step 3: check for interference sources — USB 3.0 hard drives, Wi-Fi routers, other 2.4GHz devices near the dongle cause dropouts. Step 4: move the dongle to a front USB port for better line of sight to the mouse. Step 5: ensure the dongle is not in a USB hub — use a direct motherboard USB port. Step 6: check maximum wireless range — the Raptor's specifications show 30 IPS tracking speed, designed for desk-range use. Step 7: try the dongle in a USB 2.0 port (USB 3.0 causes 2.4GHz interference)."
            },
            {
                "tag": "Buttons not working",
                "scenario": "A customer says: 'The extra buttons on my Raptor Mouse are not doing anything.'",
                "question": "Diagnose unresponsive buttons on the Raptor Mouse.",
                "rubric": "Step 1: reconnect the mouse — disconnect and reconnect in the current mode. Step 2: restart the PC and try again. Step 3: check for physical obstructions or dirt under the buttons — clean gently. Step 4: test in both wired and wireless modes to isolate if it is connection-related. Step 5: test on another computer to rule out PC-side software conflicts. Step 6: the Raptor has 6 buttons total. If specific buttons are completely unresponsive across all modes and computers, this may indicate a hardware defect — contact Cosmic Byte support. Switch lifespan is 10 million clicks (Huano)."
            },
            {
                "tag": "Charging and cable",
                "scenario": "A customer asks: 'How do I charge the Raptor Mouse? What type of cable does it use?'",
                "question": "Explain charging and cable details for the Raptor Mouse.",
                "rubric": "The Raptor Mouse uses a 1.6m braided cable. The braided cable provides durability and prevents external damage — more robust than standard rubber cables. To charge: connect the USB cable to the mouse and a USB power source. A red LED may indicate charging in progress — check LED status when connected. In wired mode the mouse functions while the cable is connected. The Raptor Mouse does NOT use a Type-C paracord like other models — it uses a braided cable which is heavier and more traditional. Battery: the Raptor has an internal battery for wireless use. Unlike the Aether, the battery is not user-replaceable."
            },
            {
                "tag": "Warranty and specifications",
                "scenario": "A customer asks: 'My Raptor Mouse got wet in the rain. Is that covered? Also can it reach 1000Hz polling?'",
                "question": "Address the warranty question and confirm the Raptor Mouse's polling rate specification.",
                "rubric": "Polling rate: the Raptor Mouse has a maximum polling rate of 500Hz — it does NOT support 1000Hz. This is a hardware specification of the PixArt 3212 sensor and cannot be upgraded. Customers expecting 1000Hz should look at the Atlas, Aether, Ignis, or Velox models. Warranty: 1 year against manufacturing defects only. Water/rain damage is NOT covered under warranty — physical and water damage are explicitly excluded. The customer's rain damage is not covered. Weight: 96g without cable — heavier than tri-mode models. Support: +91 7351615161 (Mon-Sat 10am-6pm), WhatsApp: +91 7351615161, cc@thecosmicbyte.com."
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
        "ai_flags": [],          # parallel to scores/answers/feedbacks; True if grader judged answer AI-generated
        "client_ip": _get_client_ip(),  # captured once per session for cross-ref with support portal log
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

ALSO judge whether the answer reads as AI-GENERATED rather than written by the
agent or pasted from a product manual. IMPORTANT context for this judgement:
agents ARE allowed to consult and copy from the product manual during the
test. Agents are NOT allowed to use AI tools (ChatGPT, Claude, Gemini, etc.)
to write the answer for them. You are looking specifically for AI generation,
NOT for "looks like the agent used a reference."

Set ai_likely: true when the answer shows AI tells:
- Conversational AI framing ("Great question!", "Let me walk you through",
  "I'd be happy to help", "Feel free to reach out", "I hope this helps")
- Heavy em-dashes, parallel bullet structure, "Step 1: / Step 2:" formatted
  like documentation an AI assistant produces
- Customer-facing warmth wrapped around the facts (rather than just the
  facts on their own)
- Hedging an agent would not write ("I should note that", "It's worth
  mentioning", "Please be aware that")
- Polished prose AND comprehensive coverage of every rubric point at once
  (an agent typing or pasting tends to either be terse OR cover only the
  parts they remember/found)

Set ai_likely: false when the answer looks like manual paste or human writing:
- Clipped, technical tone listing button combos and model numbers
- Wording that closely mirrors the rubric (likely because the rubric and
  the answer both come from the same manual)
- Lists of facts without softening or customer warmth
- Short, terse, or has natural human gaps, typos, or informal phrasing
- Mixes correct technical content with small inaccuracies or omissions

When uncertain, default to ai_likely: false. False positives on honest agents
who write fluent prose are worse than false negatives.

Reply with ONLY raw JSON, no markdown, starting with {{ and ending with }}:
{{"score":7,"feedback":"What was good and what was missing from their answer.","ai_likely":false}}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        import re
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            result = json.loads(match.group())
            return {
                "score": max(0, min(10, round(float(result.get("score", 5))))),
                "feedback": result.get("feedback", "No feedback provided."),
                "ai_likely": bool(result.get("ai_likely", False)),
            }
        return {"score": 5, "feedback": raw, "ai_likely": False}
    except Exception as e:
        return {"score": 0, "feedback": f"Grading error: {str(e)}", "ai_likely": False}

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

    # Category filter
    categories = ["All products"] + sorted(list(set(p["category"] for p in PRODUCTS)))
    selected_category = st.selectbox("🎮 Filter by type", categories, index=0)

    st.markdown(f"### Available tests")

    filtered_products = PRODUCTS if selected_category == "All products" else [p for p in PRODUCTS if p["category"] == selected_category]
    st.markdown(f"<small>Showing {len(filtered_products)} of {len(PRODUCTS)} controllers</small>", unsafe_allow_html=True)

    for product in filtered_products:
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
                        st.session_state.ai_flags = []
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
                    st.session_state.ai_flags.append(bool(result.get("ai_likely", False)))
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
                st.session_state.answers,
                st.session_state.ai_flags,
                st.session_state.get("client_ip", ""),
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
        ai_flag = st.session_state.ai_flags[i] if i < len(st.session_state.ai_flags) else False
        level = "score-good" if sc >= 8 else "score-ok" if sc >= 5 else "score-weak"
        lbl = "Strong" if sc >= 8 else "Partial" if sc >= 5 else "Weak"
        ai_lbl = " 🤖 AI-style" if ai_flag else ""
        with st.expander(f"Q{i+1}: {q['tag']} — {sc}/10 ({lbl}){ai_lbl}"):
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
            st.session_state.ai_flags = []
            st.session_state.screen = "quiz"
            st.rerun()


# ─────────────────────────────────────────────
#  SEND RESULT EMAIL
# ─────────────────────────────────────────────
def send_result_email(agent_name, product_name, earned, max_score, pct, passed, qs, scores, feedbacks, answers, ai_flags=None, client_ip=""):
    try:
        gmail = st.secrets["GMAIL_ADDRESS"]
        app_password = st.secrets["GMAIL_APP_PASSWORD"]

        subject = f"[Cosmic Byte] {agent_name} — {product_name} Test — {'PASSED ✅' if passed else 'FAILED ❌'} ({pct}%)"

        # AI-style summary — count of grader-flagged answers. Advisory only:
        # Haiku grading Haiku output gets the easy cases but produces both
        # false positives (fluent paragraph writers) and false negatives
        # (post-processed AI output). Cross-reference with the support-portal
        # IP log for high-confidence cases.
        ai_flags = ai_flags or []
        ai_block = ""
        if ai_flags:
            flagged_qs = [i + 1 for i, f in enumerate(ai_flags) if f]
            if flagged_qs:
                ai_block = f"AI-style: ⚠ {len(flagged_qs)} answer(s) flagged as AI-generated by grader: Q{', Q'.join(str(n) for n in flagged_qs)}\n"
            else:
                ai_block = "AI-style: no answers flagged by grader\n"

        # Client IP (captured once at session init) — cross-reference against
        # the support portal CSV log to detect agents running queries through
        # the support AI during the test window.
        ip_block = f"Test IP:  {client_ip or '(unavailable — check Streamlit deployment proxy config)'}\n"

        body = f"""
COSMIC BYTE — AGENT TEST RESULT
================================
Agent:    {agent_name}
Product:  {product_name}
Date:     {datetime.now().strftime("%d %b %Y %H:%M")}
Score:    {earned} / {max_score}
Result:   {pct}% — {"PASSED ✅" if passed else "FAILED ❌"}
{ip_block}{ai_block}================================

QUESTION BY QUESTION BREAKDOWN:
"""
        for i, q in enumerate(qs):
            sc = scores[i] if i < len(scores) else 0
            fb = feedbacks[i] if i < len(feedbacks) else ""
            ans = answers[i] if i < len(answers) else ""
            ai_flag = ai_flags[i] if i < len(ai_flags) else False
            lbl = "Strong" if sc >= 8 else "Partial" if sc >= 5 else "Weak"
            ai_str = " — 🤖 AI-STYLE" if ai_flag else ""
            body += f"""
Q{i+1}: {q['tag']} — {sc}/10 ({lbl}){ai_str}
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
