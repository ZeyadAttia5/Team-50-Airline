# Graph Retrieval Layer - Complete Documentation

## Overview

This document describes the complete implementation of the **Graph Retrieval Layer** (Milestone Requirement 2) for the Airline Travel Assistant system.

---

## Requirements Satisfied

### ✅ Requirement 2.a: Baseline Rule-based Retrieval

**Requirement:**
- Use Cypher queries to retrieve relevant information
- Create at least 10 different Cypher query templates
- Pass extracted entities from input to query the KG

**Implementation:**
- **18+ distinct Cypher query templates** implemented (exceeds requirement)
- All templates in `graph_retrieval.py::generate_cypher_baseline()`
- Full entity integration from `input_preprocessor.py`

### ✅ Requirement 2.b: Semantic Similarity Search

**Requirement:**
- Implement vector embeddings for semantic search
- Use at least 2 different embedding models

**Implementation:**
- Vector search in `graph_retrieval.py::vector_search()`
- Uses embedding models from `Create_kg.py`:
  - Model 1: `all-MiniLM-L6-v2` (384 dimensions)
  - Model 2: `paraphrase-MiniLM-L3-v2` (384 dimensions)
- Vector indexes: `journey_embeddings_1` and `journey_embeddings_2`

---

## Complete Intent Coverage

All **11 intents** from [input_preprocessor.py](input_preprocessor.py:47-57) are fully implemented:

| # | Intent | Handler Location | Query Templates |
|---|--------|------------------|----------------|
| 1 | `flight_search` | Lines 123-140 | 2 templates (basic + filtered) |
| 2 | `delay_analysis` | Lines 144-166 | 3 templates (flight/route/general) |
| 3 | `route_query` | Lines 170-188 | 4 templates (specific/from/to/all) |
| 4 | `comparison_query` | Lines 192-223 | 3 templates (route/multi-flight/generic) |
| 5 | `recommendation_query` | Lines 227-250 | 1+ template (with filters) |
| 6 | `schedule_query` | Lines 254-269 | 1 template |
| 7 | `passenger_query` | Lines 273-300 | 1+ template (with filters) |
| 8 | `journey_query` | Lines 304-323 | 1+ template (with class filter) |
| 9 | `filter_query` | Lines 327-363 | 5+ templates (nonstop/cheapest/fastest/comfort/delay) |
| 10 | `review_query` | Lines 367-384 | 1+ template (with filters) |
| 11 | `general_query` | Lines 387-394 | 1 fallback template |

**Total: 18+ distinct Cypher query templates** ✅

---

## Entity Utilization

The implementation fully leverages all extracted entities from `input_preprocessor.py`:

### Entities Extracted:
- **flights**: Flight numbers (e.g., "2411", "924")
- **airports**: Departure/arrival IATA codes (e.g., "LAX", "IAX")
- **passengers**: Traveler types (e.g., "business traveler", "premier gold")
- **journeys**: Trip properties (e.g., "business class", "economy", "comfort")
- **routes**: Route strings (e.g., "JFK-LAX")
- **dates**: Time references (currently unused as schema has no date field)
- **attributes**: Keywords (e.g., "delay", "cheapest", "nonstop", "fastest")

### How Entities Are Used:

#### 1. **Flight Numbers** (`flights`)
```python
# Example: "Is flight 2411 delayed?"
WHERE f.flight_number IN ['2411']
```

#### 2. **Airports** (`airports.departure`, `airports.arrival`)
```python
# Example: "Flights from LAX to IAX"
MATCH (f)-[:DEPARTS_FROM]->(origin:Airport {station_code: 'LAX'})
MATCH (f)-[:ARRIVES_AT]->(dest:Airport {station_code: 'IAX'})
```

#### 3. **Passengers** (`passengers`)
```python
# Example: "How do premier gold passengers rate this?"
WHERE toLower(p.loyalty_program_level) CONTAINS 'gold'
```

#### 4. **Journeys** (`journeys`)
```python
# Example: "How is business class?"
WHERE toLower(j.passenger_class) CONTAINS 'business'
```

#### 5. **Attributes** (`attributes`)
```python
# Example: "Show nonstop flights"
WHERE j.number_of_legs = 1

# Example: "Find cheapest flights"
ORDER BY j.actual_flown_miles ASC  # Miles as price proxy

# Example: "Fastest flights"
ORDER BY j.number_of_legs ASC, j.actual_flown_miles ASC
```

---

## Query Template Breakdown

### 1. Flight Search Templates

**Template 1.1: Basic Flight Search**
```cypher
MATCH (f:Flight)
MATCH (f)-[:DEPARTS_FROM]->(origin:Airport {station_code: 'LAX'})
MATCH (f)-[:ARRIVES_AT]->(dest:Airport {station_code: 'IAX'})
RETURN DISTINCT f.flight_number, f.fleet_type_description LIMIT 10
```

**Template 1.2: Filtered Flight Search (Nonstop)**
```cypher
MATCH (f:Flight)
MATCH (f)-[:DEPARTS_FROM]->(origin:Airport {station_code: 'LAX'})
MATCH (f)-[:ARRIVES_AT]->(dest:Airport {station_code: 'IAX'})
MATCH (j:Journey)-[:ON]->(f)
WHERE j.number_of_legs = 1
RETURN DISTINCT f.flight_number, f.fleet_type_description LIMIT 10
```

### 2. Delay Analysis Templates

**Template 2.1: Specific Flight Delay**
```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
WHERE f.flight_number IN ['2411']
RETURN f.flight_number, avg(j.arrival_delay_minutes) as avg_delay,
       max(j.arrival_delay_minutes) as max_delay,
       min(j.arrival_delay_minutes) as min_delay,
       count(j) as journey_count
```

**Template 2.2: Route-Based Delay**
```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
MATCH (f)-[:DEPARTS_FROM]->(a:Airport {station_code: 'LAX'})
RETURN f.flight_number, avg(j.arrival_delay_minutes) as avg_delay
ORDER BY avg_delay DESC LIMIT 10
```

**Template 2.3: General Delay Query**
```cypher
MATCH (j:Journey)
WHERE j.arrival_delay_minutes > 0
RETURN j.arrival_delay_minutes, j.text LIMIT 10
```

### 3. Route Query Templates

**Template 3.1: Specific Route**
```cypher
MATCH (a1:Airport {station_code: 'LAX'})<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport {station_code: 'IAX'})
RETURN DISTINCT f.flight_number, a1.station_code as origin, a2.station_code as destination,
       f.fleet_type_description as aircraft
```

**Template 3.2: Routes from Origin**
```cypher
MATCH (a1:Airport {station_code: 'LAX'})<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport)
RETURN DISTINCT f.flight_number, a2.station_code as destination LIMIT 20
```

**Template 3.3: Routes to Destination**
```cypher
MATCH (a1:Airport)<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport {station_code: 'IAX'})
RETURN DISTINCT f.flight_number, a1.station_code as origin LIMIT 20
```

**Template 3.4: All Routes**
```cypher
MATCH (f:Flight)-[:DEPARTS_FROM]->(a1), (f)-[:ARRIVES_AT]->(a2)
RETURN DISTINCT a1.station_code as origin, a2.station_code as destination LIMIT 20
```

### 4. Comparison Query Templates

**Template 4.1: Route-Based Comparison**
```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)-[:DEPARTS_FROM]->(a1:Airport {station_code: 'LAX'}),
      (f)-[:ARRIVES_AT]->(a2:Airport {station_code: 'IAX'})
RETURN f.flight_number, f.fleet_type_description,
       avg(j.food_satisfaction_score) as avg_rating,
       avg(j.arrival_delay_minutes) as avg_delay,
       avg(j.actual_flown_miles) as avg_miles,
       count(j) as reviews
ORDER BY avg_rating DESC LIMIT 10
```

**Template 4.2: Multi-Flight Comparison**
```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
WHERE f.flight_number IN ['924', '2411']
RETURN f.flight_number, avg(j.food_satisfaction_score) as avg_rating,
       avg(j.arrival_delay_minutes) as avg_delay, count(j) as reviews
ORDER BY avg_rating DESC
```

**Template 4.3: Generic Comparison**
```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
WITH f, avg(j.food_satisfaction_score) as avg_rating, avg(j.arrival_delay_minutes) as avg_delay, count(j) as reviews
WHERE reviews >= 2
RETURN f.flight_number, avg_rating, avg_delay, reviews
ORDER BY avg_rating DESC, avg_delay ASC LIMIT 10
```

### 5. Recommendation Query Template

```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {station_code: 'LAX'})
MATCH (f)-[:ARRIVES_AT]->(a2:Airport {station_code: 'IAX'})
WHERE toLower(j.passenger_class) CONTAINS 'economy'
WITH f, avg(j.food_satisfaction_score) as avg_rating, avg(j.arrival_delay_minutes) as avg_delay, count(j) as reviews
RETURN f.flight_number, f.fleet_type_description, avg_rating, avg_delay, reviews
ORDER BY avg_rating DESC, avg_delay ASC LIMIT 5
```

### 6. Schedule Query Template

```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {station_code: 'LAX'})
RETURN f.flight_number, avg(j.number_of_legs) as avg_legs,
       avg(j.actual_flown_miles) as avg_miles,
       avg(j.arrival_delay_minutes) as avg_delay
ORDER BY avg_legs ASC LIMIT 10
```

### 7. Passenger Query Template

```cypher
MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
WHERE toLower(p.loyalty_program_level) CONTAINS 'gold'
RETURN p.loyalty_program_level, p.generation, j.passenger_class,
       avg(j.food_satisfaction_score) as avg_rating, count(j) as journey_count
ORDER BY avg_rating DESC LIMIT 10
```

### 8. Journey Query Template

```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
WHERE toLower(j.passenger_class) CONTAINS 'business'
RETURN j.passenger_class, j.text, j.food_satisfaction_score, j.arrival_delay_minutes LIMIT 10
```

### 9. Filter Query Templates

**Template 9.1: Nonstop Filter**
```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
WHERE j.number_of_legs = 1
RETURN DISTINCT f.flight_number, f.fleet_type_description,
       avg(j.food_satisfaction_score) as avg_rating,
       avg(j.arrival_delay_minutes) as avg_delay,
       avg(j.actual_flown_miles) as avg_miles,
       avg(j.number_of_legs) as avg_legs
ORDER BY j.food_satisfaction_score DESC LIMIT 10
```

**Template 9.2-9.5**: Similar structure with different ORDER BY clauses:
- Cheapest: `ORDER BY j.actual_flown_miles ASC`
- Fastest: `ORDER BY j.number_of_legs ASC, j.actual_flown_miles ASC`
- Best Comfort: `ORDER BY j.food_satisfaction_score DESC`
- Delayed: `WHERE j.arrival_delay_minutes > 0 ORDER BY j.arrival_delay_minutes DESC`

### 10. Review Query Template

```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)
WHERE j.food_satisfaction_score IS NOT NULL
RETURN f.flight_number, j.food_satisfaction_score, j.text
ORDER BY j.food_satisfaction_score DESC LIMIT 10
```

### 11. General Query Template (Fallback)

```cypher
MATCH (j:Journey)-[:ON]->(f:Flight)-[:DEPARTS_FROM]->(a1:Airport),
      (f)-[:ARRIVES_AT]->(a2:Airport)
RETURN f.flight_number, a1.station_code as origin, a2.station_code as destination,
       j.food_satisfaction_score, j.text LIMIT 10
```

---

## Knowledge Graph Schema

**Nodes:**
- `Flight` - Properties: `flight_number`, `fleet_type_description`
- `Airport` - Properties: `station_code`
- `Journey` - Properties: `feedback_ID`, `food_satisfaction_score`, `arrival_delay_minutes`, `actual_flown_miles`, `number_of_legs`, `passenger_class`, `text`, `embedding_1`, `embedding_2`
- `Passenger` - Properties: `record_locator`, `loyalty_program_level`, `generation`

**Relationships:**
- `(Flight)-[:DEPARTS_FROM]->(Airport)`
- `(Flight)-[:ARRIVES_AT]->(Airport)`
- `(Journey)-[:ON]->(Flight)`
- `(Passenger)-[:TOOK]->(Journey)`

---

## Testing

Run the comprehensive test suite:

```bash
python test_all_intents.py
```

This will:
1. Test all 11 intents with multiple scenarios
2. Show input preprocessing (intent + entities)
3. Display generated Cypher queries
4. Execute queries and show results
5. Verify 10+ query template requirement

---

## Files

- **[graph_retrieval.py](graph_retrieval.py)** - Main retrieval layer implementation
- **[input_preprocessor.py](input_preprocessor.py)** - Intent classification and entity extraction
- **[Create_kg.py](Create_kg.py)** - Knowledge graph creation with embeddings
- **[test_all_intents.py](test_all_intents.py)** - Comprehensive test suite
- **[Airline_surveys_sample.csv](Airline_surveys_sample.csv)** - Source data

---

## Summary

✅ **All requirements satisfied:**
- ✅ Baseline rule-based retrieval (Req 2.a)
- ✅ 18+ distinct Cypher query templates (exceeds 10 requirement)
- ✅ Vector semantic search with 2 embedding models (Req 2.b)
- ✅ All 11 intents fully implemented
- ✅ Full entity extraction integration

The Graph Retrieval Layer handles all airline travel assistant queries as specified in the milestone requirements.
