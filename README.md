# EY Canvas Multi-Agent Audit Assistant

> A working prototype of EY's April 2026 enterprise-scale agentic AI launch inside EY Canvas — built independently to demonstrate hands-on expertise in multi-agent AI pipeline architecture for financial audit automation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EY Audit Assistant Pipeline                   │
└─────────────────────────────────────────────────────────────────┘

  CSV Upload
      │
      ▼
┌─────────────┐     clean DataFrame      ┌─────────────────┐
│   Agent 1   │ ────────────────────────▶│    Agent 2      │
│  Ingestion  │                          │ Anomaly Detect  │
│ Validation  │                          │  (6 rules)      │
└─────────────┘                          └────────┬────────┘
                                                  │
                                    flagged_df + severity_counts
                                                  │
                          ┌───────────────────────┤
                          │                       │
                          ▼                       ▼
                 ┌────────────────┐     ┌─────────────────┐
                 │    Agent 3     │     │    Agent 4      │
                 │ AI Summary     │     │  PDF Report     │
                 │ (Claude API)   │     │  (ReportLab)    │
                 └───────┬────────┘     └────────┬────────┘
                         │                       │
                         └──────────┬────────────┘
                                    │
                                    ▼
                         ┌──────────────────┐
                         │  Streamlit UI    │
                         │  4-tab display   │
                         │  PDF download    │
                         └──────────────────┘
```

---

## Screenshots

**Theme: Cyber Intelligence — Deep navy, electric blue, EY brand accents**

| Tab | Description |
|-----|-------------|
| 01 — Data ingestion | Status chips, dark data preview table, validation issue cards |
| 02 — Anomaly detection | Severity count badges, bar chart by detection rule, styled flagged table |
| 03 — AI audit summary | AI avatar header, blue-bordered Claude narrative panel |
| 04 — Risk report | 64px risk score, severity breakdown cards, PDF download |

**UI color system:**
- Background: `#0A0F1E` (deep navy) / `#141F38` (card surfaces)
- Primary accent: `#3B7FE8` (electric blue) / `#6B9FFF` (bright highlights)
- EY brand: `#FFE600` (yellow — critical alerts only)
- Severity: Critical `#FF4C4C` / High `#FF9F43` / Medium `#FFE600` / Low `#2ECC71`

*(Add screenshots from Streamlit Cloud after deploying)*

---

## Run Locally

### Prerequisites
- Python 3.10+
- An Anthropic API key (optional — Agents 1, 2, 4 work without it)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ey-audit-assistant.git
cd ey-audit-assistant

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
# Edit .env and replace the placeholder:
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# 5. Run the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Deploy on Streamlit Cloud

1. Push this repo to GitHub (see GitHub Setup below).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **New app** → select your repository and branch → set **Main file path** to `app.py`.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
5. Click **Deploy**. Your app will be live in ~2 minutes.

---

## GitHub Setup

```bash
cd ey-audit-assistant
git init
git add .
git commit -m "Initial commit: EY Canvas Multi-Agent Audit Assistant"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ey-audit-assistant.git
git push -u origin main
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend / UI | Streamlit 1.45 |
| AI / LLM | Claude claude-sonnet-4-20250514 (Anthropic) |
| Data Processing | Pandas 2.2 |
| PDF Generation | ReportLab 4.4 |
| Environment | python-dotenv |
| Language | Python 3.10+ |

---

## EY Connection

In April 2026, EY globally launched enterprise-scale agentic AI inside EY Canvas — a multi-agent framework processing 1.4 trillion lines of journal entry data per year. This project is a working prototype of that architecture, built independently to demonstrate hands-on expertise in the exact technology EY is investing in.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
