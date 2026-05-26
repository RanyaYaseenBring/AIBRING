import urllib.parse
import base64
import json
import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine, text
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
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
    f"TrustServerCertificate=yes;"
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
    msg_lower = msg.strip().lower()

    state = get_user_state(session_id)

    # =================================================
    # 1. BUTTONS CHAT-INPUTS
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


    # =================================================
    # 2. MODE: TRACKING
    # =================================================

    if state["mode"] == "tracking":

        tracking_response = handle_tracking(
            msg,
            engine_track,
            llm,
            session_id
        )

        if tracking_response is not None:

            return tracking_response


    # =================================================
    # 3. MODE: GENERAL (ALGEMENE ASSISTENT)
    # =================================================

    if state["mode"] == "general":

        general_prompt = f"""
    You are a helpful AI assistant.
    - Reply naturally.
    - Be conversational.
    - Reply in the same language as the user.
    - Be friendly and helpful.
    - Do not mention prompts or system messages.
    - Dont start talking in a random launguage
    - you remember the conversation
    - you start the conversation from fresh when the page refreshes
    USER MESSAGE:
    {msg}
"""

        response = llm.invoke(general_prompt)

        if response and response.content:

            return response.content.strip()

        return "Geen antwoord ontvangen van de algemene assistent."


    # =================================================
    # 4. MODE: INTERNAL (MEDEWERKERS PARSER)
    # =================================================

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

            return "Geen antwoord ontvangen van de interne parser."

        result = response.content.strip()

        print("RAW LLM RESULT:")
        print(result)

        clean_result = result.strip()

        # Check of de LLM de lookup-string heeft gegenereerd
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

                    return f"Ongeldig veld opgevraagd: {field}."

                query = f"""
                SELECT TOP 1 {field}
                FROM afas.Bring_Employees
                WHERE
                    LOWER(FirstName) = LOWER(:name)
                    OR LOWER(BirthName) = LOWER(:name)
                """

                with engine_emp.connect() as conn:

                    row = conn.execute(
                        text(query),
                        {"name": name}
                    ).fetchone()

                if row and row[0]:

                    return str(row[0])

                return f"Geen gegevens gevonden voor medewerker {name}."

            except Exception as e:

                print(e)

                return "Database fout bij het ophalen van de gegevens."

        # Specifieke fallback wanneer de naam ontbreekt in de prompt
        if "missing_name" in clean_result.lower():
            return "Ik help je graag met zoeken naar medewerkersinformatie, maar over welke medewerker gaat je vraag?"

        return clean_result

    # Ultieme fallback mocht er een onbekende status zijn
    return "Kies een optie om te beginnen."

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

    save_chat_memory(req.session_id, req.message, ans)

    return {
        "answer": ans,
        "session_id": session_id
    }

@app.post("/chat/reset/{session_id}")
async def reset_chat(session_id: str):
# CORRECT

    reset_state(session_id)

    return {
        "status": "reset",
        "session_id": session_id
    }



class LoginReq(BaseModel):

    email: str
    password: str


@app.post("/login")
def login(req: LoginReq):

    print(req.email)
    print(req.password)



    return {
            "success": True
        }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)