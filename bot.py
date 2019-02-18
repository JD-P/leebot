from telegram.ext import Updater, CommandHandler
import feedparser
import json
import re

config_file = open("config.json")
config = json.load(config_file)

# TODO: Is there a better place to store this than in a global?
feed_heads = {}

# TODO: Implement social reminder 
def remind_me(bot, update):
    """Implement a 'remind me' feature, with syntax for specifying a time in 
    the future to be reminded at."""
    reminder_string = update.message.text.split("/remind")[1].strip()
    try:
        minutes = float(re.search("([0-9]+) minutes", reminder_string).group(1))
        reminder_string = re.sub("([0-9]+) minutes", "", reminder_string)
    except AttributeError:
        minutes = 0
    try:
        hours = float(re.search("([0-9]+) hours",reminder_string).group(1))
        reminder_string = re.sub("([0-9]+) hours", "", reminder_string)
    except AttributeError:
        hours = 0
    try:
        days = float(re.search("([0-9]+) days", reminder_string).group(1))
        reminder_string = re.sub("([0-9]+) days", "", reminder_string)
    except AttributeError:
        days = 0
    reminder_string = "@{} ".format(update.message.from_user.username) + reminder_string
    updater.job_queue.run_once(callback_remind,
                               (minutes * 60) +
                               (hours * 60 * 60) +
                               (days * 24 * 60 * 60),
                               context=reminder_string.strip())
    feedback = ("Your reminder for {} minutes, " +
                "{} hours and {} days from now: " + 
                "'{}' has been registered!").format(minutes,
                                                    hours,
                                                    days,
                                                    reminder_string)
    bot.send_message(chat_id=update.message.from_user.id,
                     text=feedback)
    
def callback_remind(bot, job):
    bot.send_message(chat_id=config["channel_id"],
                     text=job.context)

def callback_git_feed(bot, job):
    for feed_url in config["git_feeds"]:
        feed = feedparser.parse(feed_url)
        try:
            same_head = feed_heads[feed["feed"]["id"]] == feed["entries"][0]["id"]
        except KeyError:
            same_head = False
            feed_heads[feed["feed"]["id"]] = feed["entries"][0]["id"]
        if not same_head:
            alert = "{} added a new commit to {}: {}\n {}".format(
                feed["entries"][0]["author"],
                feed['feed']['title'].split("to")[1].strip(),
                feed["entries"][0]["title"],
                feed["entries"][0]["link"])
            bot.send_message(chat_id=config["channel_id"],
                             text=alert)
            
def callback_30(bot, job):
    bot.send_message(chat_id=config["channel_id"], 
                     text='A single message with 30s delay')

updater = Updater(config["bot_api_key"])

updater.dispatcher.add_handler(CommandHandler('remind', remind_me))
updater.job_queue.run_repeating(callback_git_feed, interval=(60*5), first=0)

updater.start_polling()
updater.idle()
