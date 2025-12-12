"""
LLM Layer for Graph-RAG Airline Assistant
Combines KG results and queries multiple LLMs for comparison
"""

import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMLayer:
    def __init__(self):
        """Initialize LLM layer with GROQ API"""
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")

        self.client = Groq(api_key=api_key)

        # Three different models for comparison
        self.models = {
            "llama-3.3-70b": "llama-3.3-70b-versatile",        # Meta Llama 3.3 (70B)
            "llama-3.1-8b": "llama-3.1-8b-instant",            # Meta Llama 3.1 (8B)
            "qwen-3-32b": "qwen/qwen3-32b"                     # Alibaba Qwen 3 (32B)
        }

        # Persona for airline assistant
        self.persona = """You are a helpful Airline Company Flight Insights Assistant.
Your role is to provide accurate, data-driven insights about flights, routes, passenger satisfaction,
and journey analysis to help airline management make informed decisions."""

    def format_context(self, kg_results_baseline, kg_results_embeddings=None):
        """
        Combine baseline and embedding results into structured context

        Args:
            kg_results_baseline: Results from Cypher queries (baseline)
            kg_results_embeddings: Results from embedding-based retrieval (optional)

        Returns:
            Formatted context string
        """
        context = "=== KNOWLEDGE GRAPH CONTEXT ===\n\n"

        # Add baseline results
        if kg_results_baseline:
            context += "** Baseline Query Results **\n"
            context += json.dumps(kg_results_baseline, indent=2, default=str)
            context += "\n\n"

        # Add embedding results if available
        if kg_results_embeddings:
            context += "** Embedding-Based Results **\n"
            context += json.dumps(kg_results_embeddings, indent=2, default=str)
            context += "\n\n"

        if not kg_results_baseline and not kg_results_embeddings:
            context += "No relevant data found in the knowledge graph.\n"

        return context

    def create_prompt(self, user_query, context):
        """
        Create structured prompt with Context + Persona + Task

        Args:
            user_query: Original user question
            context: Formatted KG context

        Returns:
            Complete prompt string
        """
        prompt = f"""
{self.persona}

{context}

=== TASK ===
Answer the following question using ONLY the information provided in the Knowledge Graph context above.
If the context doesn't contain enough information to answer, say so clearly.
Be concise, factual, and data-driven in your response.

USER QUESTION: {user_query}

YOUR ANSWER:"""

        return prompt

    def query_llm(self, model_name, model_id, prompt):
        """
        Query a single LLM model

        Args:
            model_name: Display name of the model
            model_id: GROQ model identifier
            prompt: The complete prompt

        Returns:
            Dictionary with response details
        """
        try:
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=500
            )

            end_time = time.time()

            return {
                "model": model_name,
                "answer": response.choices[0].message.content,
                "response_time": round(end_time - start_time, 2),
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "success": True
            }

        except Exception as e:
            return {
                "model": model_name,
                "answer": f"Error: {str(e)}",
                "response_time": 0,
                "tokens_used": 0,
                "success": False
            }

    def compare_models(self, user_query, kg_results_baseline, kg_results_embeddings=None):
        """
        Query all three models and return comparison

        Args:
            user_query: User's question
            kg_results_baseline: Baseline retrieval results
            kg_results_embeddings: Embedding retrieval results (optional)

        Returns:
            Dictionary with all model responses and comparison metrics
        """
        # Step 1: Format context
        context = self.format_context(kg_results_baseline, kg_results_embeddings)

        # Step 2: Create prompt
        prompt = self.create_prompt(user_query, context)

        # Step 3: Query all models
        print("\n[LLM] Querying multiple models...")
        results = []

        for model_name, model_id in self.models.items():
            print(f"   -> Querying {model_name}...")
            result = self.query_llm(model_name, model_id, prompt)
            results.append(result)

        # Step 4: Compile comparison
        comparison = {
            "user_query": user_query,
            "context_length": len(context),
            "prompt_length": len(prompt),
            "model_responses": results,
            "summary": {
                "total_models": len(results),
                "successful_responses": sum(1 for r in results if r["success"]),
                "avg_response_time": round(sum(r["response_time"] for r in results) / len(results), 2),
                "total_tokens": sum(r["tokens_used"] or 0 for r in results)
            }
        }

        return comparison

    def print_comparison(self, comparison):
        """Pretty print the model comparison"""
        print("\n" + "="*70)
        print("LLM COMPARISON RESULTS")
        print("="*70)

        for i, response in enumerate(comparison["model_responses"], 1):
            print(f"\n[Model {i}: {response['model']}]")
            print(f"Response Time: {response['response_time']}s")
            if response['tokens_used']:
                print(f"Tokens Used: {response['tokens_used']}")
            print(f"\nAnswer:\n{response['answer']}\n")
            print("-"*70)

        print(f"\n=== SUMMARY ===")
        print(f"Average Response Time: {comparison['summary']['avg_response_time']}s")
        print(f"Total Tokens Used: {comparison['summary']['total_tokens']}")
        print(f"Successful Responses: {comparison['summary']['successful_responses']}/{comparison['summary']['total_models']}")


# Simple test function
if __name__ == "__main__":
    # Test the LLM layer
    llm = LLMLayer()

    # Dummy test data
    test_query = "What flights have the most delays?"
    test_kg_results = [
        {"flight": "AA123", "delay_minutes": 45, "origin": "LAX", "destination": "JFK"},
        {"flight": "UA456", "delay_minutes": 120, "origin": "ORD", "destination": "SFO"}
    ]

    comparison = llm.compare_models(test_query, test_kg_results)
    llm.print_comparison(comparison)
