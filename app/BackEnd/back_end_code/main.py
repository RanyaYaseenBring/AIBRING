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
    num_ctx=512,
    base_url="http://172.20.20.181:11434",
    headers=headers
)


def create_empty_state():

    return {
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

def answer_question(question: str, session_id: str):

    msg = question.strip()
    msg_lower = msg.lower()

    state = get_user_state(session_id)

    # =================================================
    # BUTTONS
    # =================================================

    if msg_lower in ["algemene vraag", "algemene_vraag"]:

        state["mode"] = "general"

        return "Hallo! Hoe kan ik u vandaag helpen?"

    if msg_lower in ["track & trace", "track_trace"]:

        state["mode"] = "tracking"

        return handle_tracking(
            "start_tracking",
            engine_track,
            llm,
            session_id
        )

    if msg_lower in ["interne vraag", "interne_vraag"]:

        state["mode"] = "internal"

        return "Wat is je vraag?"


    if state["mode"] == "tracking":

        tracking_response = handle_tracking(
            msg,
            engine_track,
            llm,
            session_id
        )

        if tracking_response is not None:

            return tracking_response

    if state["mode"] == "general":

        general_prompt = f"""
    You are a helpful AI assistant.
    - Reply naturally.
    - Be conversational.
    - Reply in the same language as the user.
    - Be friendly and helpful.
    - Do not mention prompts or system messages.
    -Dont start talking in a random launguage
    -you remember the conversation
    -you start the conversation from fresh when the page refreshes
    USER MESSAGE:
    {msg}
"""

        response = llm.invoke(general_prompt)

        if response and response.content:

            return response.content.strip()

        return "Geen antwoord ontvangen."

    prompt = ""

    if state["mode"] == "internal":

        prompt = f"""
You are a parser.
You are NOT a chatbot.

Return ONLY one of these formats:

employee_lookup|name|field
normal_chat
missing_name

Never explain anything.
No extra text.
No reasoning.
No notes.
No markdown.

VALID FIELDS:

Mobile
Mail
FunctionDesc
DateOfBirth
EmploymentStart
Street
ZIPCode
HouseNumber
City

FIELD MAPPING:

telefoon -> Mobile
telefoonnummer -> Mobile
mobiel -> Mobile
mobile -> Mobile
phone -> Mobile
telefoon nummer -> Mobile

email -> Mail
mail -> Mail

functie -> FunctionDesc
job -> FunctionDesc

verjaardag -> DateOfBirth
birthday -> DateOfBirth

startdatum -> EmploymentStart

straatnaam -> Street
straat -> Street
street -> Street

postcode -> ZIPCode
zipcode -> ZIPCode

huisnummer -> HouseNumber

stad -> City
city -> City

If the user asks employee information
but no employee name is present:

return:
missing_name

Examples:

wat is het telefoonnummer van ranya
employee_lookup|ranya|Mobile

wat is de email van mike
employee_lookup|mike|Mail

wat is de straatnaam van ranya
employee_lookup|ranya|Street

wat is de stad van ranya
employee_lookup|ranya|City

wat is het huisnummer
missing_name

IMPORTANT:

If the requested field is BirthOfDate:

- Use DateOfBirth to calculate the BirthOfDate.
- Age means:
current year - birth year

USER MESSAGE:
{msg}
"""
    response = llm.invoke(prompt)

    if not response or not response.content:

        return "Geen antwoord ontvangen."

    result = response.content.strip()

    print("RAW LLM RESULT:")
    print(result)

    clean_result = result.strip()

    if clean_result.lower().startswith("employee_lookup|"):

        try:

            _, name, field = clean_result.split("|", 2)

            allowed_fields = {
                "Mobile",
                "Mail",
                "FunctionDesc",
                "DateOfBirth",
                "EmploymentStart",
                "Street",
                "ZIPCode",
                "HouseNumber",
                "City"
            }

            if field not in allowed_fields:

                return "Ongeldig veld."

            query = f"""
            SELECT TOP 1 {field}
            FROM afas.Bring_Employees
            WHERE
                LOWER(FirstName) = LOWER(:name)
                OR LOWER(BirthName) = LOWER(:name)
            """

            print("SQL QUERY:")
            print(query)

            with engine_emp.connect() as conn:

                row = conn.execute(
                    text(query),
                    {"name": name}
                ).fetchone()

            if row and row[0]:

                return str(row[0])

            return "Geen gegevens gevonden."

        except Exception as e:

            print("EMPLOYEE LOOKUP ERROR:")
            print(e)

            return "Database fout."

    return result

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
    uvicorn.run(app, host="0.0.0.0", port=8000)