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
    #from browser_use import Agent, BrowserConfig, Browser
    from browser_use.agent.service import Agent
    from browser_use import Browser
    from browser_use.browser.config import BrowserConfig
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
    #from browser_use import Agent, BrowserConfig, Browser
    from browser_use.agent.service import Agent
    from browser_use import Browser
    from browser_use.browser.config import BrowserConfig
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
    #from browser_use import Agent, BrowserConfig, Browser
    from browser_use.agent.service import Agent
    from browser_use import Browser
    from browser_use.browser.config import BrowserConfig
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
        "Anthropic"     : ["claude-sonnet-4-5", "claude-3-5-haiku-latest", "claude-opus-4-5"],
        "Google Gemini" : ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    }
    model = st.selectbox("Model", model_options[provider], label_visibility="collapsed")

    # ── API Key ────────────────────────────────────────────────────
    st.markdown("### 🔑 API Key")

    # Try to auto-load from Streamlit secrets
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
        <a href="https://docs.browser-use.com/cloud/llms.txt" target="_blank"
           style="color:#ff0000; text-decoration:none; font-size:0.85rem;">
            📖 Browser-Use Docs
        </a>
        <a href="https://platform.openai.com/api-keys" target="_blank"
           style="color:#ff0000; text-decoration:none; font-size:0.85rem;">
            🤖 OpenAI API Keys
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#555 !important; font-size:0.73rem; text-align:center;">v1.0 · Browser-Use · 2025</p>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# Hero Banner
st.markdown("""
<div class="yt-banner">
    <h1>🎬 YouTube Automation Tool</h1>
    <p>AI-powered content discovery · Freshest videos first · Powered by Browser-Use API</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
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
            placeholder="e.g. Python tutorials 2025, AI automation, Machine learning...",
            key="search_query"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🚀 Search YouTube", key="btn_search", use_container_width=True)

    # Filter badge
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
                    time.sleep(0.3)
                    progress_bar.progress(40, text="Navigating YouTube & applying filter...")
                    videos = run_async(run_search(llm, query, max_results, filter_by))
                    progress_bar.progress(80, text="Parsing results...")
                    time.sleep(0.2)
                    progress_bar.progress(100, text="Done!")
                    st.session_state["results"]     = videos
                    st.session_state["search_done"] = True
                    st.session_state["error_msg"]   = ""
                except Exception as e:
                    st.session_state["error_msg"] = str(e)
                    st.error(f"❌ Error: {e}")
                finally:
                    progress_bar.empty()

    # ── Results display ────────────────────────────────────────────
    if st.session_state["search_done"] and st.session_state["results"]:
        videos = st.session_state["results"]

        # Metrics row
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

        # Download buttons
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            st.download_button("⬇️ Download JSON", to_json_bytes(videos),
                               "youtube_results.json", "application/json", use_container_width=True)
        with c2:
            st.download_button("⬇️ Download CSV", to_csv_bytes(videos),
                               "youtube_results.csv", "text/csv", use_container_width=True)

        st.markdown("---")

        # Video cards
        for i, v in enumerate(videos, 1):
            title    = v.get("title", "Untitled")
            channel  = v.get("channel", "Unknown")
            views    = v.get("views", "N/A")
            uploaded = v.get("uploaded", "N/A")
            duration = v.get("duration", "N/A")
            url      = v.get("url", "#")
            desc     = v.get("description", "")[:180]

            st.markdown(f"""
            <div class="video-card">
                <span class="rank">#{i}</span>
                <div class="vtitle">
                    <a href="{url}" target="_blank" style="color:#ffffff; text-decoration:none;">
                        {title}
                    </a>
                </div>
                <div class="vmeta">
                    📺 <b>{channel}</b> &nbsp;|&nbsp;
                    👁️ {views} &nbsp;|&nbsp;
                    📅 {uploaded} &nbsp;|&nbsp;
                    ⏱️ {duration}
                </div>
                {"<div class=\"vdesc\">" + desc + "...</div>" if desc else ""}
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — AI CURATED PICKS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 🤖 AI Curated Picks")
    st.markdown(
        "The AI agent opens YouTube, applies **Upload Date** filter to see freshest content, "
        "evaluates 15+ videos, and picks the **best ones** based on your criteria."
    )

    col1, col2 = st.columns([2, 2])
    with col1:
        ai_topic = st.text_input(
            "Topic to research",
            placeholder="e.g. Machine learning, React hooks, Data science...",
            key="ai_topic"
        )
    with col2:
        ai_criteria = st.text_area(
            "Quality criteria",
            value="educational, beginner-friendly, high production quality, recently uploaded",
            height=80,
            key="ai_criteria"
        )

    col3, col4 = st.columns([1, 3])
    with col3:
        top_n = st.number_input("Number of picks", min_value=3, max_value=10, value=5)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        ai_btn = st.button("🤖 Let AI Pick Best Videos", key="btn_ai", use_container_width=True)

    if ai_btn:
        if not api_key:
            st.error("⚠️ Please enter your API key in the sidebar first.")
        elif not ai_topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            with st.spinner(f"🤖 AI is browsing YouTube for the best **{ai_topic}** videos..."):
                progress_bar2 = st.progress(0, text="Launching browser agent...")
                try:
                    llm = get_llm(provider, api_key, model)
                    progress_bar2.progress(15, text="Searching YouTube...")
                    time.sleep(0.3)
                    progress_bar2.progress(35, text="Applying Upload Date filter...")
                    picks = run_async(run_ai_picks(llm, ai_topic, top_n, ai_criteria))
                    progress_bar2.progress(80, text="AI evaluating and ranking...")
                    time.sleep(0.3)
                    progress_bar2.progress(100, text="Done!")
                    st.session_state["ai_picks"] = picks
                    st.session_state["ai_done"]  = True
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                finally:
                    progress_bar2.empty()

    if st.session_state["ai_done"] and st.session_state["ai_picks"]:
        picks = st.session_state["ai_picks"]

        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            st.download_button("⬇️ Download JSON", to_json_bytes(picks),
                               "ai_picks.json", "application/json", use_container_width=True)
        with c2:
            st.download_button("⬇️ Download CSV", to_csv_bytes(picks),
                               "ai_picks.csv", "text/csv", use_container_width=True)

        st.markdown("---")
        st.markdown(f"### 🏆 Top {len(picks)} AI-Curated Videos")

        for v in picks:
            rank     = v.get("rank", "?")
            title    = v.get("title", "Untitled")
            channel  = v.get("channel", "Unknown")
            views    = v.get("views", "N/A")
            uploaded = v.get("uploaded", "N/A")
            duration = v.get("duration", "N/A")
            url      = v.get("url", "#")
            why      = v.get("why_recommended", "")[:220]

            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "🏅")
            st.markdown(f"""
            <div class="video-card">
                <span class="rank">{medal} Rank #{rank}</span>
                <div class="vtitle">
                    <a href="{url}" target="_blank" style="color:#ffffff; text-decoration:none;">
                        {title}
                    </a>
                </div>
                <div class="vmeta">
                    📺 <b>{channel}</b> &nbsp;|&nbsp;
                    👁️ {views} &nbsp;|&nbsp;
                    📅 {uploaded} &nbsp;|&nbsp;
                    ⏱️ {duration}
                </div>
                {"<div class=\"why\">💡 " + why + "</div>" if why else ""}
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — VIDEO SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📋 Deep Video Summary")
    st.markdown(
        "Paste any YouTube URL — the agent opens the video page and extracts "
        "full metadata, description, chapters, and top comments."
    )

    col1, col2 = st.columns([4, 1])
    with col1:
        video_url = st.text_input(
            "YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            key="video_url"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        summary_btn = st.button("📋 Get Summary", key="btn_summary", use_container_width=True)

    # Pre-populate from search results
    if st.session_state["results"]:
        best_url = next(
            (v.get("url") for v in st.session_state["results"]
             if v.get("url") and "watch?v=" in v.get("url", "")),
            None
        )
        if best_url and not video_url:
            st.info(f"💡 Tip: Use URL from your search results: `{best_url}`")

    if summary_btn:
        if not api_key:
            st.error("⚠️ Please enter your API key in the sidebar first.")
        elif not video_url.strip() or "youtube.com/watch" not in video_url:
            st.warning("⚠️ Please enter a valid YouTube video URL.")
        else:
            with st.spinner("🤖 Opening video page and extracting details..."):
                try:
                    llm = get_llm(provider, api_key, model)
                    summary = run_async(run_summary(llm, video_url))
                    st.session_state["summary"]      = summary
                    st.session_state["summary_done"] = True
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    if st.session_state["summary_done"] and st.session_state["summary"]:
        s = st.session_state["summary"]

        st.markdown("---")
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"### 📺 {s.get('title', 'Video Title')}")
            st.markdown(f"""
            | Field | Value |
            |---|---|
            | 📺 Channel | {s.get('channel', 'N/A')} |
            | 👁️ Views | {s.get('views', 'N/A')} |
            | 👍 Likes | {s.get('likes', 'N/A')} |
            | 📅 Published | {s.get('published_date', 'N/A')} |
            """)

            if s.get("description"):
                st.markdown("**📝 Description**")
                st.markdown(
                    f"<div style=\"background:#1e1e1e; padding:12px; border-radius:8px; "
                    f"color:#ccc; font-size:0.88rem;\">{s['description'][:600]}</div>",
                    unsafe_allow_html=True
                )

        with col2:
            if s.get("tags"):
                st.markdown("**🏷️ Tags**")
                for tag in s["tags"][:10]:
                    st.markdown(f"`{tag}`", unsafe_allow_html=False)

            if s.get("chapters"):
                st.markdown("**📑 Chapters**")
                for ch in s["chapters"][:8]:
                    st.markdown(f"- {ch}")

        if s.get("top_comments"):
            st.markdown("**💬 Top Comments**")
            for i, comment in enumerate(s["top_comments"][:5], 1):
                st.markdown(
                    f"<div style=\"background:#1e1e1e; border-left:3px solid #ff0000; "
                    f"padding:8px 12px; border-radius:4px; margin:4px 0; "
                    f"color:#ccc; font-size:0.85rem;\">💬 {comment}</div>",
                    unsafe_allow_html=True
                )

        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            st.download_button("⬇️ JSON", to_json_bytes(s),
                               "video_summary.json", "application/json", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — MY RESULTS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 📊 My Results Dashboard")

    total_search = len(st.session_state["results"])
    total_ai     = len(st.session_state["ai_picks"])
    has_summary  = bool(st.session_state["summary"])

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="mval">{total_search}</div>
            <div class="mlabel">Search Results</div>
        </div>
        <div class="metric-card">
            <div class="mval">{total_ai}</div>
            <div class="mlabel">AI Picks</div>
        </div>
        <div class="metric-card">
            <div class="mval">{"1" if has_summary else "0"}</div>
            <div class="mlabel">Summaries</div>
        </div>
        <div class="metric-card">
            <div class="mval">{total_search + total_ai}</div>
            <div class="mlabel">Total Collected</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    all_data = st.session_state["results"] + st.session_state["ai_picks"]
    if st.session_state["summary"]:
        all_data.append(st.session_state["summary"])

    if all_data:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("⬇️ All Results JSON", to_json_bytes(all_data),
                               "all_youtube_data.json", "application/json", use_container_width=True)
        with c2:
            combined = st.session_state["results"] + st.session_state["ai_picks"]
            if combined:
                st.download_button("⬇️ All Results CSV", to_csv_bytes(combined),
                                   "all_youtube_data.csv", "text/csv", use_container_width=True)
        with c3:
            if st.button("🗑️ Clear All Results", use_container_width=True):
                st.session_state["results"]      = []
                st.session_state["ai_picks"]     = []
                st.session_state["summary"]      = {}
                st.session_state["search_done"]  = False
                st.session_state["ai_done"]      = False
                st.session_state["summary_done"] = False
                st.rerun()

        st.markdown("---")

        if st.session_state["results"]:
            st.markdown("### 🔍 Search Results")
            import pandas as pd
            df = pd.DataFrame(st.session_state["results"])
            cols = [c for c in ["title","channel","views","uploaded","duration","url"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, height=300)

        if st.session_state["ai_picks"]:
            st.markdown("### 🏆 AI Picks")
            df2 = pd.DataFrame(st.session_state["ai_picks"])
            cols2 = [c for c in ["rank","title","channel","uploaded","views","url","why_recommended"] if c in df2.columns]
            st.dataframe(df2[cols2], use_container_width=True, height=280)
    else:
        st.info("📭 No results yet. Use the Search or AI Picks tabs to collect YouTube data.")

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding: 20px 0;">
        <p style="color:#555 !important; font-size:0.8rem;">
            🎬 YouTube Automation Tool · Built with
            <a href="https://docs.browser-use.com" target="_blank" style="color:#ff0000;">Browser-Use</a> +
            <a href="https://streamlit.io" target="_blank" style="color:#ff0000;">Streamlit</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
