from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
root_path = str(ROOT)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st

try:
    from app.crawler import answer_from_documents, crawl_public_pages
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    # Streamlit can execute this file without adding the project root to sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.crawler import answer_from_documents, crawl_public_pages

st.set_page_config(page_title="PhoenixAssist", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(145deg, #f8faff 0%, #edf3fb 48%, #f6f8fc 100%);
    }
    .main .block-container {
        max-width: 1050px;
        padding-top: 2.4rem;
        padding-bottom: 5rem;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10213d 0%, #172d4e 100%);
        color: white;
    }
    div[data-testid="stChatMessage"] {
        border: 1px solid rgba(32, 67, 112, 0.09);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.8);
        box-shadow: 0 8px 24px rgba(28, 53, 88, 0.045);
        padding: 1rem 1.2rem;
    }
    .welcome-box {
        background: linear-gradient(110deg, #e8f1ff 0%, #f3f7ff 100%);
        border: 1px solid #d7e5fa;
        border-right: 4px solid #3282c8;
        border-radius: 14px;
        padding: 1rem 1.25rem;
        margin: 1rem 0 1.5rem;
        color: #183251;
        line-height: 1.7;
    }
    h1 {
        color: #122847;
        letter-spacing: -0.03em;
    }
    [data-testid="stChatInput"] textarea {
        direction: rtl;
        text-align: right;
    }
    .stMarkdown, [data-testid="stChatMessage"] {
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "שלום, אני העוזר הדיגיטלי של הפניקס. אפשר לשאול אותי על המידע שמופיע באתר הציבורי. אציג קישורים לעמודים שעליהם התשובה מבוססת, ואם לא אמצא מידע מתאים — אגיד זאת בבירור.",
            "sources": [],
        }
    ]


@st.cache_data(show_spinner=False)
def load_public_documents() -> list[dict[str, str]]:
    start_urls = [
        "https://www.fnx.co.il/",
        "https://www.fnx.co.il/car-insurance/",
        "https://www.fnx.co.il/investor-relations/",
        "https://www.fnx.co.il/career/",
    ]
    return crawl_public_pages(start_urls, max_pages=12, max_depth=1)


def safe_answer(question: str) -> tuple[str, list[str]]:
    """Use the live public crawl to answer from source-backed site content."""
    docs = load_public_documents()
    return answer_from_documents(question, docs)


st.title("הפניקס | עוזר דיגיטלי")
st.caption("מענה ברור בעברית, המבוסס על המידע הציבורי באתר הפניקס")

with st.sidebar:
    st.header("סטטוס מערכת")
    st.success("מחובר למידע הציבורי")
    st.markdown(
        """
        - איסוף תוכן ציבורי מהאתר
        - שמירת מקור לכל תשובה
        - צ'אט בעברית
        - הצגה ברורה של מקורות
        - כאשר אין מספיק מידע — אנחנו לא ממציאים
        """
    )

    st.header("שאלות לדוגמה")
    sample_questions = [
        "איפה אפשר למצוא מידע על פוליסות?",
        "מה הוא המידע העיקרי באתר?",
        "מה כולל ביטוח מקיף לרכב?",
        "איך נקבע מחיר ביטוח חובה?",
    ]
    for q in sample_questions:
        if st.button(q, key=q):
            st.session_state.last_prompt = q

st.markdown(
    """
    <div class="welcome-box">
        <strong>מידע אמין, בלי ניחושים.</strong> התשובות מבוססות על עמודים ציבוריים באתר הפניקס. כשאין מקור מתאים, נגיד זאת במפורש.
    </div>
    """,
    unsafe_allow_html=True,
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("מקורות ומידע נוסף"):
                for source in message["sources"]:
                    st.markdown(f"[פתיחת עמוד המקור ↗]({source})")

prompt = st.chat_input("לדוגמה: מה כולל ביטוח מקיף לרכב?")
if not prompt:
    prompt = st.session_state.pop("last_prompt", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("מחפשת במידע הציבורי של הפניקס…"):
        answer, sources = safe_answer(prompt)

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    st.rerun()
