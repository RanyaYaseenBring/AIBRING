from sqlalchemy import text

session_states = {}

# =====================================================
# STATE MANAGEMENT
# =====================================================

def create_tracking_state():

    return {
        "tracking_active": False,
        "tracking_number": None,
        "waiting_for_tracking_number": False,
        "waiting_for_zipcode_question": False,
        "waiting_for_zipcode": False,
        "waiting_for_continue": False,
        "language": "english"
    }


def get_user_state(session_id):

    if session_id not in session_states:

        session_states[session_id] = create_tracking_state()

    return session_states[session_id]


def reset_state(session_id):

    session_states[session_id] = create_tracking_state()

# =====================================================
# AI REPLY
# =====================================================

def ai_reply(llm, language, instruction):

    prompt = f"""
You are a logistics assistant.

STRICT RULES:
- Reply ONLY in this language: {language}
- NEVER translate.
- NEVER switch languages.
- Keep responses short and natural.
- Never use random foreign languages.
- Output ONLY the final response text.
- Never explain rules.
- Never explain translations.
- Never add extra commentary.

TASK:
{instruction}
"""

    try:

        response = llm.invoke(prompt)

        return response.content.strip()

    except Exception:

        return "Something went wrong."

# =====================================================
# LANGUAGE DETECTION
# =====================================================

def detect_language(llm, msg):

    prompt = f"""
Detect the language of this message.

ONLY return:
english
or
dutch

MESSAGE:
{msg}
"""

    try:

        result = (
            llm.invoke(prompt)
            .content
            .strip()
            .lower()
        )

        if result not in ["english", "dutch"]:

            return "english"

        return result

    except:

        return "english"

# =====================================================
# INTENT CLASSIFIER
# =====================================================

def classify_tracking_intent(msg, llm):

    prompt = f"""
You are a STRICT intent classifier.

You may ONLY return ONE of these exact words:

tracking
yes
no
unknown

RULES:
- Return ONLY one word
- No punctuation
- No explanations
- No sentences
- Never answer conversationally
- Never translate

TRACKING EXAMPLES:

track and trace -> tracking
tracking -> tracking
where is my package -> tracking
where is my shipment -> tracking
pakket volgen -> tracking
zending volgen -> tracking
waar is mijn pakket -> tracking

YES EXAMPLES:

yes -> yes
yeah -> yes
ja -> yes

NO EXAMPLES:

no -> no
nee -> no

USER MESSAGE:
{msg}
"""

    try:

        result = (
            llm.invoke(prompt)
            .content
            .strip()
            .lower()
        )

        allowed = {
            "tracking",
            "yes",
            "no",
            "unknown"
        }

        return result if result in allowed else "unknown"

    except Exception:

        return "unknown"

# =====================================================
# SHOULD USE TRACKING
# =====================================================

def should_use_tracking(msg, session_id, llm):

    state = get_user_state(session_id)

    if (
        state["tracking_active"]
        or state["waiting_for_tracking_number"]
        or state["waiting_for_zipcode_question"]
        or state["waiting_for_zipcode"]
        or state["waiting_for_continue"]
    ):
        return True

    intent = classify_tracking_intent(msg, llm)

    return intent == "tracking"

# =====================================================
# FETCH TRACKING DATA
# =====================================================

def fetch_tracking_data(
    engine_track,
    tracking_number,
    include_full=False
):

    tracking_number = (
        tracking_number
        .replace("-", "")
        .replace(" ", "")
    )

    if include_full:

        sql = text("""
            SELECT
                PRIMARYREFERENCE,
                EXPECTED_DELIVERYDATE,
                EDIREFERENCE,

                L_NAMELINE1,
                L_ADDRESSLINE1,
                L_ZIPCODE,
                L_CITY,
                L_COUNTRY_FULL,

                U_NAMELINE1,
                U_ADDRESSLINE1,
                U_ZIPCODE,
                U_CITY,
                U_COUNTRY_FULL

            FROM [BRING].[v_dossiers]

            WHERE
                REPLACE(REPLACE(
                    CAST(PRIMARYREFERENCE AS NVARCHAR(100)),
                    '-', ''
                ), ' ', '') = :tracking

                OR

                REPLACE(REPLACE(
                    CAST(EDIREFERENCE AS NVARCHAR(100)),
                    '-', ''
                ), ' ', '') = :tracking

                OR

                REPLACE(REPLACE(
                    CAST(INTERNALNUMBER AS NVARCHAR(100)),
                    '-', ''
                ), ' ', '') = :tracking
        """)

    else:

        sql = text("""
            SELECT
                EDIREFERENCE,
                EXPECTED_DELIVERYDATE

            FROM [BRING].[v_dossiers]

            WHERE
                REPLACE(REPLACE(
                    CAST(PRIMARYREFERENCE AS NVARCHAR(100)),
                    '-', ''
                ), ' ', '') = :tracking

                OR

                REPLACE(REPLACE(
                    CAST(EDIREFERENCE AS NVARCHAR(100)),
                    '-', ''
                ), ' ', '') = :tracking

                OR

                REPLACE(REPLACE(
                    CAST(INTERNALNUMBER AS NVARCHAR(100)),
                    '-', ''
                ), ' ', '') = :tracking
        """)

    with engine_track.connect() as conn:

        row = conn.execute(
            sql,
            {
                "tracking": tracking_number
            }
        ).fetchone()

        return row

# =====================================================
# HANDLE TRACKING
# =====================================================

def handle_tracking(msg, engine_track, llm, session_id):

    if not should_use_tracking(msg, session_id, llm):
        return None

    user_state = get_user_state(session_id)

    msg = msg.strip()

    language = user_state["language"]

    # =====================================================
    # CONTINUE FLOW
    # =====================================================

    if user_state["waiting_for_continue"]:

        intent = classify_tracking_intent(msg, llm)

        if intent == "yes":

            reset_state(session_id)

            user_state = get_user_state(session_id)

            user_state["language"] = language
            user_state["tracking_active"] = True
            user_state["waiting_for_tracking_number"] = True

            return "Please provide the tracking number."

        if intent == "no":

            reset_state(session_id)

            return "How else can I help you?"

        return "Please answer with yes or no."


    # =====================================================
    # ZIPCODE QUESTION FLOW
    # =====================================================

    if user_state["waiting_for_zipcode_question"]:

        intent = classify_tracking_intent(msg, llm)

        if intent not in {"yes", "no"}:
            return "Please answer with yes or no."

        tracking_number = user_state["tracking_number"]

        user_state["waiting_for_zipcode_question"] = False

        # USER HAS ZIPCODE
        if intent == "yes":

            user_state["waiting_for_zipcode"] = True

            return "Please provide the zipcode."

        # USER HAS NO ZIPCODE
        try:

            row = fetch_tracking_data(
                engine_track,
                tracking_number,
                include_full=False
            )

            if not row:

                reset_state(session_id)

                return "No shipment was found."

        except Exception as e:

            reset_state(session_id)

            return str(e)

        user_state["waiting_for_continue"] = True

        response = (
            f"EDI reference: {row[0]}\n"
            f"Expected delivery day: {row[1]}"
        )

        return response
    # =====================================================
    # ZIPCODE VALIDATION FLOW
    # =====================================================

    if user_state["waiting_for_zipcode"]:

        tracking_number = user_state["tracking_number"]

        try:

            row = fetch_tracking_data(
                engine_track,
                tracking_number,
                include_full=True
            )

            if not row:

                reset_state(session_id)

                return "No shipment was found."

            data = dict(row._mapping)

        except Exception as e:

            reset_state(session_id)

            return str(e)

        zipcode_input = (
            msg
            .replace(" ", "")
            .lower()
        )

        l_zip = str(
            data.get("L_ZIPCODE", "")
        ).replace(" ", "").lower()

        u_zip = str(
            data.get("U_ZIPCODE", "")
        ).replace(" ", "").lower()

        if zipcode_input not in {l_zip, u_zip}:

            return "The provided zipcode does not match the shipment."

        user_state["waiting_for_zipcode"] = False
        user_state["waiting_for_continue"] = True

        response = (
            f"Bring reference: "
            f"{data.get('PRIMARYREFERENCE')}\n\n"

            f"Customer reference: "
            f"{data.get('EDIREFERENCE')}\n\n"

            f"Expected delivery day: "
            f"{data.get('EXPECTED_DELIVERYDATE')}\n\n"

            f"Sender:\n"
            f"{data.get('L_NAMELINE1')}\n"
            f"{data.get('L_ADDRESSLINE1')}\n"
            f"{data.get('L_ZIPCODE')} "
            f"{data.get('L_CITY')}\n"
            f"{data.get('L_COUNTRY_FULL')}\n\n"

            f"Receiver:\n"
            f"{data.get('U_NAMELINE1')}\n"
            f"{data.get('U_ADDRESSLINE1')}\n"
            f"{data.get('U_ZIPCODE')} "
            f"{data.get('U_CITY')}\n"
            f"{data.get('U_COUNTRY_FULL')}"
        )

        return response

    # =====================================================
    # TRACKING NUMBER FLOW
    # =====================================================

    if (
        user_state["tracking_active"]
        and user_state["waiting_for_tracking_number"]
    ):

        clean_msg = (
            msg
            .replace(" ", "")
            .replace("-", "")
        )

        if (
            not clean_msg.isdigit()
            or not (6 <= len(clean_msg) <= 30)
        ):

            return "Please provide a valid tracking number."

        try:

            row = fetch_tracking_data(
                engine_track,
                clean_msg,
                include_full=False
            )

            if not row:

                return "Tracking number not found."

        except Exception as e:

            return str(e)

        user_state["tracking_number"] = clean_msg

        user_state["waiting_for_tracking_number"] = False
        user_state["waiting_for_zipcode_question"] = True

        return "Do you have the recipient's zipcode? Yes or no."

    # =====================================================
    # START TRACKING FLOW
    # =====================================================

    intent = classify_tracking_intent(msg, llm)

    if intent == "tracking":

        detected_language = detect_language(
            llm,
            msg
        )

        user_state["language"] = detected_language

        user_state["tracking_active"] = True
        user_state["waiting_for_tracking_number"] = True

        return "Please provide the tracking number."
    return None