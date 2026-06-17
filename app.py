import streamlit as st
import asyncio
import json
import csv
import os
import io
import time
from datetime import datetime

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Automation Tool",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f0f0f; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid #ff0000;
    }

    /* Headers */
    h1, h2, h3 { color: #ffffff !important; }
    p, label, span { color: #cccccc !important; }

    /* YouTube red accent banner */
    .yt-banner {
        background: linear-gradient(135deg, #ff0000 0%, #cc0000 50%, #990000 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 24px rgba(255,0,0,0.3);
    }
    .yt-banner h1 {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        color: #fff !important;
    }
    .yt-banner p {
        margin: 6px 0 0 0;
        font-size: 1rem;
        color: rgba(255,255,255,0.85) !important;
    }

    /* Video cards */
    .video-card {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .video-card:hover { border-color: #ff0000; }
    .video-card .rank {
        background: #ff0000;
        color: #fff;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
    }
    .video-card .vtitle {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff !important;
        margin: 4px 0;
    }
    .video-card .vmeta {
        font-size: 0.82rem;
        color: #aaaaaa !important;
        margin: 2px 0;
    }
    .video-card .vdesc {
        font-size: 0.85rem;
        color: #888888 !important;
        margin-top: 6px;
        font-style: italic;
    }
    .video-card .why {
        background: #2a2a2a;
        border-left: 3px solid #ff0000;
        padding: 6px 10px;
        border-radius: 4px;
        margin-top: 8px;
        font-size: 0.83rem;
        color: #dddddd !important;
    }

    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 16px;
        flex: 1;
        text-align: center;
    }
    .metric-card .mval {
        font-size: 2rem;
        font-weight: 800;
        color: #ff0000 !important;
    }
    .metric-card .mlabel {
        font-size: 0.8rem;
        color: #888 !important;
        margin-top: 4px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #ff0000, #cc0000) !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-size: 1rem !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }

    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
    }

    /* Status badges */
    .badge-green {
        background:#1a7f37; color:#fff; padding:3px 10px;
        border-radius:20px; font-size:0.75rem; font-weight:700;
    }
    .badge-red {
        background:#cf222e; color:#fff; padding:3px 10px;
        border-radius:20px; font-size:0.75rem; font-weight:700;
    }
    .badge-yellow {
        background:#9a6700; color:#fff; padding:3px 10px;
        border-radius:20px; font-size:0.75rem; font-weight:700;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background:#1a1a1a; border-radius:8px; }
    .stTabs [data-baseweb="tab"] { color:#aaa !important; }
    .stTabs [aria-selected="true"] { color:#ff0000 !important; border-bottom:2px solid #ff0000 !important; }

    /* Progress / spinner */
    .stSpinner > div { border-top-color: #ff0000 !important; }

    /* Divider */
    hr { border-color: #333 !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #1a1a1a; }
    ::-webkit-scrollbar-thumb { background: #ff0000; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Session State Init ─────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "results"       : [],
        "ai_picks"      : [],
        "summary"       : {},
        "search_done"   : False,
        "ai_done"       : False,
        "summary_done"  : False,
        "active_tab"    : 0,
        "llm_ready"     : False,
        "error_msg"     : "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── LLM + Agent Factory ────────────────────────────────────────────────────────
def get_llm(provider: str, api_key: str, model: str):
    if provider == "OpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key, temperature=0)
    elif provider == "Anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key, temperature=0)
    elif provider == "Google Gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key)
    raise ValueError(f"Unknown provider: {provider}")


def parse_json_list(raw: str) -> list:
    s = raw.find("[")
    e = raw.rfind("]") + 1
    if s != -1 and e > s:
        try:
            return json.loads(raw[s:e])
        except Exception:
            pass
    return []


def parse_json_dict(raw: str) -> dict:
    s = raw.find("{")
    e = raw.rfind("}") + 1
    if s != -1 and e > s:
        try:
            return json.loads(raw[s:e])
        except Exception:
            pass
    return {}


async def run_search(llm, query, max_results, filter_by):
    from browser_use import Agent, BrowserConfig, Browser
    
    filter_map = {
        "Upload Date" : "Upload date",
        "View Count"  : "View count",
        "Rating"      : "Rating",
        "Relevance"   : "Relevance",
    }
    human_filter = filter_map.get(filter_by, "Upload date")

    task = f"""
    Go to https://www.youtube.com and follow these steps EXACTLY:

    1. Search for: "{query}"
    2. Click the Filters button, then under Sort by click "{human_filter}".
    3. Collect the top {max_results} video results.
    4. For each video extract: title, channel, views, uploaded, duration, url, description.

    Return ONLY a valid JSON array:
    [
      {{
        "title":"...", "channel":"...", "views":"...",
        "uploaded":"...", "duration":"...",
        "url":"https://www.youtube.com/watch?v=...",
        "description":"..."
      }}
    ]
    """
    browser = Browser(config=BrowserConfig(headless=True))
    try:
        agent  = Agent(task=task, llm=llm, browser=browser)
        result = await agent.run()
        raw    = result.final_result() or ""
        videos = parse_json_list(raw)
        ts     = datetime.utcnow().isoformat() + "Z"
        for v in videos:
            v["query"]     = query
            v["filter_by"] = filter_by
            v["fetched_at"] = ts
        return videos
    finally:
        await browser.close()


async def run_ai_picks(llm, topic, top_n, criteria):
    from browser_use import Agent, BrowserConfig, Browser

    task = f"""
    Go to https://www.youtube.com, search for "{topic}",
    click Filters → Sort by "Upload date", scroll through 15+ results,
    then pick the top {top_n} videos based on: {criteria}.

    Return ONLY a JSON array:
    [
      {{
        "rank":1, "title":"...", "channel":"...", "views":"...",
        "uploaded":"...", "duration":"...",
        "url":"https://www.youtube.com/watch?v=...",
        "why_recommended":"Because ..."
      }}
    ]
    """
    browser = Browser(config=BrowserConfig(headless=True))
    try:
        agent  = Agent(task=task, llm=llm, browser=browser)
        result = await agent.run()
        raw    = result.final_result() or ""
        picks  = parse_json_list(raw)
        ts     = datetime.utcnow().isoformat() + "Z"
        for p in picks:
            p["topic"]      = topic
            p["fetched_at"] = ts
        return picks
    finally:
        await browser.close()


async def run_summary(llm, url):
    from browser_use import Agent, BrowserConfig, Browser

    task = f"""
    Open this YouTube video: {url}
    Extract and return as JSON:
    {{
      "title":"...", "channel":"...", "views":"...", "likes":"...",
      "published_date":"...", "description":"(first 500 chars)",
      "tags":["..."], "chapters":["0:00 - Intro"],
      "top_comments":["comment1","comment2","comment3"]
    }}
    Return ONLY the JSON object.
    """
    browser = Browser(config=BrowserConfig(headless=True))
    try:
        agent  = Agent(task=task, llm=llm, browser=browser)
        result = await agent.run()
        raw    = result.final_result() or ""
        return parse_json_dict(raw)
    finally:
        await browser.close()


def run_async(coro):
    """Run an async coroutine safely inside Streamlit."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── CSV/JSON Export Helpers ────────────────────────────────────────────────────
def to_csv_bytes(data: list) -> bytes:
    if not data:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(data[0].keys()), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)
    return buf.getvalue().encode("utf-8")


def to_json_bytes(data) -> bytes:
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <span style="font-size:2.5rem;">🎬</span>
        <h2 style="margin:0; color:#ff0000 !important; font-weight:800;">YT Automation</h2>
        <p style="color:#888 !important; font-size:0.8rem; margin-top:4px;">Powered by Browser-Use</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── LLM Provider ──────────────────────────────────────────────
    st.markdown("### 🤖 LLM Provider")
    provider = st.selectbox(
        "Provider",
        ["OpenAI", "Anthropic", "Google Gemini"],
        label_visibility="collapsed"
    )

    model_options = {
        "OpenAI"        : ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "Anthropic"     : ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
        "Google Gemini" : ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    }
    model = st.selectbox("Model", model_options[provider], label_visibility="collapsed")

    # ── API Key ────────────────────────────────────────────────────
    st.markdown("### 🔑 API Key")

    secret_key_map = {
        "OpenAI"        : "OPENAI_API_KEY",
        "Anthropic"     : "ANTHROPIC_API_KEY",
        "Google Gemini" : "GOOGLE_API_KEY",
    }
    auto_key = ""
    try:
        auto_key = st.secrets.get(secret_key_map[provider], "")
    except Exception:
        pass

    api_key = st.text_input(
        "Enter API Key",
        value=auto_key,
        type="password",
        placeholder=f"Paste your {provider} key...",
        label_visibility="collapsed"
    )

    if api_key:
        st.markdown('<span class="badge-green">✓ Key entered</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-red">✗ Key missing</span>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Search Settings ────────────────────────────────────────────
    st.markdown("### ⚙️ Search Settings")

    filter_by = st.selectbox(
        "Sort / Filter by",
        ["Upload Date", "Relevance", "View Count", "Rating"],
        index=0,
        help="Upload Date → freshest content first ✅"
    )

    max_results = st.slider("Max results per search", 3, 20, 8)

    st.markdown("---")

    # ── Links ──────────────────────────────────────────────────────
    st.markdown("### 🔗 Quick Links")
    st.markdown("""
    <div style="display:flex; flex-direction:column; gap:6px;">
        <a href="https://cloud.browser-use.com/settings?tab=api-keys&new=1" target="_blank"
           style="color:#ff0000; text-decoration:none; font-size:0.85rem;">
            🔑 Get Browser-Use API Key
        </a>
        <a href="https://docs.browser-use.com/" target="_blank"
           style="color:#ff0000; text-decoration:none; font-size:0.85rem;">
            📖 Browser-Use Docs
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#555 !important; font-size:0.73rem; text-align:center;">v1.0 · Browser-Use · 2026</p>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="yt-banner">
    <h1>🎬 YouTube Automation Tool</h1>
    <p>AI-powered content discovery · Freshest videos first · Powered by Browser-Use API</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍  Search Videos",
    "🤖  AI Curated Picks",
    "📋  Video Summary",
    "📊  My Results"
])

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — SEARCH VIDEOS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 🔍 Search YouTube")
    st.markdown(
        f"Find the **freshest** content using `filter_by = {filter_by}` — "
        "the Browser-Use agent opens YouTube, applies the filter, and returns structured results."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="e.g. Python tutorials 2026, AI automation, Machine learning...",
            key="search_query"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🚀 Search YouTube", key="btn_search", use_container_width=True)

    filter_badge_color = {"Upload Date": "badge-green", "Relevance": "badge-yellow",
                          "View Count": "badge-yellow", "Rating": "badge-yellow"}
    st.markdown(
        f'<span class="{filter_badge_color.get(filter_by, "badge-yellow")}">📅 Filter: {filter_by}</span>'
        f'&nbsp;&nbsp;<span class="badge-yellow">🎯 Max: {max_results} results</span>',
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if search_btn:
        if not api_key:
            st.error("⚠️ Please enter your API key in the sidebar first.")
        elif not query.strip():
            st.warning("⚠️ Please enter a search query.")
        else:
            with st.spinner(f"🤖 Browser-Use agent is searching YouTube for **{query}**..."):
                progress_bar = st.progress(0, text="Opening YouTube...")
                try:
                    llm = get_llm(provider, api_key, model)
                    progress_bar.progress(20, text="LLM ready — launching browser...")
                    time.sleep(0.1)
                    progress_bar.progress(55, text="Navigating YouTube & applying filter...")
                    videos = run_async(run_search(llm, query, max_results, filter_by))
                    progress_bar.progress(90, text="Parsing results...")
                    st.session_state["results"]     = videos
                    st.session_state["search_done"] = True
                    st.session_state["error_msg"]   = ""
                    progress_bar.progress(100, text="Done!")
                except Exception as e:
                    st.session_state["error_msg"] = str(e)
                    st.error(f"❌ Error: {e}")
                finally:
                    progress_bar.empty()

    if st.session_state["search_done"] and st.session_state["results"]:
        videos = st.session_state["results"]

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="mval">{len(videos)}</div>
                <div class="mlabel">Videos Found</div>
            </div>
            <div class="metric-card">
                <div class="mval">{filter_by.split()[0]}</div>
                <div class="mlabel">Sorted By</div>
            </div>
            <div class="metric-card">
                <div class="mval">{len(set(v.get("channel","") for v in videos))}</div>
                <div class="mlabel">Unique Channels</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            st.download_button("⬇️ Download JSON", to_json_bytes(videos),
                               "youtube_results.json", "application/json", use_container_width=True)
        with c2:
            st.download_button("⬇️ Download CSV", to_csv_bytes(videos),
                               "youtube_results.csv", "text/csv", use_container_width=True)

        st.markdown("---")

        for i, v in enumerate(videos, 1):
            v_title    = v.get("title", "Untitled")
            v_channel  = v.get("channel", "Unknown")
            v_views    = v.get("views", "N/A")
            v_uploaded = v.get("uploaded", "N/A")
            v_duration = v.get("duration", "N/A")
            v_url      = v.get("url", "#")
            v_desc     = v.get("description", "")[:180]

            st.markdown(f"""
            <div class="video-card">
                <span class="rank">#{i}</span>
                <div class="vtitle">
                    <a href="{v_url}" target="_blank" style="color:#ffffff; text-decoration:none;">{v_title}</a>
                </div>
                <div class="vmeta">📺 {v_channel}  •  👀 {v_views}  •  ⏳ {v_duration}  •  📅 {v_uploaded}</div>
                <div class="vdesc">{v_desc}...</div>
            </div>
            """, unsafe_allow_html=True)

# Placeholder handling for other tabs to keep app functional
with tab2:
    st.markdown("## 🤖 AI Curated Picks")
    st.info("Enter details on the search page to compile curated metrics.")

with tab3:
    st.markdown("## 📋 Video Summary")
    st.info("Paste a URL to execute summary workflows.")

with tab4:
    st.markdown("## 📊 My Results")
    st.info("Your historical batch sessions will display here.")
