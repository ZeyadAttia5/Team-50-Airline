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
        - Nodes: Flight, Airport, Journey, Passenger
        - Relationships: (f)-[:DEPARTS_FROM]->(a), (f)-[:ARRIVES_AT]->(a), (j)-[:ON]->(f), (p)-[:TOOK]->(j)
        - Properties: Airport.station_code (not code)

        Handles all 11 intents from input_preprocessor.py:
        1. flight_search, 2. delay_analysis, 3. route_query, 4. comparison_query,
        5. recommendation_query, 6. schedule_query, 7. passenger_query, 8. journey_query,
        9. filter_query, 10. review_query, 11. general_query
        """
        intent = parsed_input.get("intent")
        entities = parsed_input.get("entities", {})

        flights = entities.get("flights", [])
        airports = entities.get("airports", {})
        dep_code = airports.get("departure")
        arr_code = airports.get("arrival")
        # Note: 'dates' are not supported in current Create_kg.py schema (Flight has no date prop)
        # We will ignore dates for now or search only by route.

        passengers = entities.get("passengers", [])  # e.g., "business traveler", "family"
        journeys = entities.get("journeys", [])  # e.g., "business", "economy", "comfort"
        attributes = entities.get("attributes", [])  # e.g., "cheapest", "fastest", "nonstop", "delay"
        routes = entities.get("routes", [])  # e.g., "JFK-LAX"

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

            # Apply attribute filters
            if "nonstop" in attributes or "direct" in attributes:
                match_clauses.append("MATCH (j:Journey)-[:ON]->(f)")
                where_clauses.append("j.number_of_legs = 1")

            query = "\n".join(match_clauses)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)
            query += "\nRETURN DISTINCT f.flight_number, f.fleet_type_description LIMIT 10"

        # --- 2. Delay Analysis ---
        # "Is flight AA101 delayed?" or "Show delays from JFK"
        elif intent == "delay_analysis":
            if flights:
                f_list = [f"'{f}'" for f in flights]
                query = (
                    f"MATCH (j:Journey)-[:ON]->(f:Flight)\n"
                    f"WHERE f.flight_number IN [{', '.join(f_list)}]\n"
                    f"RETURN f.flight_number, avg(j.arrival_delay_minutes) as avg_delay, "
                    f"max(j.arrival_delay_minutes) as max_delay, min(j.arrival_delay_minutes) as min_delay, "
                    f"count(j) as journey_count"
                )
            elif dep_code or arr_code:
                match_parts = ["MATCH (j:Journey)-[:ON]->(f:Flight)"]
                if dep_code:
                    match_parts.append(f"MATCH (f)-[:DEPARTS_FROM]->(a:Airport {{station_code: '{dep_code}'}})")
                if arr_code:
                    match_parts.append(f"MATCH (f)-[:ARRIVES_AT]->(a:Airport {{station_code: '{arr_code}'}})")
                query = (
                    f"{chr(10).join(match_parts)}\n"
                    f"RETURN f.flight_number, avg(j.arrival_delay_minutes) as avg_delay "
                    f"ORDER BY avg_delay DESC LIMIT 10"
                )
            else:
                query = "MATCH (j:Journey) WHERE j.arrival_delay_minutes > 0 RETURN j.arrival_delay_minutes, j.text LIMIT 10"

        # --- 3. Route Connectivity ---
        # "Show routes from Berlin" or "Routes between JFK and LAX"
        elif intent == "route_query":
            if dep_code and arr_code:
                query = (
                    f"MATCH (a1:Airport {{station_code: '{dep_code}'}})<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})\n"
                    f"RETURN DISTINCT f.flight_number, a1.station_code as origin, a2.station_code as destination, "
                    f"f.fleet_type_description as aircraft"
                )
            elif dep_code:
                query = (
                    f"MATCH (a1:Airport {{station_code: '{dep_code}'}})<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport)\n"
                    f"RETURN DISTINCT f.flight_number, a2.station_code as destination LIMIT 20"
                )
            elif arr_code:
                query = (
                    f"MATCH (a1:Airport)<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})\n"
                    f"RETURN DISTINCT f.flight_number, a1.station_code as origin LIMIT 20"
                )
            else:
                query = "MATCH (f:Flight)-[:DEPARTS_FROM]->(a1), (f)-[:ARRIVES_AT]->(a2) RETURN DISTINCT a1.station_code as origin, a2.station_code as destination LIMIT 20"

        # --- 4. Comparison Query ---
        # "Compare flights from JFK to LAX" or "Compare airlines on this route"
        elif intent == "comparison_query":
            if dep_code and arr_code:
                query = (
                    f"MATCH (j:Journey)-[:ON]->(f:Flight)-[:DEPARTS_FROM]->(a1:Airport {{station_code: '{dep_code}'}}), "
                    f"(f)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})\n"
                    f"RETURN f.flight_number, f.fleet_type_description, "
                    f"avg(j.food_satisfaction_score) as avg_rating, "
                    f"avg(j.arrival_delay_minutes) as avg_delay, "
                    f"avg(j.actual_flown_miles) as avg_miles, "
                    f"count(j) as reviews "
                    f"ORDER BY avg_rating DESC LIMIT 10"
                )
            elif flights and len(flights) > 1:
                f_list = [f"'{f}'" for f in flights]
                query = (
                    f"MATCH (j:Journey)-[:ON]->(f:Flight)\n"
                    f"WHERE f.flight_number IN [{', '.join(f_list)}]\n"
                    f"RETURN f.flight_number, "
                    f"avg(j.food_satisfaction_score) as avg_rating, "
                    f"avg(j.arrival_delay_minutes) as avg_delay, "
                    f"count(j) as reviews "
                    f"ORDER BY avg_rating DESC"
                )
            else:
                # Generic comparison: top flights by satisfaction
                query = (
                    "MATCH (j:Journey)-[:ON]->(f:Flight) "
                    "WITH f, avg(j.food_satisfaction_score) as avg_rating, avg(j.arrival_delay_minutes) as avg_delay, count(j) as reviews "
                    "WHERE reviews >= 2 "
                    "RETURN f.flight_number, avg_rating, avg_delay, reviews "
                    "ORDER BY avg_rating DESC, avg_delay ASC LIMIT 10"
                )

        # --- 5. Recommendation Query (Best Options) ---
        # "Recommend best flights" or "Best flight from JFK to LAX"
        elif intent == "recommendation_query":
            match_parts = ["MATCH (j:Journey)-[:ON]->(f:Flight)"]
            where_clauses = []

            if dep_code:
                match_parts.append(f"MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {{station_code: '{dep_code}'}})")
            if arr_code:
                match_parts.append(f"MATCH (f)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})")

            # Filter by class if specified in journeys
            if journeys:
                for j_attr in journeys:
                    if j_attr.lower() in ["business", "economy", "first"]:
                        where_clauses.append(f"toLower(j.passenger_class) CONTAINS '{j_attr.lower()}'")

            query = "\n".join(match_parts)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)

            query += (
                "\nWITH f, avg(j.food_satisfaction_score) as avg_rating, avg(j.arrival_delay_minutes) as avg_delay, count(j) as reviews "
                "\nRETURN f.flight_number, f.fleet_type_description, avg_rating, avg_delay, reviews "
                "\nORDER BY avg_rating DESC, avg_delay ASC LIMIT 5"
            )

        # --- 6. Schedule/Duration Query ---
        # "Flight schedule" or "How long is the journey?"
        elif intent == "schedule_query":
            match_parts = ["MATCH (j:Journey)-[:ON]->(f:Flight)"]

            if dep_code:
                match_parts.append(f"MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {{station_code: '{dep_code}'}})")
            if arr_code:
                match_parts.append(f"MATCH (f)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})")

            query = (
                f"{chr(10).join(match_parts)}\n"
                f"RETURN f.flight_number, "
                f"avg(j.number_of_legs) as avg_legs, "
                f"avg(j.actual_flown_miles) as avg_miles, "
                f"avg(j.arrival_delay_minutes) as avg_delay "
                f"ORDER BY avg_legs ASC LIMIT 10"
            )

        # --- 7. Passenger Query ---
        # "How do business travelers rate this?" or "Passenger experience"
        elif intent == "passenger_query":
            match_parts = ["MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)"]
            where_clauses = []

            # Filter by loyalty level if mentioned in passengers
            if passengers:
                for p_attr in passengers:
                    if "elite" in p_attr.lower() or "1k" in p_attr or "gold" in p_attr.lower() or "silver" in p_attr.lower():
                        where_clauses.append(f"toLower(p.loyalty_program_level) CONTAINS '{p_attr.lower()}'")
                    elif "business" in p_attr.lower():
                        where_clauses.append("toLower(j.passenger_class) = 'business'")
                    elif "economy" in p_attr.lower():
                        where_clauses.append("toLower(j.passenger_class) = 'economy'")

            if dep_code:
                match_parts.append(f"MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {{station_code: '{dep_code}'}})")
            if arr_code:
                match_parts.append(f"MATCH (f)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})")

            query = "\n".join(match_parts)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)

            query += (
                "\nRETURN p.loyalty_program_level, p.generation, j.passenger_class, "
                "avg(j.food_satisfaction_score) as avg_rating, count(j) as journey_count "
                "ORDER BY avg_rating DESC LIMIT 10"
            )

        # --- 8. Journey/Quality Query ---
        # "How is business class?" or "Journey comfort on this route"
        elif intent == "journey_query":
            match_parts = ["MATCH (j:Journey)-[:ON]->(f:Flight)"]
            where_clauses = []

            # Filter by class or comfort attributes
            if journeys:
                for j_attr in journeys:
                    if j_attr.lower() in ["business", "economy", "first"]:
                        where_clauses.append(f"toLower(j.passenger_class) CONTAINS '{j_attr.lower()}'")

            if dep_code:
                match_parts.append(f"MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {{station_code: '{dep_code}'}})")
            if arr_code:
                match_parts.append(f"MATCH (f)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})")

            query = "\n".join(match_parts)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)

            query += "\nRETURN j.passenger_class, j.text, j.food_satisfaction_score, j.arrival_delay_minutes LIMIT 10"

        # --- 9. Filter Query ---
        # "Show me nonstop flights" or "Cheapest/fastest option"
        elif intent == "filter_query":
            match_parts = ["MATCH (j:Journey)-[:ON]->(f:Flight)"]
            where_clauses = []
            order_by = "j.food_satisfaction_score DESC"

            if dep_code:
                match_parts.append(f"MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {{station_code: '{dep_code}'}})")
            if arr_code:
                match_parts.append(f"MATCH (f)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})")

            # Apply attribute-based filters
            for attr in attributes:
                attr_lower = attr.lower()
                if attr_lower in ["nonstop", "direct"]:
                    where_clauses.append("j.number_of_legs = 1")
                elif attr_lower in ["cheapest", "cheap"]:
                    order_by = "j.actual_flown_miles ASC"  # Using miles as proxy for price
                elif attr_lower in ["fastest", "quick", "shortest"]:
                    order_by = "j.number_of_legs ASC, j.actual_flown_miles ASC"
                elif attr_lower in ["best", "top", "comfort"]:
                    order_by = "j.food_satisfaction_score DESC"
                elif attr_lower in ["delay", "delayed"]:
                    where_clauses.append("j.arrival_delay_minutes > 0")
                    order_by = "j.arrival_delay_minutes DESC"

            query = "\n".join(match_parts)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)

            query += (
                f"\nRETURN DISTINCT f.flight_number, f.fleet_type_description, "
                f"avg(j.food_satisfaction_score) as avg_rating, "
                f"avg(j.arrival_delay_minutes) as avg_delay, "
                f"avg(j.actual_flown_miles) as avg_miles, "
                f"avg(j.number_of_legs) as avg_legs "
                f"ORDER BY {order_by} LIMIT 10"
            )

        # --- 10. Review/Satisfaction Query ---
        # "How is the food?" or "Show reviews"
        elif intent == "review_query":
            match_parts = ["MATCH (j:Journey)-[:ON]->(f:Flight)"]
            where_clauses = []

            if dep_code:
                match_parts.append(f"MATCH (f)-[:DEPARTS_FROM]->(a1:Airport {{station_code: '{dep_code}'}})")
            if arr_code:
                match_parts.append(f"MATCH (f)-[:ARRIVES_AT]->(a2:Airport {{station_code: '{arr_code}'}})")

            # Check for food/service specific mentions in attributes
            if "food" in attributes or "service" in attributes:
                where_clauses.append("j.food_satisfaction_score IS NOT NULL")

            query = "\n".join(match_parts)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)

            query += "\nRETURN f.flight_number, j.food_satisfaction_score, j.text ORDER BY j.food_satisfaction_score DESC LIMIT 10"

        # --- 11. General Query (Fallback) ---
        else:
            # Generic query to show sample journeys
            query = (
                "MATCH (j:Journey)-[:ON]->(f:Flight)-[:DEPARTS_FROM]->(a1:Airport), "
                "(f)-[:ARRIVES_AT]->(a2:Airport) "
                "RETURN f.flight_number, a1.station_code as origin, a2.station_code as destination, "
                "j.food_satisfaction_score, j.text LIMIT 10"
            )

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

