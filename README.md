# Airline Customer Holiday Booking - Knowledge Graph (Milestone 3)

# ✈️ Airline Graph-RAG – Input Preprocessing Module

## Overview

The first part implements the **Input Preprocessing layer** of a Graph-RAG based Airline Travel Assistant.

The module focuses on:
- **Intent Classification (Task 1a)** → Understanding what the user wants to do.
- **Entity Extraction (Task 1b)** → Identifying airline-related entities from user queries.

This structured output is designed to be used later for generating **Cypher queries** for a Neo4j Knowledge Graph.

---

## Features

### ✅ Intent Classification

The system classifies user queries into exactly one of the following intents:

- `flight_search`
- `booking_intent`
- `delay_analysis`
- `route_query`
- `comparison_query`
- `recommendation_query`
- `price_query`
- `schedule_query`
- `passenger_query`
- `baggage_query`
- `policy_query`
- `journey_query`
- `review_query`
- `filter_query`
- `explanation_query`
- `general_query`

---

### ✅ Entity Extraction (Airline Domain NER)

The system extracts and structures airline-related entities in JSON format, including:

- Flight numbers
- Departure and arrival airports
- Passenger types
- Journey attributes (class, comfort, food, duration)
- Routes
- Dates and time references
- Filters such as "cheapest", "fastest", and "nonstop"

---

## Project Structure

```text
Team-50-Airline/
├── input_preprocessor.py
└── README.md

## Requirements
- Python 3.8 or higher
- Neo4j Desktop (with database running on `neo4j://127.0.0.1:7687`)
- Required packages: `neo4j`, `groq`, `python-dotenv`, `sentence-transformers`
- Groq API key (set in `.env` file as `GROQ_API_KEY`)

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Neo4j:**
   - Start Neo4j Desktop and create/start a database
   - Update `config.txt` with your Neo4j credentials:
     ```
     URI=neo4j://127.0.0.1:7687
     USERNAME=neo4j
     PASSWORD=your_password
     ```

3. **Set up Groq API:**
   - Create a `.env` file with your Groq API key:
     ```
     GROQ_API_KEY=your_api_key_here
     ```

## To Run

**Important: Run in this order!**

1. **First, create the Knowledge Graph:**
   ```bash
   python Create_kg.py
   ```
   This will:
   - Load the CSV data
   - Generate embeddings for all journeys
   - Populate Neo4j with nodes and relationships
   - Takes 5-7 minutes on first run

2. **Then, run the application:**
   
   **Option A - Streamlit UI (Recommended):**
   ```bash
   streamlit run app.py
   ```
   This will open a web interface at `http://localhost:8501`
   
   **Option B - Command Line:**
   ```bash
   python main.py
   ```
   This will start the interactive query system in the terminal