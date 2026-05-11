import urllib.parse
import base64
import json
import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from langchain_ollama import ChatOllama

from ChatBotMemory import save_chat_memory
from ChatbotPrompt import generate_prompt
from track_traceFunction import handle_tracking
from latest_order import get_latest_order

app = FastAPI()

chat_sessions = {}
last_order_cache = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def make_engine(server, database, username, password):

    odbc_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )

    return create_engine(
        "mssql+pyodbc:///?odbc_connect="
        + urllib.parse.quote_plus(odbc_str),
        pool_pre_ping=True
    )


engine_emp = make_engine(
    "sql-bringbi-prod-001.database.windows.net",
    "sqldb-bringbi-prod-001",
    "bringgpt",
    "Qxn@7pLW$TwgHG36ewa3"
)

engine_track = make_engine(
    "sql-bringct-prod-001.database.windows.net",
    "sqldb-bringct-prod-001",
    "svc_CHATBOT",
    "GB94QV4e48NH8Vz"
)

username_llm = "ITSupport"
password_llm = "blistering-plafond-useless"

credentials = f"{username_llm}:{password_llm}"

auth_str = base64.b64encode(
    credentials.encode("utf-8")
).decode("utf-8")

headers = {
    "Authorization": f"Basic {auth_str}"
}

llm = ChatOllama(
    model="llama3.1:latest",
    temperature=0,
    base_url="http://172.20.20.181:11434",
    headers=headers
)

def create_empty_state():

    return {
        "history": [],
        "mode": "general",

        "tracking": {
            "tracking_active": False,
            "tracking_number": None,
            "waiting_for_tracking_number": False,
            "waiting_for_zipcode_question": False,
            "waiting_for_zipcode": False,
            "waiting_for_continue": False
        }
    }


def get_user_state(session_id: str):

    if session_id not in chat_sessions:

        chat_sessions[session_id] = create_empty_state()

    return chat_sessions[session_id]


def reset_state(session_id: str):

    chat_sessions[session_id] = create_empty_state()


def append_history(session_id: str, role: str, message: str):

    state = get_user_state(session_id)

    state["history"].append({
        "role": role,
        "message": message
    })

    if len(state["history"]) > 20:

        state["history"] = state["history"][-20:]


def get_history(session_id: str):

    return get_user_state(session_id)["history"]


def answer_question(question: str, session_id: str):

    msg = question.strip()

    state = get_user_state(session_id)

    if msg == "Algemene vraag":

        state["mode"] = "general"

        answer = (
            "Hallo! Hoe kan ik u vandaag helpen?"
        )

        append_history(session_id, "user", msg)
        append_history(session_id, "assistant", answer)

        return answer

    if state["mode"] == "tracking":

        tracking_response = handle_tracking(
            msg,
            engine_track,
            llm,
            session_id
        )

        if tracking_response is not None:

            append_history(session_id, "user", msg)

            append_history(
                session_id,
                "assistant",
                str(tracking_response)
            )

            return tracking_response

        if state["mode"] == "internal":

            prompt = generate_prompt(
                question=msg,
                history=formatted_context,
                schema_info=""
            )

    else:

        prompt = f"""
    You are a helpful chatbot.

    USER MESSAGE:
    {msg}
    """

    response = llm.invoke(prompt)

    if not response or not response.content:

        answer = "Geen antwoord ontvangen."

    else:

        result = response.content.strip()

        print("RAW LLM RESULT:")
        print(result)

        clean_result = (
            result
            .replace("\n", "")
            .replace("\r", "")
            .strip()
        )

        if clean_result.lower().startswith("employee_lookup|"):

            try:

                _, name, field = clean_result.split("|", 2)

                query = f"""
                SELECT {field}
                FROM afas.Bring_Employees
                WHERE
                    LOWER(FirstName) = LOWER(:name)
                    OR LOWER(BirthName) = LOWER(:name)
                """

                with engine_emp.connect() as conn:

                    row = conn.execute(
                        text(query),
                        {
                            "name": name
                        }
                    ).fetchone()

                if row:

                    answer = str(row[0])

                else:

                    answer = "Geen gegevens gevonden."

            except Exception as e:

                print("EMPLOYEE LOOKUP ERROR:", e)

                answer = "Database fout."

        else:

            answer = result

        tracking_response = handle_tracking(
            msg,
            engine_track,
            llm,
            session_id
        )

        if tracking_response is not None:

            append_history(session_id, "user", msg)

            append_history(
                session_id,
                "assistant",
                str(tracking_response)
            )

            return tracking_response

    history = get_history(session_id)

    recent_history = history[-30:]

    formatted_context = ""

    for item in recent_history:

        role_name = (
            "Gebruiker"
            if item["role"] == "user"
            else "Assistent"
        )

        formatted_context += (
            f"{role_name}: {item['message']}\n"
        )

    if state["mode"] == "internal":

        prompt = generate_prompt(
            question=msg,
            history=formatted_context,
            schema_info=""
        )

    response = llm.invoke(prompt)

    if not response or not response.content:

        answer = "Geen antwoord ontvangen."

    else:

        result = response.content.strip()

        print("RAW LLM RESULT:")
        print(result)

        clean_result = (
            result
            .replace("\n", "")
            .replace("\r", "")
            .strip()
        )


        if clean_result == "LATEST_ORDER":

            answer = get_latest_order(engine_track)

        # =================================================
        # EMPLOYEE LOOKUP
        # =================================================

        elif clean_result.lower().startswith("employee_lookup|"):

            try:

                _, name, field = clean_result.split("|", 2)

                query = f"""
                SELECT {field}
                FROM afas.Bring_Employees
                WHERE
                    LOWER(FirstName) = LOWER(:name)
                    OR LOWER(BirthName) = LOWER(:name)
                """

                with engine_emp.connect() as conn:

                    row = conn.execute(
                        text(query),
                        {
                            "name": name
                        }
                    ).fetchone()

                if row:

                    answer = str(row[0])

                else:

                    answer = (
                        f"Geen gegevens gevonden voor {name}."
                    )

            except Exception as e:

                print("EMPLOYEE LOOKUP ERROR:", e)

                answer = (
                    "Er trad een fout op bij "
                    "het ophalen van medewerkergegevens."
                )

        # =================================================
        # NORMAL RESPONSE
        # =================================================

        else:

            answer = result

    append_history(session_id, "user", msg)

    append_history(
        session_id,
        "assistant",
        str(answer)
    )

    return answer


class ChatReq(BaseModel):

    message: str
    session_id: str | None = None


@app.post("/chat")
async def chat(req: ChatReq):

    session_id = (
        req.session_id
        or "default-session"
    )

    ans = await run_in_threadpool(
        lambda: answer_question(
            req.message,
            session_id
        )
    )

    save_chat_memory(req.message, ans)

    return {
        "answer": ans,
        "session_id": session_id
    }


@app.post("/chat/reset/{session_id}")
async def reset_chat(session_id: str):

    reset_state(session_id)

    return {
        "status": "reset",
        "session_id": session_id
    }


@app.websocket("/ws/latest-order")
async def websocket_latest_order(websocket: WebSocket):

    await websocket.accept()

    global last_order_cache

    while True:

        try:

            data = get_latest_order(engine_track)

            if data != last_order_cache:

                last_order_cache = data

                await websocket.send_text(
                    json.dumps(data)
                )

            await asyncio.sleep(5)

        except Exception as e:

            print("WS ERROR:", e)

            break


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )