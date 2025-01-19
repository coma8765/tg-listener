import gspread
from oauth2client.client import Credentials
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

# Инициализация Google Sheets
def initialize_google_sheet(sheet_name, credentials_file="service_account.json"):
    """
    Инициализация подключения к Google Sheet через gspread.
    
    :param sheet_name: Название Google Таблицы.
    :param credentials_file: Путь к файлу учетных данных Service Account.
    :return: Объект таблицы (sheet).
    """
    # try:
    # Указываем области авторизации
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Загружаем учетные данные
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)

    # Авторизация в gspread
    client = gspread.authorize(credentials)
    
    # Открытие таблицы по имени
    raw_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1gb6rinB092NgxNgBUdj-cKPNSAPyvRn2u_rRUdFfOLA')
    # client.open_by_url(raw_sheet.url)
    sheet = raw_sheet.get_worksheet_by_id('1995862865')

    print(raw_sheet.url)
    print("Успешно подключено к Google Sheet.")
    return sheet
    # except Exception as e:
    #     print("Ошибка подключения к Google Sheet:", e)
    #     return None

# Функция для обработки и записи статусов в таблицу
def log_status_to_google_sheet(sheet: gspread.worksheet.Worksheet, events: list[dict]):
    """
    Записывает информацию о статусе пользователя из события JSON в Google Таблицу.
    
    :param sheet: Объект таблицы (sheet) из gspread.
    :param event: JSON-объект события.
    """

    rows = []

    for event in events:
        try:
            # Получаем данные из JSON
            user_id = event['user_id']
            status_type = event['status']['_']
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Определяем дополнительные детали (например, время `expires`/`was_online`)
            details = ""
            if status_type == "UserStatusOnline":
                details = f"expires: {event['status'].get('expires', 'N/A')}"
            elif status_type == "UserStatusOffline":
                details = f"was_online: {event['status'].get('was_online', 'N/A')}"

            # Данные для записи в таблицу
            row = [timestamp, user_id, status_type, details]

            rows.append(row)
        except Exception as e:
            print("Ошибка записи в Google Таблицу:", e)

    sheet.append_rows(rows)

# Пример использования
if __name__ == "__main__":
    # Имя Google Таблицы
    SHEET_NAME = "Telegram Status Logger"
    CREDENTIALS_FILE = "/Users/ananevn002/Downloads/bauman-help-21dc97a5e5f8.json"

    # Подключаемся к Google Таблице
    sheet = initialize_google_sheet(SHEET_NAME, CREDENTIALS_FILE)

    # Проверяем, что таблица подключена
    if sheet:
        # Пример журнала статусов в JSON формате
        events = [
            {"_": "UpdateUserStatus", "user_id": 503697665, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:14:21+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 503697665, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:19:55+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 6938433068, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:20:03+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1124038569, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:20:04+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 6938433068, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:15:06+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 503697665, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:15:18+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1062187409, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:20:33+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1062187409, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:15:39+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1424970102, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:20:47+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1124038569, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:15:55+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1062187409, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:20:58+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1124038569, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:20:59+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1124038569, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:16:01+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 963334626, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:21:05+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1062187409, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:16:15+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 503697665, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:21:26+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 503697665, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:16:35+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 963334626, "status": {"_": "UserStatusOffline", "was_online": "2025-01-18T20:16:38+00:00"}},
            {"_": "UpdateUserStatus", "user_id": 1062187409, "status": {"_": "UserStatusOnline", "expires": "2025-01-18T20:21:54+00:00"}}
        ]

        # Передаем каждое событие в функцию записи
        # for event in events:
        log_status_to_google_sheet(sheet, events)
