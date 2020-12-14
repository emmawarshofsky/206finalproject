#finalproject
import sys
import requests
import sqlite3
import os
import tweepy
import csv
from bs4 import BeautifulSoup
import twitter_info
from datetime import datetime
import string
import re

import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import matplotlib.pyplot as plt
import numpy as np

consumer_key_f = twitter_info.consumer_key_f
consumer_key_secret_f = twitter_info.consumer_key_secret_f
access_token_f = twitter_info.access_token_f
access_token_secret_f = twitter_info.access_token_secret_f


def save_to_database(tw_text, cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS Tweets (tweet_text TEXT, date TEXT)")
    cur.execute("SELECT tweet_text FROM Tweets")
    rows = cur.fetchall()
    #count = 0
    for i in range(len(tw_text)):
        tweet_text = parse_tweet(tw_text[i][0])
        in_database = False
        for row in rows:
            if row[0] == tweet_text:
                in_database = True
        if (in_database == False): #and (count < 25):
            timestamp = tw_text[i][1]
            date = timestamp.strftime("%m/%d/%Y")
            if not tweet_text.startswith("rt"): 
                cur.execute('''INSERT INTO TWEETS (tweet_text, date)
                    VALUES (?, ?)''', (tweet_text, date))
            conn.commit()
            #count += 1

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


def tweet_analysis(end_date, cur, conn):
    day = end_date[5:7]
    if day.startswith('0'):
        day = int(day[1])
    else:
        day = int(day)
    i = day - 7
    overall_scores = {} #dict of dicts, keys are dates, values dict with the sum
    while i <= day:
        if i < 10:
            date = "12/0{}/2020".format(str(i))
        else:
            date = "12/{}/2020".format(str(i))
        cur.execute("SELECT tweet_text FROM Tweets WHERE date = ?", (date, ))
        try:
            text_tpls = cur.fetchall()
            pos_sum = 0.0
            neg_sum = 0.0
            neutral_sum = 0.0
            compound_sum = 0.0
            num_tweets = 0
            for tweet in text_tpls:
                sid = SentimentIntensityAnalyzer()
                analysis = sid.polarity_scores(tweet[0])
                num_tweets += 1
                pos_sum += analysis["pos"] 
                neg_sum += analysis["neg"]
                neutral_sum += analysis["neu"]
                compound_sum += analysis["compound"]
            pos_avg = round(float(pos_sum / num_tweets), 4)
            neg_avg = round(float(neg_sum / num_tweets), 4)
            neutral_avg = round(float(neutral_sum / num_tweets), 4)
            average = round(float(compound_sum / num_tweets), 4)
            day_dict = {"positive average": pos_avg, "negative average": neg_avg, 
                "neutral average": neutral_avg, "overall average": average}
            overall_scores[date] = day_dict
            i += 1
        except:
            print("Error")
            i += 1
            return {}
    return overall_scores

def write_to_csv(twitter_data, filename):
    with open(filename, "w") as outfile:
        csv_writer = csv.writer(outfile, delimiter = ",", lineterminator = '\n')
        headers = ["Date", "Average Positive Score", "Average Negative Score", "Average Neutral Score", "Overall Average"]
        csv_writer.writerow(headers)
        for day in list(twitter_data.items()):
            row = []
            row.append(day[0])
            for score in list(day[1].items()):
                row.append(score[1])
            csv_writer.writerow(row)

def make_bar_chart(infile, draw_file):
    root_path = os.path.dirname(os.path.abspath(__file__)) + os.sep
    f = os.path.join(root_path, infile)
    csv_file = open(f, "r")
    lines = csv_file.readlines()
    csv_file.close()
    
    pos_scores = []
    neg_scores = []
    avg_scores = []
    for line in lines:
        if line == lines[0]:
            continue
        if line.strip() != '':
            cols = line.split(",")
            pos_scores.append(float(cols[1]))
            neg_scores.append(float(cols[2]))
            avg_scores.append(float(cols[-1]))
    data = [neg_scores, pos_scores, avg_scores]

    fig, ax = plt.subplots()
    num_groups = 8
    width = 0.25
    ind = np.arange(num_groups)

    neg = ax.bar(ind - width, data[0], width = width, color = "red", label = "Negative Score")
    pos = ax.bar(ind, data[1], width = width, color = "green", label = "Positive Score")
    avg = ax.bar(ind + width, data[2], width = width, color = "blue", label = "Average Score")
    
    ax.set_xticks(ind + width / 3)
    ax.set_xticklabels(("12/06/2020", "12/07/2020", "12/08/2020", "12/09/2020", "12/10/2020", "12/11/2020", "12/12/2020", "12/13/2020"))
    ax.legend((neg[0], pos[0], avg[0]), ("Negative Score", "Positive Score", "Average Score"))
    ax.autoscale_view()

    ax.set(xlabel = "Date", ylabel= "Sentiment Scores", title = "Tweets about Michigan Football: Grouped by Date and Sentiment")
    ax.grid()
    fig.savefig(draw_file)
    plt.show()



auth = tweepy.OAuthHandler(consumer_key_f, consumer_key_secret_f)
auth.set_access_token(access_token_f, access_token_secret_f)
api = tweepy.API(auth)

#create database file
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + '/' + 'finalproject.db')
cur = conn.cursor()

hashtag = "#michiganfootball"
end_date = input("Enter today's date in format: YYYY-MM-DD")
tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", until = end_date, tweet_mode = "extended").items(500)
tw_text = []
for tweet in tweets:
    text_date = (tweet.full_text, tweet.created_at)
    tw_text.append(text_date)
save_to_database(tw_text, cur, conn)

twitter_data = tweet_analysis(end_date, cur, conn)
write_to_csv(twitter_data, "twitter_sentiments.csv")
make_bar_chart("twitter_sentiments.csv", "SentimentScores.png")
conn.close()
