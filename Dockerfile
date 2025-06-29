FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ✅ Add -u for unbuffered output so print() logs show up in real-time
CMD ["python", "-u", "bot.py"]
