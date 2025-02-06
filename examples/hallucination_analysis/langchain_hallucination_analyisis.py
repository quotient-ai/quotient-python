import os
from quotientai import QuotientAI
from langchain import hub
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

quotient = QuotientAI()
llm = ChatOpenAI(model="gpt-4o-mini")


def create_vectorstore_example():
    # Create simple example documents
    documents = [
        Document(
            page_content="Document 1: Overview of employee benefits. Health insurance, dental, vision, etc."
        ),
        Document(
            page_content="Document 2: Company policies on remote work. Remote work is allowed, but must be approved by the manager."
        ),
        Document(
            page_content="Document 3: PTO policy. Unlimited PTO is allowed, but must be approved by the manager."
        ),
        Document(
            page_content="Document 4: Payroll policy. Payroll is processed on the 15th of each month."
        ),
        Document(
            page_content="Document 5: How to bake a cake. This document contains all the instructions for baking a cake."
        ),
        # Random documents
    ]

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # Create embeddings for the document splits
    embeddings = OpenAIEmbeddings()

    # Add the document splits to Chroma
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)

    return vectorstore.as_retriever()


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


@quotient.log(environment="dev", tags=["v1", "gpt-4o"], hallucination_analysis=True)
def invoke_rag_chain(rag_chain, model_input):
    return rag_chain.invoke(model_input)


def get_completions():
    retriever = create_vectorstore_example()
    prompt = hub.pull("rlm/rag-prompt")

    # Define the RAG chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # List of questions to ask
    questions = [
        "What benefits are available to employees?",
    ]

    # Initialize a list to store responses
    responses = []

    # Loop through each question, invoke the RAG chain, and store the response
    for question in questions:
        response = invoke_rag_chain(rag_chain, question)
        responses.append((question, response))

    # TODO get chain to return resources
    # https://python.langchain.com/v0.2/docs/how_to/qa_sources/

    # Print each question and its corresponding response
    for question, response in responses:
        print(f"\n\nQuestion: {question}")
        print(f"Answer: {response}\n")


if __name__ == "__main__":
    get_completions()
