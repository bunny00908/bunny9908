# imggen.py

import telebot
import random
import requests
from io import BytesIO
from threading import Thread
import time

user_quantity = {}
DEFAULT_QUANTITY = 1

def generate_image_url(prompt: str = ""):
    base_url = "https://image.pollinations.ai/prompt/"
    seed = random.randint(1000000000, 9999999999)
    full_url = f"{base_url}{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&nologo=true&model=flux-pro"
    return full_url

def download_image(url, retries=3, timeout=30):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return BytesIO(response.content)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise e

def process_image_request(bot, chat_id, message_id, prompt, quantity):
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="🖌 Generating your images... Please wait a moment! 😊"
        )

        images = []
        for _ in range(quantity):
            image_url = generate_image_url(prompt)
            image_data = download_image(image_url)
            images.append(image_data)

        media_group = [telebot.types.InputMediaPhoto(image, caption=f"🌟 Image {_ + 1} for: {prompt}") for _, image in enumerate(images)]
        bot.send_media_group(chat_id, media=media_group)
    except requests.exceptions.Timeout:
        bot.send_message(chat_id, "❌ The image generation service took too long to respond. Please try again later.")
    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"❌ Failed to generate image due to a network error: {e}")
    finally:
        bot.delete_message(chat_id, message_id)

def register_imggen_handlers(bot):

    user_quantity = {}

    @bot.message_handler(commands=["img"])
    def send_images(message):
        text = message.text.strip()
        if len(text.split(maxsplit=1)) > 1:
            prompt = text.split(maxsplit=1)[1]
        else:
            imgur_link = "https://imgur.com/a/2nNhKko"
            bot.send_photo(
                message.chat.id,
                photo=imgur_link,
                caption="⚠️ Use a prompt after /img command, noob! 😂\n\nExample: `.img a rolex watch`",
                parse_mode="Markdown"
            )
            return

        quantity = user_quantity.get(message.chat.id, 1)

        wait_message = bot.reply_to(message, "⏳ Please wait while I generate your images...")

        Thread(target=process_image_request, args=(bot, message.chat.id, wait_message.message_id, prompt, quantity)).start()

    @bot.message_handler(func=lambda message: message.text.startswith(('.img', '!img')))
    def alias_commands(message):
        message.text = message.text.replace('.img', '/img').replace('!img', '/img', 1)
        send_images(message)

    @bot.message_handler(commands=["quantity"])
    def set_quantity(message):
        text = message.text.strip()
        if len(text.split(maxsplit=1)) > 1:
            try:
                quantity = int(text.split(maxsplit=1)[1])
                if 1 <= quantity <= 5:
                    user_quantity[message.chat.id] = quantity
                    bot.reply_to(message, f"✅ Quantity set to {quantity} images per request.")
                else:
                    bot.reply_to(message, "⚠️ Please choose a quantity between 1 and 5.")
            except ValueError:
                bot.reply_to(message, "⚠️ Please provide a valid number between 1 and 5.")
        else:
            bot.reply_to(message, "⚠️ Please specify a quantity. Example: `/quantity 3`", parse_mode="Markdown")
