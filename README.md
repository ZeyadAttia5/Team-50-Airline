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
(Optional for LLM-based classification)
- Ollama installed
- A local model (model_name="llama3.2:3b")

## To Run
- python input_preprocessor.py