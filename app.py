"""
Streamlit UI for Airline Graph-RAG System
Milestone 3 - German University in Cairo
"""

import streamlit as st
import json
import sys
import os
from typing import Dict, Any, List

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from input_preprocessor import InputPreprocessor
from graph_retrieval import GraphRetriever

# Page configuration
st.set_page_config(
    page_title="Airline Graph-RAG Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Minimalistic Design
st.markdown("""
<style>
    /* Global minimalist styling */
    .main {
        background-color: #ffffff;
    }
    
    .main-header {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .section-header {
        background-color: #3333;
        color: #fff;
        padding: 12px 16px;
        border-radius: 6px;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-left: 3px solid #e5e7eb;
    }
    .section-header h3 {
        color: #ffffff !important;
        margin: 0;
        font-weight: 600;
        font-size: 1.1rem;
    }
    .result-box {
        background-color: #1a1a1a;
        padding: 10px 14px;
        border-radius: 6px;
        border: 1px solid #333333;
        margin-bottom: 3px;
        transition: border-color 0.2s;
    }
    .result-box:hover {
        border-color: #444444;
    }
    .result-box p {
        color: #ffffff !important;
        margin: 4px 0 !important;
        line-height: 1.4;
    }
    .result-box strong {
        color: #ffffff !important;
    }
    .cypher-box {
        background-color: #f9fafb;
        color: #374151;
        padding: 16px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        border: 1px solid #e5e7eb;
        overflow-x: auto;
    }
    .placeholder-box {
        background-color: #fefce8;
        padding: 16px;
        border-radius: 6px;
        border-left: 3px solid #fbbf24;
        border: 1px solid #fde68a;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
    }
    
    /* Sidebar - Black minimalist */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #1a1a1a;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #333333 !important;
    }
    /* Sidebar buttons styling */
    [data-testid="stSidebar"] .stButton>button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #2a2a2a !important;
        border-color: #444444 !important;
    }
    
    /* Primary CTA Button - BlueViolet Gradient */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 4px 12px rgba(67, 56, 202, 0.3);
        transform: translateY(-1px);
    }
    
    /* Secondary Buttons - Gray/White */
    .stButton>button:not([kind="primary"]) {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s;
    }
    .stButton>button:not([kind="primary"]):hover {
        background-color: #e5e7eb;
        border-color: #d1d5db;
    }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f3f4f6;
        border-radius: 6px 6px 0 0;
        border: 1px solid #e5e7eb;
        padding: 8px 16px;
        color: #6b7280;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%);
        color: white !important;
        border-color: transparent;
    }
    .stTabs [data-baseweb="tab"] p {
        color: inherit !important;
    }
    /* Hide dividers after results */
    .element-container + hr {
        display: none;
    }
    hr {
        margin: 0.5rem 0;
        border-color: #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'preprocessor' not in st.session_state:
    try:
        st.session_state.preprocessor = InputPreprocessor()
        st.session_state.retriever = GraphRetriever()
        st.session_state.initialized = True
    except Exception as e:
        st.session_state.initialized = False
        st.session_state.error = str(e)

if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Sidebar
with st.sidebar:
    # System Status (First)
    st.markdown("### 📊 System Status")
    if st.session_state.initialized:
        st.success("✅ System Ready")
        st.metric("Knowledge Graph", "Connected")
        st.metric("Preprocessor", "Active")
    else:
        st.error("❌ System Error")
        st.error(st.session_state.get('error', 'Unknown error'))
    
    st.markdown("---")
    
    # Quick Examples (Second)
    st.markdown("### 📚 Quick Examples")
    example_queries = [
        "Show flights from LAX to ORX",
        "Which flights have the most delays?",
        "Show routes from EWX",
        "What are the highest rated journeys?",
        "Find flights with good food ratings"
    ]
    
    for example in example_queries:
        if st.button(example, key=f"example_{example}", use_container_width=True):
            st.session_state.example_query = example
    
    st.markdown("---")
    
    # Configuration (Third)
    st.markdown("## ⚙️ Configuration")
    
    # Retrieval Method Selection
    st.markdown("### 🔍 Retrieval Method")
    retrieval_method = st.radio(
        "Select retrieval method",
        ["Baseline (Cypher)", "Embeddings (Vector Search)", "Hybrid (Both)"],
        help="Choose how to retrieve information from the Knowledge Graph"
    )
    
    # LLM Model Selection (Placeholder)
    st.markdown("### 🤖 LLM Model (Coming Soon)")
    llm_model = st.selectbox(
        "Select LLM Model",
        ["Gemma-2-2b", "Llama-3.3-70b", "Mistral-7b"],
        disabled=True,
        help="LLM integration pending - will be available soon"
    )

# Main content
st.markdown('<div class="main-header">✈️ Airline Graph-RAG Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Airline Company Flight Insights System | Milestone 3</div>', unsafe_allow_html=True)

if not st.session_state.initialized:
    st.error("⚠️ System initialization failed. Please check your configuration.")
    st.error(f"Error details: {st.session_state.get('error', 'Unknown error')}")
    st.info("Make sure Neo4j is running and Create_kg.py has been executed.")
    st.stop()

# Query Input
st.markdown("## 💬 Enter Your Query")
query_input = st.text_area(
    "Ask a question about flights, routes, delays, or passenger satisfaction:",
    value=st.session_state.get('example_query', ''),
    height=100,
    placeholder="Example: Show me flights from LAX with minimal delays"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

if clear_button:
    st.session_state.example_query = ""
    st.rerun()

if search_button and query_input:
    with st.spinner("Processing your query..."):
        
        # Step 1: Input Preprocessing
        st.markdown('<div class="section-header"><h3>📝 Step 1: Input Preprocessing</h3></div>', unsafe_allow_html=True)
        
        try:
            parsed_input = st.session_state.preprocessor.process_query(query_input)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎯 Intent Classification")
                st.info(f"**Detected Intent:** `{parsed_input['intent']}`")
            
            with col2:
                st.markdown("#### 🏷️ Extracted Entities")
                entities = parsed_input.get('entities', {})
                
                # Display entities in a clean format
                entity_display = []
                if entities.get('flights'):
                    entity_display.append(f"**Flights:** {', '.join(entities['flights'])}")
                if entities.get('airports', {}).get('departure'):
                    entity_display.append(f"**From:** {entities['airports']['departure']}")
                if entities.get('airports', {}).get('arrival'):
                    entity_display.append(f"**To:** {entities['airports']['arrival']}")
                if entities.get('attributes'):
                    entity_display.append(f"**Filters:** {', '.join(entities['attributes'])}")
                
                if entity_display:
                    st.markdown("<br>".join(entity_display), unsafe_allow_html=True)
                else:
                    st.info("No specific entities extracted")
            
            # Show full parsed data in expander
            with st.expander("🔍 View Full Parsed Data (JSON)"):
                st.json(parsed_input)
            
            # Step 2: Graph Retrieval
            st.markdown('<div class="section-header"><h3>🔎 Step 2: Graph Retrieval Layer</h3></div>', unsafe_allow_html=True)
            
            baseline_results = []
            embedding_results = []
            cypher_query = ""
            
            # Baseline Retrieval
            if retrieval_method in ["Baseline (Cypher)", "Hybrid (Both)"]:
                st.markdown("#### 📊 Baseline Retrieval (Cypher Queries)")
                
                cypher_query = st.session_state.retriever.generate_cypher_baseline(parsed_input)
                
                with st.expander("📜 View Generated Cypher Query"):
                    st.markdown(f'<div class="cypher-box">{cypher_query}</div>', unsafe_allow_html=True)
                
                baseline_results = st.session_state.retriever.run_search(parsed_input)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Records Found", len(baseline_results))
                with col2:
                    if baseline_results:
                        st.success(f"✅ Retrieved {len(baseline_results)} records from Knowledge Graph")
                    else:
                        st.warning("⚠️ No results found with baseline retrieval")
            
            # Embedding-based Retrieval
            if retrieval_method in ["Embeddings (Vector Search)", "Hybrid (Both)"]:
                st.markdown("#### 🧠 Embedding-based Retrieval (Semantic Search)")
                
                embedding_results = st.session_state.retriever.vector_search(query_input, limit=5)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Similar Journeys", len(embedding_results))
                with col2:
                    if embedding_results:
                        st.success(f"✅ Found {len(embedding_results)} semantically similar journeys")
                    else:
                        st.warning("⚠️ No similar journeys found")
            
            # Step 3: Display Retrieved Context
            st.markdown('<div class="section-header"><h3>📦 Step 3: Retrieved Knowledge Graph Context</h3></div>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["📊 Baseline Results", "🧠 Embedding Results"])
            
            with tab1:
                if baseline_results:
                    st.markdown(f"<p style='color: #ffffff; background-color: #1a1a1a; padding: 8px 12px; border-radius: 4px; margin-bottom: 8px;'><strong>Found {len(baseline_results)} records:</strong></p>", unsafe_allow_html=True)
                    
                    # Display results in a nice table format
                    for idx, result in enumerate(baseline_results[:10], 1):
                        with st.container():
                            st.markdown(f'<div class="result-box">', unsafe_allow_html=True)
                            st.markdown(f"<p style='color: #ffffff; margin: 0;'><strong>Result {idx}:</strong></p>", unsafe_allow_html=True)
                            
                            # Format the result nicely
                            for key, value in result.items():
                                if value is not None:
                                    st.markdown(f"<p style='color: #ffffff; margin: 2px 0; font-size: 0.9rem;'>• <strong>{key}:</strong> {value}</p>", unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    if len(baseline_results) > 10:
                        st.info(f"Showing first 10 of {len(baseline_results)} results")
                    
                    # Download option
                    st.download_button(
                        "📥 Download Results (JSON)",
                        data=json.dumps(baseline_results, indent=2, default=str),
                        file_name="baseline_results.json",
                        mime="application/json"
                    )
                else:
                    st.info("No baseline results to display")
            
            with tab2:
                if embedding_results:
                    st.markdown(f"<p style='color: #ffffff; background-color: #1a1a1a; padding: 8px 12px; border-radius: 4px; margin-bottom: 8px;'><strong>Found {len(embedding_results)} similar journeys:</strong></p>", unsafe_allow_html=True)
                    
                    for idx, result in enumerate(embedding_results, 1):
                        with st.container():
                            st.markdown(f'<div class="result-box">', unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"<p style='color: #ffffff; margin: 0; font-size: 0.9rem;'><strong>Journey {idx}:</strong> {result.get('description', 'N/A')[:150]}...</p>", unsafe_allow_html=True)
                            with col2:
                                similarity = result.get('score', 0)
                                st.metric("Similarity", f"{similarity:.3f}")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"<p style='color: #ffffff; margin: 4px 0; font-size: 0.85rem;'><strong>Food Rating:</strong> {result.get('food_rating', 'N/A')}/5</p>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"<p style='color: #ffffff; margin: 4px 0; font-size: 0.85rem;'><strong>Delay:</strong> {result.get('delay', 'N/A')} min</p>", unsafe_allow_html=True)
                            with col3:
                                st.markdown(f"<p style='color: #ffffff; margin: 4px 0; font-size: 0.85rem;'><strong>ID:</strong> {result.get('id', 'N/A')}</p>", unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Download option
                    st.download_button(
                        "📥 Download Results (JSON)",
                        data=json.dumps(embedding_results, indent=2, default=str),
                        file_name="embedding_results.json",
                        mime="application/json"
                    )
                else:
                    st.info("No embedding results to display")
            
            # Step 4: LLM Response (Placeholder)
            st.markdown('<div class="section-header"><h3>🤖 Step 4: LLM-Generated Answer</h3></div>', unsafe_allow_html=True)
            
            st.markdown('<div class="placeholder-box">', unsafe_allow_html=True)
            st.markdown("### 🚧 LLM Integration - Coming Soon")
            st.markdown("""
            **What will happen here:**
            1. The retrieved context from Steps 2-3 will be combined
            2. A structured prompt will be created with:
               - **Context:** KG results (baseline + embeddings)
               - **Persona:** "You are an airline insights assistant"
               - **Task:** "Answer the question using only the provided data"
            3. Multiple LLM models will generate answers (Gemma, Llama, Mistral)
            4. Responses will be compared for quality and accuracy
            
            **Current Status:** Waiting for LLM layer implementation
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Placeholder for LLM response
            with st.expander("💡 Example LLM Response (Mock)"):
                st.markdown("""
                **Mock Answer:**
                
                Based on the Knowledge Graph data:
                - Found {} flight records matching your query
                - Average delay: [To be calculated]
                - Most common route: [To be determined]
                - Passenger satisfaction: [To be analyzed]
                
                *This is a placeholder. Actual LLM will provide detailed, context-aware answers.*
                """.format(len(baseline_results)))
            
            # Save to history
            st.session_state.query_history.append({
                'query': query_input,
                'intent': parsed_input['intent'],
                'baseline_count': len(baseline_results),
                'embedding_count': len(embedding_results)
            })
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            st.exception(e)

# Query History
if st.session_state.query_history:
    with st.expander("📜 Query History"):
        for idx, item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            st.markdown(f"**{idx}.** {item['query']} - Intent: `{item['intent']}` - Results: {item['baseline_count']} baseline, {item['embedding_count']} embedding")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Milestone 3 - GUC**")
with col2:
    st.markdown("**Team 50 - Airline Theme**")
with col3:
    st.markdown("**Graph-RAG System**")
