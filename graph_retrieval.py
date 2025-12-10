import os
import json
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class GraphRetriever:
    """
    Graph Retrieval Layer for Airline Travel Assistant.
    Implements the first experiment (baseline) of the second requirement.
    """
    def __init__(self):
        self.uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.environ.get("NEO4J_USER", "neo4j")
        self.password = os.environ.get("NEO4J_PASSWORD", "password")
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

    def generate_cypher_baseline(self, parsed_input: Dict[str, Any]) -> str:
        """
        Experiment 1 (Baseline): Rule-based mapping from intent/entities to Cypher.
        Implements library of at least 10 query templates.
        """
        intent = parsed_input.get("intent")
        entities = parsed_input.get("entities", {})
        
        flights = entities.get("flights", [])
        airports = entities.get("airports", {})
        dep_code = airports.get("departure")
        arr_code = airports.get("arrival")
        dates = entities.get("dates", [])
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
                match_clauses.append(f"MATCH (f)-[:ORIGIN]->(origin:Airport {{code: '{dep_code}'}})")
            if arr_code:
                match_clauses.append(f"MATCH (f)-[:DESTINATION]->(dest:Airport {{code: '{arr_code}'}})")
            if dates:
                where_clauses.append(f"f.date = '{dates[0]}'")
            
            query = "\n".join(match_clauses)
            if where_clauses:
                query += "\nWHERE " + " AND ".join(where_clauses)
            query += "\nRETURN f, origin, dest LIMIT 10"

        # --- 2. Delay Analysis ---
        # "Is flight AA101 delayed?" or "delays from JFK"
        elif intent == "delay_analysis":
            if flights:
                f_list = [f"'{f}'" for f in flights]
                query = (
                    f"MATCH (f:Flight)\n"
                    f"WHERE f.flight_number IN [{', '.join(f_list)}]\n"
                    f"RETURN f.flight_number, f.status, f.delay_minutes, f.departure_time"
                )
            elif dep_code:
                query = (
                    f"MATCH (f:Flight)-[:ORIGIN]->(a:Airport {{code: '{dep_code}'}})\n"
                    f"WHERE f.delay_minutes > 0\n"
                    f"RETURN f.flight_number, f.delay_minutes, f.status ORDER BY f.delay_minutes DESC LIMIT 10"
                )
            else:
                 query = "MATCH (f:Flight) WHERE f.delay_minutes > 0 RETURN f LIMIT 10"

        # --- 3. Route Connectivity ---
        # "Show routes from Berlin"
        elif intent == "route_query":
            if dep_code and arr_code:
                query = (
                    f"MATCH (a1:Airport {{code: '{dep_code}'}})-[r:Route]-(a2:Airport {{code: '{arr_code}'}})\n"
                    f"RETURN r, a1, a2"
                )
            elif dep_code:
                query = (
                    f"MATCH (a1:Airport {{code: '{dep_code}'}})-[:HAS_ROUTE]->(r:Route)\n"
                    f"RETURN r LIMIT 20"
                )
            else:
                query = "MATCH (r:Route) RETURN r LIMIT 10"

        # --- 4. Price Query (Cheapest Flights) ---
        # "How much is a ticket to Paris?" or "Cheapest flight JFK to LHR"
        elif intent == "price_query":
            match_part = "MATCH (f:Flight)"
            if dep_code:
                match_part += f"-[:ORIGIN]->(:Airport {{code: '{dep_code}'}})"
            if arr_code:
                match_part += f"-[:DESTINATION]->(:Airport {{code: '{arr_code}'}})"
            
            query = (
                f"{match_part}\n"
                f"RETURN f.flight_number, f.price, f.currency ORDER BY f.price ASC LIMIT 5"
            )

        # --- 5. Schedule/Duration Query (Fastest/Times) ---
        # "When does flight AA123 leave?" or "Fastest flight to NY"
        elif intent == "schedule_query":
            if "fastest" in attributes or "duration" in attributes:
                match_part = "MATCH (f:Flight)"
                if dep_code: match_part += f"-[:ORIGIN]->(:Airport {{code: '{dep_code}'}})"
                if arr_code: match_part += f"-[:DESTINATION]->(:Airport {{code: '{arr_code}'}})"
                query = f"{match_part} RETURN f.flight_number, f.duration_minutes ORDER BY f.duration_minutes ASC LIMIT 5"
            elif flights:
                f_list = [f"'{f}'" for f in flights]
                query = f"MATCH (f:Flight) WHERE f.flight_number IN [{', '.join(f_list)}] RETURN f.flight_number, f.departure_time, f.arrival_time"
            else:
                query = "MATCH (f:Flight) RETURN f.flight_number, f.departure_time, f.arrival_time LIMIT 10"

        # --- 6. Full Itinerary / Journey Details ---
        # "Details for business class on AA101"
        elif intent == "journey_query":
            # Focusing on cabin class or specific journey amenities
            matches = ["MATCH (f:Flight)"]
            if flights:
                f_list = [f"'{f}'" for f in flights]
                matches.append(f"WHERE f.flight_number IN [{', '.join(f_list)}]")
            
            # If user asks for 'business' or 'economy', we might check properties or related nodes
            # Assuming 'class' is a property or relation. Let's assume property f.cabin_classes (list)
            if journeys:
                class_req = journeys[0] # e.g. "business"
                matches.append(f"AND '{class_req}' IN f.available_classes")
            
            query = "\n".join(matches) + "\nRETURN f.flight_number, f.available_classes, f.amenities LIMIT 5"

        # --- 7. Aircraft Information ---
        # "What plane is used for ..." (Often part of journey or general query, but let's separate standard questions)
        # Using "general_query" or falling back if intent is vague but mentions aircraft type
        # For now, let's map 'baggage_query' here as a distinct template or create a new 'aircraft' bucket.
        # But per requirements, let's use:
        elif intent == "baggage_query":
             # "What is the baggage allowance?"
             query = "MATCH (p:Policy {type: 'Baggage'}) RETURN p.description, p.allowance_kg LIMIT 5"

        # --- 8. Passenger Satisfaction / Reviews ---
        # "How is the food on AirFrance?"
        elif intent == "review_query":
            # Assuming (f:Flight)-[:HAS_REVIEW]->(r:Review) or f.rating
            match_part = "MATCH (f:Flight)"
            if flights:
                f_list = [f"'{f}'" for f in flights]
                match_part += f" WHERE f.flight_number IN [{', '.join(f_list)}]"
            
            query = f"{match_part} RETURN f.flight_number, f.overall_rating, f.food_rating, f.seat_rating LIMIT 5"

        # --- 9. Recommendation Query (Highest Rated) ---
        # "Recommend best flights to London"
        elif intent == "recommendation_query":
            match_part = "MATCH (f:Flight)"
            if arr_code:
                match_part += f"-[:DESTINATION]->(:Airport {{code: '{arr_code}'}})"
            
            query = (
                f"{match_part}\n"
                f"WHERE f.overall_rating IS NOT NULL\n"
                f"RETURN f.flight_number, f.overall_rating ORDER BY f.overall_rating DESC LIMIT 5"
            )

        # --- 10. Airport Amenities / Info ---
        # "Does JFK have a lounge?" -> Mapped typically from 'general' or specific intent
        # Let's handle generic 'flight_search' with no date/flight but specific airport as a fallback airport query
        # OR if we have a specific 'airport_query' intent (though not in the list I saw effectively, let's overlap with route or general)
        # Re-using 'explanation_query' or creating a catch-all for Policy/Airport if intent is vague.
        elif intent == "policy_query":
             query = "MATCH (pol:Policy) RETURN pol.name, pol.details LIMIT 5"

        # --- Fallback / catch-all for "booking_intent" or others ---
        else:
            # Fallback for "booking_intent" -> show available flights
            if intent == "booking_intent":
                 match_part = "MATCH (f:Flight {status: 'Scheduled'})"
                 if dep_code: match_part += f"-[:ORIGIN]->(:Airport {{code: '{dep_code}'}})"
                 if arr_code: match_part += f"-[:DESTINATION]->(:Airport {{code: '{arr_code}'}})"
                 query = f"{match_part} RETURN f.flight_number, f.price, f.seats_available LIMIT 5"
            else:
                 query = "MATCH (n) RETURN n LIMIT 5"

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
    # Simple test harness
    # Requires a running Neo4j instance to return real data
    
    retriever = GraphRetriever()
    
    # Test Case 1: Flight Search
    test_input_1 = {
        "intent": "flight_search",
        "entities": {
            "flights": [],
            "airports": {"departure": "JFK", "arrival": "LHR"},
            "dates": ["2025-05-20"]
        }
    }
    
    print("--- Test Case 1: Flight Search ---")
    results_1 = retriever.run_search(test_input_1)
    print(f"Result Count: {len(results_1)}")

    # Test Case 2: Delay Analysis
    test_input_2 = {
        "intent": "delay_analysis",
        "entities": {
            "flights": ["AA101"],
            "airports": {}
        }
    }

    print("\n--- Test Case 2: Delay Analysis ---")
    results_2 = retriever.run_search(test_input_2)
    print(f"Result Count: {len(results_2)}")
    
    retriever.close()
