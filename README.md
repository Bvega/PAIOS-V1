# PAIOS-V1 — Personal AI Operating System

## Overview

PAIOS is a local AI-powered system that:

- Ingests documents
- Processes and summarizes them
- Indexes content
- Allows search, extraction, and reasoning
- Produces structured answers from real data

---

## System Flow

```text
inbox/ → pipeline → summaries → index → query → answer

Folder Structure
PAIOS-V1/
├── inbox/        # Raw input files (.txt)
├── memory/       # Processed summaries + index
├── outputs/      # Optional outputs
├── logs/         # Logs
├── scripts/      # Core logic
├── cli.py        # CLI interface
├── api_server.py # Local API server
Step 1 — Add Data

Place .txt files inside:

inbox/

Example:

inbox/contract_example.txt
Step 2 — Run Pipeline
python3 start_pipeline.py

This will:

Clean text
Generate summaries
Build index
Step 3 — Query via CLI
python3 cli.py
Examples
find termination
find payment terms
find termination mode=short
find termination mode=sources
Modes
short → one sentence
detailed → explanation + document count
sources → answer + sources
Step 4 — Query via API

Run server:

python3 api_server.py

Open browser or use curl:

http://127.0.0.1:8000/ask?q=termination
http://127.0.0.1:8000/ask?q=termination&mode=short
http://127.0.0.1:8000/ask?q=termination&mode=sources
API Endpoints
Endpoint	Description
/health	System status
/search	Raw search results
/top	Best result
/open	Open document
/ask	Final AI answer
Example Output
{
  "answer": "Contracts may be terminated with 30 days written notice.",
  "documents": 1
}
What This System Is

PAIOS is:

A local reasoning engine
A document intelligence system
A structured AI assistant
What This System Is NOT
Not an LLM
Not a chatbot
Not cloud-dependent