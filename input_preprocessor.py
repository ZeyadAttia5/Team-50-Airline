import json
import ollama
from typing import Dict, Any, Optional

class InputPreprocessor:
    def __init__(self, model_name: str = "llama3.2:3b"):
        """
        Initialize the InputPreprocessor with an Ollama model.
        
        Args:
            model_name: The name of the Ollama model to use (default: "llama3.2:3b").
        """
        self.model_name = model_name
        self.system_prompt = """
            You are an Input Preprocessing Assistant for a Graph-RAG Airline Travel System.

            Your job is to analyze the user’s query and perform two tasks only:

            ------------------------------------------------

            1. Intent Classification (Task 1a)

            Classify the user’s intent into EXACTLY ONE of the following categories:

            - flight_search → User wants to find available flights
            - booking_intent → User expresses desire to book or reserve a flight
            - delay_analysis → User asks about delays, cancellations, or on-time performance
            - route_query → User asks about airline routes or connectivity
            - comparison_query → User wants to compare flights, airlines, routes, or airports
            - recommendation_query → User asks for recommended or best options
            - price_query → User asks about ticket prices or cost-related information
            - schedule_query → User asks about departure/arrival times or schedules
            - passenger_query → User asks about passengers or travel experience
            - baggage_query → User asks about baggage allowances or policies
            - policy_query → User asks about airline rules, policies, or regulations
            - journey_query → User asks about journey details (class, food, comfort, duration)
            - review_query → User asks about reviews or passenger feedback
            - filter_query → User applies filters like nonstop, cheapest, fastest, best comfort
            - explanation_query → User asks for definitions or clarifications
            - general_query → Airline-related questions that do not match other categories

            Choose the most accurate intent based on the meaning of the query, not only keywords.

            ------------------------------------------------

            2. Entity Extraction (Task 1b – NER for Airline Domain)

            Extract relevant airline-related entities from the query and return them in the following JSON structure:

            {
            "flights": [],
            "airports": {
                "departure": null,
                "arrival": null
            },
            "passengers": [],
            "journeys": [],
            "routes": [],
            "dates": [],
            "attributes": []
            }

            Entity Rules:

            - Flights → Flight numbers (e.g., "AA101", "EK202")
            - Airports → IATA codes or full airport names (e.g., "JFK", "Heathrow")
            - Passengers → traveller types (e.g., business, family, solo, economy traveler)
            - Journeys → trip properties like class (economy/business/first), comfort, food, seat, duration
            - Routes → routes like "JFK–LAX" or "London–Paris"
            - Dates → travel dates or time references (e.g., "tomorrow", "next week", "2025-01-20")
            - Attributes → words like delay, price, cheapest, fastest, comfort, service, nonstop

            Only extract entities clearly expressed or strongly implied in the query.

            ------------------------------------------------

            3. Output Format

            Respond ONLY in valid JSON using this structure:

            {
            "intent": "",
            "entities": {
                "flights": [],
                "airports": {
                "departure": null,
                "arrival": null
                },
                "passengers": [],
                "journeys": [],
                "routes": [],
                "dates": [],
                "attributes": []
            }
            }
            """

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Analyzes the user's query to classify intent and extract entities using Ollama.

        Args:
            query: The user's input string.

        Returns:
            A dictionary containing the classified intent and extracted entities.
        """
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": query}
                ],
                format="json",
                options={"temperature": 0}
            )
            
            content = response['message']['content']
            parsed_response = json.loads(content)
            return parsed_response

        except Exception as e:
            print(f"Error processing query with Ollama: {e}")
            return {
                "intent": "general_query",
                "entities": {
                    "flights": [],
                    "airports": {"departure": None, "arrival": None},
                    "passengers": [],
                    "journeys": [],
                    "routes": [],
                    "dates": [],
                    "attributes": []
                }
            }

if __name__ == "__main__":
    # Example usage with Ollama
    preprocessor = InputPreprocessor(model_name="llama3.2:3b")
    query = "What is the cheapest nonstop flight from JFK to LAX tomorrow?"
    print(f"Processing query: '{query}'")
    result = preprocessor.process_query(query)
    print(json.dumps(result, indent=2))
