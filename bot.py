import os
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime

# Налаштування доступу до Google Sheets
def setup_google_sheets():
    # Визначаємо обсяг доступу
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Завантажуємо облікові дані як словник зі змінної середовища
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    creds_dict = json.loads(creds_json)  # Парсимо JSON строку
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Відкриваємо таблицю за ID з посилання
    spreadsheet_id = "15Cp8O9FMz4UMxAtGBllC0urHqDozrlzfHNueXc4V5oI"
    sheet = client.open_by_key(spreadsheet_id).worksheet("Telegram ID")
    return sheet

# Функція для запису даних
def write_to_google_sheets(sheet, chat_id, user_name):
    # Визначаємо часову зону для Києва
    kyiv_tz = pytz.timezone('Europe/Kiev')

    # Поточна дата та час у Києві
    timestamp = datetime.now(kyiv_tz).strftime('%Y-%m-%d %H:%M:%S')

    # Отримуємо всі існуючі ID, щоб уникнути дублювання
    existing_ids = [row[0] for row in sheet.get_all_values()]

    if str(chat_id) not in existing_ids:
        # Додаємо рядок із даними
        sheet.append_row([chat_id, user_name, timestamp])
        return False  # Повертаємо False, якщо запису ще не було
    else:
        print(f"Chat ID {chat_id} вже існує.")
        return True  # Повертаємо True, якщо запис вже існує

# Обробка команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отримуємо ID чату та ім'я користувача
    chat_id = update.message.chat.id
    user_name = update.message.from_user.first_name

    # Записуємо дані в Google Таблицю
    try:
        sheet = setup_google_sheets()
        exists = write_to_google_sheets(sheet, chat_id, user_name)

        if exists:
            # Якщо запис існує
            await update.message.reply_text("Дякуємо, що запустили бота! Ваш запис вже існує.")
        else:
            # Якщо запису ще не було
            await update.message.reply_text(f"Привіт, {user_name}! Ваші дані збережено в таблиці.")
    except Exception as e:
        print(f"Помилка запису в Google Таблицю: {e}")
        await update.message.reply_text("Сталася помилка під час запису в Google Таблицю.")


# Основна функція
def main():
    # Отримання токена із змінної середовища
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додаємо обробник команди /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
