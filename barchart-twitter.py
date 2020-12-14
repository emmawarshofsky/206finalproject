import sys
import requests
import sqlite3
import os
import tweepy
import csv
from bs4 import BeautifulSoup
from datetime import datetime
import string
import re

import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import matplotlib.pyplot as plt
import numpy as np


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

make_bar_chart("twitter_sentiments.csv", "SentimentScores.png")