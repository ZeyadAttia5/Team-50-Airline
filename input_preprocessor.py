import json
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Error: 'python-dotenv' is not installed. Please run 'pip install python-dotenv' or activate your virtual environment.")


try:
    from groq import Groq
except ImportError:
    print("Error: 'groq' is not installed. Please run 'pip install groq' or activate your virtual environment.")
    exit(1)

from typing import Dict, Any, Optional

class InputPreprocessor:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", api_key: Optional[str] = None):
        """
        Initialize the InputPreprocessor with a Groq model.
        
        Args:
            model_name: The name of the Groq model to use (default: "llama3-8b-8192").
            api_key: The Groq API key. If None, it will be read from the 'GROQ_API_KEY' environment variable.
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("Groq API Key is required. Set it in the constructor or as 'GROQ_API_KEY' environment variable.")
        
        self.client = Groq(api_key=self.api_key)
        
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
        Analyzes the user's query to classify intent and extract entities using Groq.

        Args:
            query: The user's input string.

        Returns:
            A dictionary containing the classified intent and extracted entities.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                model=self.model_name,
                response_format={"type": "json_object"},
                temperature=0
            )
            
            content = chat_completion.choices[0].message.content
            parsed_response = json.loads(content)
            return parsed_response

        except Exception as e:
            print(f"Error processing query with Groq: {e}")
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
    # Example usage with Groq
    # Ensure GROQ_API_KEY is set in your environment
    try:
        preprocessor = InputPreprocessor()
        query = "what are flights from JFK to LAX with minimum delay?"
        print(f"Processing query: '{query}'")
        result = preprocessor.process_query(query)
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(e)
