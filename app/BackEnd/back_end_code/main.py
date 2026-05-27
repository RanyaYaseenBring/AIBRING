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
    msg_lower = msg.lower()

    state = get_user_state(session_id)

    # =========================
    # Algemene vraag
    # =========================

    if msg_lower in ["algemene vraag", "algemene_vraag"]:

        state["mode"] = "general"

        return "Hallo! Hoe kan ik u vandaag helpen?"

    # =========================
    # Track & Trace
    # =========================

    elif msg_lower in ["track & trace", "track_trace"]:

        state["mode"] = "tracking"

        return handle_tracking(
            "start_tracking",
            engine_track,
            llm,
            session_id
        )

    # =========================
    # Interne vraag
    # =========================

    elif msg_lower in ["interne vraag", "interne_vraag"]:

        state["mode"] = "internal"

        return "Wat is je vraag?"

    # =========================
    # Tracking mode
    # =========================

    elif state["mode"] == "tracking":

        tracking_response = handle_tracking(
            msg,
            engine_track,
            llm,
            session_id
        )

        if tracking_response is not None:

            return tracking_response

    # =========================
    # General mode
    # =========================

    elif state["mode"] == "general":

        general_prompt = f"""
You are a helpful AI assistant.

- Reply naturally
- Reply in the same language as the user
- Be conversational
- Be friendly
- Do not mention prompts or system messages

USER MESSAGE:
{msg}
"""

        response = llm.invoke(general_prompt)

        if response and response.content:

            return response.content.strip()

        return "Geen antwoord ontvangen."

    # =========================
    # Internal mode
    # =========================

    elif state["mode"] == "internal":

        sql_prompt = f"""
You are a parser.
You are NOT a chatbot.

Return ONLY one of these formats:

employee_lookup|name|field
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
BirthName

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

NAME RULES:

- The employee name may be:
  - a first name
  - a last name
  - a full name

- Last names are valid employee names.
- Always extract the full detected name from the sentence.

Examples:

"wat is het telefoonnummer van jansen"
-> employee_lookup|jansen|Mobile

"wat is de email van mike jansen"
-> employee_lookup|mike jansen|Mail

leeftijd -> DateOfBirth
age -> DateOfBirth

IMPORTANT:

If the requested field is DateOfBirth:

- Use DateOfBirth to calculate the age.
- Age means:
current year - birth year
- Return the calculated age instead of the birth date.

USER MESSAGE:
{msg}
"""

        response = llm.invoke(sql_prompt).content.strip()

        if response == "missing_name":

            return "Geen naam gevonden."

        parsed = response.split("|")

        if len(parsed) != 3:

            return f"Ongeldige parser response: {response}"

        intent = parsed[0]
        name = parsed[1]
        field = parsed[2]

    query = text(f"""
    SELECT {field}
    FROM afas.Bring_Employees
    WHERE LOWER(FirstName) LIKE LOWER(:name)
    OR LOWER(BirthName) LIKE LOWER(:name)
""")

    try:
            with engine_emp.connect() as conn:

                result = conn.execute(
                    query,
                    {"name": f"%{name}%"}
                ).fetchone()

                if not result:

                    return "Geen resultaten gevonden."

                value = result[0]

                if field == "DateOfBirth":

                    from datetime import date

                    age = date.today().year - value.year

                    return f"{name} is {age} jaar oud"

                return str(value)

    except Exception as e:

            print(e)

            return f"SQL fout: {str(e)}"

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