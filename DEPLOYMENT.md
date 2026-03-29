# Grafana to Kibana Converter — Deployment Guide

## Vercel (Production)

### Prerequisites
- A [Vercel](https://vercel.com) account
- The [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`

### Deploy

```bash
vercel
```

Vercel auto-detects the Python runtime via `api/index.py` and the `requirements.txt` at the
root. All routes are rewritten through the FastAPI app via `vercel.json`.

### Environment variables

Set these in the Vercel dashboard (Project → Settings → Environment Variables):

| Variable | Description |
|---|---|
| `OTLP_ENDPOINT` | Elastic APM endpoint, e.g. `https://otel-demo-a5630c.apm.us-east-1.aws.elastic.cloud` |
| `OTLP_API_KEY` | Elastic API key with APM ingest privileges |
| `OPENAI_API_KEY` | OpenAI key (optional — enables LLM-powered conversion) |
| `ENABLE_LLM_CONVERSION` | Set `true` to enable LLM features |

> **Note:** File uploads and downloads use `/tmp` on Vercel (ephemeral — files do not persist
> between requests). The main JSON-paste conversion flow (`/convert`) is stateless and
> unaffected.

---

## Local Development

### Prerequisites
- Python 3.11+

### Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.env.example .env   # then edit .env with your keys
python main.py
```

Open [http://localhost:8000](http://localhost:8000).

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## Project structure

```
grakibana/
├── api/
│   └── index.py            # Vercel entry point
├── app/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── converter.py        # Dashboard conversion logic
│   ├── mcp.py              # MCP API handlers
│   ├── models.py           # Pydantic models
│   └── web.py              # Web routes + OTLP proxy
├── static/                 # CSS, JS, favicon
├── templates/
│   └── index.html          # Main UI
├── main.py                 # FastAPI app definition
├── requirements.txt
├── vercel.json             # Vercel rewrite rules
└── config.env.example      # Environment variable template
```
