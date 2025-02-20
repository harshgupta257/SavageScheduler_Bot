# Telegram Task Manager & Roasting Bot

## 🤖 Overview
This is a Telegram bot that helps users manage tasks with reminders and a unique **roasting feature**. If you miss your tasks, the bot will roast you in a savage way! 🔥

## ✨ Features
- 📌 **Add Tasks** with deadlines
- ✅ **Mark Tasks as Completed**
- 📜 **View Pending & Completed Tasks**
- ⛔ **Remove Tasks**
- ⏰ **Automatic Reminders** for pending tasks
- 🤬 **Savage Roasting** if you miss your deadlines
- ⚙️ **Customizable Roast Interval**

## 🚀 Commands
```
/addtask - Add a new task (Usage: /addtask Task_Name YYYY-MM-DD HH:MM)
/tasks - View all tasks
/completed - View all completed tasks
/pending - View all pending tasks
/done - Mark a task as completed (Usage: /done Task_Name)
/removetask - Remove a task (Usage: /removetask Task_Name)
/help - Get help and command list
/setroastinterval - Change the roast check interval (Usage: /setroastinterval 120 for 2 minutes)
```

## 🛠️ Tech Stack
- **Python** 🐍
- **Telegram Bot API** 🤖
- **SQLite** 📂 (for task storage)
- **APScheduler** ⏳ (for scheduling reminders & roasting)

## 📦 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-bot-repo.git
   cd your-bot-repo
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your bot:
   - Get a **Bot Token** from [BotFather](https://t.me/BotFather)
   - Create a `.env` file and add your token:
     ```
     BOT_TOKEN=your_telegram_bot_token
     ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## 📤 Hosting
You can host this bot on:
- **Heroku** ☁️
- **Railway.app** 🚂
- **VPS (DigitalOcean, AWS, etc.)**

## 🛠 Future Enhancements
- 🤖 **NLP-Based Smart Responses**
- 📊 **Task Completion Analytics**
- ⏳ **Snooze Task Feature**

## 📜 License
This project is licensed under the MIT License.

## 🤝 Contributing
Feel free to fork this repository and submit a **pull request**. Let's make this bot even better! 💪
