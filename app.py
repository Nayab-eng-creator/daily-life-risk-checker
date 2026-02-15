import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Daily Life Risk Checker Agent", page_icon="🛡️", layout="centered")

# ---------- Helpers ----------
CATEGORIES = ["health", "travel", "money", "study", "security"]

DEFAULT_STATE = {
    "health": 0,
    "travel": 0,
    "money": 0,
    "study": 0,
    "security": 0,
    "last_updated": None,
}

def clamp_0_10(x):
    return max(0, min(10, x))

def compute_score(state):
    weights = {
        "health": 0.25,
        "travel": 0.15,
        "money": 0.20,
        "study": 0.25,
        "security": 0.15,
    }
    raw = 0.0
    for k, w in weights.items():
        raw += state[k] * w
    return round(raw * 10)

def risk_level(score):
    if score <= 20: return "Low ✅"
    elif score <= 40: return "Moderate 🙂"
    elif score <= 60: return "High ⚠️"
    elif score <= 80: return "Very High 🚨"
    return "Critical 🛑"

def parse_kv_log(text):
    t = text.lower().replace(",", " ").strip()
    if not t.startswith("log "): return None
    parts = t.split()
    updates = {}
    for p in parts[1:]:
        if "=" in p:
            key, val = p.split("=", 1)
            if key in CATEGORIES:
                try:
                    updates[key] = clamp_0_10(int(float(val)))
                except:
                    pass
    return updates if updates else {}

def simple_advice(state, score):
    tips = []
    if state["health"] >= 7: tips.append("🩺 Improve sleep and hydration.")
    if state["study"] >= 7: tips.append("📚 Focus on closest deadline first.")
    if state["money"] >= 7: tips.append("💸 Reduce non-essential spending.")
    if state["security"] >= 7: tips.append("🔐 Change passwords & enable 2FA.")
    if state["travel"] >= 7: tips.append("🚗 Avoid risky travel times.")

    if score <= 40: tips.insert(0, "🙂 Risk manageable. Keep routine.")
    elif score <= 70: tips.insert(0, "⚠️ Focus on highest risk area.")
    else: tips.insert(0, "🚨 Take immediate safety steps.")

    return tips[:6]

def help_text():
    return """
### Commands
- log health=7 travel=3 money=5 study=8 security=6
- score
- advice
- status
- reset

You can also say:
"ask health questions"
"""

def format_status(state):
    return "\n".join([f"- **{k.title()}**: {state[k]}/10" for k in CATEGORIES])

# ---------- HEALTH QUESTION SYSTEM ----------
HEALTH_QUESTIONS = [
    ("sleep", "How many hours did you sleep last night?"),
    ("symptoms", "Any symptoms? (none / mild / moderate / severe)"),
    ("stress", "Stress level today (0-10)?"),
    ("water", "Water intake? (low / ok / good)"),
    ("activity", "Physical activity? (none / light / moderate)")
]

def health_score(ans):
    score = 0
    try:
        if float(ans.get("sleep",7)) < 5: score += 3
    except: pass
    if "severe" in ans.get("symptoms",""): score += 4
    if "moderate" in ans.get("symptoms",""): score += 2
    try:
        if int(ans.get("stress",3)) > 7: score += 3
    except: pass
    if "low" in ans.get("water",""): score += 1
    if "none" in ans.get("activity",""): score += 1
    return clamp_0_10(score)

# ---------- Session State ----------
if "risk_state" not in st.session_state:
    st.session_state.risk_state = DEFAULT_STATE.copy()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"assistant","content":"Hi 👋 I’m your Risk Checker Agent.\nType help."}]

if "mode" not in st.session_state:
    st.session_state.mode = None

if "health_step" not in st.session_state:
    st.session_state.health_step = 0

if "health_answers" not in st.session_state:
    st.session_state.health_answers = {}

# ---------- UI ----------
st.title("🛡️ Daily Life Risk Checker Agent")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_text = st.chat_input("Type here...")

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"): st.markdown(user_text)

    text = user_text.strip()
    lower = text.lower()
    state = st.session_state.risk_state
    reply = ""

    # ---------- HEALTH MODE ----------
    if st.session_state.mode == "health":
        step = st.session_state.health_step
        key,_q = HEALTH_QUESTIONS[step]
        st.session_state.health_answers[key] = text
        st.session_state.health_step += 1

        if st.session_state.health_step >= len(HEALTH_QUESTIONS):
            health_val = health_score(st.session_state.health_answers)
            state["health"] = health_val
            score = compute_score(state)

            st.session_state.mode=None
            st.session_state.health_step=0

            reply = f"✅ Health Risk Updated: {health_val}/10\nOverall Score: {score}/100"
        else:
            reply = HEALTH_QUESTIONS[st.session_state.health_step][1]

    # ---------- COMMANDS ----------
    elif lower in ["help"]:
        reply = help_text()

    elif lower=="score":
        score=compute_score(state)
        reply=f"Score: {score}/100 ({risk_level(score)})"

    elif lower=="advice":
        score=compute_score(state)
        reply="\n".join(simple_advice(state,score))

    elif lower=="status":
        reply=format_status(state)

    elif lower=="reset":
        st.session_state.risk_state=DEFAULT_STATE.copy()
        reply="Reset done"

    elif lower.startswith("log "):
        upd=parse_kv_log(text)
        if upd:
            state.update(upd)
            reply="Updated ✅"
        else:
            reply="Format: log health=5 study=6"

    # ---------- GREETINGS ----------
    elif any(x in lower for x in ["hi","hello","salam","aoa"]):
        reply="Hello 👋 I can track your risks or ask health questions. Type help."

    elif "ask health" in lower or "ask questions" in lower:
        st.session_state.mode="health"
        st.session_state.health_step=0
        reply=HEALTH_QUESTIONS[0][1]

    else:
        reply="Type help to see options."

    st.session_state.messages.append({"role":"assistant","content":reply})
    with st.chat_message("assistant"): st.markdown(reply)
