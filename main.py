import telebot
from telebot import types
from rembg import remove
from PIL import Image
import logging
import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные окружения из файла .env

# Устанавливаем переменные и пути к изображениям
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
background_images = {
    "Белый фон ⬜": os.getenv("BACKGROUND_IMAGE_WHITE"),  # Путь к изображению белого фона
    "Черный фон ⬛": os.getenv("BACKGROUND_IMAGE_BLACK")   # Путь к изображению черного фона
}
user_image = os.getenv("USER_IMAGE")  # Путь к изображению, загружаемому пользователем
result_image = os.getenv("RESULT_IMAGE")  # Путь к итоговому изображению

selected_background = {}  # Словарь для хранения выбранного фона

# Объект бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=["start"])
def start_handler(message):
    """Обрабатывает команду /start и предоставляет пользователю инструкции."""
    # Создание клавиатуры с кнопками
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    white_button = types.KeyboardButton("Белый фон ⬜")
    black_button = types.KeyboardButton("Черный фон ⬛")
    markup.add(white_button, black_button)
    bot.send_message(chat_id=message.chat.id, text="Привет! Я бот 👋\nОтправьте мне фотографию, и я удалю фон!")
    bot.send_message(chat_id=message.chat.id, text="Но сначала выберите фон для замены 🤔", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in background_images.keys())
def background_handler(message):
    """Обрабатывает выбор фона пользователем и сохраняет его для дальнейшего использования.
        Args:
            message: Объект сообщения от Telegram.
        """
    selected_background[message.chat.id] = background_images[message.text]
    bot.reply_to(message, f"Вы выбрали {message.text.split()[0]} фон.\nТеперь отправьте мне фотографию.")


@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    """Обрабатывает полученную фотографию, удаляет фон и заменяет его на выбранный фон.
    Args:
        message: Объект сообщения от Telegram, содержащий фотографию.
    """
    try:
        if message.chat.id not in selected_background:
            bot.reply_to(message, "Пожалуйста, сначала выберите фон.")
            return

        bot.reply_to(message,"Обрабатываю изображение...\nПожалуйста, подождите 💤")
        # Получаем файл фотографии
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Сохраняем фото
        with open(user_image, "wb") as new_file:
            new_file.write(downloaded_file)

        # Удаляем фон
        input_image = Image.open(user_image)
        output_image = remove(input_image)

        # Загружаем фон
        background_path = selected_background[message.chat.id]
        background = Image.open(background_path).resize(output_image.size)

        # Соединяем изображения
        combined = Image.alpha_composite(background.convert("RGBA"), output_image)
        combined.save(result_image)

        # Отправляем результат пользователю
        with open(result_image, "rb") as file:
            bot.send_photo(message.chat.id, file)

        # Удаляем временные файлы, чтобы избежать перезаписи
        os.remove(user_image)
        os.remove(result_image)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        bot.reply_to(message, "Произошла ошибка при обработке вашего изображения 😢")

if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)