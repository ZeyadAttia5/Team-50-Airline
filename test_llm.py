"""
Quick Test Script for LLM Layer
Run this to test your LLM implementation without the full pipeline
"""

from llm_layer import LLMLayer
from llm_comparison_logger import ComparisonLogger

def main():
    print("=== LLM Layer Test ===\n")

    # Initialize
    llm = LLMLayer()
    logger = ComparisonLogger()

    # Test queries with dummy KG data
    test_cases = [
        {
            "query": "Which flights have the most delays?",
            "kg_results": [
                {"flight_number": "2411", "origin": "LAX", "destination": "IAX", "arrival_delay_minutes": 177},
                {"flight_number": "924", "origin": "LAX", "destination": "LHX", "arrival_delay_minutes": -29},
                {"flight_number": "659", "origin": "EWX", "destination": "IAX", "arrival_delay_minutes": 177}
            ],
            "notes": "Testing delay analysis"
        },
        {
            "query": "What's the average food satisfaction score?",
            "kg_results": [
                {"flight_number": "2411", "food_satisfaction_score": 3},
                {"flight_number": "924", "food_satisfaction_score": 1},
                {"flight_number": "659", "food_satisfaction_score": 1}
            ],
            "notes": "Testing satisfaction metrics"
        }
    ]

    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST CASE {i}: {test['query']}")
        print(f"{'='*70}")

        comparison = llm.compare_models(
            test["query"],
            test["kg_results"]
        )

        llm.print_comparison(comparison)

        # Log the result
        logger.log_comparison(comparison, notes=test["notes"])

        input("\nPress Enter to continue to next test...")

    # Generate summary
    print("\n\nGenerating summary report...")
    logger.generate_summary_report()

    print("\n✓ All tests complete!")
    print("\nCheck the 'llm_comparisons' folder for detailed logs.")


if __name__ == "__main__":
    main()
