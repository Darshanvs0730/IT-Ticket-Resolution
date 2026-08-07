<div align="center">
  <img src="complianceai/assets/header-animation.svg" alt="ComplianceAI" width="100%">
</div>

<p align="center">
  <img src="complianceai/assets/divider-animation.svg" alt="divider" width="100%">
</p>

## 📖 Project Status

- **Version**: 1.0.0
- **Production Ready**: Yes
- **Test Suite**: 183/183 Tests Passing
- **Latest Production Run ID**: `01KWPYG76MSN0GXCJ4ZJ5TVD2D`
- **Integrity Checks**: All Passed (Conservation of Elements, Grounding)
- **Architecture**: Strict Clean Architecture (Frozen)
- **LLM Engine**: Groq Llama 3.3 70B (Gate 3)
- **Artifacts**: Generates Canonical JSON / HTML / CSV Reports

---

## 📖 Project Overview

ComplianceAI is a sequential, highly-deterministic evaluation engine designed to ensure that user interfaces and live digital properties strictly conform to written policies, guidelines, or regulatory documents (e.g., PDFs, standard operating procedures).

Unlike traditional LLM wrappers, ComplianceAI operates as a **Comparison Engine** protected by strict invariant-checking gates. It parses truth documents, crawls live sites, maps semantic elements, and generates evidence-backed verification reports where every single verdict is explicitly grounded in a cited rule.

---

## 🎯 Problem Statement

Manual compliance auditing is slow, subjective, and prone to human error. Evaluating complex digital properties against multi-page legal and brand guidelines requires massive cognitive load. Simple Generative AI solutions suffer from hallucinations and lack determinism. ComplianceAI solves this by strictly enforcing mathematically grounded comparisons before delegating highly nuanced decisions to an LLM.

---

## 🏗 Architecture

See `ARCHITECTURE.md`.

---

## 🚀 Pipeline

<div align="center">
  <img src="complianceai/assets/pipeline-animation.svg" alt="Pipeline Animation" width="100%">
</div>

The deterministic extraction and comparison pipeline successfully orchestrates an immutable sequence:
1. **Knowledge Extraction**: Parses multi-section PDFs into a vector store.
2. **Stealth Crawler & DOM Extraction**: Navigates targets natively with Playwright, circumventing UI blockers and capturing coordinates.
3. **Deduplication**: Resolves structural aliases to optimize downstream processing.
4. **Gate 1 (Exact Match)**: O(1) deterministic checks (exact, case-insensitive, synonyms).
5. **Gate 2 (Semantic Match)**: Local `sentence-transformers` evaluating embedding distances.
6. **Gate 3 (LLM Verification)**: Semantic arbitration by Groq Llama 3.3 70B.
7. **Canonical Reporting**: Standardized JSON, CSV, and HTML outputs.

---

## 💻 Tech Stack

<div align="center">
  <img src="complianceai/assets/tech-stack-animation.svg" alt="Tech Stack" width="100%">
</div>

- **Backend Framework**: Python 3.10+, FastAPI
- **Web Scraping / Automation**: Playwright
- **Embeddings**: `sentence-transformers`
- **LLM API**: Groq (Llama 3.3 70B)
- **Database / Queues**: SQLite, Redis, RQ (Redis Queue)
- **Containerization**: Docker, Docker Compose

---

## 📂 Folder Structure

```
complianceai/
├── Assignment.pdf                        # Source assignment requirements
├── WaiverPro-User-Guidelines.pdf         # Source-of-truth document
├── README.md                             # This file
├── FINAL_REPOSITORY_RELEASE_REPORT.md    # Master engineering release audit
├── Dockerfile                            # Production image definition
├── docker-compose.yml                    # Production orchestration
├── pyproject.toml                        # Dependency definitions
├── .env.example                          # Environment template
├── apps/                                 # API and Background Worker entrypoints
├── docs/                                 # Community & technical documentation
├── packages/                             # Core Domain, Crawler, Compare engines
├── scripts/                              # E2E test scripts & production runners
└── tests/                                # 183 unit and integration tests
```

---

## 🛠 Installation

### Prerequisites
- Python 3.10+
- Redis (for background workers)
- Docker & Docker Compose (optional for local deployment)

### Local Setup
```bash
# Clone the repository
git clone https://github.com/your-org/complianceai.git
cd complianceai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package with all optional dependencies
pip install -e ".[dev,api,worker,crawler,llm-openai]"

# Install playwright browsers
playwright install --with-deps chromium
```

---

## 🔑 Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```
Ensure you provide a valid `GROQ_API_KEY` for Gate 3 LLM verification (free key at https://console.groq.com).

---

## 🚀 Running Production

You can boot the full stack using Docker Compose:
```bash
docker-compose up --build
```
Alternatively, for a standalone offline production script run:
```bash
source .venv/bin/activate
python scripts/run_production.py
```

---

## 📊 Latest Validated Production Metrics

<div align="center">
  <img src="complianceai/assets/metrics-animation.svg" alt="Metrics Dashboard" width="100%">
</div>

> Computed from the final certified production run. All historical metrics have been deprecated.

| Metric | Value |
|--------|-------|
| **Run ID** | `01KWPYG76MSN0GXCJ4ZJ5TVD2D` |
| **Pipeline Status** | COMPLETE |
| **Routes Discovered** | 92 |
| **Routes Visited** | 14 |
| **Elements Extracted** | 1,525 |
| **Elements Compared** | 945 |
| **Gate 1 Resolved** | 2 |
| **Gate 2 Resolved** | 702 |
| **Gate 3 Resolved** | 241 |
| **COMPLIANT Verdicts** | 2 |
| **NOT_COVERED Verdicts**| 1,523 |
| **DISCREPANCY Verdicts**| 0 |

---

## 📄 Generated Reports

Upon completion of a pipeline run, the reporting engine deterministically generates three synchronized artifacts in `.storage/reports/{run_id}/`:
1. `report.json`: The canonical, machine-readable JSON payload containing citations and structural DOM metadata.
2. `report.csv`: A flat data file for spreadsheet auditing.
3. `report.html`: A human-readable, stylized HTML audit report.

---

## 📑 Assignment Mapping

1. **Parse PDF**: ✅ `ingestion/pdf/parser.py`
2. **Chunk/Embed**: ✅ `pipeline/stages/ingest.py`
3. **Extract Claims**: ✅ `ingestion/pdf/claim_extractor.py`
4. **Authenticate Target**: ✅ `crawler/auth/form_login.py`
5. **Crawl/Discover**: ✅ `crawler/discovery.py`
6. **Extract UI DOM**: ✅ `crawler/extractor.py`
7. **Deduplicate Elements**: ✅ `crawler/dedup.py`
8. **Gate 1 (Exact Match)**: ✅ `compare/gate1.py`
9. **Gate 2 (Semantic)**: ✅ `compare/gate2.py`
10. **Gate 3 (LLM)**: ✅ `compare/gate3.py`
11. **Anti-Hallucination**: ✅ `compare/gate3.py`
12. **JSON Report**: ✅ `reporting/canonical_json.py`
13. **HTML Report**: ✅ `reporting/html_renderer.py`
14. **CSV Report**: ✅ `reporting/csv_renderer.py`
15. **Screenshot Page**: ✅ `core/services/orchestrator.py`
16. **REST API**: ✅ `apps/api/main.py`
17. **Worker Arch**: ✅ `apps/worker/`
18. **Docker**: ✅ `Dockerfile`
19. **Tenant Isolation**: ✅ `apps/api/dependencies.py`
20. **Conservation Invariant**: ✅ `scripts/run_production.py`

---

## 🚦 Known Limitations

- **LLM Context Bottlenecks**: Extreme DOM sizes with high Gate 3 fallout can cause rate limit exhaustion on standard Groq tiers.
- **Authentication Resilience**: Form-based authentication currently relies on standard CSS selector defaults. Dynamic Captchas are unsupported.
- **Semantic Mismatch**: Gate 2 semantic searches occasionally misalign very short UI fragments with dense, multi-page guideline chunks, delegating the burden to Gate 3.

---

## 🔮 Future Improvements

- **Managed Vector Store**: Swap local `sentence-transformers` for PgVector or Pinecone to support massive parallel scaling.
- **Streaming Reports**: Implement Server-Sent Events (SSE) in FastAPI for real-time Pipeline status telemetry on the frontend.
- **Proxy Support**: Add managed proxy routing support for the Playwright `BrowserPool` to circumvent advanced WAF blockades.
- **A/B Testing Framework**: Introduce a configuration framework for LLM prompts to measure Gate 3 arbitration accuracy continuously.
