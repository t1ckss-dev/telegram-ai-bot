
# AI Image Generator Telegram Bot 🎨🤖

A Dockerized Telegram bot that generates photorealistic images using a local Stable Diffusion instance. The bot is designed for educational purposes and showcases skills in Python, AI integration, containerization, and database management.

## 🚀 Features

- **Text-to-Image Generation**: Accepts any prompt in English and returns a high-quality AI-generated image.
- **User Balance System**: SQLite database tracks user credits. New users get **5 free generations**.
- **In-App Purchases Demo**: `/buy` command simulates a payment system, adding 10 credits to the user's balance.
- **Strict Content Moderation**: Multi-layer NSFW filter and age-sensitive keyword blocking for safe usage.
- **Dockerized Deployment**: Fully containerized for easy setup and portability.

## 🛠️ Tech Stack

- **Python** (async/await, `python-telegram-bot`)
- **Docker** (containerization)
- **SQLite** (lightweight database)
- **Stable Diffusion WebUI (Forge)** (AI backend via HTTP API)
- **aiohttp** (async HTTP requests)

## 📸 Demo

*(You can insert screenshots of the bot in action here, e.g., prompt and response.)*

## 🏗️ Architecture

The bot communicates with a local Stable Diffusion WebUI instance via its API endpoint.  
A persistent volume (`-v`) mounts the `data/` folder to ensure user balances survive container restarts.

## 🚦 How to Run (Locally)

1. Clone the repository:
   ```bash
   git clone https://github.com/t1ckss-dev/telegram-ai-bot.git
   cd telegram-ai-bot

2. Build the Docker image:

   ```bash
   docker build -t mybot .

3. Run the container with persistent storage:

   ```bash
   docker run -it --rm --network="host" -v $(pwd)/data:/app/data mybot

4. Send /start to your bot in Telegram to begin.

🔒 Moderation
The bot implements a strict filter that blocks prompts containing:

NSFW words (slang, misspellings, explicit terms)

Age-related keywords combined with any NSFW content

📝 License
This project is open-source and available under the MIT License.




# telegram-ai-bot
A Dockerized Telegram bot for AI image generation using Stable Diffusion.
 83f36dd4c14c74042f7bcedb03cda88e588ca0d1
