import streamlit as st
from langchain.llms import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from dotenv import load_dotenv
import os

st.title("🧪 Chemicals RAG Test 🧪")

load_status = load_dotenv("googleapikey.txt")
if load_status is False:
    raise RuntimeError('Environment variables not loaded.')

load_status = load_dotenv("auraconnection.txt")
if load_status is False:
    raise RuntimeError('Environment variables not loaded.')

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
API_KEY = os.getenv("API_KEY")

graph = Neo4jGraph(
    url=URI,
    username=AUTH[0],
    password=AUTH[1]
)

chain = GraphCypherQAChain.from_llm(
    ChatGoogleGenerativeAI(temperature=0, model="gemini-2.0-flash",google_api_key=API_KEY, allow_dangerous_requests=True), graph=graph, verbose=True, allow_dangerous_requests=True
)


def generate_response(input_text):
    st.info(chain.run(input_text))


with st.form("my_form"):
    text = st.text_area("Enter text:", "What are 3 key advice for learning how to code?")
    submitted = st.form_submit_button("Submit")
    if submitted:
        generate_response(text)