#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from dotenv import load_dotenv
import praw

load_dotenv()

TAGS = os.getenv('tags').split()


def filter_by_tags(posts, tags=TAGS):
    return [post for post in posts 
            if any(tag in post.title.lower() for tag in tags)]


def authenticate():
    return praw.Reddit("mybot", user_agent="mybot v0.1")


def get_posts(reddit):
    posts = reddit.subreddit(os.getenv('sub')).new(limit=20)
    posts = filter_by_tags(posts)
    return list(posts)


def main():
    reddit = authenticate()
    subs = get_posts(reddit)
    x = subs[0]
    import pprint
    pprint.pprint(x.url)


if __name__ == '__main__':
    main()
