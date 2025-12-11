"""
LLM Comparison Logger - For documentation and presentation
Saves comparison results for analysis
"""

import json
import os
from datetime import datetime

class ComparisonLogger:
    def __init__(self, output_dir="llm_comparisons"):
        """Initialize logger with output directory"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def log_comparison(self, comparison, notes=""):
        """
        Log a comparison result to file

        Args:
            comparison: The comparison dict from LLMLayer
            notes: Optional notes about the query/test
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/comparison_{timestamp}.json"

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "query": comparison["user_query"],
            "notes": notes,
            "summary": comparison["summary"],
            "responses": [
                {
                    "model": r["model"],
                    "answer": r["answer"],
                    "response_time": r["response_time"],
                    "tokens_used": r["tokens_used"],
                    "success": r["success"]
                }
                for r in comparison["model_responses"]
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)

        print(f"\n✓ Comparison logged to: {filename}")
        return filename

    def generate_summary_report(self):
        """Generate a summary report from all logged comparisons"""
        files = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]

        if not files:
            print("No comparison logs found.")
            return

        print("\n" + "="*70)
        print("LLM COMPARISON SUMMARY REPORT")
        print("="*70)

        total_queries = len(files)
        model_stats = {}

        for filename in files:
            with open(os.path.join(self.output_dir, filename), 'r') as f:
                data = json.load(f)

            for response in data["responses"]:
                model = response["model"]
                if model not in model_stats:
                    model_stats[model] = {
                        "total_queries": 0,
                        "successful": 0,
                        "total_time": 0,
                        "total_tokens": 0
                    }

                model_stats[model]["total_queries"] += 1
                if response["success"]:
                    model_stats[model]["successful"] += 1
                model_stats[model]["total_time"] += response["response_time"]
                model_stats[model]["total_tokens"] += response["tokens_used"] or 0

        print(f"\nTotal Test Queries: {total_queries}")
        print("\n" + "-"*70)

        for model, stats in model_stats.items():
            print(f"\n[{model}]")
            print(f"  Success Rate: {stats['successful']}/{stats['total_queries']} ({stats['successful']/stats['total_queries']*100:.1f}%)")
            print(f"  Avg Response Time: {stats['total_time']/stats['total_queries']:.2f}s")
            print(f"  Total Tokens Used: {stats['total_tokens']}")

        print("\n" + "="*70)

        # Save report
        report_file = f"{self.output_dir}/summary_report.txt"
        with open(report_file, 'w') as f:
            f.write("LLM COMPARISON SUMMARY\n")
            f.write("="*70 + "\n\n")
            f.write(f"Total Test Queries: {total_queries}\n\n")
            for model, stats in model_stats.items():
                f.write(f"[{model}]\n")
                f.write(f"  Success Rate: {stats['successful']}/{stats['total_queries']}\n")
                f.write(f"  Avg Response Time: {stats['total_time']/stats['total_queries']:.2f}s\n")
                f.write(f"  Total Tokens: {stats['total_tokens']}\n\n")

        print(f"\n✓ Summary report saved to: {report_file}")


# Quick test
if __name__ == "__main__":
    logger = ComparisonLogger()
    print("Comparison logger ready.")
    print(f"Logs will be saved to: {logger.output_dir}/")
