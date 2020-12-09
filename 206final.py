#finalproject
import requests
import sqlite3
import os
import json
import tweepy
from bs4 import BeautifulSoup
import twitter_info

consumer_key_f = twitter_info.consumer_key_f
consumer_key_secret_f = twitter_info.consumer_key_secret_f
access_token_f = twitter_info.access_token_f
access_token_secret_f = twitter_info.access_token_secret_f

def save_to_database(tw_text, cur, conn):
    cur.execute("DROP TABLE IF EXISTS Tweets")
    cur.execute("CREATE TABLE Tweets (tweet_id INTEGER KEY, tweet_text TEXT, tweet_date TEXT, month_id INTEGER)")
    for i in range(len(tw_text)):
        cur.execute("INSERT INTO Tweets (id, tweet_text, tweet_date, month_id) VALUE (?)", (i, ))
    pass

auth = tweepy.OAuthHandler(consumer_key_f, consumer_key_secret_f)
auth.set_access_token(access_token_f, access_token_secret_f)

api = tweepy.API(auth)

hashtag = "#michiganfootball"
start_date = "2020-09-26"
end_date = "2020-12-08"
tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", since = start_date, until = end_date).items(25)
tw_text = []
for tweet in tweets:
    text_date = (tweet.text, tweet.created_at)
    tw_text.append(text_date)

#create database file
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + '/' + 'finalproject.db')
cur = conn.cursor()
save_to_database(tw_text, cur, conn)
conn.close()
