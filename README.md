# 🎬 YouTube Automation Tool — Streamlit App

> **AI-powered YouTube content discovery** · Built with Browser-Use API + Streamlit
> 
> 👁️ `headless=False` in dev — watch the browser work live!  
> 📅 `filter_by="upload_date"` — always get the freshest content first!

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Smart Search** | Browser-Use agent searches YouTube and applies filters |
| 📅 **Upload Date Filter** | Always surfaces the freshest content first |
| 🤖 **AI Curation** | AI evaluates 15+ videos and picks the best ones for you |
| 📋 **Deep Summaries** | Full video metadata, chapters, tags, and top comments |
| 📊 **Results Dashboard** | View, filter, and export all results as JSON/CSV |
| 🎨 **Dark YouTube Theme** | YouTube-inspired red & dark UI |

---

## 🚀 Deploy on Streamlit Community Cloud (Free)

### Step 1 — Push to GitHub

```bash
# In your project folder
git init
git add .
git commit -m "🎬 YouTube Automation Tool — initial commit"

# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/youtube-automation-tool.git
git branch -M main
git push -u origin main
```

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to 👉 [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub account
4. Select your repository: `youtube-automation-tool`
5. Set **Main file path**: `app.py`
6. Click **"Deploy!"**

### Step 3 — Add Secrets (API Keys)

In Streamlit Cloud → your app → **Settings → Secrets**, paste:

```toml
OPENAI_API_KEY       = "sk-..."
ANTHROPIC_API_KEY    = "sk-ant-..."     # optional
GOOGLE_API_KEY       = "AIza..."        # optional
BROWSER_USE_API_KEY  = "bu-..."
```

> **That's it!** Your app is live at `https://your-app-name.streamlit.app` 🎉

---

## 💻 Run Locally

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/youtube-automation-tool.git
cd youtube-automation-tool

# Setup
bash setup.sh          # installs deps + playwright browsers

# Add keys
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your real keys

# Run
streamlit run app.py
```

The app opens at **http://localhost:8501** 🚀

---

## 📁 Project Structure

```
youtube-automation-tool/
├── app.py                          ← 🎯 Main Streamlit UI
├── youtube_agent.py                ← 🤖 Browser-Use agent logic
├── utils.py                        ← 🛠️  Helpers
├── requirements.txt                ← 📦 Python dependencies
├── packages.txt                    ← 🖥️  System packages (Chromium)
├── setup.sh                        ← ⚙️  Local setup script
├── .gitignore
├── .streamlit/
│   ├── config.toml                 ← 🎨 Theme (YouTube dark red)
│   └── secrets.toml.example        ← 🔑 API key template
└── results/                        ← 💾 Saved exports (gitignored)
```

---

## 🔑 API Keys

| Service | Link | Used For |
|---|---|---|
| Browser-Use | [cloud.browser-use.com](https://cloud.browser-use.com/settings?tab=api-keys&new=1) | Browser automation |
| OpenAI | [platform.openai.com](https://platform.openai.com/api-keys) | GPT-4o LLM |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | Claude LLM |
| Google | [aistudio.google.com](https://aistudio.google.com/apikey) | Gemini LLM |

---

## 🎛️ Configuration

Edit `youtube_agent.py` lines 13–14:

```python
HEADLESS  = False         # 👁️  True = silent (required for Streamlit Cloud)
FILTER_BY = "upload_date" # 📅  freshest content first
```

> **Note:** Streamlit Community Cloud runs headless — set `HEADLESS = True` for production.
> Use `HEADLESS = False` only during local development to watch the browser live.

---

## 📖 Resources

- 📖 [Browser-Use Docs](https://docs.browser-use.com/cloud/llms.txt)
- 🎈 [Streamlit Community Cloud](https://share.streamlit.io)
- 🐙 [Browser-Use GitHub](https://github.com/browser-use/browser-use)
- 🔑 [Get Browser-Use API Key](https://cloud.browser-use.com/settings?tab=api-keys&new=1)
