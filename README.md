# ✈️ Airline Graph-RAG System - Milestone 3

## Overview

A complete **Graph-RAG (Retrieval-Augmented Generation)** system for airline flight insights, combining Knowledge Graph technology with Large Language Models to provide data-driven answers about flights, routes, delays, and passenger satisfaction.

### System Architecture

The system integrates four main components:
1. **Input Preprocessing** → Intent classification & entity extraction
2. **Graph Retrieval** → Baseline (Cypher) + Embeddings (Vector search)
3. **LLM Layer** → Multi-model comparison & answer generation
4. **Streamlit UI** → Interactive web interface

---

## Features

### ✅ Part 1: Input Preprocessing
- **Intent Classification**: Classifies queries into 16 different intents (flight_search, delay_analysis, route_query, etc.)
- **Entity Extraction**: Extracts flights, airports, passengers, routes, dates, and attributes
- Powered by GROQ LLM for intelligent parsing

### ✅ Part 2: Graph Retrieval Layer
- **Baseline Retrieval**: Cypher queries for structured data retrieval
- **Embedding-based Retrieval**: Semantic similarity search using vector embeddings
- **Hybrid Mode**: Combines both approaches for comprehensive results
- 10+ query templates for different question types

### ✅ Part 3: LLM Layer
- **Multi-Model Comparison**: Queries 3 different LLMs simultaneously
  - Llama 3.3 70B (Meta) - Most capable
  - Llama 3.1 8B (Meta) - Fastest
  - Qwen 3 32B (Alibaba) - Balanced
- **Structured Prompts**: Context + Persona + Task format
- **Performance Metrics**: Response time, token usage, success rate tracking
- **Qualitative & Quantitative Analysis**: Compare model quality and speed

### ✅ Part 4: Streamlit UI
- **Interactive Web Interface**: Clean, professional design
- **Real-time Visualization**: View all 4 processing steps
- **Model Selection**: Compare all models or choose one
- **Retrieval Method Selection**: Baseline, embeddings, or hybrid
- **Download Results**: Export JSON data
- **Query History**: Track previous searches

---

## Project Structure

```
Team-50-Airline/
├── app.py                          # Streamlit UI (Part 4)
├── input_preprocessor.py          # Input preprocessing (Part 1)
├── graph_retrieval.py             # Graph retrieval (Part 2)
├── llm_layer.py                   # LLM layer (Part 3)
├── llm_comparison_logger.py       # Result logging
├── Create_kg.py                   # Knowledge Graph creation
├── main.py                        # CLI version
├── .env                           # API keys (GROQ_API_KEY)
├── config.txt                     # Neo4j credentials
├── requirements.txt               # Python dependencies
├── Airline_surveys_sample.csv     # Dataset
└── README.md                      # This file
```

---

## Requirements

- **Python 3.8 or higher**
- **Neo4j Desktop** (running on `neo4j://127.0.0.1:7687`)
- **GROQ API Key** (free from https://console.groq.com)

### Python Packages:
- `neo4j` - Neo4j database driver
- `groq` - GROQ API client
- `python-dotenv` - Environment variable management
- `sentence-transformers` - Embedding generation
- `streamlit` - Web UI framework

---

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Neo4j
- Start **Neo4j Desktop** and create/start a database
- Update `config.txt` with your credentials:
  ```
  URI=neo4j://127.0.0.1:7687
  USERNAME=neo4j
  PASSWORD=your_password
  ```

### 3. Set up GROQ API
- Get a free API key from https://console.groq.com
- Create a `.env` file in the project root:
  ```
  GROQ_API_KEY=your_api_key_here
  ```

---

## How to Run

### Step 1: Create the Knowledge Graph (First Time Only)
```bash
python Create_kg.py
```

This will:
- Load the airline survey CSV data (3000 records)
- Generate embeddings for all journeys (using sentence-transformers)
- Populate Neo4j with nodes and relationships
- Create vector indexes for semantic search
- **Takes 5-7 minutes on first run**

### Step 2: Launch the Application

**Option A - Streamlit UI (Recommended):**
```bash
python -m streamlit run app.py
```
This opens a web interface at `http://localhost:8501`

**Option B - Command Line:**
```bash
python main.py
```
Interactive terminal-based query system

---

## Using the System

### Example Queries to Try:
1. "Which flights have the most delays?"
2. "Show flights from LAX to ORX"
3. "What are the highest rated journeys?"
4. "Find flights with good food ratings"
5. "Show routes from EWX with minimal delays"

### Workflow in the UI:
1. **Enter your query** in the text area
2. **Select retrieval method** (Baseline, Embeddings, or Hybrid)
3. **Choose LLM mode** (Compare all models or select one)
4. **Click Search** to process
5. **View results**:
   - Step 1: See parsed intent and entities
   - Step 2: View Cypher queries and retrieval stats
   - Step 3: Browse retrieved knowledge graph data
   - Step 4: Read LLM-generated answers from all 3 models

### UI Features:
- **Quick Examples**: Pre-loaded example queries in sidebar
- **System Status**: Real-time component health monitoring
- **Multi-Model Comparison**: See answers from all 3 LLMs in tabs
- **Performance Metrics**: Response time and token usage
- **Download Results**: Export data as JSON
- **Query History**: Review previous searches

---

## System Components

### Knowledge Graph Schema
- **Nodes**: Passenger, Journey, Flight, Airport
- **Relationships**: TOOK, ON, DEPARTS_FROM, ARRIVES_AT
- **Properties**: Food ratings, delays, loyalty levels, routes, etc.

### LLM Models
1. **Llama 3.3 70B** - Best for complex analysis and detailed answers
2. **Llama 3.1 8B** - Fastest responses, good for simple queries
3. **Qwen 3 32B** - Balanced performance and quality

### Retrieval Methods
- **Baseline (Cypher)**: Structured queries using exact matches
- **Embeddings (Vector)**: Semantic similarity search
- **Hybrid**: Combines both for comprehensive results

---

## Troubleshooting

### "GROQ_API_KEY not found"
- Check `.env` file exists in project root
- Verify it contains `GROQ_API_KEY=your_key`

### "Neo4j connection failed"
- Start Neo4j Desktop
- Verify credentials in `config.txt`
- Ensure database is running on `neo4j://127.0.0.1:7687`

### "Module not found"
```bash
pip install -r requirements.txt
```

### Streamlit not found
```bash
pip install streamlit
# Or use: python -m streamlit run app.py
```

### No results returned
- Make sure you ran `python Create_kg.py` first
- Check Neo4j has data (should have 3000 Journey nodes)

---

## Performance Notes

- **Knowledge Graph Creation**: 5-7 minutes (one-time setup)
- **Query Processing**: 1-3 seconds (baseline retrieval)
- **LLM Response Time**:
  - Llama 3.3 70B: ~0.5-2s
  - Llama 3.1 8B: ~0.3-0.8s
  - Qwen 3 32B: ~0.5-1.5s

---

## Team & Credits

**Milestone 3 - German University in Cairo**
**Team 50 - Airline Theme**

### Component Ownership:
- Part 1 (Input Preprocessing): [Team Member]
- Part 2 (Graph Retrieval): [Team Member]
- Part 3 (LLM Layer): Saqr
- Part 4 (UI): [Team Member]

---

## Technical Stack

- **Language**: Python 3.11
- **Database**: Neo4j (Graph Database)
- **LLM Provider**: GROQ (Llama, Qwen models)
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2, paraphrase-MiniLM-L3-v2)
- **UI Framework**: Streamlit
- **Vector Search**: Neo4j Vector Index

---

## Milestone 3 Requirements ✅

| Requirement | Status | Implementation |
|------------|--------|----------------|
| **1. Input Preprocessing** | ✅ | `input_preprocessor.py` |
| - Intent Classification | ✅ | LLM-based classification |
| - Entity Extraction | ✅ | Custom NER |
| **2. Graph Retrieval** | ✅ | `graph_retrieval.py` |
| - Baseline (10+ Cypher queries) | ✅ | Query templates |
| - Embeddings (2 models) | ✅ | Vector similarity search |
| **3. LLM Layer** | ✅ | `llm_layer.py` |
| - Combine results | ✅ | Merges baseline + embeddings |
| - Structured prompts | ✅ | Context + Persona + Task |
| - Compare 3+ models | ✅ | Llama 3.3, 3.1, Qwen 3 |
| - Quantitative metrics | ✅ | Time, tokens, success rate |
| - Qualitative analysis | ✅ | Answer quality comparison |
| **4. UI (Streamlit)** | ✅ | `app.py` |
| - View KG context | ✅ | Tabs for baseline/embeddings |
| - View LLM answer | ✅ | Multi-model comparison |
| - Functional interface | ✅ | Clean, interactive UI |

---

## License

This project is for educational purposes as part of Milestone 3 coursework.

## Support

For issues or questions:
- Check this README
- Review `INTEGRATION_COMPLETE.md` for detailed setup
- Contact team members
