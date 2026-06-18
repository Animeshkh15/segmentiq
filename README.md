# SegmentIQ

AI-Powered Intelligent Document Segmentation System

## Overview

SegmentIQ is an AI-driven document processing system that automatically analyzes multi-document PDF files, classifies pages, detects document boundaries, groups pages into logical document segments, and exports results in structured JSON and Excel formats.

The system is designed for enterprise document processing workflows where large PDF packages contain multiple document types such as invoices, medical reports, bank statements, resumes, research papers, and other business documents.

---

## Features

### OCR Pipeline

* PDF to Image Conversion using pdf2image
* Text Extraction using Tesseract OCR
* OCR Quality Assessment
* Poor OCR Detection

### Multi-Agent Classification

* Multiple AI agents classify each page independently
* Parallel execution using ThreadPoolExecutor
* Ensemble voting mechanism
* Confidence score generation

### Voting Engine

* Majority voting
* Confidence calculation
* Agent agreement analysis
* Low-confidence detection

### Human Review Queue

* Automatic review flagging
* Low confidence detection
* High disagreement detection
* Poor OCR detection

### Document Segmentation

* Page-level classification
* Boundary detection
* Segment creation
* Multi-document package handling

### Export System

* JSON Export
* Excel Export

---

## Current Architecture

```text
PDF Upload
    │
    ▼
OCR Service
    │
    ▼
Page Extraction
    │
    ▼
Multi-Agent Classification
    │
    ▼
Voting Engine
    │
    ▼
Confidence Scoring
    │
    ▼
Review Queue
    │
    ▼
Boundary Detection
    │
    ▼
Document Segmentation
    │
    ▼
JSON Export
    │
    ▼
Excel Export
```

---

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn

### OCR

* Tesseract OCR
* pdf2image
* Poppler

### AI

* Groq API
* Llama 3.3 70B Versatile

### Data Processing

* Pydantic
* Pandas
* OpenPyXL

### Concurrency

* ThreadPoolExecutor

---

## Project Structure

```text
backend/
│
├── app/
│   ├── api/
│   │   ├── upload.py
│   │   ├── routes.py
│   │
│   ├── core/
│   │   ├── adk_runner.py
│   │   ├── agent_pool.py
│   │   ├── voting.py
│   │   ├── review_manager.py
│   │   ├── boundary.py
│   │   └── ocr.py
│   │
│   ├── pipeline/
│   │   └── document_pipeline.py
│   │
│   ├── exporters/
│   │   ├── json_exporter.py
│   │   └── excel_exporter.py
│   │
│   └── schemas/
│       └── schemas.py
│
├── config/
│   └── config.yaml
│
├── storage/
│
├── .env
│
└── main.py
```

---

## Workflow

### Step 1: Upload PDF

User uploads a PDF document package.

### Step 2: OCR

Each page is converted into text using OCR.

### Step 3: Multi-Agent Classification

Multiple AI agents classify each page independently.

Example:

```text
Page 1

Agent 1 → Invoice
Agent 2 → Invoice
Agent 3 → Invoice
Agent 4 → Medical Report
Agent 5 → Invoice
```

### Step 4: Voting

The voting engine determines the final category.

Example:

```text
Invoice = 4 votes
Medical Report = 1 vote

Final Category = Invoice
Confidence = 0.80
```

### Step 5: Review Detection

Pages are flagged for review when:

* Confidence is below threshold
* OCR quality is poor
* Agent disagreement is high

### Step 6: Segmentation

Pages are grouped into document segments.

Example:

```text
Page 1 → Invoice
Page 2 → Invoice
Page 3 → Invoice

Segment 1

Invoice
Pages 1-3
```

### Step 7: Export

Results are exported to:

* JSON
* Excel

---

## Example JSON Output

```json
{
  "document_name": "sample.pdf",

  "agent_results": [
    {
      "page_number": 1,
      "agents": [
        {
          "agent_id": 1,
          "category": "Invoice",
          "reasoning": "Invoice number detected."
        }
      ]
    }
  ],

  "voting_results": [
    {
      "page_number": 1,
      "category": "Invoice",
      "confidence": 0.80,
      "review_required": false
    }
  ],

  "review_queue": [],

  "segments": [
    {
      "segment_id": 1,
      "category": "Invoice",
      "start_page": 1,
      "end_page": 3,
      "pages": [1, 2, 3]
    }
  ]
}
```

---

## Configuration

Example:

```yaml
model:
  provider: groq
  model_name: llama-3.3-70b-versatile
  temperature: 0.2

agents:
  count: 5

review:
  threshold: 0.60
```

---

## Running the Project

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start FastAPI

```bash
uvicorn app.main:app --reload
```

### Open Swagger

```text
http://127.0.0.1:8000/docs
```

---

## Current Status

Completed:

* OCR Pipeline
* Multi-Agent Classification
* Parallel Agent Execution
* Voting Engine
* Confidence Scoring
* Review Queue
* Segmentation
* JSON Export
* Excel Export
* FastAPI APIs

Planned:

* PostgreSQL Integration
* React Frontend
* Human Review Dashboard
* Authentication
* Audit Logs
* Evaluation Framework
* Agent Personas
* LLM Provider Abstraction Layer

---

## Future Roadmap

### Phase 1

* PostgreSQL Integration
* Persistent Storage

### Phase 2

* React Frontend
* Human Review Dashboard

### Phase 3

* Agent Specialization
* Evaluation Framework
* Performance Monitoring

### Phase 4

* Enterprise Deployment
* User Management
* Audit Trail
* Analytics Dashboard

---

## Author

Animesh Khandelwal

SegmentIQ - Intelligent AI Document Segmentation System
