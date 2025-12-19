from dotenv import load_dotenv
load_dotenv("secret.env")  # <- сразу

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_nebius import ChatNebius
from langchain_nebius import NebiusEmbeddings
from dotenv import load_dotenv
import pandas as pd
import chromadb
import sqlite3
import json
from datetime import datetime
import os
class AgentState(TypedDict):
    user_input: str
    user_id: str
    massage_type: bool
    search_status: bool
    doc_elements: list
    graph_output: str | None
    search_content: str | None
    dialogue_history: list


class CarAssistent:
    def __init__(self):
        # --------- GRAPH ---------
        self.graph = StateGraph(AgentState)

        # --------- DATA ---------
        self.df_name = "data/Price.xlsx"
        self.df = None

        # --------- MODELS ---------
        self.generate_model = ChatNebius(
            api_key=os.getenv("NEBIUS_API_KEY"),
            model="Qwen/Qwen3-235B-A22B-Instruct-2507",
            temperature=0.1,
            top_p=0.95,
        )

        self.embedding_model = NebiusEmbeddings(
            api_key=os.getenv("NEBIUS_API_KEY"),
            model="Qwen/Qwen3-Embedding-8B",
        )

        # --------- VECTOR DB ---------
        self.vec_db_client = chromadb.PersistentClient(path="data/chroma_db")
        self.collection = self.vec_db_client.get_or_create_collection("cars")

        self.init_vector_store()

        # --------- STATE DB ---------
        self.conn = sqlite3.connect("agent_state.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS states (
                user_id TEXT PRIMARY KEY,
                date DATETIME,
                state TEXT
            )
            """
        )
        self.conn.commit()

        # --------- GRAPH NODES ---------
        self.graph.add_node("input", self.input_node)
        self.graph.add_node("search", self.search_node)
        self.graph.add_node("reasoning", self.reasoning_node)
        self.graph.add_node("output", self.output_node)

        self.graph.add_edge(START, "input")
        self.graph.add_conditional_edges(
            "input",
            self.input_to_search_or_output,
            {
                "search": "search",
                "output": "output",
            },
        )
        self.graph.add_edge("search", "reasoning")
        self.graph.add_edge("reasoning", "output")
        self.graph.add_edge("output", END)

        self.app = self.graph.compile()

    # ---------- UTILS ----------

    def safe_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except Exception:
            return {}

    # ---------- VECTOR STORE ----------

    def init_vector_store(self):
        if self.collection.count() > 0:
            print("📦 Chroma уже инициализирована")
            return

        print("📥 Загружаю прайс-лист в Chroma...")
        self.read_df()

    def read_df(self):
        print("📥 Чтение Excel файла:", self.df_name)
        self.df = pd.read_excel(self.df_name)
        print(f"✅ Файл загружен, всего строк: {len(self.df)}")

        last_category = None
        for idx, row in self.df.iterrows():
            category = row["Категория"] if pd.notna(row["Категория"]) else last_category
            last_category = category

            service = (
                f"Категория: {category}, "
                f"Услуга: {row['Услуга']}, "
                f"Цена: {row['Цена']}"
            )

            print(f"🔹 Обрабатываю строку {idx}: {service}")

            try:
                embedding = self.embedding_model.embed_query(service)
                print(f"   ✅ Эмбеддинг создан, длина: {len(embedding)}")
            except Exception as e:
                print(f"   ❌ Ошибка при создании эмбеддинга: {e}")
                continue

            try:
                self.collection.add(
                    embeddings=[embedding],
                    documents=[service],
                    metadatas=[{"category": category}],
                    ids=[str(idx)],
                )
                print(f"   ✅ Строка добавлена в Chroma: ID={idx}")
            except Exception as e:
                print(f"   ❌ Ошибка при добавлении в Chroma: {e}")

    # ---------- RUN ----------

    def run(self, user_id: str, user_input: str) -> str:
        row = self.cursor.execute(
            "SELECT state FROM states WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if row:
            state = self.safe_json(row[0])
            state["user_input"] = user_input
        else:
            state = {
                "user_input": user_input,
                "user_id": user_id,
                "massage_type": False,
                "search_status": False,
                "doc_elements": [],
                "graph_output": "",
                "search_content": "",
                "dialogue_history": [],
            }

        result = self.app.invoke(state)
        return result.get("graph_output", "")

    # ---------- GRAPH LOGIC ----------

    def input_to_search_or_output(self, state: AgentState) -> str:
        return "search" if state.get("massage_type") else "output"

    def input_node(self, state: AgentState):
        state["dialogue_history"].append(
            {"role": "user", "message": state["user_input"]}
        )

        prompt = f"""
Ты менеджер автосервиса по ремонту автомобилей. Ты НЕ продаёшь автомобили. Определи, относится ли запрос к автосервису. Если нет мягко верни пользователя к основной теме.
Ответ строго в JSON:
{{
  "massage_type": true | false,
  "graph_output": string
}}

История диалога:
{state["dialogue_history"]}
"""

        answer = self.safe_json(self.generate_model.invoke(prompt).content)

        return {
            "massage_type": answer.get("massage_type", False),
            "graph_output": answer.get("graph_output"),
            "dialogue_history": state["dialogue_history"],
        }

    def search_node(self, state: AgentState):
        embedding = self.embedding_model.embed_query(state["user_input"])

        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=10,
        )

        documents = result["documents"][0] if result.get("documents") else []
        context = "\n".join(documents)

        return {
            "search_content": context,
            "doc_elements": documents,
        }

    def reasoning_node(self, state: AgentState):
        prompt = f"""
Ты менеджер автосервиса. Используй ТОЛЬКО список услуг ниже.
Если ничего не найдено — честно скажи.

Услуги:
{state["search_content"]}

История:
{state["dialogue_history"]}

Ответ в JSON:
{{
  "graph_output": string
}}
"""

        answer = self.safe_json(self.generate_model.invoke(prompt).content)

        return {
            "graph_output": answer.get(
                "graph_output",
                "К сожалению, по вашему запросу услуги не найдены."
            )
        }

    def output_node(self, state: AgentState):
        state["dialogue_history"].append(
            {"role": "assistant", "message": state["graph_output"]}
        )

        self.cursor.execute(
            """
            INSERT OR REPLACE INTO states (user_id, date, state)
            VALUES (?, ?, ?)
            """,
            (state["user_id"], datetime.utcnow(), json.dumps(state)),
        )
        self.conn.commit()

        return state

print("NEBIUS_API_KEY:", os.getenv("NEBIUS_API_KEY"))
car_assistant = CarAssistent()
graph_app = car_assistant.app