import json
import os

MEMORY_FILE = "chat_memory.json"


def save_chat_memory(
    username,
    user_message,
    bot_answer
):

    # =========================
    # LOAD JSON
    # =========================

    if os.path.exists(MEMORY_FILE):

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    else:

        data = {}

    # =========================
    # CREATE USER SECTION
    # =========================

    if username not in data:

        data[username] = []

    # =========================
    # ADD CHAT MEMORY
    # =========================

    data[username].append({

        "user": user_message,

        "bot": bot_answer

    })

    # =========================
    # SAVE JSON
    # =========================

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )