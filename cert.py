import os
import telebot
import datetime
import ssl
import OpenSSL.crypto
import time

# # Настройки
CERT_FOLDERS = [
    r"\\localhost\e$\cert" #Указать путь
]

#окальный путь
# CERT_FOLDERS = [
#     os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert")
# ]

EXPIRATION_THRESHOLD = 40
BOT_TOKEN = ""
CHAT_ID = ""
CHECK_INTERVAL = 3600  # Проверять каждые 3600 секунд (1 час)
# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)


def send_telegram_message(message):
    try:
        bot.send_message(CHAT_ID, message, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


def check_certificates():
    for cert_folder in CERT_FOLDERS:
        for root, _, files in os.walk(cert_folder):
            for file in files:
                if file.endswith((".cer", ".crt")):
                    cert_path = os.path.join(root, file)
                    try:
                        with open(cert_path, "rb") as f:
                            cert_data = f.read()

                        try:
                            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
                        except OpenSSL.crypto.Error:
                            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_data)

                        cn = cert.get_subject().CN or "Common Name (CN) не найдено."

                        not_after = datetime.datetime.strptime(cert.get_notAfter().decode("ascii"), "%Y%m%d%H%M%SZ")
                        not_after = not_after.replace(
                            tzinfo=datetime.timezone.utc)  # Добавляем информацию о временной зоне
                        days_until_expiration = (not_after - datetime.datetime.now(datetime.timezone.utc)).days

                        if days_until_expiration < EXPIRATION_THRESHOLD:
                            expiration_date = not_after.strftime(
                                "%d %B %Y %H:%M:%S")  # Форматирование даты окончания действия сертификата
                            if days_until_expiration >= 0:
                                message = f"Сертификат '<b>{cn}</b>' заканчивается через <b>{days_until_expiration}</b> дней. Дата окончания: <b>{expiration_date}</b>."
                            else:
                                message = f"Сертификат '<b>{cn}</b>' срок действия <b>истёк!</b> Дата окончания: <b>{expiration_date}</b>."
                            send_telegram_message(message)
                    except Exception as e:
                        error_message = f"Не удалось прочитать сертификат {cert_path}: {e}"
                        print(error_message)
                        send_telegram_message(error_message)


if __name__ == "__main__":
    while True:
        check_certificates()
        time.sleep(CHECK_INTERVAL)
