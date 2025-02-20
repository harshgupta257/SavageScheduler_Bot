import sqlite3
import random
import datetime
import asyncio  # For async tasks
import pytz     # Timezone handling

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext
)
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = " "

ROASTS = {
    "mild": [
        "Come on, you can do better!",
        "Oops, forgot something?",
        "Hey lazybones, maybe try actually finishing something!",
        "This ain't a Netflix show, stop pausing and get to work!"
    ],
    "medium": [
        "Bro, even a sloth moves faster than you!",
        "That was pathetic!",
        "You had one job. Just one!",
        "Procrastination king strikes again!"
    ],
    "savage": [
        "You're the reason warnings exist.",
        "If procrastination was a sport, you'd have gold medals!",
        "Deadlines fear you... because they know you'll never respect them.",
        "You ignored the task so hard it thought it was ghosted!",
        "Your productivity level is lower than your phone battery at 3%.",
        "Even Google can't find your work ethic!",
        "NASA called. They’re studying your ability to do nothing for science!",
        "Your task list is starting to look like a graveyard of abandoned dreams."
    ]
}

# SQLite database setup
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT,
        deadline TEXT,
        completed INTEGER DEFAULT 0
    )"""
)
conn.commit()

scheduler = BackgroundScheduler()
scheduler.start()

IST = pytz.timezone("Asia/Kolkata")  # Define IST timezone

# Global variable to store the roast job (for changing intervals on the fly)
roast_job = None

async def add_task(update: Update, context: CallbackContext) -> None:
    """Command to add a task and schedule a reminder"""
    user_id = update.message.chat_id
    print(f"Received args: {context.args}")  # Debugging line

    try:
        if len(context.args) < 2:
            raise ValueError("Invalid number of arguments")

        task_text = " ".join(context.args[:-2])  # Extract task name
        deadline_str = f"{context.args[-2]} {context.args[-1]}"  # Extract deadline

        # Convert deadline to IST datetime object
        deadline_ist = datetime.datetime.strptime(deadline_str, r"%Y-%m-%d %H:%M")
        deadline_ist = IST.localize(deadline_ist)  # Convert to timezone-aware IST

        now_ist = datetime.datetime.now(IST)  # Get current time in IST

        if deadline_ist <= now_ist:
            await update.message.reply_text("⚠️ Deadline must be in the future!")
            return

        # Store task in the database (store in DATETIME format)
        cursor.execute(
            "INSERT INTO tasks (user_id, task, deadline) VALUES (?, ?, ?)",
            (user_id, task_text, deadline_ist.strftime(r"%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

        # Schedule a reminder 30 minutes before the deadline
        reminder_time_ist = deadline_ist - datetime.timedelta(minutes=30)

        if reminder_time_ist > now_ist:
            reminder_time_utc = reminder_time_ist.astimezone(pytz.utc)  # Convert to UTC
            context.job_queue.run_once(
                send_reminder,
                reminder_time_utc,
                chat_id=user_id,
                name=f"reminder_{task_text}",
                data=task_text
            )

            await update.message.reply_text(
                f"✅ Task added: {task_text}\n📅 Deadline: {deadline_str}\n⏳ Reminder set for 30 minutes before!"
            )
        else:
            await update.message.reply_text(
                f"✅ Task added: {task_text}\n📅 Deadline: {deadline_str}\n⚠️ Reminder skipped (deadline too close)"
            )

    except Exception as e:
        print(f"Error in add_task: {e}")  # Debugging
        await update.message.reply_text("⚠️ Usage: /addtask Task_Name YYYY-MM-DD HH:MM")


async def send_reminder(context: CallbackContext) -> None:
    """Send a reminder before the deadline"""
    job = context.job
    print(f"📢 Sending reminder for task: {job.data} at {datetime.datetime.now(IST)} (IST)")  # Debugging

    await context.bot.send_message(
        job.chat_id,
        text=f"⏳ Reminder: '{job.data}' is due soon. Don't slack off!"
    )


async def complete_task(update: Update, context: CallbackContext) -> None:
    """Command to mark a task as completed"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please specify the task name to complete. Example:\n/done Task_Name"
        )
        return

    task_text = " ".join(context.args)
    user_id = update.message.chat_id

    cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND task = ?", (user_id, task_text))
    task = cursor.fetchone()

    if task:
        cursor.execute("UPDATE tasks SET completed = 1 WHERE user_id = ? AND task = ?", (user_id, task_text))
        conn.commit()
        await update.message.reply_text(f"🎉 Good job! '{task_text}' completed!")
    else:
        await update.message.reply_text(
            f"⚠️ No task found with the name '{task_text}'. Please check and try again."
        )


async def check_deadlines(context: CallbackContext) -> None:
    """Check overdue tasks and roast users"""
    now = datetime.datetime.now(IST)  # Current time in IST

    cursor.execute(
        "SELECT user_id, task FROM tasks WHERE datetime(deadline) < ? AND completed = 0",
        (now.strftime(r"%Y-%m-%d %H:%M:%S"),)
    )
    overdue_tasks = cursor.fetchall()

    for user_id, task_text in overdue_tasks:
        roast_level = random.choice(["mild", "medium", "savage"])
        roast_message = random.choice(ROASTS[roast_level])

        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔥 You missed your task: '{task_text}'\n{roast_message}"
        )


async def view_tasks(update: Update, context: CallbackContext) -> None:
    """Show all tasks"""
    user_id = update.message.chat_id

    cursor.execute(
        "SELECT task, deadline FROM tasks WHERE user_id = ? ORDER BY deadline ASC",
        (user_id,)
    )
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("🙅‍♂️ No pending tasks for you! Chill Maar Tu Ab Yaaar!")
        return

    task_list = "**📌 Your Tasks:**\n\n"
    for task, deadline in tasks:
        task_list += f"🔹 {task} - ⏳ {deadline}\n"

    await update.message.reply_text(task_list, parse_mode="Markdown")


async def pending_tasks(update: Update, context: CallbackContext) -> None:
    """Show all pending tasks"""
    user_id = update.message.chat_id

    cursor.execute(
        "SELECT task, deadline FROM tasks WHERE user_id = ? AND completed = 0 ORDER BY deadline ASC",
        (user_id,)
    )
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("🙅‍♂️ No pending tasks for you! Chill Maar Tu Ab Yaaar!")
        return

    task_list = "**📌 Your Pending Tasks:**\n\n"
    for task, deadline in tasks:
        task_list += f"🔹 {task} - ⏳ {deadline}\n"

    await update.message.reply_text(task_list, parse_mode="Markdown")


async def completed_tasks(update: Update, context: CallbackContext) -> None:
    """Show all completed tasks"""
    user_id = update.message.chat_id

    cursor.execute(
        "SELECT task, deadline FROM tasks WHERE user_id = ? AND completed = 1 ORDER BY deadline ASC",
        (user_id,)
    )
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("🙅‍♂️ Kuch Toh Kaam Karle Yaar! Besharam Hi Hai Kya bilkul?")
        return

    task_list = "**📌 Your Completed Tasks:**\n\n"
    for task, deadline in tasks:
        task_list += f"🔹 {task} - ⏳ {deadline}\n"

    await update.message.reply_text(task_list, parse_mode="Markdown")


async def remove_tasks(update: Update, context: CallbackContext) -> None:
    """Remove a task by name"""
    if not context.args:
        await update.message.reply_text(
            "🤔 Please provide the task name you want to remove! Example:\n/removetask Task_Name"
        )
        return

    task_text = " ".join(context.args)
    user_id = update.message.chat_id

    cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND task = ?", (user_id, task_text))
    task = cursor.fetchone()

    if task:
        cursor.execute("DELETE FROM tasks WHERE user_id = ? AND task = ?", (user_id, task_text))
        conn.commit()
        await update.message.reply_text(f"👍 Task '{task_text}' has been removed successfully!")
    else:
        await update.message.reply_text(
            f"🤔  No task found with the name '{task_text}'. Please check and try again."
        )


async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a list of available commands"""
    help_text = (
        "**🤖 Available Commands:**\n\n"
        "/addtask - Add a new task (Usage: `/addtask Task_Name YYYY-MM-DD HH:MM`)\n"
        "/tasks - View all tasks\n"
        "/completed - View all completed tasks\n"
        "/pending - View all pending tasks\n"
        "/done - Mark a task as completed (Usage: `/done Task_Name`)\n"
        "/removetask - Remove a task (Usage: `/removetask Task_Name`)\n"
        "/help - Get help and command list\n"
        "/setroastinterval - Change the roast check interval (Usage: `/setroastinterval 120` for 2 minutes)"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def set_roast_interval(update: Update, context: CallbackContext) -> None:
    """
    Command to let user set a custom interval for roasting checks.
    First roast check will happen 10 seconds after setting the interval.
    """
    global roast_job

    # /setroastinterval <seconds>
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /setroastinterval <seconds>")
        return

    try:
        new_interval = int(context.args[0])
        if new_interval < 1:
            await update.message.reply_text("Interval must be a positive integer in seconds.")
            return
    except ValueError:
        await update.message.reply_text("Invalid interval. Please enter an integer (seconds).")
        return

    # Cancel the old job if it exists
    if roast_job is not None:
        roast_job.schedule_removal()

    job_queue = context.application.job_queue
    # Schedule the new repeating job with the user-defined interval
    # The first run is after 10 seconds
    roast_job = job_queue.run_repeating(check_deadlines, interval=new_interval, first=10)

    await update.message.reply_text(
        f"Roast interval set to {new_interval} seconds.\n"
        f"First roast check in 10 seconds!"
    )


def main():
    """Main function to run the bot"""
    app = Application.builder().token(TOKEN).build()

    # ✅ Adding command handlers
    app.add_handler(CommandHandler("addtask", add_task))
    app.add_handler(CommandHandler("done", complete_task))
    app.add_handler(CommandHandler("tasks", view_tasks))
    app.add_handler(CommandHandler("pending", pending_tasks))
    app.add_handler(CommandHandler("completed", completed_tasks))
    app.add_handler(CommandHandler("removetask", remove_tasks))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setroastinterval", set_roast_interval))

    # ✅ Initialize job queue AFTER setting up handlers
    job_queue = app.job_queue

    # ✅ Default roast job: runs check_deadlines every 60 seconds, first run at 10 seconds
    global roast_job
    roast_job = job_queue.run_repeating(check_deadlines, interval=60, first=10)

    print("🚀 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
