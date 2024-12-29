# run.py
import threading
import subprocess

def run_app():
    subprocess.run(["python", "app.py"])

def run_bot():
    subprocess.run(["python", "bot.py"])

if __name__ == "__main__":
    app_thread = threading.Thread(target=run_app)
    bot_thread = threading.Thread(target=run_bot)

    app_thread.start()
    bot_thread.start()

    app_thread.join()
    bot_thread.join()