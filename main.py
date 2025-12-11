import json
import os
import sys

# Add current directory to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from input_preprocessor import InputPreprocessor
    from graph_retrieval import GraphRetriever
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def main():
    print("--- Airline Graph-RAG System ---")
    
    # 1. Initialize Modules
    try:
        preprocessor = InputPreprocessor()
        print("Input Preprocessor initialized.")
    except Exception as e:
        print(f"Failed to initialize Input Preprocessor: {e}")
        return

    try:
        retriever = GraphRetriever()
        print("Graph Retriever initialized.")
    except Exception as e:
        print(f"Failed to initialize Graph Retriever: {e}")
        return



    # 2. Main Loop
    while True:
        try:
            user_query = input("\nEnter your query (or 'exit' to quit): ")
            if user_query.lower() in ['exit', 'quit']:
                break
            
            if not user_query.strip():
                continue

            # --- Step 1: Pre-processing (Task 1) ---
            print("\n[1] Processing Query...")
            structured_data = preprocessor.process_query(user_query)
            print(json.dumps(structured_data, indent=2))

            # --- Step 2: Graph Retrieval (Task 2 - Baseline) ---
            print("\n[2] Generating Cypher & Retrieving...")
            results = retriever.run_search(structured_data)
            print(f"   -> Found {len(results)} records.")

            # --- Step 3: Response (Raw Output) ---
            print(f"\n[3] Results Found: {len(results)}")
            if results:
                print(json.dumps(results, indent=2, default=str))
            else:
                print("No results found.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")

    retriever.close()
    print("\nSystem closed.")

if __name__ == "__main__":
    main()
