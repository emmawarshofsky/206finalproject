#finalproject
import requests
import sqlite3
import os
import json
import tweepy
from bs4 import BeautifulSoup
import twitter_info
from datetime import datetime

consumer_key_f = twitter_info.consumer_key_f
consumer_key_secret_f = twitter_info.consumer_key_secret_f
access_token_f = twitter_info.access_token_f
access_token_secret_f = twitter_info.access_token_secret_f

def save_to_database(tw_text, cur, conn):
    cur.execute("DROP TABLE IF EXISTS Tweets")
    cur.execute("CREATE TABLE Tweets (tweet_text TEXT, tweet_date TEXT, month_id INTEGER)")
    for i in range(len(tw_text)):
        timestamp = tw_text[i][1]
        date = timestamp.strftime("%m/%d/%Y")
        month_id = timestamp.strftime("%m")
        tweet_text = parse_tweet(tw_text[i][0])
        if not tweet_text.startswith("rt"):     #getting rid of retweets
            cur.execute('''INSERT INTO Tweets (tweet_text, tweet_date, month_id) 
                VALUES (?, ?, ?)''', (tweet_text, date, month_id)) 
        conn.commit()

#function to parse through tweet text and get rid of unnecessary info
def parse_tweet(tweet_text):
    tweet_text = tweet_text.strip().lower() 
    words = tweet_text.split()
    if words[-1].startswith("https://"):
        words = words[:-1]
    tweet = " ".join(words)
    return tweet

auth = tweepy.OAuthHandler(consumer_key_f, consumer_key_secret_f)
auth.set_access_token(access_token_f, access_token_secret_f)
api = tweepy.API(auth)

#create database file
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + '/' + 'finalproject.db')
cur = conn.cursor()

hashtag = "#michiganfootball"
start_date = "2020-09-26"
end_date = "2020-12-08"
tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", since = start_date, until = end_date, tweet_mode = "extended").items(500)
tw_text = []
for tweet in tweets:
    text_date = (tweet.full_text, tweet.created_at)
    tw_text.append(text_date)

save_to_database(tw_text, cur, conn)
#only getting 97 items in db rn (exclude tweets)
conn.close()
