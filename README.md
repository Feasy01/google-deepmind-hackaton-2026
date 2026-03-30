# Echo — AI-Powered Podcast Assistant

Echo is a next-generation podcast web application that leverages Retrieval-Augmented Generation (RAG) and Voice AI to not only let you listen to podcasts but **converse with them**. Built for the Google DeepMind Hackathon 2026, Echo currently features the Huberman Lab podcast, allowing you to search through past episodes, ask factual questions backed by academic articles, and speak directly with an AI assistant contextualized on the podcast's knowledge base.

## Features

- 🎧 **Modern Podcast Player:** A beautiful, responsive, warm-themed React frontend built with Vite and Tailwind CSS v4, featuring a floating desktop player and a slick mobile overlay.
- 🧠 **RAG System (Knowledge + Episodes):** Ingests and process podcast transcripts and related academic articles, embedding them with Google's `text-embedding-004` into a Qdrant vector database.
- 🗣️ **Interactive Voice AI:** Integrated with VAPI, the assistant can intelligently answer questions by utilizing two custom tools:
  - `search_knowledge`: Queries the related academic articles for deep, factual answers.
  - `search_previous_episodes`: Retrieves exact timestamps and context from past podcast episodes.
- 🚀 **Automated Tooling:** Includes Python scripts for scraping academic articles right from episode descriptions, parsing transcripts, chunking text, and seeding the vector database.

## Architecture & Tech Stack

- **Frontend:** React 19, TypeScript, Tailwind CSS v4, Vite, `@tanstack/react-query`, and VAPI Web SDK.
- **Backend:** Python 3.12, FastAPI, Pydantic, HTTPX.
- **AI & RAG:** Google GenAI SDK (Gemini embeddings), Qdrant (Vector DB run via Docker), VAPI Server SDK.
- **Infrastructure:** Docker Compose (for Qdrant), ngrok (for local webhook tunneling), and a unified unified `start-dev.sh` startup script.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI router and endpoints (health, podcast, vapi_webhook)
│   │   ├── core/         # App configuration and settings
│   │   └── services/     # RAG, VAPI, and database business logic
│   ├── assets/           # Scripts to scrape articles and parse transcripts
│   ├── ingest.py         # Data scraping, chunking, embedding, and insertion logic
│   ├── pyproject.toml    # Backend dependencies managed via uv
│   └── .env.example      # Environment variables template
├── frontend/
│   ├── src/              # React components, hooks, api layer, and Tailwind config
│   ├── package.json      # Frontend package configuration
│   └── vite.config.ts    # Build configuration
├── data/
│   ├── articles/         # Scraped academic articles related to episodes (.md)
│   └── podcasts/         # Transcripts and parsed episode data
├── db/                   # Docker Compose setup for Qdrant
├── notebooks/            # Jupyter notebooks for testing the ingestion pipeline
└── start-dev.sh          # All-in-one local runner script
```

## Getting Started

### Prerequisites

You will need the following installed on your machine:
- [Node.js](https://nodejs.org/) & npm
- [uv](https://github.com/astral-sh/uv) (for Python dependency management)
- [Docker](https://www.docker.com/) & Docker Compose
- [ngrok](https://ngrok.com/) (for exposing webhooks to VAPI)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Feasy01/google-deepmind-hackaton-2026.git
   cd google-deepmind-hackaton-2026
   ```

2. **Environment Variables:**
   Copy the example `.env` file and fill in your keys.
   ```bash
   cp backend/.env.example backend/.env
   ```
   *Make sure to provide your `GOOGLE_API_KEY` and VAPI credentials.*

3. **Install Dependencies:**
   - **Backend:** `cd backend && uv sync`
   - **Frontend:** `cd frontend && npm install`

4. **Data Ingestion (Optional):**
   If you want to re-seed the vector database with transcripts and articles:
   ```bash
   cd backend
   uv run python ingest.py
   ```

### Running Locally

To run the full stack locally with a single command, use the provided `start-dev.sh` script. This script automatically:
1. Boots up Qdrant in Docker.
2. Creates an ngrok tunnel to port `8000` and configures your `backend/.env` with the webhook URL.
3. Starts the FastAPI backend.
4. Starts the Vite frontend dev server.

```bash
chmod +x start-dev.sh
./start-dev.sh
```

**Services will be available at:**
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API Docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- Qdrant Dashboard: [http://localhost:6333](http://localhost:6333)

To gracefully stop all services, simply hit `Ctrl+C` in the terminal running the start script.

---

*Developed for the Google DeepMind Hackathon 2026.*