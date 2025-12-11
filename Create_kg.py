"""
Neo4j Knowledge Graph Construction Script for Airline Passenger Data
Creates a Knowledge Graph with Passenger, Journey, Flight, and Airport nodes
"""

import csv
import os
from neo4j import GraphDatabase

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence_transformers not installed. Embeddings will not be generated.")


def read_config(config_path):
    """Read Neo4j credentials from config.txt file"""
    config = {}
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        raise


def create_knowledge_graph(uri, username, password, csv_path):
    """Create the Knowledge Graph from CSV data"""

    # Connect to Neo4j
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session() as session:
            # Clear existing data
            print("Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Existing data cleared.")

            # Load Embedding Models
            if EMBEDDINGS_AVAILABLE:
                print("Loading embedding models (this may take a moment)...")
                # Model 1: Standard, balanced (384 dims)
                model_1 = SentenceTransformer('all-MiniLM-L6-v2') 
                # Model 2: Faster, lighter (384 dims) - complying with "at least 2 models"
                model_2 = SentenceTransformer('paraphrase-MiniLM-L3-v2')
            else:
                model_1 = None
                model_2 = None

            # Create constraints/indexes for better performance
            print("Creating constraints and indexes...")

            # Create constraints for unique identifiers
            try:
                session.run("CREATE CONSTRAINT passenger_record_locator IF NOT EXISTS FOR (p:Passenger) REQUIRE p.record_locator IS UNIQUE")
            except Exception:
                pass

            try:
                session.run("CREATE CONSTRAINT journey_feedback_id IF NOT EXISTS FOR (j:Journey) REQUIRE j.feedback_ID IS UNIQUE")
            except Exception:
                pass

            try:
                session.run("CREATE CONSTRAINT airport_station_code IF NOT EXISTS FOR (a:Airport) REQUIRE a.station_code IS UNIQUE")
            except Exception:
                pass

            # Create Vector Indexes (if embeddings available)
            if EMBEDDINGS_AVAILABLE:
                try:
                    # Index for Model 1
                    session.run("""
                        CREATE VECTOR INDEX journey_embeddings_1 IF NOT EXISTS
                        FOR (j:Journey) ON (j.embedding_1)
                        OPTIONS {indexConfig: {
                            `vector.dimensions`: 384,
                            `vector.similarity_function`: 'cosine'
                        }}
                    """)
                    # Index for Model 2
                    session.run("""
                        CREATE VECTOR INDEX journey_embeddings_2 IF NOT EXISTS
                        FOR (j:Journey) ON (j.embedding_2)
                        OPTIONS {indexConfig: {
                            `vector.dimensions`: 384,
                            `vector.similarity_function`: 'cosine'
                        }}
                    """)
                    print("Vector indexes created.")
                except Exception as e:
                    print(f"Warning: Could not create vector indexes (check Neo4j version): {e}")

            # Read CSV data
            print(f"Reading CSV file: {csv_path}")
            rows = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Strip whitespace from column names and values
                    cleaned_row = {key.strip(): value.strip() for key, value in row.items()}
                    rows.append(cleaned_row)

            print(f"Found {len(rows)} records to process.")

            # Process data in batches
            batch_size = 500
            total_processed = 0

            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]

                # Prepare batch parameters with embeddings
                batch_params = []
                for row in batch:
                    # Clean numerical values
                    food_score = int(row['food_satisfaction_score']) if row['food_satisfaction_score'] else 0
                    delay = int(row['arrival_delay_minutes']) if row['arrival_delay_minutes'] else 0
                    
                    # Generate Text Description (Feature Vector approach)
                    text_desc = (
                        f"Journey from {row['origin_station_code']} to {row['destination_station_code']}. "
                        f"Class: {row['passenger_class']}. "
                        f"Flight: {row['flight_number']} ({row['fleet_type_description']}). "
                        f"Rating: {food_score}/5. "
                        f"Delay: {delay} mins. "
                        f"Loyalty: {row['loyalty_program_level']}."
                    )

                    params = {
                        'record_locator': row['record_locator'],
                        'loyalty_program_level': row['loyalty_program_level'],
                        'generation': row['generation'],
                        'feedback_ID': row['feedback_ID'],
                        'food_satisfaction_score': food_score,
                        'arrival_delay_minutes': delay,
                        'actual_flown_miles': int(row['actual_flown_miles']) if row['actual_flown_miles'] else 0,
                        'number_of_legs': int(row['number_of_legs']) if row['number_of_legs'] else 0,
                        'passenger_class': row['passenger_class'],
                        'flight_number': row['flight_number'],
                        'fleet_type_description': row['fleet_type_description'],
                        'origin_station_code': row['origin_station_code'],
                        'destination_station_code': row['destination_station_code'],
                        'text_representation': text_desc,
                        'embedding_1': None,
                        'embedding_2': None
                    }
                    
                    if EMBEDDINGS_AVAILABLE:
                        params['embedding_1'] = model_1.encode(text_desc).tolist()
                        params['embedding_2'] = model_2.encode(text_desc).tolist()
                    
                    batch_params.append(params)

                # Execute batch query
                for params in batch_params:
                    query = """
                    // Create or match Passenger node
                    MERGE (p:Passenger {record_locator: $record_locator})
                    ON CREATE SET p.loyalty_program_level = $loyalty_program_level,
                                  p.generation = $generation

                    // Create Journey node (unique by feedback_ID)
                    MERGE (j:Journey {feedback_ID: $feedback_ID})
                    ON CREATE SET j.food_satisfaction_score = $food_satisfaction_score,
                                  j.arrival_delay_minutes = $arrival_delay_minutes,
                                  j.actual_flown_miles = $actual_flown_miles,
                                  j.number_of_legs = $number_of_legs,
                                  j.passenger_class = $passenger_class,
                                  j.text = $text_representation,
                                  j.embedding_1 = $embedding_1,
                                  j.embedding_2 = $embedding_2

                    // Create or match Flight node (unique by both flight_number AND fleet_type_description)
                    MERGE (f:Flight {flight_number: $flight_number, fleet_type_description: $fleet_type_description})

                    // Create or match Airport nodes
                    MERGE (origin:Airport {station_code: $origin_station_code})
                    MERGE (dest:Airport {station_code: $destination_station_code})

                    // Create relationships
                    MERGE (p)-[:TOOK]->(j)
                    MERGE (j)-[:ON]->(f)
                    MERGE (f)-[:DEPARTS_FROM]->(origin)
                    MERGE (f)-[:ARRIVES_AT]->(dest)
                    """
                    session.run(query, params)

                total_processed += len(batch)
                print(f"Processed {total_processed}/{len(rows)} records...")

            # Print summary statistics
            print("\n" + "="*50)
            print("Knowledge Graph Creation Complete!")
            print("="*50)

            # Count nodes
            result = session.run("MATCH (p:Passenger) RETURN count(p) as count")
            passenger_count = result.single()["count"]

            result = session.run("MATCH (j:Journey) RETURN count(j) as count")
            journey_count = result.single()["count"]

            result = session.run("MATCH (f:Flight) RETURN count(f) as count")
            flight_count = result.single()["count"]

            result = session.run("MATCH (a:Airport) RETURN count(a) as count")
            airport_count = result.single()["count"]

            print(f"\nNode Statistics:")
            print(f"  - Passengers: {passenger_count}")
            print(f"  - Journeys: {journey_count}")
            print(f"  - Flights: {flight_count}")
            print(f"  - Airports: {airport_count}")

            # Count relationships
            result = session.run("MATCH ()-[r:TOOK]->() RETURN count(r) as count")
            took_count = result.single()["count"]

            result = session.run("MATCH ()-[r:ON]->() RETURN count(r) as count")
            on_count = result.single()["count"]

            result = session.run("MATCH ()-[r:DEPARTS_FROM]->() RETURN count(r) as count")
            departs_count = result.single()["count"]

            result = session.run("MATCH ()-[r:ARRIVES_AT]->() RETURN count(r) as count")
            arrives_count = result.single()["count"]

            print(f"\nRelationship Statistics:")
            print(f"  - TOOK: {took_count}")
            print(f"  - ON: {on_count}")
            print(f"  - DEPARTS_FROM: {departs_count}")
            print(f"  - ARRIVES_AT: {arrives_count}")

            print("\n" + "="*50)

    finally:
        driver.close()
        print("Neo4j connection closed.")


def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # File paths
    config_path = os.path.join(script_dir, 'config.txt')
    csv_path = os.path.join(script_dir, 'Airline_surveys_sample.csv')

    # Check if files exist
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    # Read configuration
    print("Reading configuration...")
    config = read_config(config_path)

    uri = config.get('URI', 'neo4j://localhost:7687')
    username = config.get('USERNAME', 'neo4j')
    password = config.get('PASSWORD', 'password')

    print(f"URI: {uri}")
    print(f"Username: {username}")

    # Create the Knowledge Graph
    try:
        create_knowledge_graph(uri, username, password, csv_path)
    except Exception as e:
        print(f"Error creating Knowledge Graph: {e}")
        raise


if __name__ == "__main__":
    main()
