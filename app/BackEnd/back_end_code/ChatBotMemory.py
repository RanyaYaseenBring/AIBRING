import json
import os

def save_chat_memory(user_message, bot_response, file_path="chat_memory.json"):
    
    if not os.path.exists(file_path):
        data = {"default": []}
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {"default": []}

    data["default"].append({
        "user": user_message,
        "bot": bot_response
    })

    # Opslaan
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)