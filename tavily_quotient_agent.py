#!/usr/bin/env python3
"""
Build and Monitor a Web Research Agent with Tavily, OpenAI, LangChain & Quotient

This script shows how to build a LangChain-based research assistant powered by Tavily and OpenAI.
The agent answers real-world search queries using live web content via Tavily tools, and is monitored
using Quotient AI to detect hallucinations, irrelevant retrievals, and other failure modes.
"""

import os
import json
import datetime
from typing import List, Dict, Any
from tqdm import tqdm

# LangChain imports
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch, TavilyExtract
from langchain.schema import HumanMessage

from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.instrumentation.openai import OpenAIInstrumentor

# Quotient AI import
from quotientai import QuotientAI



def create_research_agent(model: str = "gpt-4o") -> AgentExecutor:
    """
    Create a LangChain research agent with Tavily tools.
    
    Args:
        model: The OpenAI model to use (default: "gpt-4o")
    
    Returns:
        AgentExecutor: Configured agent executor
    """
    # Initialize LLM and tools
    llm = ChatOpenAI(model=model, temperature=0)
    tools = [TavilySearch(max_results=5, topic="general"), TavilyExtract()]
    
    # Set up prompt with 'agent_scratchpad'
    today = datetime.datetime.today().strftime("%B %d, %Y")
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful research assistant. You'll be given a query and should search the web, extract relevant content, and summarize insights. Today is {today}."""),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create agent + executor
    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)
    
    return agent_executor


def initialize_quotient(app_name: str = "tavily-agent", environment: str = "test") -> QuotientAI:
    """
    Initialize the Quotient SDK for monitoring.
    
    Args:
        app_name: Name of the application
        environment: Environment (e.g., "dev", "prod", "staging")
    
    Returns:
        QuotientAI: Initialized Quotient instance
    """
    quotient = QuotientAI()
    
    quotient.logger.init(
        app_name=app_name,
        environment=environment,
        sample_rate=1.0,
        hallucination_detection=True,
        hallucination_detection_sample_rate=1.0,
    )
    
    return quotient


def extract_documents_from_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract documents from the agent response.
    
    Args:
        response: The response from the agent executor
    
    Returns:
        List of document dictionaries with page_content and metadata
    """
    documents = []
    
    for step in response.get("intermediate_steps", []):
        tool_call, tool_output = step
        
        # Handle tavily_extract (advanced search) - full content
        if getattr(tool_call, "tool", "") == "tavily_extract":
            for result in tool_output['results']:
                doc = {
                    "page_content": result.get('raw_content', ''),
                    "metadata": {"source": result.get('url', '')}
                }
                documents.append(doc)
        
        # Handle tavily_search (basic search) - snippets only
        elif getattr(tool_call, "tool", "") == "tavily_search":
            for result in tool_output['results']:
                doc = {
                    "page_content": result.get('content', ''),
                    "metadata": {"source": result.get('url', '')}
                }
                documents.append(doc)
    
    return documents


def load_queries_from_file(file_path: str) -> List[str]:
    """
    Load queries from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file containing queries
    
    Returns:
        List of query strings
    """
    with open(file_path) as f:
        queries = [json.loads(line)["question"] for line in f]
    return queries


def run_queries_and_log(agent_executor: AgentExecutor, quotient: QuotientAI, 
                       queries: List[str], model: str, num_queries: int = 10) -> List[str]:
    """
    Run queries through the agent and log responses to Quotient.
    
    Args:
        agent_executor: The configured agent executor
        quotient: Initialized Quotient instance
        queries: List of queries to process
        model: Model name for tagging
        num_queries: Number of queries to process (default: 10)
    
    Returns:
        List of log IDs from Quotient
    """
    log_ids = []
    
    for i, query in enumerate(queries[:num_queries]):
        print(f"\nProcessing query {i+1}/{min(num_queries, len(queries))}")
        
        # Invoke the agent
        response = agent_executor.invoke({"messages": [HumanMessage(content=query)]})
        model_output = response['output']
        
        print(f"🧠 {query}")
        print(f"➡️ {response['output']}")
        
        # Extract documents from the response
        documents = extract_documents_from_response(response)
        print(f"📄 Found {len(documents)} documents")
        
        # Log to Quotient
        # log_id = quotient.log(
        #     user_query=query,
        #     model_output=model_output,
        #     documents=documents,
        #     tags={'model': model},
        # )
        
        # print(f"📝 Logged to Quotient with log_id: {log_id}")
        # log_ids.append(log_id)
    
    return log_ids


def fetch_detection_results(quotient: QuotientAI, log_ids: List[str]) -> Dict[str, float]:
    """
    Fetch detection results from Quotient.
    
    Args:
        quotient: Initialized Quotient instance
        log_ids: List of log IDs to fetch results for
    
    Returns:
        Dictionary with hallucination percentage and document relevancy percentage
    """
    hallucination_detections = []
    doc_relevancy_detections = []
    
    for log_id in tqdm(log_ids, desc="Fetching detection results"):
        try:
            detection = quotient.poll_for_detection(log_id=log_id)
            # Add the hallucination detection
            hallucination_detections.append(detection.has_hallucination)
            # Add the document relevancy detection
            docs = detection.log_documents
            doc_relevancy_detections.append(
                sum(1 for doc in docs if doc.get('is_relevant') is True) / len(docs) if docs else None
            )
        except Exception as e:
            print(f"Error fetching detection for log_id {log_id}: {e}")
            continue
    
    # Calculate percentages
    hallucination_percentage = (sum(hallucination_detections) / len(hallucination_detections) * 100) if hallucination_detections else 0
    doc_relevancy_percentage = (sum(doc_relevancy_detections) / len(doc_relevancy_detections) * 100) if doc_relevancy_detections else 0
    
    return {
        'hallucination_percentage': hallucination_percentage,
        'doc_relevancy_percentage': doc_relevancy_percentage,
        'total_results': len(log_ids)
    }


from quotientai import QuotientAI

quotient = QuotientAI()
quotient.tracer.init(
    app_name="tavily-quotient-agent",
    environment="local",
    instruments=[OpenAIInstrumentor(), LangChainInstrumentor()],
    detections_array=[
        "hallucination_detection",
        "document_relevancy_detection",
    ],
)

@quotient.trace()
def main():
    """Main function to run the Tavily-Quotient research agent."""
    
    # File containing queries (create this file with your queries)
    QUERIES_FILE = "search_queries.jsonl"
    
    # Number of queries to process
    NUM_QUERIES = 1
    
    # Model to use
    MODEL = "gpt-4o"
    
    print("🚀 Initializing Tavily-Quotient Research Agent...")
    
    # Step 1: Create research agent
    print("📚 Creating research agent...")
    agent_executor = create_research_agent(MODEL)
    
    # Step 2: Initialize Quotient
    print("📊 Initializing Quotient monitoring...")
    # quotient = initialize_quotient()
    
    # Step 3: Load queries
    print(f"📖 Loading queries from {QUERIES_FILE}...")
    try:
        queries = load_queries_from_file(QUERIES_FILE)
        print(f"Loaded {len(queries)} queries")
    except FileNotFoundError:
        print(f"❌ Error: {QUERIES_FILE} not found. Please create this file with your queries.")
        print("Example format for search_queries.jsonl:")
        print('{"question": "What are the latest AI trends?"}')
        return
    
    # Step 4: Run queries and log to Quotient
    print(f"🔍 Running {NUM_QUERIES} queries through the agent...")
    log_ids = run_queries_and_log(agent_executor, quotient, queries, MODEL, NUM_QUERIES)
    
    # Step 5: Fetch detection results
    print("📈 Fetching detection results from Quotient...")
    # results = fetch_detection_results(quotient, log_ids)
    
    # Step 6: Print summary
    print("\n" + "="*50)
    print("📊 RESULTS SUMMARY")
    print("="*50)
    # print(f"Number of results: {results['total_results']}")
    # print(f"Percentage of hallucinations: {results['hallucination_percentage']:.2f}%")
    # print(f"Average percentage of relevant documents: {results['doc_relevancy_percentage']:.2f}%")
    
    # Step 7: Interpretation guidance
    print("\n" + "="*50)
    print("📋 INTERPRETATION GUIDE")
    print("="*50)
    print("• Well-grounded systems typically show < 5% hallucination rate")
    print("• High-performing systems typically show > 75% document relevance")
    print("• View detailed results in the Quotient dashboard: https://app.quotientai.co")
    
    print("\n✅ Research agent execution completed!")


if __name__ == "__main__":
    main() 