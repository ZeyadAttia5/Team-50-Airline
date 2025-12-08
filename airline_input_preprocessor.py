import re
import json

class AirlineInputPreprocessor:
    def __init__(self):
        # Intent keywords
        self.intent_keywords = {
            "flight_search": ["flight", "flights", "book", "find", "search", "available"],
            "delay_analysis": ["delay", "delayed", "late", "on-time", "punctual"],
            "route_query": ["route", "routes", "path"],
            "passenger_query": ["passenger", "traveler", "traveller", "people"],
            "journey_query": ["journey", "trip", "travel", "class", "seat", "food", "comfort"],
        }

        # Regex patterns
        self.flight_pattern = r"\b[A-Z]{2}\d{1,4}\b"        # e.g. AA123, EK202
        self.airport_pattern = r"\b[A-Z]{3}\b"             # e.g. JFK, LAX, ORD
        self.date_pattern = r"\b(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})\b"

    # ---------- 1a: Intent Classification ----------
    def classify_intent(self, text: str) -> str:
        text_lower = text.lower()

        for intent, keywords in self.intent_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent

        return "general_query"

    # ---------- 1b: Entity Extraction ----------
    def extract_entities(self, text: str) -> dict:
        # Flights
        flights = re.findall(self.flight_pattern, text.upper())

        # Airports
        airports = re.findall(self.airport_pattern, text.upper())
        departure = airports[0] if len(airports) > 0 else None
        arrival = airports[1] if len(airports) > 1 else None

        # Routes
        routes = []
        if departure and arrival:
            routes.append(f"{departure}-{arrival}")

        # Dates
        dates = re.findall(self.date_pattern, text)

        # Journey attributes
        journey_keywords = ["economy", "business", "first class", "comfort", "food", "seat"]
        journeys = [word for word in journey_keywords if word in text.lower()]

        # Passenger types
        passenger_keywords = ["family", "solo", "business traveler", "child", "adult"]
        passengers = [word for word in passenger_keywords if word in text.lower()]

        # Other attributes
        attribute_keywords = ["cheap", "cheapest", "fastest", "delay", "delays", "on-time"]
        attributes = [word for word in attribute_keywords if word in text.lower()]

        return {
            "flights": flights,
            "airports": {
                "departure": departure,
                "arrival": arrival
            },
            "passengers": passengers,
            "journeys": journeys,
            "routes": routes,
            "dates": dates,
            "attributes": attributes
        }

    # ---------- Main Processing Function ----------
    def process_query(self, text: str) -> dict:
        intent = self.classify_intent(text)
        entities = self.extract_entities(text)

        return {
            "intent": intent,
            "entities": entities
        }


# ---------- Run Example ----------
if __name__ == "__main__":
    processor = AirlineInputPreprocessor()

    user_query = input("Enter your airline query: ")

    result = processor.process_query(user_query)

    print("\n--- Parsed Output ---")
    print(json.dumps(result, indent=4))
