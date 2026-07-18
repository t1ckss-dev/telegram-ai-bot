FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install python-telegram-bot aiohttp

CMD ["python", "bot.py"]