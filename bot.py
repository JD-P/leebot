from telegram.ext import Updater, CommandHandler
from typing import Callable
from urllib.parse import urlparse
import threading
import feedparser
import json
import re

config_file = open("config.json")
config = json.load(config_file)
config_file.close()

# TODO: Is there a better place to store this than in a global?
try:
    feed_heads_infile = open("feed_heads.json")
    FEED_HEADS = json.load(feed_heads_infile)
    feed_heads_infile.close()
except IOError:
    FEED_HEADS = {}

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


def validate_feed_add(command: str) -> tuple:
    args = command.split(" ")
    feed_type = args[1]
    url = args[2]
    url_components = urlparse(url)
    # Verify that it's a real url
    if not (url_components.scheme and url_components.netloc):
        raise ValueError("'{}' does not seem to be a url.".format(url))
    # Prevent arbitrary modification of config options
    if feed_type not in ["git_feeds","blog_feeds"]:
        raise ValueError("Improper feed type '{}'".format(feed_type))
    else:
        return(feed_type, url)
    
def add_feed(bot, update):
    try:
        (feed_type, url) = do_add_feed(update.message.text)
        config[feed_type].append(url)
    except ValueError as e:
        update.message.reply_text(str(e))
    
def do_shutdown():
    updater.stop()
    updater.is_idle = False
    
def shutdown(bot, update):
    try:
        is_admin = update.message.from_user.id == config["admin_id"]
    except KeyError:
        update.message.reply_text("There is no administrator configured. " +
                                  "Set one by adding a telegram account ID under " +
                                  "the admin_id config parameter." +
                                  "\n\nYour id is {}".format(
                                      update.message.from_user.id))
    if is_admin:
        bot.send_message(chat_id=update.message.from_user.id,
                         text="Saving files...")
        # Change this to use a command line flag or something for the filename
        config_outfile = open("config.json", "w")
        json.dump(config, config_outfile)
        config_outfile.close()
        feed_heads_outfile = open("feed_heads.json", "w")
        json.dump(FEED_HEADS, feed_heads_outfile)
        feed_heads_outfile.close()
        bot.send_message(chat_id=update.message.from_user.id,
                         text="Shutting down now.")
        # Have to shut down this way, see:
        # https://github.com/python-telegram-bot/python-telegram-bot/issues/801
        threading.Thread(target=do_shutdown).start()
    else:
        if type(config["admin_id"]) == str:
                update.message.reply_text("Use an int in the configuration for admin_id.")
        else:
                update.message.reply_text("You are not set as an administrator.")
        
        
def callback_remind(bot, job):
    bot.send_message(chat_id=config["channel_id"],
                     text=job.context)
    
def check_feed(feed: dict,
               feed_heads: dict,
               alert_gen: Callable[[dict],str]) -> tuple:
    try:
        same_head = feed_heads[feed["feed"]["id"]] == feed["entries"][0]["id"]
    except KeyError:
        same_head = False
    if not same_head:
        feed_heads[feed["feed"]["id"]] = feed["entries"][0]["id"]
        alert = alert_gen(feed)
    else:
        alert = None
    return alert, feed_heads

def git_alert(feed):
    return "{} added a new commit to {}: {}\n {}".format(
        feed["entries"][0]["author"],
        feed['feed']['title'].split("to")[1].strip(),
        feed["entries"][0]["title"],
        feed["entries"][0]["link"])

def blog_alert(feed):
    return "[{}]\n{}\n\n{}".format(
        feed["feed"]["title"],
        feed["entries"][0]["title"],
        feed["entries"][0]["link"])

def callback_feeds(bot, job):
    global FEED_HEADS
    for feed_url in job.context["feeds"]:
        feed = feedparser.parse(feed_url)
        (alert, feed_heads) = check_feed(feed, FEED_HEADS, git_alert)
        if alert:
            FEED_HEADS = feed_heads
            bot.send_message(chat_id=config["channel_id"],
                             text=alert)
            
def callback_auto_save(bot, job):
    """Autosave the bot state so it's not lost if improper shutdown occurs."""
    # If/when this becomes more complex, split logic off into own function and test
    # TODO: Change this to use a command line flag or something for the filename
    config_outfile = open("config.json", "w")
    json.dump(config, config_outfile)
    config_outfile.close()
    feed_heads_outfile = open("feed_heads.json", "w")
    json.dump(FEED_HEADS, feed_heads_outfile)
    feed_heads_outfile.close()
            
if __name__ == '__main__':
    updater = Updater(config["bot_api_key"])

    updater.dispatcher.add_handler(CommandHandler('remind', remind_me))
    updater.dispatcher.add_handler(CommandHandler('shutdown', shutdown))
    try:
        updater.job_queue.run_repeating(callback_feeds, interval=(60*5),
                                        context={"feeds":config["git_feeds"]},
                                        first=0)
    except KeyError:
        pass
    try:
        updater.job_queue.run_repeating(callback_feeds, interval=(60*10),
                                        context={"feeds":config["blog_feeds"]},
                                        first=0)
    except KeyError:
        pass
    updater.job_queue.run_repeating(callback_auto_save, interval=(60*10))
    
    updater.start_polling()
    updater.idle()
