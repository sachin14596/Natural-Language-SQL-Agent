import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langchain_core.tools import tool
from langchain_community.utilities import SQLDatabase
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode
from typing import Annotated, Any
from typing_extensions import TypedDict
import sqlite3

# --------------------------- DATABASE SETUP ---------------------------
connection = sqlite3.connect("mydb.db")
db = SQLDatabase.from_uri("sqlite:///mydb.db")

cursor = connection.cursor()

# Drop tables if exist
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("DROP TABLE IF EXISTS customers")
cursor.execute("DROP TABLE IF EXISTS employees")

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    emp_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hire_date TEXT NOT NULL,
    salary REAL NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);
""")

# Insert data
cursor.executemany("""
INSERT INTO employees (emp_id, first_name, last_name, email, hire_date, salary)
VALUES (?, ?, ?, ?, ?, ?);
""", [
    (1, "Sunny", "Savita", "sunny.sv@abc.com", "2023-06-01", 50000.00),
    (2, "Arhun", "Meheta", "arhun.m@gmail.com", "2022-04-15", 60000.00),
    (3, "Alice", "Johnson", "alice.johnson@jpg.com", "2021-09-30", 55000.00),
    (4, "Bob", "Brown", "bob.brown@uio.com", "2020-01-20", 45000.00),
])

cursor.executemany("""
INSERT INTO customers (customer_id, first_name, last_name, email, phone)
VALUES (?, ?, ?, ?, ?);
""", [
    (1, "John", "Doe", "john.doe@example.com", "1234567890"),
    (2, "Jane", "Smith", "jane.smith@example.com", "9876543210"),
    (3, "Emily", "Davis", "emily.davis@example.com", "4567891230"),
    (4, "Michael", "Brown", "michael.brown@example.com", "7894561230"),
])

cursor.executemany("""
INSERT INTO orders (order_id, customer_id, order_date, amount)
VALUES (?, ?, ?, ?);
""", [
    (1, 1, "2023-12-01", 250.75),
    (2, 2, "2023-11-20", 150.50),
    (3, 3, "2023-11-25", 300.00),
    (4, 4, "2023-12-02", 450.00),
])

connection.commit()

# --------------------------- AGENT SETUP ---------------------------
from langchain_groq import ChatGroq
llm = ChatGroq(model="llama3-70b-8192")
# Remove incorrect 'toolkit' placeholder line
# toolkit = db.get_table_info, db.get_usable_table_names

@tool
def query_to_database(query: str) -> str:
    """
    Executes a SQL query safely and returns the result.
    If the query fails, returns a helpful error message instead.
    """
    result = db.run_no_throw(query)
    return result if result else "Error: Query failed. Please rewrite your query and try again."

class SubmitFinalAnswer(BaseModel):
    final_answer: str = Field(..., description="The final answer to the user")

llm_with_final_answer = llm.bind_tools([SubmitFinalAnswer])
llm_with_tools = llm.bind_tools([query_to_database])

query_check_system = """You are a SQL expert. Carefully review the SQL query..."""
query_check_prompt = ChatPromptTemplate.from_messages([
    ("system", query_check_system),
    ("placeholder", "{messages}")
])
check_generated_query = query_check_prompt | llm_with_tools

all_schemas = "\n\n".join(
    [f"{table}:\n{db.get_table_info([table])}" for table in db.get_usable_table_names()]
)

query_gen_system_prompt = f"""You are a SQL expert with strong attention to detail.

Here are the schemas of the available tables:
{all_schemas}

Given an input question, output a syntactically correct SQLite query that answers the question.
Then use the query result to write a final answer.

RULES:
1. Only call SubmitFinalAnswer to give the result.
2. Do not include the query as output — only the answer.
3. If you are unsure, say you don't have enough information.
"""

query_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", query_gen_system_prompt),
    ("placeholder", "{messages}")
])
query_generator = query_gen_prompt | llm_with_final_answer

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def generation_query(state: State):
    message = query_generator.invoke(state)
    tool_messages = []
    if message.tool_calls:
        for tc in message.tool_calls:
            if tc["name"] != "SubmitFinalAnswer":
                tool_messages.append(ToolMessage(
                    content=f"Error: The wrong tool was called: {tc['name']}.",
                    tool_call_id=tc["id"]))
    return {"messages": [message] + tool_messages}

def check_the_given_query(state: State):
    return {"messages": [check_generated_query.invoke({"messages": [state["messages"][-1]]})]}

def should_continue(state: State):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return END
    elif last_message.content.startswith("Error:"):
        return "query_gen"
    else:
        return "correct_query"

def llm_get_schema(state: State):
    return {
        "messages": [HumanMessage(content=f"What is the schema of the table '{state['messages'][-1].content}'?")]
    }

def dummy_schema_tool(state: State):
    return {
        "messages": [AIMessage(content=db.get_table_info(["employees", "orders", "customers"]))]
    }

workflow = StateGraph(State)
workflow.add_node("query_gen", generation_query)
workflow.add_node("correct_query", check_the_given_query)
workflow.add_conditional_edges("query_gen", should_continue, {
    END: END,
    "correct_query": "correct_query"
})
workflow.add_edge("correct_query", "query_gen")
workflow.add_edge(START, "query_gen")
app = workflow.compile()

# --------------------------- STREAMLIT UI ---------------------------
st.set_page_config(page_title="SQL Agent Demo", page_icon="🤖")
st.title("🧠 LangGraph SQL Agent")
st.markdown("""
Ask natural language questions about your database.

**Examples:**
- How many employees are there?
- Show me orders over 300 rupees.
- List the first names of employees hired after 2020.
""")

# Show database tables and structure
with st.expander("📊 Database Tables"):
    try:
        table_names = db.get_usable_table_names()
        st.write("**Tables in the database:**")
        for table in table_names:
            st.markdown(f"### 🧾 {table}")
            try:
                schema = db.get_table_info([table])
                st.code(schema)
            except Exception as e:
                st.warning(f"Couldn't fetch schema for {table}: {e}")
    except Exception as e:
        st.error("Could not fetch database information.")
        st.code(str(e))

user_query = st.text_input("💬 Ask your question:", placeholder="e.g. How many orders are above 300 rupees?")

if "history" not in st.session_state:
    st.session_state.history = []

if user_query:
    st.session_state.history.append(user_query)
    st.markdown("---")
    with st.spinner("🤖 Agent is thinking..."):
        try:
            response = app.invoke({"messages": [HumanMessage(content=user_query)]})
            answer = response["messages"][-1].tool_calls[0]["args"]["final_answer"]

            st.success("✅ Answer: ")
            st.markdown(f"**{answer}**")
        except Exception as e:
            st.error("❌ Agent could not return a valid answer.")
            st.code(str(e))

    st.markdown("---")
    with st.expander("🧾 Chat History"):
        for q in st.session_state.history:
            st.markdown(f"- {q}")

    with st.expander("🛠️ Raw Agent Response"):
        st.json(response)
