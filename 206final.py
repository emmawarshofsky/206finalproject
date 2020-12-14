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

#reminder: delete the dates table you made

def save_to_database(tw_text, cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS Tweets (tweet_text TEXT, date TEXT)")
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
#DELETE THIS FUNCTION: or use for bonus visualization
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
    i = 2
    overall_scores = {} #dict of dicts, keys are dates, values dict with the sum
    while i <= 9:
        date = "12/0{}/2020".format(str(i))
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
            pos_scores.append(cols[1])
            neg_scores.append(cols[2])
            avg_scores.append(cols[-1])

    fig, ax = plt.subplots()
    num_groups = 8
    width = 0.35
    ind = np.arange(num_groups)
    ax.bar(ind - width, neg_scores, width, color = "red", label = "Negative Score")
    ax.bar(ind, pos_scores, width, color = "green", label = "Positive Score")
    ax.bar(ind + width, avg_scores, width, color = "blue", label = "Average Score")
    
    ax.set_ylabel("Sentiment Scores")
    ax.set_title("Sentiment Scores about Michigan Football: Grouped by Date and Feeling")
    ax.set_xticks(ind + width / 3)
    ax.set_xticklabels(["12/03/2020", "12/04/2020", "12/05/2020", "12/06/2020", "12/07/2020", "12/08/2020", "12/09/2020", "12/10/2020"])
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
start_date = "2020-09-26"
end_date = "2020-12-10" #this date gives more items
tweets = tweepy.Cursor(api.search, q = hashtag, lang = "en", since = start_date, until = end_date, tweet_mode = "extended").items(500)
tw_text = []
for tweet in tweets:
    text_date = (tweet.full_text, tweet.created_at)
    tw_text.append(text_date)
save_to_database(tw_text, cur, conn)
#word_counts_dict = count_words(cur, conn)
#print(word_counts_dict) #going to have to add our own stop words

twitter_data = tweet_analysis(cur, conn)
write_to_csv(twitter_data, "twitter_sentiments.csv")
make_bar_chart("twitter_sentiments.csv", "SentimentScores.png")
conn.close()
