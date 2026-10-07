import html
import json
import os

import requests
import streamlit as st

# The server link and access key are saved here, so you only paste them once per Kaggle run
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.json")

PAGES = ["🏠  Dashboard", "📖  Learn", "📝  Quiz", "📚  Material"]


# ===================== Helpers =====================

def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"url": "", "key": ""}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f)


def call_api(path, payload=None, files=None):
    """Send a request to the Kaggle server. Returns the JSON reply, or None if something failed."""
    server = st.session_state["server"]
    url = server["url"] + path
    headers = {"Authorization": f"Bearer {server['key']}"}
    try:
        if files is not None:
            res = requests.post(url, headers=headers, files=files, timeout=600)
        elif payload is not None:
            res = requests.post(url, headers=headers, json=payload, timeout=600)
        else:
            res = requests.get(url, headers=headers, timeout=60)
    except requests.exceptions.RequestException:
        st.error("Can't reach the server. Check that Kaggle is running and the server link is correct.")
        return None
    if res.status_code == 401:
        st.error("The access key is wrong. Copy it again from Kaggle.")
        return None
    if not res.ok:
        try:
            message = res.json().get("detail", res.text)
        except ValueError:
            message = res.text
        st.error(message)
        return None
    return res.json()


def level(score):
    """Name and color for a score out of 10."""
    if score >= 7:
        return "Strong", "#4ADE80"
    if score >= 6:
        return "Getting there", "#FBBF24"
    return "Review", "#F87171"


def badge(text, color):
    return (f'<span class="badge" style="color:{color};background:{color}22;'
            f'border:1px solid {color}55">{html.escape(text)}</span>')


def pretty_lesson(text):
    """Make the section names in the explanation bold, each on its own line."""
    for label in ["Explanation:", "Example:", "Tip for you:"]:
        text = text.replace(label, f"\n\n**{label}**\n\n")
    return text


def go_to(topic, page):
    """Used by buttons: put the topic in both boxes and open a page."""
    st.session_state["learn_topic"] = topic
    st.session_state["quiz_topic"] = topic
    st.session_state["page"] = page


def set_page(page):
    """Used by buttons that open another page."""
    st.session_state["page"] = page


def upload_box(key):
    """File upload used on the empty dashboard and on the Material page."""
    uploaded = st.file_uploader("PDF, DOCX, EPUB or TXT", type=["pdf", "docx", "epub", "txt"],
                                key=f"{key}_file")
    st.caption("Arabic material works best as DOCX, EPUB or TXT. "
               "Uploading new material starts your progress from zero.")
    if uploaded and st.button("Use this file", type="primary", key=f"{key}_btn"):
        with st.spinner("Reading the file and finding topics. A full book can take a few minutes..."):
            data = call_api("/upload", files={"file": (uploaded.name, uploaded.getvalue())})
        if data:
            for key_name in ["explanation", "quiz", "results"]:
                st.session_state.pop(key_name, None)
            st.toast(f"Ready! {data['chunks']} chunks loaded from {data['book']}.")
            st.session_state["next_page"] = PAGES[0]
            st.rerun()


def need_material():
    """Shown on Learn and Quiz when nothing is uploaded yet."""
    st.info("Upload a book or lecture notes first.")
    st.button("Upload material", type="primary", on_click=set_page, args=(PAGES[0],))
    st.stop()


def page_header(kicker, title, subtitle=""):
    sub = f'<p class="subtitle">{html.escape(subtitle)}</p>' if subtitle else ""
    st.markdown(f'<p class="kicker">{kicker}</p><h1 class="title">{title}</h1>{sub}',
                unsafe_allow_html=True)


def stat_card(icon, label, value, note, note_color):
    return f"""
    <div class="card stat">
      <div class="stat-top"><span class="icon">{icon}</span><span class="label">{label}</span></div>
      <div class="value">{value}</div>
      <div class="note" style="color:{note_color}">{note}</div>
    </div>"""


# ===================== Page setup and style =====================

st.set_page_config(page_title="AI Personal Tutor", page_icon="📚", layout="wide")

st.markdown("""
<style>
/* Soft violet glow in the corner of the page */
.stApp { background:
    radial-gradient(900px 420px at 92% -8%, rgba(139,124,246,0.22), transparent 60%),
    radial-gradient(700px 380px at 0% 105%, rgba(99,102,241,0.10), transparent 60%),
    #0D0F14; }
.block-container { padding-top: 3.2rem; max-width: 1200px; }

/* Arabic paragraphs go right-to-left automatically, English stays left-to-right */
p, li, h1, h2, h3, textarea, input { unicode-bidi: plaintext; text-align: start; }

/* Page titles */
.kicker { color: #8E92A8; font-size: 0.78rem; letter-spacing: 0.12em; margin: 0; text-transform: uppercase; }
.title { font-size: 2rem; font-weight: 700; margin: 0.15rem 0 0.2rem 0; padding: 0; }
.subtitle { color: #9CA0B5; margin: 0 0 1.2rem 0; }

/* Glass cards */
.card { position: relative; overflow: hidden; border-radius: 16px; padding: 1.1rem 1.2rem;
        background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.08); margin-bottom: 1rem; }
.card::after { content: ""; position: absolute; right: -40px; bottom: -60px; width: 180px; height: 140px;
               background: radial-gradient(closest-side, rgba(139,124,246,0.35), transparent); }
.card h3, .card-title { margin: 0 0 0.6rem 0 !important; padding: 0 !important; font-size: 1.05rem !important; font-weight: 600; }
div[data-testid="stVerticalBlockBorderWrapper"], div[class*="st-key-card"] { border-radius: 16px !important;
        background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.015));
        border-color: rgba(255,255,255,0.08) !important; }

/* Stat cards */
.stat-top { display: flex; align-items: center; gap: 0.6rem; }
.icon { display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px;
        border-radius: 10px; background: rgba(139,124,246,0.18); font-size: 1.05rem; }
.label { color: #C9CBD8; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat { min-height: 150px; }
.value { font-size: 2.2rem; font-weight: 700; margin-top: 0.6rem; line-height: 1.1; }
.note { font-size: 0.85rem; margin-top: 0.25rem; }

/* Badges and rows */
.badge { display: inline-block; padding: 0.1rem 0.6rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.row-title { font-weight: 600; margin: 0; }
.row-sub { color: #8E92A8; font-size: 0.82rem; margin: 0; }

/* Topics table */
.ttable { width: 100%; border-collapse: collapse; border: none !important; }
.ttable tr, .ttable th, .ttable td { border-left: none !important; border-right: none !important;
                                     border-top: none !important; background: transparent !important; }
.ttable th { color: #8E92A8; font-weight: 500; font-size: 0.82rem; text-align: start; padding: 0.5rem 0.4rem;
             border-bottom: 1px solid rgba(255,255,255,0.08); }
.ttable td { padding: 0.65rem 0.4rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
.bar { height: 6px; border-radius: 99px; background: rgba(255,255,255,0.08); min-width: 90px; }
.bar > div { height: 6px; border-radius: 99px; }

/* Buttons */
.stButton > button { border-radius: 10px; }
button[kind="primary"], button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #8B7CF6, #6D5DE8) !important; border: none !important; }

/* Sidebar menu: the radio buttons look like menu items */
section[data-testid="stSidebar"] { background: #0B0D12; border-right: 1px solid rgba(255,255,255,0.06); }
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.2rem; width: 100%; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div { width: 100%; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { padding: 0.55rem 0.75rem; border-radius: 10px;
        width: 100%; cursor: pointer; }
/* hide the round radio dot (newer and older Streamlit) */
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child,
section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: rgba(255,255,255,0.05); }
section[data-testid="stSidebar"] label[data-selected="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: rgba(139,124,246,0.16); }
.empty { text-align: center; padding: 2.2rem 1.5rem 1.4rem 1.5rem; }
.empty .big { font-size: 2.6rem; }
.empty h2 { margin: 0.4rem 0 0.3rem 0; padding: 0; text-align: center !important; }
.empty p { color: #9CA0B5; margin: 0 auto; max-width: 560px; text-align: center; }
.brand { font-size: 1.25rem; font-weight: 700; margin: 0.2rem 0 1rem 0; }
.brand span { color: #8B7CF6; }
.side-card { border-radius: 14px; padding: 0.9rem; margin: 1rem 0 0.6rem 0; font-size: 0.85rem;
        background: linear-gradient(160deg, rgba(139,124,246,0.28), rgba(139,124,246,0.06));
        border: 1px solid rgba(139,124,246,0.35); }
.side-card b { display: block; margin-bottom: 0.2rem; }
</style>
""", unsafe_allow_html=True)

if "server" not in st.session_state:
    st.session_state["server"] = load_config()
if "page" not in st.session_state:
    st.session_state["page"] = PAGES[0]
# Streamlit forgets the value of a box that isn't on the current page. Copying each value
# onto itself at the start of every run keeps it while the student moves between pages.
st.session_state.setdefault("num_questions", 3)
st.session_state.setdefault("difficulty", "Medium")
for box in ["learn_topic", "quiz_topic", "num_questions", "difficulty"]:
    if box in st.session_state:
        st.session_state[box] = st.session_state[box]
# A page change asked for after the menu was drawn (like after an upload) is applied here
if "next_page" in st.session_state:
    st.session_state["page"] = st.session_state.pop("next_page")

# ===================== Sidebar =====================

with st.sidebar:
    st.markdown('<div class="brand">📚 AI <span>Tutor</span></div>', unsafe_allow_html=True)
    st.caption("MENU")
    page = st.radio("Menu", PAGES, key="page", label_visibility="collapsed")

connected = bool(st.session_state["server"]["url"])
status = call_api("/progress") if connected else None

with st.sidebar:
    if status and status["book"]:
        st.markdown(f'<div class="side-card"><b>Studying from</b>{html.escape(status["book"])}</div>',
                    unsafe_allow_html=True)
        st.button("Change material", on_click=set_page, args=(PAGES[3],), use_container_width=True)
    st.write("")
    with st.expander("🔌 Server connection", expanded=not connected):
        st.caption("Paste the two lines Kaggle printed at the end of the notebook.")
        url = st.text_input("Server link", value=st.session_state["server"]["url"])
        key = st.text_input("Access key", value=st.session_state["server"]["key"], type="password")
        if st.button("Connect", use_container_width=True):
            # strip() and rstrip("/") remove the extra spaces and slashes that break the link
            st.session_state["server"] = {"url": url.strip().rstrip("/"), "key": key.strip()}
            save_config(st.session_state["server"])
            st.rerun()

if not connected:
    page_header("Welcome", "AI Personal Tutor", "Learn any topic from your own material, then test yourself.")
    st.info("Start the notebook on Kaggle, then open 🔌 Server connection in the sidebar "
            "and paste the server link and access key.")
    st.stop()

topics = status["topics"] if status else {}
suggested = status["suggested"] if status else []
weak = status["weak_topics"] if status else []
has_book = bool(status and status["book"])

# ===================== Page: Dashboard =====================

if page == PAGES[0]:
    if not has_book:
        page_header("Dashboard", "Welcome 👋", "Your personal tutor for any book or lecture notes.")
        st.markdown('<div class="card empty"><div class="big">📚</div>'
                    '<h2>Start by uploading your material</h2>'
                    '<p>Upload a book or your lecture notes. The tutor will suggest topics, explain them, '
                    'and quiz you, all from your own material.</p></div>', unsafe_allow_html=True)
        with st.container(border=True, key="card_start"):
            upload_box("start")
        st.stop()

    page_header("Dashboard", "Welcome back 👋", f"Studying from {status['book']}")
    answers = sum(info["count"] for info in topics.values())
    overall = (sum(info["average"] * info["count"] for info in topics.values()) / answers) if answers else 0
    overall_name, overall_color = level(overall) if answers else ("No quizzes yet", "#8E92A8")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card("📘", "Topics studied", len(topics),
                          f"{len(suggested)} suggested for you", "#A5A0F7"), unsafe_allow_html=True)
    c2.markdown(stat_card("✍️", "Answers", answers,
                          "across all quizzes", "#8E92A8"), unsafe_allow_html=True)
    c3.markdown(stat_card("🎯", "Average score", f"{overall:.1f}" if answers else "–",
                          overall_name, overall_color), unsafe_allow_html=True)
    c4.markdown(stat_card("🔁", "Topics to review", len(weak),
                          "keep going!" if not weak else "worth a second look",
                          "#4ADE80" if not weak else "#FBBF24"), unsafe_allow_html=True)

    left, right = st.columns([3, 2])

    # Study next: weak topics first, then suggested topics the student hasn't tried yet
    with left:
        with st.container(border=True, key="card_next"):
            st.markdown('<p class="card-title">Study next</p>', unsafe_allow_html=True)
            plan = [(t, "review") for t in weak]
            plan += [(t, "new") for t in suggested if t.strip().lower() not in topics]
            if not plan:
                st.caption("Upload material to get topic suggestions.")
            for i, (t, kind) in enumerate(plan[:6]):
                a, b = st.columns([5, 1.3])
                if kind == "review":
                    avg = topics[t]["average"]
                    a.markdown(f'<p class="row-title">{html.escape(t.title())} &nbsp;'
                               f'{badge("Review", "#F87171")}</p>'
                               f'<p class="row-sub">Your average: {avg:.1f}/10</p>', unsafe_allow_html=True)
                else:
                    a.markdown(f'<p class="row-title">{html.escape(t)} &nbsp;{badge("New", "#A5A0F7")}</p>'
                               f'<p class="row-sub">Suggested from your material</p>', unsafe_allow_html=True)
                b.button("Study", key=f"plan_{i}", on_click=go_to, args=(t, PAGES[1]),
                         use_container_width=True)

    # A short message based on the student's results
    with right:
        if weak:
            worst = min(weak, key=lambda t: topics[t]["average"])
            msg = (f"Your weakest topic is <b>{html.escape(worst.title())}</b> "
                   f"({topics[worst]['average']:.1f}/10). Read the explanation again, then retake the quiz. "
                   "The explanation will focus on the mistakes you made.")
        elif answers:
            msg = "Nice work, no weak topics so far. Try a <b>Hard</b> quiz to push yourself."
        else:
            msg = "Pick a topic from <b>Study next</b>, read the explanation, then test yourself with a quiz."
        st.markdown(f'<div class="card"><p class="card-title">✨ Your tutor says</p><p>{msg}</p></div>', unsafe_allow_html=True)

        if suggested:
            st.markdown('<div class="card"><p class="card-title">📚 In your material</p><p>'
                        + " ".join(badge(t, "#A5A0F7") for t in suggested) + "</p></div>",
                        unsafe_allow_html=True)

    # Topics table
    if topics:
        rows = ""
        for name, info in sorted(topics.items(), key=lambda x: x[1]["average"]):
            label, color = level(info["average"])
            rows += (f"<tr><td>{html.escape(name.title())}</td><td>{info['count']}</td>"
                     f"<td>{info['average']:.1f}/10</td><td>{badge(label, color)}</td>"
                     f'<td><div class="bar"><div style="width:{info["average"] * 10:.0f}%;'
                     f'background:{color}"></div></div></td></tr>')
        st.markdown('<div class="card"><p class="card-title">Your topics</p><table class="ttable">'
                    "<tr><th>Topic</th><th>Answers</th><th>Average</th><th>Status</th><th>Progress</th></tr>"
                    f"{rows}</table></div>", unsafe_allow_html=True)

# ===================== Page: Learn =====================

elif page == PAGES[1]:
    page_header("Learn", "What do you want to learn?", "Every explanation comes from your own material.")
    if not has_book:
        need_material()

    if suggested:
        cols = st.columns(3)
        for i, t in enumerate(suggested):
            cols[i % 3].button(t, key=f"chip_{i}", on_click=go_to, args=(t, PAGES[1]), use_container_width=True)

    a, b = st.columns([5, 1])
    topic = a.text_input("Topic", placeholder="e.g. variables", key="learn_topic", label_visibility="collapsed")
    explain = b.button("Explain", type="primary", use_container_width=True)
    if explain and not topic.strip():
        st.warning("Write a topic first.")
    elif explain:
        with st.spinner("Preparing your explanation. This takes a few seconds..."):
            data = call_api("/explain", {"topic": topic})
        if data:
            st.session_state["explanation"] = data

    if "explanation" in st.session_state:
        lesson = st.session_state["explanation"]
        with st.container(border=True, key="card_lesson"):
            st.subheader(lesson["topic"].title())
            st.markdown(pretty_lesson(lesson["explanation"]))
        st.button("Test yourself on this topic →", type="primary",
                  on_click=go_to, args=(lesson["topic"], PAGES[2]))

# ===================== Page: Quiz =====================

elif page == PAGES[2]:
    page_header("Quiz", "Test yourself", "Short-answer questions, graded with feedback.")
    if not has_book:
        need_material()

    with st.container(border=True, key="card_quizsetup"):
        quiz_topic = st.text_input("Quiz topic", placeholder="e.g. variables", key="quiz_topic")
        c1, c2, c3 = st.columns([2, 2, 1])
        num_questions = c1.slider("Number of questions", min_value=1, max_value=10, key="num_questions")
        difficulty = c2.radio("Difficulty", ["Easy", "Medium", "Hard"], horizontal=True, key="difficulty")
        c3.write("")
        create = c3.button("Create quiz", type="primary", use_container_width=True)

    if create and not quiz_topic.strip():
        st.warning("Write a topic first.")
    elif create:
        with st.spinner("Writing your questions. More questions take longer..."):
            data = call_api("/quiz", {"topic": quiz_topic, "num_questions": num_questions,
                                      "difficulty": difficulty.lower()})
        if data:
            st.session_state["quiz"] = data
            # A new id gives the answer boxes new keys, so old answers don't stay in them
            st.session_state["quiz_id"] = st.session_state.get("quiz_id", 0) + 1
            st.session_state.pop("results", None)

    if "quiz" in st.session_state:
        quiz = st.session_state["quiz"]
        quiz_id = st.session_state["quiz_id"]
        st.markdown(f"### {html.escape(quiz['topic'])} &nbsp;{badge(quiz['difficulty'].title(), '#A5A0F7')}",
                    unsafe_allow_html=True)

        student_answers = []
        for i, q in enumerate(quiz["questions"], start=1):
            with st.container(border=True, key=f"card_q_{quiz_id}_{i}"):
                st.markdown(f"**Question {i}**")
                st.markdown(q)  # own paragraph, so Arabic questions show right-to-left
                student_answers.append(st.text_area(f"Answer {i}", key=f"answer_{quiz_id}_{i}", height=80,
                                                    label_visibility="collapsed",
                                                    placeholder="Write your answer here"))

        if st.button("Check my answers", type="primary"):
            results = []
            total_q = len(quiz["questions"])
            bar = st.progress(0.0, text=f"Grading question 1 of {total_q}...")
            for i, (q, a, s) in enumerate(zip(quiz["questions"], quiz["answers"], student_answers), start=1):
                bar.progress((i - 1) / total_q, text=f"Grading question {i} of {total_q}...")
                r = call_api("/evaluate", {"topic": quiz["topic"], "question": q,
                                           "correct_answer": a, "student_answer": s})
                results.append(r or {"score": None, "feedback": "Couldn't grade this answer."})
            bar.progress(1.0, text="Done!")
            st.session_state["results"] = results
            st.rerun()  # refresh so the dashboard gets the new scores

        if "results" in st.session_state:
            results = st.session_state["results"]
            total = sum(r["score"] for r in results if r["score"] is not None)
            max_total = 10 * len(results)
            name, color = level(total / max_total * 10)
            st.markdown(f'<div class="card"><p class="card-title">Results</p><div class="value">{total}/{max_total}</div>'
                        f'<div class="note" style="color:{color}">{name}</div></div>', unsafe_allow_html=True)
            for i, (r, a) in enumerate(zip(results, quiz["answers"]), start=1):
                with st.container(border=True, key=f"card_r_{quiz_id}_{i}"):
                    if r["score"] is None:
                        st.write(f"Question {i}: {r['feedback']}")
                        continue
                    _, c = level(r["score"])
                    st.markdown(f"**Question {i}** &nbsp; {badge(str(r['score']) + '/10', c)}",
                                unsafe_allow_html=True)
                    st.write(r["feedback"])
                    st.caption("Correct answer:")
                    st.caption(a)  # own line, so Arabic answers show right-to-left

# ===================== Page: Material =====================

elif page == PAGES[3]:
    page_header("Material", "Your study material", "Upload a book or lecture notes. English or Arabic.")
    if has_book:
        st.success(f"Studying from: {status['book']}")
        if status["warning"]:
            st.warning(status["warning"])

    with st.container(border=True, key="card_upload"):
        upload_box("material")
