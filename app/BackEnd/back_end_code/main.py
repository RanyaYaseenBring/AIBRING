import urllib.parse
import base64
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from langchain_ollama import ChatOllama

from ChatBotMemory import save_chat_memory
from track_traceFunction import handle_tracking

import urllib.parse
import base64
import json
import re
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
        "mssql+pyodbc:///?odbc_connect="
        + urllib.parse.quote_plus(odbc_str),
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
    num_ctx=8192,
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
# DATABASE SCHEMA
# =========================

def get_tables_for_prompt():
    text = ""

    for table_name, info in SCHEMA.items():
        text += f"- {table_name}: {info['description']}\n"

    return text


def get_columns_for_table(table_name):
    return SCHEMA.get(table_name, {}).get("columns", [])


def clean_table_name(response):
    response = response.strip()

    for table_name in SCHEMA.keys():
        if table_name.lower() in response.lower():
            return table_name

    return None


def clean_sql_response(response):
    match = re.search(r"(SELECT[\s\S]*)", response, re.IGNORECASE)

    if not match:
        return None

    sql = match.group(1).strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql

       
# =========================
# MAIN CHAT FUNCTION
# =========================

def answer_question(question: str, session_id: str):

    msg = question.strip()
    msg_lower = msg.lower()

    state = get_user_state(session_id)

    # =========================
    # ALGEMENE VRAAG
    # =========================

    if msg_lower in ["algemene vraag", "algemene_vraag"]:

        state["mode"] = "general"

        return "Hallo! Hoe kan ik u vandaag helpen?"

    # =========================
    # TRACK & TRACE
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
    # INTERNE MODUS STARTEN
    # =========================

    elif msg_lower in ["interne vraag", "intern"]:

        state["mode"] = "internal"

        return "Interne modus geactiveerd. Stel uw vraag."

    # =========================
    # INTERNE SQL VRAGEN
    # =========================

    elif state["mode"] == "internal":

        # =========================
        # STAP 1: TABEL KIEZEN
        # =========================

        table_prompt = f"""
Jij bent een database expert.

Gebruikersvraag:
{question}

Beschikbare tabellen:
{get_tables_for_prompt()}

BELANGRIJKE REGELS:

- BSN -> afas.Profit_Employees
- telefoon -> afas.Profit_Employees
- mobiel -> afas.Profit_Employees
- email medewerker -> afas.Profit_Employees
- adres -> afas.Profit_Employees

- fulltime -> afas.Bring_Employees
- parttime -> afas.Bring_Employees
- FTE -> afas.Bring_Employees
- uren per week -> afas.Bring_Employees

- ziekte -> afas.Bring_Verzuim
- aanwezig -> afas.Bring_Verzuim
- afwezig -> afas.Bring_Verzuim

- vakantiedagen -> afas.Profit_LeaveBalance
- verlofsaldo -> afas.Profit_LeaveBalance

- login -> afas.Profit_Users
- gebruiker -> afas.Profit_Users
- UPN -> afas.Profit_Users

Geef ALLEEN de tabelnaam terug.
Geen uitleg.
Geen SQL.
Geen markdown.
"""
        table_response = llm.invoke(table_prompt).content.strip()

        print("========== TABLE RESPONSE ==========")
        print(table_response)

        selected_table = clean_table_name(table_response)

        if not selected_table:
            return f"Geen tabel gevonden. AI antwoordde: {table_response}"

        print("========== SELECTED TABLE ==========")
        print(selected_table)

        table_info = SCHEMA[selected_table]
        columns = table_info["columns"]
        columns_text = "\n".join(columns)

        # =========================
        # STAP 2: SQL GENEREREN
        # =========================

        sql_prompt = f"""
Je bent een SQL Server query generator.
Gebruikersvraag:
{question}

Database resultaat:
Regels:
- Gebruik ALLEEN de data uit het database resultaat.
- Verzin NOOIT gegevens.
- Als er geen resultaten zijn, zeg exact:
  'Geen resultaten gevonden.'
- Als er resultaten zijn, noem deze resultaten.

BELANGRIJK:
- Je geeft ALLEEN SQL terug
- Geen uitleg
- Geen markdown
- Geen waarschuwingen
- Geen weigeringen
- Gebruik alleen SELECT
- Gebruik TOP 10 tenzij anders gevraagd
- Gebruik GEEN LIMIT
- Gebruik GEEN DELETE, UPDATE, INSERT, DROP, ALTER, CREATE, TRUNCATE of MERGE
- Gebruik alleen deze tabel
- Gebruik alleen bestaande kolommen
- Verzin geen kolommen
- Verzin geen tabellen

BELANGRIJKE REGELS

Voor afas.Bring_Verzuim:

- Medewerker is GEEN naam.
- Naam bevat de medewerkernaam.
- Zoek medewerkers altijd via Naam.

Voorbeeld:

SELECT TOP 10 *
FROM afas.Bring_Verzuim
WHERE Naam LIKE '%Ranya%'

Persoonsnaam zoeken:

afas.Profit_Employees:
- FirstName

Gebruik ALTIJD deze kolommen voor naamzoeken.
Gebruik NOOIT andere kolommen voor persoonsnamen.


VOORBEELDEN

Vraag:
Wie wonen er in Dordrecht?

Tabel:
afas.Profit_Employees

Vraag:
Wie wonen er in Rotterdam?

Tabel:
afas.Profit_Employees

Vraag:
Wie zijn er geboren in maart?

Tabel:
afas.Profit_Employees

Vraag:
Wie is er ziek vandaag?

Tabel:
afas.Bring_Verzuim

Vraag:
Wie is er afwezig?

Tabel:
afas.Bring_Verzuim

Vraag:
Wie werkt fulltime?

Tabel:
afas.Bring_Employees

Vraag:
Wie heeft nog vakantiedagen?

Tabel:
afas.Profit_LeaveBalance

Persoonsgegevens
→ Profit_Employees

Contracten
→ Bring_Employees

Verzuim
→ Bring_Verzuim

Vakantiedagen
→ Profit_LeaveBalance

Gebruikersaccounts
→ Profit_Users
Tabel:
{selected_table}

Beschrijving:
{table_info["description"]}

Beschikbare kolommen:
{columns_text}

Regels voor kolommen:
- telefoon -> Phone of Mobile
- email/mail -> Mail of Email
- BSN -> BSN
- fulltime/parttime -> EmploymentTypeDesc
- uren per week -> HourPerWeek
- FTE -> FTE

Naam zoeken:
Als FirstName en BirthName bestaan, zoek dan altijd zo:
WHERE FirstName LIKE '%naam%'
OR BirthName LIKE '%achternaam%'

Voorbeeld:
SELECT TOP 10 Phone
FROM afas.Bring_Employees
WHERE FirstName LIKE '%Jan%'

FULLTIME / PARTTIME

Gebruik EmploymentTypeDesc.

Mogelijke waarden:

- Fulltimer
- Parttimer
- Oproepkracht
- Stagiair
- Vaste medewerker

Voor fulltime:

WHERE EmploymentTypeDesc LIKE '%Full%'

Voor parttime:

WHERE EmploymentTypeDesc LIKE '%Part%'

Gebruik NOOIT:

Fulltime
Parttime
Full-time
Part-time

WOONPLAATS VRAGEN

Als de gebruiker vraagt:

- wie wonen er in ...
- welke collega's wonen er in ...
- medewerkers uit ...
- wie komen uit ...

Gebruik ALTIJD:

afas.Profit_Employees

Kolommen:
- City
- FirstName
- BirthName

Gebruik NOOIT:

afas.Bring_KnOrganisation

Gebruikersvraag:
{question}
"""

        response = llm.invoke(sql_prompt).content.strip()

        print("========== RAW SQL RESPONSE ==========")
        print(response)

        sql_query = clean_sql_response(response)

        if not sql_query:
            return f"RAW RESPONSE: {response}"

        print("========== SQL QUERY ==========")
        print(sql_query)

        # =========================
        # VEILIGHEID
        # =========================

        sql_query_lower = sql_query.lower().strip()

        blocked_words = [
            "drop",
            "delete",
            "update",
            "insert",
            "alter",
            "create",
            "truncate",
            "merge"
        ]

        if not sql_query_lower.startswith("select"):
            return "Alleen SELECT queries zijn toegestaan."

        if any(word in sql_query_lower for word in blocked_words):
            return "Alleen veilige SELECT queries zijn toegestaan."

        try:
            with engine_emp.connect() as conn:
                result = conn.execute(text(sql_query))
                rows = result.fetchall()

                if not rows:
                    return "Geen resultaten gevonden."

                formatted = []

                for row in rows:
                    formatted.append(dict(row._mapping))

                formatted_json = json.dumps(
                    formatted,
                    indent=2,
                    ensure_ascii=False,
                    default=str
                )

                final_prompt = f"""
Gebruikersvraag:
{question}

Database resultaat:
{formatted_json}

Geef een kort duidelijk Nederlands antwoord.
"""

                final_answer = llm.invoke(final_prompt).content.strip()

                return final_answer

        except Exception as e:
            print("SQL ERROR:")
            print(e)

            return f"SQL fout: {str(e)}"
        print(e)

        return f"SQL fout: {str(e)}"

    # =========================
    # FALLBACK
    # =========================

    return "Ik begrijp de vraag niet."

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
# CHAT ENDPOINT
# =========================

@app.post("/chat")
async def chat(req: ChatReq):

    session_id = (
        req.session_id
        or "default-session"
    )

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

# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )