#!/usr/bin/env python3
import praw
import os
from dotenv import load_dotenv
import time
import threading
import traceback

import expense
import finder

def main():
    inbox_thread = threading.Thread(name="Inbox Monitor", target=inbox_monitor, args=[])
    inbox_thread.start()

    bogle_thread = threading.Thread(name="Boglehead Monitor", target=bogle_monitor, args=[])
    bogle_thread.start()

    

def inbox_monitor():
    for mention in reddit.inbox.stream():
        inbox_handler(mention)

def bogle_monitor():
    subreddit = reddit.subreddit("Bogleheads")
    for submission in subreddit.stream.submissions():
        try:
            process_submission(submission, min_expenses=3)
        except:
            traceback.print_exc()

def inbox_handler(mention):
    time.sleep(10) # Ensure reddit is up to date for the refresh
    mention = mention.refresh()

    is_replying_to_me = is_a_reply_to_me(mention)
    is_requesting_me = reddit.user.me().name in mention.body and not is_replying_to_me
    is_requesting_refresh = "refresh" in mention.body.lower() and is_replying_to_me
    try:
        if is_requesting_me:
            process_mention(mention)
        elif is_requesting_refresh:
            process_submission(mention.submission, True)
        else:
            print("This doesn't look like an actionable mention: " + mention.body)
    except:
        traceback.print_exc()
    
    mention.upvote() # Reward people for interacting
    mention.mark_read() # Don't handle this again, (you only get one shot to prevent any issues when bot is restarted, better to just silently fail)

def login():
    load_dotenv() # Store environment variables from .env file

    reddit = praw.Reddit(
        user_agent = os.getenv("reddit_bot_user_agent"),
        client_id = os.getenv("reddit_bot_client_id"),
        client_secret = os.getenv("reddit_bot_client_secret"),
        username = os.getenv("reddit_bot_username"),
        password = os.getenv("reddit_bot_password"),
    )
    reddit.validate_on_submit = True
    reddit.user.me().name # Ensure logged in
    return reddit

def process_mention(mention):
    global reddit
    comment = process_submission(mention.submission)
    if (comment != None):
        mention.reply(f"[Here are the funds I found in this thread]({comment.permalink}).\n\n ^(If you see any more come up, just respond to me with \"Refresh\")")
    else:
        mention.reply("I didn't find any funds worth researching in this thread.")

def is_a_reply_to_me(comment):
    global reddit
    myName = reddit.user.me().name
    parent = comment.parent()
    if parent == comment.submission:
        return comment.submission.author.name == myName
    else:
        # Check if this is my comment, and recursively check my parents if not
        return (parent.author and parent.author.name == myName) or is_a_reply_to_me(parent)

def checkForMore(comment):
    if hasattr(comment, "body"):
       return comment.body
    else:
        more = comment.comments()
        if hasattr(more, "list"):
            return getCommentsText(comment.comments().list())
        else:
            return getCommentsText(comment.comments())

def getCommentsText(comments):
    return " ".join(list(map(lambda c: checkForMore(c), comments)))

def find_my_comment(reddit, comments):
    for comment in comments:
        if (comment.author and comment.author.name == reddit.user.me().name):
            return comment
    return None

def process_url(url):
    global reddit
    # e.g "r/Bogleheads/comments/mogb9g/adapting_my_portfolio_to_five_factor_investing/"
    return process_submission(reddit.get(url)[0].children[0])

def process_submission(submission, onlyAllowEdits=False, commentsToCheck=None, min_expenses=0):
    global reddit
    if commentsToCheck == None:
        submission.comments.replace_more(limit=None)
        commentsToCheck = submission.comments.list()

    submission.comments.replace_more(limit=None)
    myComment = find_my_comment(reddit, submission.comments.list())

    print(f"\nChecking: {submission.title}")
    commentText = getCommentsText(commentsToCheck)
    allText = " ".join([submission.title, submission.selftext, commentText])

    stockSymbols = finder.stockSymbols(allText)
    print(stockSymbols)
    expenses = expense.findInfo(stockSymbols)

    
    if len(expenses) > min_expenses:
        text = createRedditTable(expenses)
    
        timeString = time.strftime("%d %b %Y %H:%M:%S GMT%z", time.localtime())
        response = "Looks like people are talking about these funds:\n\n" + text + f"\n\n ^(Table last updated at {timeString})"
        if myComment == None and not onlyAllowEdits:
            print(f"\nReplying to: {submission.title}")
            myComment = submission.reply(response)
        elif myComment != None:
            # beforeTime = "Table last updated"
            # if myComment.body.split(beforeTime)[0] != response.split(beforeTime)[0]: # WANT refresh to refresh time though
            print(f"\nEditing reply to: {submission.title}")
            myComment.edit(response)
            # else:
                # print("\nNo change: " + submission.title)

        add_submission_listener(submission, stockSymbols, myComment)
        return myComment
    else:
        print(f"\nSkipping: {submission.title}")
        return None

def add_stock_info_to_comment(comment, stock_symbols):
    expenses = expense.findInfo(stock_symbols)
    text = createRedditTable(expenses)
    timeString = time.strftime("%d %b %Y %H:%M:%S GMT%z", time.localtime())
    response = "Looks like people are talking about these funds:\n\n" + text + f"\n\n ^(Table last updated at {timeString})"
    comment.edit(response)

def add_submission_listener(submission, stock_symbols, my_comment):
    tracked_submission_ids = tracked_submissions.keys()
    if not submission.id in tracked_submission_ids:
        create_submission_thread(submission, stock_symbols, my_comment)

def create_submission_thread(submission, stock_symbols, my_comment, max_threads=50):
    global tracked_submissions
    global submission_ids
    
    thread = threading.Thread(name=submission.permalink, target=submission_listener, args=(submission.id,))
    submission_ids.append(submission.id)
    tracked_submissions[submission.id] = {"id": submission.id, "stock_symbols": stock_symbols, "my_comment_id": my_comment.id, "thread": thread}
    thread.start()
    if len(submission_ids) > max_threads:
        toKillId = submission_ids.pop(0)
        stop_submission_thread(toKillId)

def stop_submission_thread(submission_id):
    toKill = tracked_submissions[submission_id]
    toKill["thread"].delete()
    del tracked_submissions[submission_id]

def submission_listener(submission_id):
    stream = praw.models.util.stream_generator(lambda **kwargs: submission_stream(reddit.submission(id=submission_id), **kwargs))
    for reply in stream:
        try:
            handle_new_comment(submission_id, reply)
        except:
            traceback.print_exc()
        reply.mark_read()

def submission_stream(submission, **kwargs):
    results = []
    results.extend(submission.comments)
    results.sort(key=lambda post: post.created_utc, reverse=True)
    return results

def handle_new_comment(submission_id, comment):
    global tracked_submissions
    print("New comment: " + comment.body)
    submission_info = tracked_submissions[submission_id] 
    my_comment = reddit.comment(id=submission_info["my_comment_id"])
    new_stocks = finder.stockSymbols(comment.body)
    old_stock_symbols = submission_info["stock_symbols"]
    stock_symbols = old_stock_symbols + new_stocks
    stock_symbols = list(set(stock_symbols))
    tracked_submissions[submission_id]["stock_symbols"] = stock_symbols

    if len(old_stock_symbols) < len(stock_symbols):
        add_stock_info_to_comment(my_comment, stock_symbols)


def createRedditTable(funds):
    headers = "|Symbol|Full Name|Expense|Type|"
    alignment = "|:-|:-|:-|:-|"
    rows = "\n".join(list(map(lambda fund: f"|{fund[0]}|{fund[1]}|{fund[2]}|{fund[3]}|", funds)))
    return "\n".join([headers, alignment, rows])

if __name__ == "__main__":
    global submission_ids
    global tracked_submissions
    global reddit
    tracked_submissions = {}
    submission_ids = []
    reddit = login()
    main()