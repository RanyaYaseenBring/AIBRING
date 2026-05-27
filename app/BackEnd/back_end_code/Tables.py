from sqlalchemy import text
from main import engine
# =========================================================
# TABLE GROUPS
# =========================================================

TABLE_GROUPS = {

    "employees": [
        "afas.Bring_Employees",
        "afas.Profit_Employees",
        "afas.Profit_Users",
        "afas.Profit_UserGroups"
    ],

    "employee_details": [
        "afas.Bring_Medewerker_Functie",
        "afas.Bring_Medewerker_Contract",
        "afas.Bring_Medewerker_Salaris",
        "afas.Bring_Verzuim",
        "afas.Bring_LeaveTypes",
        "afas.Profit_LeaveBalance"
    ],

    "finance": [
        "afas.Bring_FinancieleMutaties_ESJ",
        "afas.Bring_Debtor_Invoices",
        "afas.Profit_Debtor",
        "afas.Profit_Journals"
    ],

    "organization": [
        "afas.Bring_KNOrganisation"
    ],

    "workflow": [
        "afas.Bring_workflow_log"
    ],

    "logs": [
        "_logs.ProcesssingLog",
        "_logs.EtlRunLog"
    ],

    "system": [
        "_etl.APITokens",
        "_etl.Data_processor",
        "_etl.EndpointConfig"
    ],

    "LSP": [
        "dbo.Tally",
        "LSP_NL.bcnl_edirefs",
        "LSP_NL.peppol_lijn12"
    ]
}


# =========================================================
# DATABASE SCHEMA BUILDER
# =========================================================

def get_database_schema(engine):

    schema_text = ""

    with engine.connect() as conn:

        for group_name, tables in TABLE_GROUPS.items():

            schema_text += f"\n\n==============================\n"
            schema_text += f"GROUP: {group_name}\n"
            schema_text += f"==============================\n"

            for table in tables:

                try:

                    # -----------------------------
                    # SPLIT SCHEMA + TABLE
                    # -----------------------------

                    if "." in table:
                        schema_name, table_name = table.split(".", 1)
                    else:
                        schema_name = "dbo"
                        table_name = table

                    schema_text += f"\n\nTable: {table}\n"
                    schema_text += "-" * 50 + "\n"

                    # -----------------------------
                    # GET COLUMNS
                    # -----------------------------

                    column_query = text("""
                        SELECT 
                            COLUMN_NAME,
                            DATA_TYPE,
                            IS_NULLABLE
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = :schema
                        AND TABLE_NAME = :table
                        ORDER BY ORDINAL_POSITION
                    """)

                    columns = conn.execute(
                        column_query,
                        {
                            "schema": schema_name,
                            "table": table_name
                        }
                    ).fetchall()

                    if not columns:

                        schema_text += "No columns found.\n"
                        continue

                    # -----------------------------
                    # WRITE COLUMNS
                    # -----------------------------

                    for col in columns:

                        nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"

                        schema_text += (
                            f"- {col.COLUMN_NAME} "
                            f"({col.DATA_TYPE}, {nullable})\n"
                        )

                    # -----------------------------
                    # SAMPLE DATA
                    # -----------------------------

                    try:

                        sample_query = text(f"""
                            SELECT TOP 3 *
                            FROM [{schema_name}].[{table_name}]
                        """)

                        sample_rows = conn.execute(sample_query).fetchall()

                        if sample_rows:

                            schema_text += "\nSample rows:\n"

                            for row in sample_rows:

                                row_dict = dict(row._mapping)

                                cleaned_row = {}

                                for key, value in row_dict.items():

                                    value = str(value)

                                    if len(value) > 50:
                                        value = value[:50] + "..."

                                    cleaned_row[key] = value

                                schema_text += f"{cleaned_row}\n"

                    except Exception as sample_error:

                        schema_text += (
                            f"\nCould not load sample data: "
                            f"{sample_error}\n"
                        )

                except Exception as table_error:

                    schema_text += (
                        f"\nERROR loading table {table}: "
                        f"{table_error}\n"
                    )

    return schema_text


# =========================================================
# LOAD DATABASE SCHEMA ON STARTUP
# =========================================================

DATABASE_SCHEMA = get_database_schema(engine)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = f"""
You are an advanced SQL Server AI assistant.

You have access to the following database schema:

{DATABASE_SCHEMA}

Rules:
- Only use existing tables and columns
- Never invent columns or tables
- Use valid SQL Server syntax
- Use TOP instead of LIMIT
- Use readable JOINs
- Prefer exact column names
- Return only valid SQL when generating queries
- If information is missing, say so
- Be careful with DELETE or UPDATE statements
- Never generate destructive SQL unless explicitly requested
"""


# =========================================================
# BUILD FINAL PROMPT
# =========================================================

def build_prompt(question: str):

    return f"""
User question:
{question}
"""


# =========================================================
# ASK OLLAMA
# =========================================================

def ask_ollama(llm, question: str):

    user_prompt = build_prompt(question)

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", user_prompt)
    ])

    return response.content