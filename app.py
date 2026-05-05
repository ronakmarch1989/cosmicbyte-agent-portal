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
    # {
    #     "id": "atlas",
    #     "name": "Atlas",
    #     "category": "Mouse",
    #     "description": "Tri-mode wireless gaming mouse.",
    #     "available": False,
    #     "questions": []
    # },
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
