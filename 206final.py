#finalproject
import sys
import requests
import sqlite3
import os
import json
import tweepy
from bs4 import BeautifulSoup
import twitter_info
from datetime import datetime
import string
import nltk
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment import SentimentIntensityAnalyzer


consumer_key_f = twitter_info.consumer_key_f
consumer_key_secret_f = twitter_info.consumer_key_secret_f
access_token_f = twitter_info.access_token_f
access_token_secret_f = twitter_info.access_token_secret_f

#reminder: delete the dates table you made

def save_to_database(tw_text, cur, conn):
    cur.execute("DROP TABLE IF EXISTS Tweets")
    cur.execute("CREATE TABLE Tweets (tweet_text TEXT, date TEXT)")
    for i in range(len(tw_text)):
        timestamp = tw_text[i][1]
        date = timestamp.strftime("%m/%d/%Y")
        tweet_text = parse_tweet(tw_text[i][0])
        if not tweet_text.startswith("rt"): 
            cur.execute('''INSERT INTO TWEETS (tweet_text, date)
                VALUES (?, ?)''', (tweet_text, date))
        conn.commit()

#function to parse through tweet text and get rid of unnecessary info
def parse_tweet(tweet_text):
    tweet_text = tweet_text.strip().lower() 
    words = tweet_text.split()
    idx = None
    for i in range(len(words)):
        if words[i].startswith("https://") or words[i].startswith("http://"):
            idx = i
    if idx != None:
        words.remove(words[idx])
    tweet = " ".join(words)
    return tweet


#counts the occurrences for each words, returns a dictionary
#come back and see if we need this
def count_words(cur, conn):
    full_path = os.path.join(os.path.dirname(__file__), "stopwords.txt")
    f = open(full_path, "r")
    lines = f.readlines()
    f.close()
    stop_words = []
    for word in lines:
        word = word.strip()
        stop_words.append(word)
    word_counts = {}
    cur.execute("SELECT tweet_text FROM Tweets")
    try:
        tweets = cur.fetchall()
        for tweet in tweets:
            tweet = tweet[0]
            tweet = tweet.translate(str.maketrans('', '', string.punctuation))
            tweet = tweet.translate(str.maketrans('', '', '1234567890'))
            words = tweet.split()
            for word in words:
                if word not in stop_words:
                    word_counts[word] = word_counts.get(word, 0) + 1
        word_counts = dict(sorted(word_counts.items(), key = lambda x: x[1], reverse = True))
        return word_counts
    except:
        print("Error: couldn't retrieve tweet texts")
        return {}
    
    def tweet_analysis(cur, conn):
        cur.execute("SELECT * FROM Tweets")
        text_tpls = cur.fetchall()[0]
        sid = SentimentIntensityAnalyzer()
        for text in text_tpls:
            score = sid.polarity_scores(text)
            print(score)

        pass

auth = tweepy.OAuthHandler(consumer_key_f, consumer_key_secret_f)
auth.set_access_token(access_token_f, access_token_secret_f)
api = tweepy.API(auth)

#create database file
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + '/' + 'finalproject.db')
cur = conn.cursor()

hashtag = "#michiganfootball"
start_date = "2020-09-26"
end_date = "2020-12-09" #this date gives more items
tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", since = start_date, until = end_date, tweet_mode = "extended").items(500)
tw_text = []
for tweet in tweets:
    text_date = (tweet.full_text, tweet.created_at)
    tw_text.append(text_date)
save_to_database(tw_text, cur, conn)
word_counts_dict = count_words(cur, conn)
#print(word_counts_dict) #going to have to add our own stop words

tweet_analysis(cur, conn)

conn.close()
