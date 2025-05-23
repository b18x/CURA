import streamlit as st
from langchain.callbacks import StreamlitCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from dotenv import load_dotenv
import os

st.title("🧪 CURA AI Output Test 🧪")

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
    ChatGoogleGenerativeAI(temperature=0, model="gemini-2.0-flash", google_api_key=API_KEY, allow_dangerous_requests=True), graph=graph, top_k=200, verbose=True, allow_dangerous_requests=True
)


def generate_response(input_text):
    st.info(chain.run(input_text))


# with st.form("my_form"):
#     text = st.text_area("Enter text:", "What are 3 key advice for learning how to code?")
#     submitted = st.form_submit_button("Submit")
#     if submitted:
#         generate_response(text)


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, how can I help you with the chemical graph?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="What chemicals are regulated by Apple?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key, streaming=True)
    # search = DuckDuckGoSearchRun(name="Search")
    # search_agent = initialize_agent([search], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, handle_parsing_errors=True)
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(
            st.container(), expand_new_thoughts=False)
        response = chain.run(
            st.session_state.messages[-1]["content"], callbacks=[st_cb])
        # response = search_agent.run(st.session_state.messages, callbacks=[st_cb])
        st.session_state.messages.append(
            {"role": "assistant", "content": response})
        st.write(response)
