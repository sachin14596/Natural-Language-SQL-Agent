# 🧠 Natural Language SQL Agent with LangGraph + Llama3
An autonomous LLM-powered agent that converts natural language questions into SQL queries with error correction, retries, and instant answers via Streamlit UI.

---

## 📌 What is this?

A fully working **Autonomous LLM Agent** that:

✅ Accepts natural language queries  
✅ Understands your database schema  
✅ Generates syntactically correct SQL  
✅ Validates the query logic  
✅ Fixes errors and retries  
✅ Runs the query and returns the final answer

---

## 🧠 Powered By

- [LangGraph](https://github.com/langchain-ai/langgraph) – to define and run the agent flow
- [Groq + LLaMA3](https://groq.com) – for ultra-fast LLM inference
- [LangChain Tools](https://docs.langchain.com/docs/expression-language/tools/) – for tool management
- [Streamlit](https://streamlit.io) – for interactive frontend
- [SQLite] – for lightweight demo DB

---

## 📸 Flow

![image](https://github.com/user-attachments/assets/76e31c68-c0f4-46fa-b12b-5eb5b7639181)
![langgraph_sql_agent_workflow](https://github.com/user-attachments/assets/c12cc367-808a-46dd-8f03-e0b139ea5f3c)

---

## 📽 Demo Video

https://github.com/user-attachments/assets/7dec4864-3d8d-4666-955e-5201121be082




---

## 🚀 Try It Locally

```bash
git clone https://github.com/your-username/natural-language-sql-agent.git
cd natural-language-sql-agent
pip install -r requirements.txt
streamlit run app.py

