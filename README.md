# Airline Customer Holiday Booking - Knowledge Graph (Milestone 2)

This project implements a Neo4j Knowledge Graph for analyzing airline passenger satisfaction and travel patterns. It transforms tabular airline survey data into an interconnected graph structure that captures relationships among passengers, flights, routes, cabin classes, and satisfaction drivers.

## Project Overview

Based on the requirements from `Airline - M2 Description.pdf`, this milestone builds a Knowledge Graph that will serve as the foundation for a Graph Retrieval-Augmented Generation (GraphRAG) system, enabling natural language queries about airline booking data.

## What Has Been Implemented

### 1. Knowledge Graph Construction (`Create_kg.py`)
A Python script that:
- Reads airline survey data from `Airline_surveys_sample.csv`
- Connects to Neo4j using credentials from `config.txt`
- Creates the following **nodes**:
  - **Passenger**: `record_locator` (unique), `loyalty_program_level`, `generation`
  - **Journey**: `feedback_ID` (unique), `food_satisfaction_score`, `arrival_delay_minutes`, `actual_flown_miles`, `number_of_legs`, `passenger_class`
  - **Flight**: `flight_number`, `fleet_type_description` (uniquely identified by both)
  - **Airport**: `station_code`
- Creates the following **relationships**:
  - `(Passenger)-[:TOOK]->(Journey)`
  - `(Journey)-[:ON]->(Flight)`
  - `(Flight)-[:DEPARTS_FROM]->(Airport)`
  - `(Flight)-[:ARRIVES_AT]->(Airport)`
- Includes constraints/indexes for performance optimization
- Provides summary statistics after creation

### 2. Verification Queries (`test_kg.py`)
A Python script that runs 5 verification queries to validate the Knowledge Graph structure:
1. Top 5 airport-to-airport routes by flight count
2. Top 10 flights with most passenger feedback
3. Average food satisfaction for multi-leg journeys by generation
4. Top 10 flights with shortest average arrival delays
5. Average flown miles by loyalty program level

### 3. Expected Query Results
The `Airline - Query Answers/` folder contains expected JSON results for each query:
- `Airline - Query 1.json` through `Airline - Query 5.json`

## Prerequisites

- **Python 3.8+**
- **Neo4j Desktop** (download from [neo4j.com/download](https://neo4j.com/download/))

## Setup Instructions

### 1. Install Neo4j Desktop
1. Download Neo4j Desktop from [https://neo4j.com/download/](https://neo4j.com/download/)
2. Install and launch Neo4j Desktop
3. Create a new project

### 2. Create a Neo4j Database Instance
1. In your Neo4j project, click "Add" → "Local DBMS"
2. Set the database name (e.g., "AirlineKG")
3. Set password to match your `config.txt` (default: `password`)
4. Select Neo4j version 5.x (recommended)
5. Click "Create"
6. Start the database by clicking the "Start" button

### 3. Configure Connection Settings
Edit `config.txt` to match your Neo4j instance:
```
URI=neo4j://127.0.0.1:7687
USERNAME=neo4j
PASSWORD=your_password
```
Replace `your_password` with the password you set when creating the database.

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `neo4j` - Official Neo4j Python driver
- `pytz` - Timezone library

### 5. Create the Knowledge Graph
```bash
python Create_kg.py
```

Expected output:
```
Reading configuration...
URI: neo4j://127.0.0.1:7687
Username: neo4j
Connecting to Neo4j...
Clearing existing data...
Creating constraints and indexes...
Reading CSV file: .../Airline_surveys_sample.csv
Found XXXX records to process.
...
Knowledge Graph Creation Complete!
```

### 6. Verify the Knowledge Graph
```bash
python test_kg.py
```

This runs all 5 verification queries and displays the results. Compare with expected answers in the `Airline - Query Answers/` folder.

## What is Missing

The following deliverables from the M2 requirements are **NOT yet implemented**:

### 1. `rule.txt` - Overall Satisfaction Score Calculation
The scoring rule that calculates `overall_satisfaction_score` for each passenger:
```
overall_satisfaction_score = 0.5*food + 0.35*delay_score + 0.1*legs_score + 0.05*miles_score
```

Where:
- **Food Score**: Direct value from `Journey.food_satisfaction_score` (1-5)
- **Delay Score**: `5 - clamp(abs(arrival_delay_minutes)/20, 0, 5)`
- **Legs Score**: `5 - clamp(number_of_legs * 1.5, 0, 5)`
- **Miles Score**: `5 - clamp(actual_flown_miles / 3000, 0, 5)`

Expected answer: **1856 passengers** with score > 3

### 2. `queries.txt` - Cypher Queries File
A text file containing all 5 verification queries in the required format:
```cypher
//1. Query 1
MATCH(...)
RETURN (...)

//2. Query 2
...
```

### 3. Query for Satisfaction Score Count
A Cypher query to count passengers with `overall_satisfaction_score > 3` needs to be developed and included in `queries.txt`.

## Project Structure

```
Team-50-Airline/
├── Airline - M2 Description.pdf    # Project requirements
├── Airline_surveys_sample.csv      # Source data
├── Create_kg.py                    # KG creation script
├── test_kg.py                      # Verification queries script
├── config.txt                      # Neo4j connection settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── Airline - Query Answers/        # Expected query results
    ├── Airline - Query 1.json
    ├── Airline - Query 2.json
    ├── Airline - Query 3.json
    ├── Airline - Query 4.json
    └── Airline - Query 5.json
```

## Troubleshooting

### Connection Refused
- Ensure Neo4j database is running (check Neo4j Desktop)
- Verify URI in `config.txt` matches your setup (try `bolt://localhost:7687` if `neo4j://` doesn't work)

### Authentication Failed
- Double-check password in `config.txt` matches your Neo4j database password

### CSV Not Found
- Ensure `Airline_surveys_sample.csv` is in the same directory as `Create_kg.py`

## Next Steps (Milestone 3)

The Knowledge Graph will serve as the foundation for:
- Graph Retrieval-Augmented Generation (GraphRAG) system
- Natural language query interface for complex, multi-criteria airline booking questions
