import os
import json
import gspread
import pytz
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime

app = Flask(__name__)

# Налаштування доступу до Google Sheets
def setup_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet_id = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"
    sheet = client.open_by_key(spreadsheet_id).worksheet("Telegram ID")
    return sheet

# Функція для запису даних
def write_to_google_sheets(sheet, chat_id, user_name):
    kyiv_tz = pytz.timezone('Europe/Kiev')
    timestamp = datetime.now(kyiv_tz).strftime('%Y-%m-%d %H:%M:%S')
    existing_ids = [row[0] for row in sheet.get_all_values()]
    if str(chat_id) not in existing_ids:
        sheet.append_row([chat_id, user_name, timestamp])
        return False
    else:
        print(f"Chat ID {chat_id} вже існує.")
        return True

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return 'OK'

def main():
    global bot
    global dispatcher
    token = os.getenv('TELEGRAM_TOKEN')
    bot = Bot(token)
    application = Application.builder(bot=bot).build()

    # Додаємо обробник команди /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    global dispatcher
    dispatcher = application.dispatcher
    
    webhook_url = 'https://telegram-bot-t1cy.onrender.com/webhook'
    application.bot.set_webhook(webhook_url)

    app.run(port=5000)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    try:
        sheet = setup_google_sheets()
        exists = write_to_google_sheets(sheet, chat_id, user_name)
        if exists:
            await update.message.reply_text("Дякуємо, що запустили бота! Ваш запис вже існує.")
        else:
            await update.message.reply_text(f"Привіт, {user_name}! Ваші дані збережено в таблиці.")
    except Exception as e:
        print(f"Помилка запису в Google Таблицю: {e}")
        await update.message.reply_text("Сталася помилка під час запису в Google Таблицю.")

if __name__ == '__main__':
    main()
