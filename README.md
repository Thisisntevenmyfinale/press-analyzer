# PressAnalyzer

Pre-publication editorial review prototype. Scores articles on balance, sourcing, tone neutrality and transparency. Extracts high-risk claims, identifies missing perspectives and simulates a newsroom editorial panel.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## API Key

Either set it via the sidebar input, or add a `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-..."
```

## Run

```bash
streamlit run app.py
```

## Project structure

```
app.py                  ← main Streamlit application
requirements.txt
src/
  article_extractor.py  ← URL → clean text
  claim_analyzer.py     ← OpenAI API calls
  indicators.py         ← deterministic text metrics
  prompts.py            ← all LLM prompt templates
  scoring.py            ← scoring, claim risk, verdict logic
  utils.py              ← shared helpers
```