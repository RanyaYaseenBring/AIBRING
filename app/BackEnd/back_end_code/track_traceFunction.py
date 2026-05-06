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


def should_use_tracking(msg, session_id):
    state = get_user_state(session_id)
    msg_lower = msg.strip().lower()

    tracking_keywords = {"track", "trace", "tracking", "shipment", "package"}

    if any(keyword in msg_lower for keyword in tracking_keywords):
        return True

    if (
        state["tracking_active"]
        or state["waiting_for_tracking_number"]
        or state["waiting_for_zipcode_question"]
        or state["waiting_for_zipcode"]
        or state["waiting_for_choice"]
        or state["waiting_for_continue"]
    ):
        return True

    return False


def classify_yes_no(msg, llm):
    msg_clean = msg.strip().lower()

    if msg_clean in {"yes", "yeah", "yep", "ja", "zeker", "natuurlijk"}:
        return "yes"

    if msg_clean in {"no", "nope", "nee", "nah"}:
        return "no"

    try:
        result = llm.invoke(generate_prompt(msg, mode="yesno")).content.strip().lower()

        if result.startswith("yes"):
            return "yes"

        if result.startswith("no"):
            return "no"

        return "unknown"

    except Exception:
        return "unknown"


def classify_tracking_intent(msg, llm):
    prompt = f"""
You are a strict intent classifier.
Understand the user input in ANY language.

User input: "{msg}"

Return EXACTLY one of:
delivery
reference
sender_name
sender_address
receiver_name
receiver_address
full
unknown

Only return one word. No explanation.
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
            "unknown"
        }
        return result if result in allowed else "unknown"

    except Exception:
        return "unknown"


def fetch_tracking_data(engine_track, tracking_number, include_full=False):
    tracking_number = tracking_number.replace("-", "").replace(" ", "")

    if include_full:
        sql = text("""
            SELECT PRIMARYREFERENCE, EXPECTED_DELIVERYDATE, EDIREFERENCE,
                   L_NAMELINE1, L_ADDRESSLINE1, L_ZIPCODE, L_CITY, L_COUNTRY_FULL,
                   U_NAMELINE1, U_ADDRESSLINE1, U_ZIPCODE, U_CITY, U_COUNTRY_FULL
            FROM [BRING].[v_dossiers]
            WHERE
                REPLACE(REPLACE(CAST(PRIMARYREFERENCE AS NVARCHAR(100)), '-', ''), ' ', '') LIKE :tracking
                OR REPLACE(REPLACE(CAST(EDIREFERENCE AS NVARCHAR(100)), '-', ''), ' ', '') LIKE :tracking
                OR REPLACE(REPLACE(CAST(INTERNALNUMBER AS NVARCHAR(100)), '-', ''), ' ', '') LIKE :tracking
        """)
    else:
        sql = text("""
            SELECT PRIMARYREFERENCE, EXPECTED_DELIVERYDATE
            FROM [BRING].[v_dossiers]
            WHERE
                REPLACE(REPLACE(CAST(PRIMARYREFERENCE AS NVARCHAR(100)), '-', ''), ' ', '') LIKE :tracking
                OR REPLACE(REPLACE(CAST(EDIREFERENCE AS NVARCHAR(100)), '-', ''), ' ', '') LIKE :tracking
                OR REPLACE(REPLACE(CAST(INTERNALNUMBER AS NVARCHAR(100)), '-', ''), ' ', '') LIKE :tracking
        """)

    with engine_track.connect() as conn:
        return conn.execute(sql, {"tracking": f"%{tracking_number}%"}).fetchone()


def handle_tracking(msg, engine_track, llm, session_id):
    if not should_use_tracking(msg, session_id):
        return None

    user_state = get_user_state(session_id)
    msg = msg.strip()
    msg_lower = msg.lower()

    # Continue flow
    if user_state["waiting_for_continue"]:
        answer = classify_yes_no(msg, llm)

        if answer == "yes":
            reset_state(session_id)
            user_state = get_user_state(session_id)
            user_state["tracking_active"] = True
            user_state["waiting_for_tracking_number"] = True
            return "Please provide your tracking number"

        if answer == "no":
            reset_state(session_id)
            return "Hoe kan ik je verder helpen?"

        return "Please answer yes or no"

    # Choice flow
    if user_state["waiting_for_choice"]:
        data = user_state["data"]
        msg_clean = msg.lower()

        if msg_clean in {"sender", "sender name", "sender_name", "zender naam"}:
            intent = "sender_name"
        elif msg_clean in {"sender address", "address sender", "sender_address" "zender naam"}:
            intent = "sender_address"
        elif msg_clean in {"receiver", "receiver name", "receiver_name", "ontvanger naam"}:
            intent = "receiver_name"
        elif msg_clean in {"receiver address", "address receiver", "receiver_address" "ontvanger adres"}:
            intent = "receiver_address"
        elif msg_clean in {"delivery", "delivery date", "eta", "when"}:
            intent = "delivery"
        elif msg_clean in {"reference", "tracking reference"}:
            intent = "reference"
        elif msg_clean in {"all", "full", "everything" "alles"}:
            intent = "full"
        else:
            intent = classify_tracking_intent(msg, llm)

        if intent == "unknown":
            return "I did not understand what you want to see."

        if intent == "delivery":
            response = f"Expected deliveryday: {data.get('EXPECTED_DELIVERYDATE')}"
        elif intent == "reference":
            response = f"Bring reference: {data.get('PRIMARYREFERENCE')}"
        elif intent == "sender_name":
            response = f"Sender: {data.get('L_NAMELINE1')}"
        elif intent == "sender_address":
            response = (
                f"Sender Address:\n"
                f"{data.get('L_ADDRESSLINE1')}\n"
                f"{data.get('L_ZIPCODE')} {data.get('L_CITY')}\n"
                f"{data.get('L_COUNTRY_FULL')}"
            )
        elif intent == "receiver_name":
            response = f"Receiver: {data.get('U_NAMELINE1')}"
        elif intent == "receiver_address":
            response = (
                f"Receiver Address:\n"
                f"{data.get('U_ADDRESSLINE1')}\n"
                f"{data.get('U_ZIPCODE')} {data.get('U_CITY')}\n"
                f"{data.get('U_COUNTRY_FULL')}"
            )
        else:
            response = (
                f"Bring reference: {data.get('PRIMARYREFERENCE')}\n"
                f"Customer reference: {data.get('EDIREFERENCE')}\n"
                f"Expected deliveryday: {data.get('EXPECTED_DELIVERYDATE')}\n\n"
                f"Sender:\n{data.get('L_NAMELINE1')}\n"
                f"{data.get('L_ADDRESSLINE1')}\n"
                f"{data.get('L_ZIPCODE')} {data.get('L_CITY')}\n"
                f"{data.get('L_COUNTRY_FULL')}\n\n"
                f"Receiver:\n{data.get('U_NAMELINE1')}\n"
                f"{data.get('U_ADDRESSLINE1')}\n"
                f"{data.get('U_ZIPCODE')} {data.get('U_CITY')}\n"
                f"{data.get('U_COUNTRY_FULL')}"
            )

        user_state["waiting_for_choice"] = False
        user_state["waiting_for_continue"] = True
        return response + "\n\nDo you want to see something else? (yes/no)"

    # Zipcode validation flow
    if user_state["waiting_for_zipcode"]:
        tracking_number = user_state["tracking_number"]

        try:
            row = fetch_tracking_data(engine_track, tracking_number, include_full=True)
            if not row:
                reset_state(session_id)
                return "No result found"

            data = dict(row._mapping)

        except Exception as e:
            reset_state(session_id)
            return str(e)

        zipcode_input = msg.replace(" ", "").lower()
        l_zip = str(data.get("L_ZIPCODE", "")).replace(" ", "").lower()
        u_zip = str(data.get("U_ZIPCODE", "")).replace(" ", "").lower()

        if zipcode_input not in {l_zip, u_zip}:
            return "ZipCode does not match this shipment. Please try again"

        user_state["waiting_for_zipcode"] = False
        user_state["waiting_for_choice"] = True
        user_state["data"] = data

        return (
            f"What would you like to know about order {tracking_number}?\n"
            f"- delivery\n"
            f"- reference\n"
            f"- sender name\n"
            f"- sender address\n"
            f"- receiver name\n"
            f"- receiver address\n"
            f"- full"
        )

    # Ask if user has zipcode
    if user_state["waiting_for_zipcode_question"]:
        answer = classify_yes_no(msg, llm)

        if answer == "unknown":
            return "Please answer yes or no"

        tracking_number = user_state["tracking_number"]
        user_state["waiting_for_zipcode_question"] = False

        if answer == "yes":
            user_state["waiting_for_zipcode"] = True
            return "Please provide your ZipCode"

        try:
            row = fetch_tracking_data(engine_track, tracking_number, include_full=False)
            if not row:
                reset_state(session_id)
                return "No result found"

        except Exception as e:
            reset_state(session_id)
            return str(e)

        user_state["waiting_for_continue"] = True
        return (
            f"Bring reference: {row[0]}\n"
            f"Expected deliveryday: {row[1]}\n\n"
            "Do you want to see something else? (yes/no)"
        )

    # Start tracking flow
    if any(keyword in msg_lower for keyword in {"track", "trace", "tracking"}):
        user_state["tracking_active"] = True
        user_state["waiting_for_tracking_number"] = True
        return "Please provide your tracking number"

    # Tracking number input
    if user_state["tracking_active"] and user_state["waiting_for_tracking_number"]:
        clean_msg = msg.replace(" ", "").replace("-", "")

        if not clean_msg.isdigit() or not (6 <= len(clean_msg) <= 30):
            return "Please provide a valid tracking number"

        try:
            row = fetch_tracking_data(engine_track, clean_msg, include_full=False)
            if not row:
                return "Tracking number not found"

        except Exception as e:
            return str(e)

        user_state["tracking_number"] = clean_msg
        user_state["waiting_for_tracking_number"] = False
        user_state["waiting_for_zipcode_question"] = True
        return "Do you have a ZipCode? (yes/no)"

    return None