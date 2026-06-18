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

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)



app = FastAPI()
chat_sessions = {}


# =========================
# CORS
# =========================

# Definieer de exacte URL's die toegang krijgen tot je API
origins = [
    "http://localhost:3000",  # Standaard React poort
    "http://localhost:5173",  # Standaard Vite + React poort
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Gebruik de lijst in plaats van "*"
    allow_credentials=True,  # Dit is vaak nodig voor inlogsessies
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DATABASE CONNECTION
# =========================

def make_engine(server, database, username, password):
    odbc_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
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

engine_ranya = make_engine(
    "172.20.20.66",
    "Test_2025",
    "ranya",
    "BobrKurwa1996!"
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
        state["history"] = []
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
    if msg_lower in ["interne vraag", "intern"]:
        state["mode"] = "internal"
        return "Interne modus geactiveerd. Stel uw vraag."

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

    if state["mode"] == "internal":
        try:
            return handle_internal_question(msg)
        except Exception as e:
            return f"SQL fout: {str(e)}"

    if state["mode"] == "general":
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

# =========================
# REQUEST MODELS
# =========================


# =========================
# REQUEST MODELS
# =========================

class ChatReq(BaseModel):
    message: str
    session_id: str | None = None


class LoginReq(BaseModel):
    username: str
    password: str


class ChangePasswordReq(BaseModel):
    username: str
    password: str

class DeleteUserReq(BaseModel):
    username: str


# =========================
# ROUTES
# =========================
# =========================
# ROUTES
# =========================

@app.get("/users")
def get_users():
    with engine_ranya.connect() as conn:
        result = conn.execute(text("""
            SELECT user_id, username
            FROM dbo.users_ai
            ORDER BY user_id
        """))

        users = [
            {
                "user_id": row["user_id"],
                "username": row["username"],
                "role": "admin" if row["username"] == "admin" else "user"
            }
            for row in result.mappings()
        ]

    return {
        "success": True,
        "users": users
    }


@app.post("/register")
def register(req: LoginReq):
    print("REGISTER AANGEROEPEN VOOR:", req.username)
    try:
        with engine_ranya.connect() as conn:
            exist_check = conn.execute(
                text("SELECT TOP 1 username FROM dbo.users_ai WHERE username = :username"),
                {"username": req.username}
            ).mappings().first()

        if exist_check:
            return {"success": False, "message": "Gebruikersnaam bestaat al!"}

        hashed_password = pwd_context.hash(req.password)

        with engine_ranya.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO dbo.users_ai (username, password_hash)
                    VALUES (:username, :password_hash)
                """),
                {"username": req.username, "password_hash": hashed_password}
            )
        return {"success": True, "message": "Gebruiker succesvol toegevoegd!"}
    except Exception as e:
        print("REGISTER ERROR:", str(e))
        return {"success": False, "message": f"Database fout: {str(e)}"}

# VERWIJDER DE DUBBELE /CHAT ROUTE ONDERAAN EN HOUD ALLEEN DEZE OVER:
@app.post("/chat")
async def chat(req: ChatReq):
    session_id = req.session_id or "default-session"
    print(f"Bericht ontvangen van {session_id}: {req.message}")

    try:
        # Roep je LLM / AI functie aan
        ans = await run_in_threadpool(
            lambda: answer_question(
                req.message,
                session_id
            )
        )
    except Exception as e:
        print("CHAT ERROR:", str(e))
        ans = f"Backend fout: {str(e)}"

    # Sla het gesprek op in het geheugen
    try:
        save_chat_memory(
            session_id,
            req.message,
            ans
        )
    except Exception as mem_err:
        print("GEHEUGEN OPSLAG FOUT:", str(mem_err))

    return {
        "answer": ans,
        "session_id": session_id
    }


@app.post("/login")
def login(req: LoginReq):
    print("LOGIN POGING VOOR:", req.username)
    
    try:
        with engine_ranya.connect() as conn:
            # We halen ALLEEEN username en password_hash op, GEEN role!
            user = conn.execute(
                text("SELECT username, password_hash FROM dbo.users_ai WHERE username = :username"),
                {"username": req.username}
            ).mappings().first()

        if not user:
            return {"success": False, "message": "Gebruikersnaam of wachtwoord onjuist."}

        # Veilige check voor het wachtwoord
        try:
            is_valid = pwd_context.verify(req.password, user["password_hash"])
        except Exception as hash_err:
            print(f"Hash verificatie gecrasht voor {req.username}: {hash_err}")
            return {"success": False, "message": "Database integriteitsfout."}

        if not is_valid:
            return {"success": False, "message": "Gebruikersnaam of wachtwoord onjuist."}

        # Omdat je geen role-kolom hebt, bepalen we de rol hier in Python:
        # Als de gebruikersnaam 'admin' is, krijgt deze de rol 'admin', anders 'user'.
        user_role = "admin" if user["username"].lower() == "admin" else "user"

        return {
            "success": True,
            "username": user["username"],
            "role": user_role,  # De frontend krijgt hiermee netjes een rol doorgestuurd
            "message": "Succesvol ingelogd!"
        }

    except Exception as e:
        print("LOGIN ALGEMENE ERROR:", str(e))
        return {"success": False, "message": f"Serverfout tijdens inloggen: {str(e)}"}

@app.post("/change-password")
def change_password(req: ChangePasswordReq):
    try:
        hashed_password = pwd_context.hash(req.password)

        with engine_ranya.begin() as conn:
            conn.execute(
                text("""
                    UPDATE dbo.users_ai
                    SET password_hash = :password
                    WHERE username = :username
                """),
                {
                    "username": req.username,
                    "password": hashed_password
                }
            )
        return {"success": True}
    except Exception as e:
        print("CHANGE PASSWORD ERROR:", str(e))
        return {"success": False, "error": str(e)}

    
@app.post("/delete-user")
def delete_user(req: DeleteUserReq):
    if req.username == "admin":
        return {
            "success": False,
            "message": "Admin mag niet verwijderd worden"
        }

    try:
        with engine_ranya.begin() as conn:
            conn.execute(
                text("""
                    DELETE FROM dbo.users_ai
                    WHERE username = :username
                """),
                {"username": req.username}
            )
        return {"success": True}
    except Exception as e:
        print("DELETE ERROR:", str(e))
        return {"success": False, "error": str(e)}


@app.get("/dbtest")
def dbtest():
    try:
        with engine_ranya.connect() as conn:
            result = conn.execute(text("SELECT DB_NAME()"))
            return {
                "success": True,
                "database": result.scalar()
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)