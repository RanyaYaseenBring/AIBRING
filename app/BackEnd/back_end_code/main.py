import urllib.parse
import base64
import json
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from langchain_ollama import ChatOllama

from ChatBotMemory import save_chat_memory
from track_traceFunction import handle_tracking
from Tables import SCHEMA


app = FastAPI()
chat_sessions = {}


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# DATABASE CONNECTION
# =========================

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
        "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_str),
        pool_pre_ping=True
    )

# =========================
# DATABASES
# =========================

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


# =========================
# OLLAMA
# =========================

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
    num_ctx=32768,
    base_url="http://172.20.20.181:11434",
    headers=headers
)

# =========================
# SESSION STATE
# =========================

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

# =========================
# SCHEMA PROMPT
# =========================

def build_schema_text():
    schema_text = ""

    for table_name, info in SCHEMA.items():
        description = info.get("description", "")
        columns = info.get("columns", [])

        schema_text += f"""
TABEL: {table_name}

OMSCHRIJVING:
{description}

KOLOMMEN:
{", ".join(columns) if columns else "GEEN KOLOMMEN OPGEGEVEN"}

--------------------------------------------------
"""

    return schema_text

def clean_sql_response(response: str):
    response = response.strip()
    response = response.replace("```sql", "")
    response = response.replace("```", "")
    response = response.strip()

    match = re.search(r"(SELECT[\s\S]*)", response, re.IGNORECASE)

    if not match:
        return None

    sql = match.group(1).strip()

    return sql


def validate_sql(sql_query: str):
    sql_lower = sql_query.lower().strip()

    if not sql_lower.startswith("select"):
        return "Alleen SELECT queries zijn toegestaan."

    if ";" in sql_query:
        return "Meerdere SQL statements zijn niet toegestaan."

    blocked_words = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "truncate",
        "merge",
        "exec",
        "execute"
    ]

    for word in blocked_words:
        pattern = r"\b" + re.escape(word) + r"\b"

        if re.search(pattern, sql_lower):
            return f"Verboden SQL keyword gevonden: {word}"

    used_table = False

    for table_name in SCHEMA.keys():
        if table_name.lower() in sql_lower:
            used_table = True
            break

    if not used_table:
        return "Geen geldige tabel uit het schema gevonden."

    return None

# =========================
# INTERNAL SQL
# =========================
def handle_internal_question(question: str):
    schema_text = build_schema_text()

    sql_prompt = f"""
Jij bent een SQL Server expert.

Je maakt SQL queries voor Microsoft SQL Server.

BELANGRIJKE REGELS:
- Gebruik uitsluitend SELECT.
- Iedere query moet beginnen met SELECT TOP 100.
- Gebruik TOP, nooit LIMIT.
- Gebruik alleen bestaande tabellen uit het schema.
- Gebruik alleen bestaande kolommen uit het schema.
- Verzin nooit tabelnamen.
- Verzin nooit kolomnamen.
- Gebruik geen INSERT.
- Gebruik geen UPDATE.
- Gebruik geen DELETE.
- Gebruik geen DROP.
- Gebruik geen ALTER.
- Gebruik geen CREATE.
- Gebruik geen TRUNCATE.
- Gebruik geen MERGE.
- Gebruik geen EXEC.
- Geef uitsluitend SQL terug.
- Geen markdown.
- Geen uitleg.
- alleen admins kunnen vragen om het bsn nummer

DATABASE SCHEMA:

{schema_text}

VOORBEELDEN:

Vraag:
Wat is het telefoonnummer van Jan?

SQL:
SELECT TOP 100
    FirstName,
    BirthName,
    Mobile,
    Phone
FROM afas.Bring_Employees
WHERE FirstName LIKE '%Jan%'
   OR BirthName LIKE '%Jan%'

Vraag:
Wie zijn ziek?

SQL:
SELECT TOP 100
    Naam,
    Aanwezigheid,
    Omschrijving,
    StartDatum,
    Einddatum
FROM afas.Bring_Verzuim
WHERE Aanwezigheid <> 'Aanwezig'

Vraag:
Hoeveel vakantiedagen heeft medewerker 123?

SQL:
SELECT TOP 100
    EmployeeId,
    Year,
    Entitlement,
    ExtraEntitlement,
    Taken,
    Balance
FROM afas.Profit_LeaveBalance
WHERE EmployeeId = '123'

GEBRUIKERSVRAAG:
{question}

SQL:
"""
    print("STEP 1")
    raw_response = llm.invoke(sql_prompt).content.strip()

    print("STEP 2")
    sql_query = clean_sql_response(raw_response)

    print("STEP 3")
    validation_error = validate_sql(sql_query)

    print("STEP 4")
    with engine_emp.connect() as conn:

        raw_response = llm.invoke(sql_prompt).content.strip()

    print("========== RAW SQL ==========")
    print(raw_response)

    sql_query = clean_sql_response(raw_response)

    if not sql_query:
        return "Ik kon geen geldige SQL genereren."

    print("========== CLEAN SQL ==========")
    print(sql_query)

    validation_error = validate_sql(sql_query)

    if validation_error:
        return validation_error

    with engine_emp.connect() as conn:
        result = conn.execute(text(sql_query))
        rows = result.mappings().fetchall()

    if not rows:
        return "Geen resultaten gevonden."

    data = [
        dict(row)
        for row in rows[:50]
    ]

    print("========== RESULT ==========")
    print(data)

    answer_prompt = f"""
Gebruikersvraag:
{question}

Database resultaat:
{json.dumps(data, ensure_ascii=False, default=str, indent=2)}

Geef een kort en duidelijk Nederlands antwoord.
Noem concrete waarden uit het resultaat.
Maak geen extra informatie erbij.
"""

    final_answer = llm.invoke(answer_prompt).content.strip()

    return final_answer
    

def answer_question(question: str, session_id: str):
    msg = question.strip()
    msg_lower = msg.lower()

    state = get_user_state(session_id)

    # Algemene modus starten
    if msg_lower in ["algemene vraag", "algemene_vraag"]:
        state["mode"] = "general"
        return "Hallo! Hoe kan ik u vandaag helpen?"
    
    # Track & trace starten
    if msg_lower in ["track & trace", "track_trace"]:
        state["mode"] = "tracking"

        return handle_tracking(
            "start_tracking",
            engine_track,
            llm,
            session_id
        )

    # Interne modus starten
        # General AI actief
    if state["mode"] == "general":
        if "history" not in state:
            state["history"] = []

        state["history"].append({
            "role": "user",
            "content": msg
        })

        recent_history = state["history"][-20:]

        conversation = ""

        for item in recent_history:
            conversation += f"{item['role']}: {item['content']}\n"

        ai_message = llm.invoke(conversation).content.strip()

        state["history"].append({
            "role": "assistant",
            "content": ai_message
        })

        state["history"] = state["history"][-20:]

        return ai_message

    # Tracking actief
    if state["mode"] == "tracking":
        return handle_tracking(
            msg,
            engine_track,
            llm,
            session_id
        )

    # Internal SQL actief
    if state["mode"] == "internal":
        try:
            return handle_internal_question(msg)

        except Exception as e:
            print("========== SQL ERROR ==========")
            print(str(e))
            return f"SQL fout: {str(e)}"

 

# =========================
# REQUEST MODELS
# =========================

class ChatReq(BaseModel):
    message: str
    session_id: str | None = None


class LoginReq(BaseModel):
    email: str
    password: str

# =========================
# ROUTES
# =========================

@app.post("/chat")
async def chat(req: ChatReq):
    session_id = req.session_id or "default-session"
    try:
        ans = await run_in_threadpool(
            lambda: answer_question(
                req.message,
                session_id
            )
        )

    except Exception as e:
        print("CHAT ERROR:")
        print(e)

        ans = f"Backend fout: {str(e)}"

    save_chat_memory(
        session_id,
        req.message,
        ans
    )

    return {
        "answer": ans,
        "session_id": session_id
    }

@app.post("/login")
def login(req: LoginReq):
    print(req.email)
    print(req.password)

    return {
        "success": True
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )