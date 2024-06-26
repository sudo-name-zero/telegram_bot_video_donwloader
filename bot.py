import logging
import os
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.error import BadRequest
import yt_dlp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Define a command handler. This usually takes the two arguments update and context.
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me a URL of a video to download.')

def download_video(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    update.message.reply_text('Downloading the video...')

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloaded_video.%(ext)s',
        'merge_output_format': 'mkv',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)
            audio_path = video_path.replace('.mp4', '.m4a')

        merged_path = 'merged_video.mp4'
        ffmpeg_command = [
            'ffmpeg', '-i', video_path, '-i', audio_path, '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-movflags', '+faststart', merged_path
        ]
        subprocess.run(ffmpeg_command, check=True)

        with open(merged_path, 'rb') as video_file:
            context.bot.send_video(chat_id=update.message.chat_id, video=video_file)

        update.message.reply_text('Video downloaded and sent!')
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        update.message.reply_text('An error occurred while downloading the video.')

def clear_chat(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    message_id = update.message.message_id

    try:
        for i in range(message_id, message_id-100, -1):
            context.bot.delete_message(chat_id=chat_id, message_id=i)
    except BadRequest as e:
        if "message to delete not found" in str(e):
            pass
        else:
            logger.error(f"Error clearing chat: {e}")

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("clear", clear_chat))

    # on noncommand i.e message - download the video
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
