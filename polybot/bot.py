import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img



class Bot:

    def __init__(self, token, bot_app_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{bot_app_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):

    def handle_message(self, msg):

        logger.info(f"The message which arrived {msg}")

        if not self.is_current_msg_photo(msg):
            self.send_text(msg['chat']['id'], "Please send a photo with a valid caption.")
            return

        caption = msg.get('caption', '').strip().capitalize()

        if not caption:
            self.send_text(msg['chat']['id'], "Please provide a caption for the image processing.")
            return

        try:
            # Attempt to download the user's photo
            photo_path = self.download_user_photo(msg)
            logger.info(f'Downloaded photo path: {photo_path}')

            if not photo_path or not os.path.exists(photo_path):
                logger.error('Photo download failed or path is invalid.')
                self.send_text(msg['chat']['id'],
                               "Failed to download the photo or the photo path is invalid. Please try again.")
                return

            if caption.lower() == 'concat':
                if hasattr(self, '_first_image_path') and self._first_image_path:
                    # Process second image for concatenation
                    second_photo_path = photo_path
                    logger.info(
                        f'Processing concatenation - First: {self._first_image_path}, Second: {second_photo_path}')

                    # Create image objects
                    first_img = Img(self._first_image_path)
                    second_img = Img(second_photo_path)

                    # Perform concatenation
                    result_path = first_img.concat(second_img)

                    # Send result and clean up
                    self.send_photo(msg['chat']['id'], result_path)
                    self._first_image_path = None  # Reset after successful concat
                else:
                    # Store first image and wait for second
                    self._first_image_path = photo_path
                    logger.info(f'Stored first image for concat: {self._first_image_path}')
                    self.send_text(msg['chat']['id'],
                                   "First image received. Please send the second image with 'concat' caption.")
                    return

            img = Img(photo_path)
            if caption == 'Blur':
                img.blur()
            elif caption == 'Contour':
                img.contour()
            elif caption == 'Rotate':
                img.rotate()
            elif caption == 'Segment':
                img.segment()
            elif caption == 'Salt and pepper':
                img.salt_n_pepper()
            else:
                self.send_text(msg['chat']['id'],
                               "Invalid caption. Supported captions: 'Blur', 'Contour', 'Rotate', 'Segment', 'Salt and pepper', 'Concat'.")
                return

            self.send_photo(msg['chat']['id'], img.save_img())

        except Exception as e:
            logger.error(f'Error processing image: {str(e)}')
            self.send_text(msg['chat']['id'], f"Error processing image: {str(e)}")