from sqlalchemy import text
from ChatbotPrompt import generate_prompt

session_states = {}

def create_tracking_state():
    return {
        "tracking_active": False,
        "tracking_number": None,
        "waiting_for_tracking_number": False,
        "waiting_for_zipcode_question": False,
        "waiting_for_zipcode": False,
        "waiting_for_choice": False,
        "waiting_for_continue": False,
        "data": None
    }


def get_user_state(session_id):
    if session_id not in session_states:
        session_states[session_id] = create_tracking_state()
    return session_states[session_id]


def reset_state(session_id):
    session_states[session_id] = create_tracking_state()


# =====================================================
# AI RESPONSE HELPER
# =====================================================

def ai_reply(llm, user_message, instruction):

    prompt = f"""
You are a multilingual logistics assistant.

IMPORTANT:
- Always answer in the SAME language as the user.
- Keep responses short and natural.
- Be conversational.
- Never explain your reasoning.

User message:
{user_message}

Instruction:
{instruction}
"""

    try:
        return llm.invoke(prompt).content.strip()

    except Exception:
        return instruction


# =====================================================
# INTENT CLASSIFIER
# =====================================================

def classify_tracking_intent(msg, llm):

    prompt = f"""
You are a strict intent classifier.

Understand the user input in ANY language.
You start in englsh and ONLY continue in the launguage of the user

User input:
"{msg}"

Return EXACTLY one of:

delivery
reference
sender_name
sender_address
receiver_name
receiver_address
full
tracking
yes
no
unknown

Only return one word.
No explanation.
"""
    try:

        result = llm.invoke(prompt).content.strip().lower()

        allowed = {
            "delivery",
            "reference",
            "sender_name",
            "sender_address",
            "receiver_name",
            "receiver_address",
            "full",
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
        or state["waiting_for_choice"]
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
                PRIMARYREFERENCE,
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
# MAIN TRACKING HANDLER
# =====================================================

def handle_tracking(msg, engine_track, llm, session_id):

    if not should_use_tracking(msg, session_id, llm):
        return None

    user_state = get_user_state(session_id)

    msg = msg.strip()

    # =================================================
    # CONTINUE FLOW
    # =================================================

    if user_state["waiting_for_continue"]:

        intent = classify_tracking_intent(msg, llm)

        if intent == "yes":

            reset_state(session_id)

            user_state = get_user_state(session_id)

            user_state["tracking_active"] = True
            user_state["waiting_for_tracking_number"] = True

            return ai_reply(
                llm,
                msg,
                "Ask the user to provide the tracking number."
            )

        if intent == "no":

            reset_state(session_id)

            return ai_reply(
                llm,
                msg,
                "Ask the user how else you can help."
            )

        return ai_reply(
            llm,
            msg,
            "Ask the user to answer yes or no."
        )

    # =================================================
    # CHOICE FLOW
    # =================================================

    if user_state["waiting_for_choice"]:

        data = user_state["data"]

        intent = classify_tracking_intent(msg, llm)

        if intent == "unknown":

            return ai_reply(
                llm,
                msg,
                "Tell the user you did not understand what information they want."
            )

        if intent == "delivery":

            response = (
                f"Expected delivery day: "
                f"{data.get('EXPECTED_DELIVERYDATE')}"
            )

        elif intent == "reference":

            response = (
                f"Bring reference: "
                f"{data.get('PRIMARYREFERENCE')}"
            )

        elif intent == "sender_name":

            response = (
                f"Sender: "
                f"{data.get('L_NAMELINE1')}"
            )

        elif intent == "sender_address":

            response = (
                f"Sender Address:\n"
                f"{data.get('L_ADDRESSLINE1')}\n"
                f"{data.get('L_ZIPCODE')} "
                f"{data.get('L_CITY')}\n"
                f"{data.get('L_COUNTRY_FULL')}"
            )

        elif intent == "receiver_name":

            response = (
                f"Receiver: "
                f"{data.get('U_NAMELINE1')}"
            )

        elif intent == "receiver_address":

            response = (
                f"Receiver Address:\n"
                f"{data.get('U_ADDRESSLINE1')}\n"
                f"{data.get('U_ZIPCODE')} "
                f"{data.get('U_CITY')}\n"
                f"{data.get('U_COUNTRY_FULL')}"
            )

        else:

            response = (
                f"Bring reference: "
                f"{data.get('PRIMARYREFERENCE')}\n"

                f"Customer reference: "
                f"{data.get('EDIREFERENCE')}\n"

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

        user_state["waiting_for_choice"] = False
        user_state["waiting_for_continue"] = True

        followup = ai_reply(
            llm,
            msg,
            "Ask the user if they want to see something else."
        )

        return f"{response}\n\n{followup}"

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

                return ai_reply(
                    llm,
                    msg,
                    "Tell the user no shipment was found."
                )

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

            return ai_reply(
                llm,
                msg,
                "Tell the user the zipcode does not match the shipment."
            )

        user_state["waiting_for_zipcode"] = False
        user_state["waiting_for_choice"] = True
        user_state["data"] = data

        return ai_reply(
            llm,
            msg,
            """
Ask the user what they want to know.

Options:
- delivery
- reference
- sender name
- sender address
- receiver name
- receiver address
- full
"""
        )

    # =================================================
    # ZIPCODE QUESTION
    # =================================================

    if user_state["waiting_for_zipcode_question"]:

        intent = classify_tracking_intent(msg, llm)

        if intent not in {"yes", "no"}:

            return ai_reply(
                llm,
                msg,
                "Ask the user to answer yes or no."
            )

        tracking_number = user_state["tracking_number"]

        user_state["waiting_for_zipcode_question"] = False

        if intent == "yes":

            user_state["waiting_for_zipcode"] = True

            return ai_reply(
                llm,
                msg,
                "Ask the user to provide the zipcode."
            )

        try:

            row = fetch_tracking_data(
                engine_track,
                tracking_number,
                include_full=False
            )

            if not row:

                reset_state(session_id)

                return ai_reply(
                    llm,
                    msg,
                    "Tell the user no shipment was found."
                )

        except Exception as e:

            reset_state(session_id)

            return str(e)

        user_state["waiting_for_continue"] = True

        followup = ai_reply(
            llm,
            msg,
            "Ask the user if they want to see something else."
        )

        return (
            f"Bring reference: {row[0]}\n"
            f"Expected delivery day: {row[1]}\n\n"
            f"{followup}"
        )

    # =================================================
    # START TRACKING
    # =================================================

    intent = classify_tracking_intent(msg, llm)

    if intent == "tracking":

        user_state["tracking_active"] = True
        user_state["waiting_for_tracking_number"] = True

        return ai_reply(
            llm,
            msg,
            "Ask the user to provide the tracking number."
        )

    # =================================================
    # TRACKING NUMBER INPUT
    # =================================================

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

            return ai_reply(
                llm,
                msg,
                "Tell the user to provide a valid tracking number."
            )

        try:

            row = fetch_tracking_data(
                engine_track,
                clean_msg,
                include_full=False
            )

            if not row:

                return ai_reply(
                    llm,
                    msg,
                    "Tell the user the tracking number was not found."
                )

        except Exception as e:

            return str(e)

        user_state["tracking_number"] = clean_msg

        user_state["waiting_for_tracking_number"] = False

        user_state["waiting_for_zipcode_question"] = True

        return ai_reply(
            llm,
            msg,
            "Ask the user if they have the zipcode."
        )

    return None

