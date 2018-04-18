#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shelve
import logging

from flask import Flask, request
import telepot
from reddit import authenticate, get_posts
from dotenv import load_dotenv

from storit import Storit


MSG_DB = 'last'
SUBS_DB = 'subs'


load_dotenv()


def get_last_message(user_id):
    store = Storit(MSG_DB)
    return store[user_id]
    

def save_last_message(user_id, msg_id):
    store = Storit(MSG_DB)
    store[user_id] = msg_id
    

def subscribe_user(user_id):
    store = Storit(SUBS_DB)
    store[user_id] = True
    logging.debug('user %s has subscribed' % user_id)


def unsubscribe_user(user_id):
    store = Storit(SUBS_DB)
    ret = store.delete_if_exists(user_id)
    if ret:
        logging.debug('user %s has unsubscribed' % user_id)


def get_subscribed_users():
    store = Storit(SUBS_DB)
    return store.keys()


def get_pending_messages(user_id, ads):
    '''
    Returns pending messages for each user
    The order is from oldest to newest
    '''
    last_msg = get_last_message(user_id)
    if last_msg and last_msg in ads:
        pos = ads.index(last_msg)
        if pos > 0:
            # send pending ads
            return reversed(ads[:pos])
        else:
            # no new ads
            return []
    # send all ads
    return reversed(ads)


def send_ads_to_user(tgbot, user, manual=False):
    posts = get_hiring_posts(reddit=authenticate())
    pending = get_pending_messages(user, posts)
    if pending:
        lm = None
        for post in pending:
            lm = post
            try:
                tgbot.sendMessage(user, "*{}*\n[link]({})".format(post.title, post.url), parse_mode='Markdown')
            except telepot.exception.BotWasBlockedError:
                logging.debug('User {} blocked me'.format(user))
        assert lm is not None
        logging.debug("saving user %s with msg %s" % (user, lm))
        save_last_message(user, lm)
    elif manual:
        tgbot.sendMessage(user, 'Nothing new to see here')

secret = os.getenv('botsecret')
bot = os.getenv('botid')
bot.setWebhook("https://mybot.mydomain.net/{}".format(secret),
               max_connections=1)


app = Flask(__name__)


@app.route('/{}'.format(secret), methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        text = update["message"]["text"]
        chat_id = update["message"]["chat"]["id"]
        if text == '/new':
            send_ads_to_user(tgbot=bot, user=chat_id, manual=True)
        elif text == '/sub':
            subscribe_user(chat_id)
            bot.sendMessage(chat_id, 'New submissions will be notified'
                                     ' every 10 minutes (if any)')
        elif text == '/unsub':
            unsubscribe_user(chat_id)
            bot.sendMessage(chat_id, 'Subscription cancelled')
        else:
            bot.sendMessage(chat_id, "Doesn't look like anything to me..")
    return 'OK'


@app.route('/crony-secret-url')
def periodic_msg_pooler():
"""
Curl this URL every x minutes with cron.
(This is a quick hack for avoiding something like apscheduler)
"""
    for user in get_subscribed_users():
        logging.info('sending ads to user %s' % user)
        send_ads_to_user(tgbot=bot, user=user)
    return 'OK'
