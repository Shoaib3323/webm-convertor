# ---- Fake Web Server for Render ----
from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run).start()
# ----------------
import os
import logging
import tempfile
import asyncio
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler


# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


BOT_TOKEN = "8192774962:AAGYfF3nSUvUil3DT3qKfXpB7O6H5FGqNSo"


# Store user choices
user_choices = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎥 Video Emoji (100x100)", callback_data="emoji")],
        [InlineKeyboardButton("🖼️ Video Sticker (512x512)", callback_data="sticker")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
   
    await update.message.reply_text(
        "🤖 Telegram Video Converter Bot\n\n"
        "Choose what you want to create:\n\n"
        "🎥 **Video Emoji**: 100x100 pixels, no audio, max 3s\n"
        "🖼️ **Video Sticker**: 512x512 pixels, no audio, max 3s\n\n"
        "Both produce WebM files that work perfectly in Telegram!",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📋 **How to use:**
1. Click a button below to choose type
2. Send me your video file
3. I'll convert it automatically!


🎥 **Video Emoji Requirements:**
• WebM VP9 format
• 100x100 pixels
• No audio
• Max 3 seconds
• Max 256KB


🖼️ **Video Sticker Requirements:**
• WebM VP9 format  
• 512x512 pixels
• No audio (required for stickers)
• Max 3 seconds
• Max 256KB


⚡ Both formats work perfectly in Telegram!
"""
   
    keyboard = [
        [InlineKeyboardButton("🎥 Video Emoji", callback_data="emoji")],
        [InlineKeyboardButton("🖼️ Video Sticker", callback_data="sticker")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
   
    await update.message.reply_text(help_text, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
   
    user_id = query.from_user.id
    choice = query.data
   
    user_choices[user_id] = choice
   
    if choice == "emoji":
        await query.edit_message_text(
            "✅ Selected: 🎥 Video Emoji (100x100)\n\n"
            "Now send me your video! I'll convert it to:\n"
            "• WebM VP9 format\n• 100x100 pixels\n• No audio\n• Max 3 seconds\n• Under 256KB"
        )
    else:
        await query.edit_message_text(
            "✅ Selected: 🖼️ Video Sticker (512x512)\n\n"
            "Now send me your video! I'll convert it to:\n"
            "• WebM VP9 format\n• 512x512 pixels\n• No audio (required)\n• Max 3 seconds\n• Under 256KB"
        )


async def convert_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert video based on user's choice"""
    user_id = update.message.from_user.id
   
    # Check if user has made a choice
    if user_id not in user_choices:
        keyboard = [
            [InlineKeyboardButton("🎥 Video Emoji", callback_data="emoji")],
            [InlineKeyboardButton("🖼️ Video Sticker", callback_data="sticker")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Please choose what you want to create first:",
            reply_markup=reply_markup
        )
        return


    choice = user_choices[user_id]
   
    try:
        # Get the video file
        if update.message.video:
            file = await update.message.video.get_file()
            file_size = update.message.video.file_size
        elif update.message.document:
            # Check if it's a video file
            mime_type = update.message.document.mime_type or ""
            document_name = update.message.document.file_name or ""
           
            if not any(x in mime_type for x in ['video', 'mp4', 'mov']) and not any(x in document_name.lower() for x in ['.mp4', '.mov', '.avi', '.mkv']):
                await update.message.reply_text("❌ Please send a video file (MP4, MOV, etc.)")
                return
               
            file = await update.message.document.get_file()
            file_size = update.message.document.file_size
        else:
            await update.message.reply_text("❌ Please send a video file")
            return


        # Check file size
        if file_size > 50 * 1024 * 1024:
            await update.message.reply_text("❌ File too large! Max 50MB")
            return


        processing_msg = await update.message.reply_text("📥 Downloading video...")


        # Create temp files
        with tempfile.NamedTemporaryFile(suffix='.input', delete=False) as infile:
            input_path = infile.name
       
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as outfile:
            output_path = outfile.name


        # Download video
        await file.download_to_drive(input_path)
       
        if os.path.getsize(input_path) == 0:
            await processing_msg.edit_text("❌ Download failed")
            return


        conversion_type = "Video Emoji" if choice == "emoji" else "Video Sticker"
        resolution = "100:100" if choice == "emoji" else "512:512"
       
        await processing_msg.edit_text(f"🔄 Converting to {conversion_type}...")


        # FFmpeg command with EXACT Telegram requirements
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libvpx-vp9',           # Must be VP9 codec
            '-b:v', '0',
            '-crf', '30',                   # Quality (lower = better)
            '-deadline', 'good',            # Good quality encoding
            '-vf', f'scale={resolution}:force_original_aspect_ratio=disable,format=yuv420p',  # Correct pixel format
            '-t', '3.0',                    # Max 3 seconds
            '-an',                          # NO AUDIO (required for both emoji and stickers)
            '-row-mt', '1',                 # Multi-threading
            '-threads', '0',                # Use all CPU threads
            '-movflags', '+faststart',      # WebM optimization
            '-y',                           # Overwrite output
            output_path
        ]


        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )


        # Wait for conversion
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            success = process.returncode == 0
           
        except asyncio.TimeoutError:
            await processing_msg.edit_text("❌ Conversion timed out")
            success = False


        # Check if conversion succeeded
        if not success:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"FFmpeg error: {error_msg}")
            await processing_msg.edit_text("❌ Conversion failed. Try a different video.")
            return


        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            await processing_msg.edit_text("❌ No output file created")
            return


        # Check size limit (256KB)
        output_size = os.path.getsize(output_path)
        if output_size > 256 * 1024:
            # Try more aggressive compression
            await processing_msg.edit_text("📦 File too large, optimizing...")
           
            ffmpeg_compress_cmd = [
                'ffmpeg',
                '-i', output_path,
                '-c:v', 'libvpx-vp9',
                '-b:v', '0',
                '-crf', '40',               # Higher compression
                '-deadline', 'realtime',    # Faster encoding
                '-an',
                '-row-mt', '1',
                '-threads', '0',
                '-y',
                output_path + '_compressed.webm'
            ]
           
            process_compress = await asyncio.create_subprocess_exec(
                *ffmpeg_compress_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
           
            try:
                stdout, stderr = await asyncio.wait_for(process_compress.communicate(), timeout=20.0)
                if process_compress.returncode == 0 and os.path.exists(output_path + '_compressed.webm'):
                    os.replace(output_path + '_compressed.webm', output_path)
                    output_size = os.path.getsize(output_path)
            except:
                pass


        # Final size check
        if output_size > 256 * 1024:
            await processing_msg.edit_text(
                f"❌ File size: {output_size//1024}KB (max 256KB)\n"
                "💡 Try a shorter video (1-2 seconds) or simpler animation"
            )
            return


        # Send the converted file
        await processing_msg.edit_text("✅ Conversion complete! Uploading...")
       
        with open(output_path, 'rb') as video_file:
            caption = (
                f"🎉 Your {conversion_type} is ready!\n\n"
                f"• Format: WebM VP9 ✓\n"
                f"• Resolution: {resolution.replace(':', 'x')} ✓\n"
                f"• Size: {output_size//1024}KB ✓\n"
                f"• Audio: Removed ✓\n\n"
                f"Ready to use in Telegram! ✅"
            )
           
            await update.message.reply_document(
                document=video_file,
                filename=f"{conversion_type.lower().replace(' ', '_')}.webm",
                caption=caption
            )


        await processing_msg.delete()


    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
   
    finally:
        # Cleanup temp files
        for path in [input_path, output_path, output_path + '_compressed.webm']:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user's choice"""
    user_id = update.message.from_user.id
    if user_id in user_choices:
        del user_choices[user_id]
   
    keyboard = [
        [InlineKeyboardButton("🎥 Video Emoji", callback_data="emoji")],
        [InlineKeyboardButton("🖼️ Video Sticker", callback_data="sticker")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
   
    await update.message.reply_text(
        "Choose what you want to create:",
        reply_markup=reply_markup
    )


def main():
    """Start the bot"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()


        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("reset", reset_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, convert_video))


        logger.info("Starting WebM Converter Bot...")
        application.run_polling()
       
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")


if __name__ == '__main__':
    main()

