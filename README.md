# Telegram Video Converter Bot

A powerful Telegram bot that converts videos to WebM format for emojis and stickers.

## Features

- 🎥 Convert videos to Video Emoji (100x100)
- 🖼️ Convert videos to Video Sticker (512x512)
- ⚡ Fast conversion using FFmpeg
- 📱 User-friendly interface with buttons
- 🔄 Automatic file optimization

## Requirements

- Python 3.11+
- FFmpeg (installed on server)
- Telegram Bot Token

## Bot Commands

- `/start` - Start the bot and choose conversion type
- `/help` - Show help information
- `/reset` - Reset your choice

## Conversion Types

### 🎥 Video Emoji
- 100x100 pixels
- WebM VP9 format
- No audio
- Max 3 seconds
- Max 256KB

### 🖼️ Video Sticker
- 512x512 pixels
- WebM VP9 format
- No audio
- Max 3 seconds
- Max 256KB

## Deployment on Render

1. Fork this repository
2. Connect to Render
3. Deploy automatically

## Usage

1. Start the bot with `/start`
2. Choose conversion type
3. Send your video file
4. Get your converted WebM file!

## Technical Details

- Uses `python-telegram-bot` library
- FFmpeg for video processing
- Temporary files for security
- Automatic cleanup
