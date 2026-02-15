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
    # Weighted score (you can tweak these)
    weights = {
        "health": 0.25,
        "travel": 0.15,
        "money": 0.20,
        "study": 0.25,
        "security": 0.15,
    }
    raw = 0.0
    for k, w in weights.items():
        raw += state[k] * w  # each category 0..10
    # Convert 0..10 to 0..100
    return round(raw * 10)

def risk_level(score):
    if score <= 20:
        return "Low ✅"
    elif score <= 40:
        return "Moderate 🙂"
    elif score <= 60:
        return "High ⚠️"
    elif score <= 80:
        return "Very High 🚨"
    return "Critical 🛑"

def parse_kv_log(text):
    """
    Accepts:
    log health=7 travel=3 money=5 study=8 security=6
    also accepts commas:
    log health=7, travel=3
    """
    t = text.lower().replace(",", " ").strip()
    if not t.startswith("log "):
        return None

    parts = t.split()
    updates = {}
    for p in parts[1:]:
        if "=" in p:
            key, val = p.split("=", 1)
            key = key.strip()
            val = val.strip()
            if key in CATEGORIES:
                try:
                    num = float(val)
                    updates[key] = clamp_0_10(int(round(num)))
                except:
                    pass
    return updates if updates else {}

def simple_advice(state, score):
    tips = []

    # Category tips
    if state["health"] >= 7:
        tips.append("🩺 Health: Sleep, hydration, and a 10–20 min walk today. Avoid junk/late-night screens.")
    elif state["health"] >= 4:
        tips.append("🩺 Health: Keep routine steady. Drink water + take short breaks.")

    if state["travel"] >= 7:
        tips.append("🚗 Travel: Avoid peak traffic, keep phone charged, and share live location if going far.")
    elif state["travel"] >= 4:
        tips.append("🚗 Travel: Leave early and keep emergency cash + powerbank.")

    if state["money"] >= 7:
        tips.append("💸 Money: Freeze non-essential spending for 48 hours. Track expenses today.")
    elif state["money"] >= 4:
        tips.append("💸 Money: Set a daily spending limit and note all purchases.")

    if state["study"] >= 7:
        tips.append("📚 Study: Do a 25-min focus sprint now. List deadlines and pick the closest one first.")
    elif state["study"] >= 4:
        tips.append("📚 Study: Make a 3-task plan for today (small + doable).")

    if state["security"] >= 7:
        tips.append("🔐 Security: Change important passwords, enable 2FA, and avoid unknown links.")
    elif state["security"] >= 4:
        tips.append("🔐 Security: Review privacy settings and update apps.")

    # Overall tip based on score
    if score <= 20:
        tips.insert(0, "✅ Overall: You’re safe today. Just maintain your routine.")
    elif score <= 40:
        tips.insert(0, "🙂 Overall: Some risk is building. Fix 1–2 areas today.")
    elif score <= 60:
        tips.insert(0, "⚠️ Overall: Prioritize your highest category and reduce optional stress.")
    elif score <= 80:
        tips.insert(0, "🚨 Overall: Take action now—reduce workload, avoid risky travel, tighten spending.")
    else:
        tips.insert(0, "🛑 Overall: Critical level—pause non-essential activities and focus on safety essentials.")

    return tips[:6]  # keep it short

def help_text():
    return (
        "### Commands you can type\n"
        "- `log health=7 travel=3 money=5 study=8 security=6`  (each 0–10)\n"
        "- `score`  → show your current risk score\n"
        "- `advice` → show simple advice\n"
        "- `status` → show all category values\n"
        "- `reset`  → clear everything\n\n"
        "### Tips\n"
        "- You can update only one value too: `log study=9`\n"
        "- Higher number = higher risk.\n"
    )

def format_status(state):
    lines = []
    for k in CATEGORIES:
        lines.append(f"- **{k.title()}**: {state[k]}/10")
    if state["last_updated"]:
        lines.append(f"- **Last updated**: {state['last_updated']}")
    return "\n".join(lines)

# ---------- Session State ----------
if "risk_state" not in st.session_state:
    st.session_state.risk_state = DEFAULT_STATE.copy()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I’m your **Daily Life Risk Checker Agent** 🛡️\n\n"
                "Type `help` to see commands.\n"
                "Example: `log health=6 travel=2 money=4 study=8 security=5`"
            ),
        }
    ]

# ---------- UI ----------
st.title("🛡️ Daily Life Risk Checker Agent")
st.caption("ChatGPT-style: you type → I answer. I won’t ask questions unless you ask me.")

# Show chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Chat input
user_text = st.chat_input("Type here… (try: help, log ..., score, advice)")

if user_text:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    text = user_text.strip()
    lower = text.lower().strip()

    state = st.session_state.risk_state
    reply = ""

    # Commands
    if lower in ["help", "/help", "commands"]:
        reply = help_text()

    elif lower in ["reset", "/reset", "clear"]:
        st.session_state.risk_state = DEFAULT_STATE.copy()
        reply = "✅ Reset done. Type `log health=...` to start again."

    elif lower in ["status", "/status"]:
        reply = "### Current status\n" + format_status(state)

    elif lower in ["score", "/score"]:
        score = compute_score(state)
        reply = f"### Risk Score: **{score}/100**\n**Level:** {risk_level(score)}\n\n" + format_status(state)

    elif lower in ["advice", "/advice"]:
        score = compute_score(state)
        tips = simple_advice(state, score)
        reply = f"### Advice (Score {score}/100 • {risk_level(score)})\n" + "\n".join([f"- {t}" for t in tips])

    elif lower.startswith("log "):
        updates = parse_kv_log(text)
        if updates is None:
            reply = "Type like: `log health=7 travel=3 money=5 study=8 security=6`"
        elif updates == {}:
            reply = "I couldn’t find valid values. Use 0–10 like: `log study=8`"
        else:
            for k, v in updates.items():
                state[k] = v
            state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            score = compute_score(state)
            reply = (
                "✅ Updated.\n\n"
                f"### Risk Score: **{score}/100**\n**Level:** {risk_level(score)}\n\n"
                "Type `advice` for tips or `status` to view categories."
            )

    else:
        # Default: explain what to do, without asking questions
        reply = (
            "I can track your daily risks and calculate a score.\n\n"
            "Type `help` to see commands.\n"
            "Example: `log health=6 travel=2 money=4 study=8 security=5`\n"
            "Then type: `score` or `advice`."
        )

    # Add assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
