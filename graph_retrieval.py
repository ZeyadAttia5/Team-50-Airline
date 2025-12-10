import os
import json
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
    print("Loading Sentence Transformer model for retrieval...")
    # Using Model 1 (all-MiniLM-L6-v2) by default as it's the standard/balanced one
    # model = SentenceTransformer('all-MiniLM-L6-v2') 
    model = SentenceTransformer('paraphrase-MiniLM-L3-v2') 
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("WARNING: 'sentence_transformers' not installed. Vector search will fail.")

class GraphRetriever:
    """
    Graph Retrieval Layer for Airline Travel Assistant.
    Satisfies Requirement 2:
    - 2.a: Baseline Rule-based Retrieval (Template Cypher)
    - 2.b: Semantic Similarity Search (Vector Embeddings)
    """
    def __init__(self):
        # Read config from file if env vars not set (fallback)
        self.uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.environ.get("NEO4J_USER", "neo4j")
        self.password = os.environ.get("NEO4J_PASSWORD", "password")
        
        # Try reading config.txt if available
        if os.path.exists("config.txt"):
            with open("config.txt", "r") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        if k == "URI": self.uri = v
                        elif k == "USERNAME": self.user = v
                        elif k == "PASSWORD": self.password = v

        self.driver = None
        self._connect()

    def _connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            print(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def vector_search(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Requirement 2.b: Semantic Similarity Search using Vector Embeddings.
        Uses 'journey_embeddings_1' index created by Create_kg.py.
        """
        if not EMBEDDINGS_AVAILABLE:
            print("Embeddings not available.")
            return []

        # 1. Embed query
        query_vector = model.encode(query_text).tolist()
        
        # 2. Run Vector Search
        cypher = """
        CALL db.index.vector.queryNodes('journey_embeddings_1', $limit, $embedding)
        YIELD node, score
        RETURN node.feedback_ID AS id, 
               node.text AS description, 
               node.food_satisfaction_score AS food_rating,
               node.arrival_delay_minutes AS delay,
               score
        """
        
        if self.driver:
            with self.driver.session() as session:
                result = session.run(cypher, limit=limit, embedding=query_vector)
                return [record.data() for record in result]
        return []

    def generate_cypher_baseline(self, parsed_input: Dict[str, Any]) -> str:
        """
        Experiment 1 (Baseline): Rule-based mapping from intent/entities to Cypher.
        Updated to match Create_kg.py schema:
        - Nodes: Flight, Airport, Journey
        - Relationships: (f)-[:DEPARTS_FROM]->(a), (f)-[:ARRIVES_AT]->(a), (j)-[:ON]->(f)
        - Properties: Airport.station_code (not code)
        """
        intent = parsed_input.get("intent")
        entities = parsed_input.get("entities", {})
        
        flights = entities.get("flights", [])
        airports = entities.get("airports", {})
        dep_code = airports.get("departure")
        arr_code = airports.get("arrival")
        # Note: 'dates' are not supported in current Create_kg.py schema (Flight has no date prop)
        # We will ignore dates for now or search only by route.
        
        passengers = entities.get("passengers", [])
        journeys = entities.get("journeys", []) # e.g., "business", "economy"
        attributes = entities.get("attributes", []) # e.g., "cheapest", "fastest"

        query = ""

        # --- 1. Flight Search (Standard) ---
        # "Find flights from JFK to LHR"
        if intent == "flight_search":
            match_clauses = ["MATCH (f:Flight)"]
            where_clauses = []
            if dep_code:
                match_clauses.append(f"MATCH (f)-[:DEPARTS_FROM]->(origin:Airport {{station_code: '{dep_code}'}})")
            if arr_code:
                match_clauses.append(f"MATCH (f)-[:ARRIVES_AT]->(dest:Airport {{station_code: '{arr_code}'}})")
            
            query = "\n".join(match_clauses)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)
            query += "\nRETURN f.flight_number, f.fleet_type_description LIMIT 10"

        # --- 2. Delay Analysis ---
        # "Is flight AA101 delayed?" -> Aggregate Journey delays
        elif intent == "delay_analysis":
            if flights:
                f_list = [f"'{f}'" for f in flights]
                query = (
                    f"MATCH (j:Journey)-[:ON]->(f:Flight)\n"
                    f"WHERE f.flight_number IN [{', '.join(f_list)}]\n"
                    f"RETURN f.flight_number, avg(j.arrival_delay_minutes) as avg_delay, max(j.arrival_delay_minutes) as max_delay"
                )
            elif dep_code:
                query = (
                    f"MATCH (j:Journey)-[:ON]->(f:Flight)-[:DEPARTS_FROM]->(a:Airport {{station_code: '{dep_code}'}})\n"
                    f"RETURN f.flight_number, avg(j.arrival_delay_minutes) as avg_delay ORDER BY avg_delay DESC LIMIT 10"
                )
            else:
                 query = "MATCH (j:Journey) WHERE j.arrival_delay_minutes > 0 RETURN j.arrival_delay_minutes, j.text LIMIT 10"

        # --- 3. Route Connectivity ---
        # "Show routes from Berlin"
        elif intent == "route_query":
            if dep_code and arr_code:
                query = (
                    f"MATCH (a1:Airport {{station_code: '{dep_code}'}})<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})\n"
                    f"RETURN DISTINCT f.flight_number, a1.station_code, a2.station_code"
                )
            elif dep_code:
                query = (
                    f"MATCH (a1:Airport {{station_code: '{dep_code}'}})<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport)\n"
                    f"RETURN DISTINCT f.flight_number, a2.station_code LIMIT 20"
                )
            else:
                query = "MATCH (f:Flight)-[:DEPARTS_FROM]->(a1), (f)-[:ARRIVES_AT]->(a2) RETURN DISTINCT a1.station_code, a2.station_code LIMIT 10"

        # --- 4. Price Query (Cheapest Flights) ---
        # Note: 'price' is NOT in the Create_kg.py CSV import (only miles, satisfaction, delay).
        # We will fallback to returning general flight info or miles.
        elif intent == "price_query":
             # "How many miles?"
            match_part = "MATCH (j:Journey)"
            if dep_code:
                match_part += f"-[:ON]->(:Flight)-[:DEPARTS_FROM]->(:Airport {{station_code: '{dep_code}'}})"
            
            query = (
                f"{match_part}\n"
                f"RETURN j.actual_flown_miles ORDER BY j.actual_flown_miles ASC LIMIT 5"
            )

        # --- 5. Schedule/Duration Query ---
        # No schedule data in graph. Return Journey delay stats or miles.
        elif intent == "schedule_query":
             query = "MATCH (j:Journey)-[:ON]->(f:Flight) RETURN f.flight_number, avg(j.number_of_legs) as avg_legs LIMIT 5"

        # --- 6. Journey/Quality Query ---
        elif intent == "journey_query":
            # "How is business class?"
            match_part = "MATCH (j:Journey)"
            where_clauses = []
            if journeys: # e.g. "business"
                match_part += f" WHERE j.passenger_class CONTAINS '{journeys[0]}'" # Case sensitive usually, but simpler here
            
            query = f"{match_part} RETURN j.text, j.food_satisfaction_score LIMIT 5"

        # --- 7. Review/Satisfaction Query ---
        elif intent == "review_query":
             # "How is the food?"
            query = "MATCH (j:Journey) RETURN j.food_satisfaction_score, j.text ORDER BY j.food_satisfaction_score DESC LIMIT 5"

        # --- 8. Recommendation Query (Best Rated) ---
        elif intent == "recommendation_query":
            query = (
                "MATCH (j:Journey)-[:ON]->(f:Flight) "
                "RETURN f.flight_number, avg(j.food_satisfaction_score) as avg_rating "
                "ORDER BY avg_rating DESC LIMIT 5"
            )

        # --- Fallback to Vector Search for Unmatched Intents (or generic) ---
        else:
            # If we were processing a real NL query here we might default to vector search, 
            # but this method returns Cypher string.
            query = "MATCH (j:Journey) RETURN j.text LIMIT 5"

        return query

    def run_search(self, parsed_input: Dict[str, Any]):
        """
        Executes the baseline retrieval manually.
        """
        cypher = self.generate_cypher_baseline(parsed_input)
        print(f"\n[Baseline] Generated Cypher:\n{cypher}\n")
        
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher)
                    records = [record.data() for record in result]
                    return records
            except Exception as e:
                print(f"Error executing Cypher: {e}")
                return []
        else:
            print("Driver not connected. Skipping execution.")
            return []

if __name__ == "__main__":
    # Test Harness
    retriever = GraphRetriever()
    
    # Test 1: Vector Search (Req 2.b)
    user_query = "bad food and delayed flight"
    print(f"--- Test 1: Vector Search for '{user_query}' ---")
    vec_results = retriever.vector_search(user_query)
    for r in vec_results:
        print(f"[{r['score']:.4f}] {r['description'][:80]}... (Food: {r['food_rating']}, Delay: {r['delay']})")

    # Test 2: Baseline Flight Search (Req 2.a)
    # Using codes that likely exist in the sample (from walkthrough: MKX, ORX, LAX...)
    test_input_1 = {
        "intent": "flight_search",
        "entities": {
            "flights": [],
            "airports": {"departure": "LAX", "arrival": "ORX"}, # Guessed from previous output
            "dates": []
        }
    }
    
    print("\n--- Test 2: Baseline Flight Search (LAX -> ORX) ---")
    results_1 = retriever.run_search(test_input_1)
    if not results_1: 
        print("No exact matches found (codes might differ in sample data).")
    else:
        for r in results_1: print(r)

    # Test 3: Delay Analysis
    test_input_2 = {
        "intent": "delay_analysis",
        "entities": {
            "flights": ["1866"], # From previous output
            "airports": {}
        }
    }

    print("\n--- Test 3: Delay Analysis (Flight 1866) ---")
    results_2 = retriever.run_search(test_input_2)
    for r in results_2: print(r)
    
    retriever.close()

