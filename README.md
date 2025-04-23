# 🧠 Natural Language SQL Agent with LangGraph + Streamlit
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

## 📸 Demo Preview

![Agentic Flow](./langgraph_sql_agent_workflow.png)  
![Visual Explainer](./image.png)

---

## 🚀 Try It Locally

```bash
git clone https://github.com/your-username/natural-language-sql-agent.git
cd natural-language-sql-agent
pip install -r requirements.txt
streamlit run app.py

