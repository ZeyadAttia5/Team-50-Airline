"""
Neo4j Knowledge Graph Verification Script
Runs the 5 verification queries from the PDF document
"""

import os
from neo4j import GraphDatabase


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


def run_verification_queries(uri, username, password):
    """Run all 5 verification queries"""

    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session() as session:
            print("\n" + "="*60)
            print("KNOWLEDGE GRAPH VERIFICATION QUERIES")
            print("="*60)

            # Query 1: Top 5 routes by flight count
            print("\n" + "-"*60)
            print("Query 1: Top 5 airport-to-airport routes by flight count")
            print("-"*60)

            query1 = """
            MATCH (origin:Airport)<-[:DEPARTS_FROM]-(f:Flight)-[:ARRIVES_AT]->(dest:Airport)
            RETURN origin.station_code AS origin,
                   dest.station_code AS destination,
                   count(f) AS flight_count
            ORDER BY flight_count DESC, destination ASC
            LIMIT 5
            """

            result = session.run(query1)
            records = list(result)

            print(f"{'Origin':<10} {'Destination':<15} {'Flight Count':<15}")
            print("-" * 40)
            for record in records:
                print(f"{record['origin']:<10} {record['destination']:<15} {record['flight_count']:<15}")

            # Query 2: Top 10 flights by passenger feedback count
            print("\n" + "-"*60)
            print("Query 2: Top 10 flights with most passenger feedback")
            print("-"*60)

            query2 = """
            MATCH (j:Journey)-[:ON]->(f:Flight)
            RETURN toInteger(f.flight_number) AS flight_id,
                   count(j) AS feedback_count
            ORDER BY feedback_count DESC
            LIMIT 10
            """

            result = session.run(query2)
            records = list(result)

            print(f"{'Flight ID':<15} {'Feedback Count':<15}")
            print("-" * 30)
            for record in records:
                print(f"{record['flight_id']:<15} {record['feedback_count']:<15}")

            # Query 3: Multi-leg journey food satisfaction by generation
            print("\n" + "-"*60)
            print("Query 3: Average food satisfaction for multi-leg journeys by generation")
            print("-"*60)

            query3 = """
            MATCH (p:Passenger)-[:TOOK]->(j:Journey)
            WHERE j.number_of_legs > 1
            RETURN p.generation AS generation,
                   count(j) AS multi_leg_count,
                   avg(j.food_satisfaction_score) AS avg_score
            ORDER BY multi_leg_count DESC
            """

            result = session.run(query3)
            records = list(result)

            print(f"{'Generation':<15} {'Multi-leg Count':<18} {'Avg Score':<10}")
            print("-" * 43)
            for record in records:
                print(f"{record['generation']:<15} {record['multi_leg_count']:<18} {record['avg_score']:<10}")

            # Query 4: Top 10 flights with shortest delays
            print("\n" + "-"*60)
            print("Query 4: Top 10 flights with shortest average arrival delays")
            print("-"*60)

            query4 = """
            MATCH (j:Journey)-[:ON]->(f:Flight)
            RETURN toInteger(f.flight_number) AS flight_id,
                   avg(j.arrival_delay_minutes) AS avg_arrival_delay
            ORDER BY avg_arrival_delay ASC
            LIMIT 10
            """

            result = session.run(query4)
            records = list(result)

            print(f"{'Flight ID':<15} {'Avg Arrival Delay':<20}")
            print("-" * 35)
            for record in records:
                print(f"{record['flight_id']:<15} {record['avg_arrival_delay']:<20}")

            # Query 5: Average flown miles by loyalty level
            print("\n" + "-"*60)
            print("Query 5: Average flown miles by loyalty program level")
            print("-"*60)

            query5 = """
            MATCH (p:Passenger)-[:TOOK]->(j:Journey)
            RETURN p.loyalty_program_level AS loyalty_level,
                   round(avg(j.actual_flown_miles) * 100) / 100 AS avg_actual_flown_miles
            ORDER BY avg_actual_flown_miles DESC
            """

            result = session.run(query5)
            records = list(result)

            print(f"{'Loyalty Level':<20} {'Avg Flown Miles':<20}")
            print("-" * 40)
            for record in records:
                print(f"{record['loyalty_level']:<20} {record['avg_actual_flown_miles']:<20}")

            print("\n" + "="*60)
            print("VERIFICATION COMPLETE")
            print("="*60)

    finally:
        driver.close()
        print("\nNeo4j connection closed.")


def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Config file path
    config_path = os.path.join(script_dir, 'config.txt')

    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        return

    # Read configuration
    print("Reading configuration...")
    config = read_config(config_path)

    uri = config.get('URI', 'neo4j://localhost:7687')
    username = config.get('USERNAME', 'neo4j')
    password = config.get('PASSWORD', 'password')

    # Run verification queries
    try:
        run_verification_queries(uri, username, password)
    except Exception as e:
        print(f"Error running queries: {e}")
        raise


if __name__ == "__main__":
    main()
