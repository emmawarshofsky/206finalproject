import requests
import os
import json
import sqlite3
from bs4 import BeautifulSoup
import nltk
nltk.downloader.download("stopwords")
from nltk.corpus import stopwords

import matplotlib.pyplot as plt

url = "https://en.wikipedia.org/wiki/COVID-19_pandemic"
covid_keywords = {"Epidemiology": ["outbreak", "counts", "rate", "pandemic", "number", "origin", "studies", "laboratory"],
    "Disease": ["symptom", "severe", "acute", "transmission", "transmit", "illness", "asymptomatic"],
    "Mitigation": ["containment", "distancing", "curve", "reduce", "isolate", "measures", "mask", "quarantine"],
    "History": ["december", "2019", "2020", "march", "january", "china", "wuhan", "early"],
    "National responses": ["border", "states", "italy", "lockdown", "trump", "restrictions", "response", "government"],
    "International responses": ["foreign", "travel", "nations", "who", "evacuate", "countries", "international", "travellers"],
    "Impact": ["economy", "tourism", "culture", "politics", "agriculture", "education", "environment", "racism"],
    "Information dissemination": ["misinformation", "conspiracy", "news", "fake", "media", "claimed", "distrust", "theories"]}

def get_category_info(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    tags = soup.find_all("h2") #get desired categories
    category_lst = []
    for tag in tags:
        category = tag.find("span", class_="mw-headline")
        if category != None:
            category_lst.append(tag.text) 
    return category_lst

def get_sentences(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    tags = soup.find_all("p")
    sentences_lst = []
    for tag in tags:
        paragraph = tag.text.strip()
        sentences = paragraph.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence != '':
                sentences_lst.append(sentence)
    return sentences_lst

def create_categories_table(category_lst, cur, conn):
    cur.execute("DROP TABLE IF EXISTS Categories")
    cur.execute("CREATE TABLE Categories (id INTEGER PRIMARY KEY, category TEXT)")
    for i in range(8): #8 categories that we want
        cur.execute('''INSERT INTO Categories (id, category) 
            VALUES (?, ?)''', (i, category_lst[i]))
    conn.commit()

def parse_sentences(sentences_lst):
    stop_words = set(stopwords.words("english"))
    filter_sentence_lst = []
    for sentence in sentences_lst:
        words = sentence.split()
        words_of_interest = []
        for word in words:
            word = word.lower()
            if (word.isalnum() == True) and (word not in stop_words):
                words_of_interest.append(word)
        filter_sentence = ' '.join(words_of_interest)
        if filter_sentence != '':
            filter_sentence_lst.append(filter_sentence)
    return filter_sentence_lst


def create_text_table(filtered_sentences, cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS Wikipedia (sentence TEXT, category_id INTEGER)")
    cur.execute("SELECT sentence FROM Wikipedia")
    rows = cur.fetchall()
    #count = 0
    for sentence in filtered_sentences:
        in_database = False
        for row in rows:
            if sentence == row[0]:
                in_database = True
        if (in_database == False): #and (count < 25):
            words = sentence.split()
            found_category = False
            word_idx = 0
            while (found_category == False) and (word_idx < len(words)): #and (count < 25)
                category = find_category(words[word_idx])
                word_idx += 1
                if category != None:
                    cur.execute("SELECT * FROM Categories WHERE category = ?", (category, ))
                    category_id = cur.fetchone()[0]
                    cur.execute("INSERT OR IGNORE INTO Wikipedia (sentence, category_id) VALUES (?, ?)", 
                        (sentence, category_id))
                    conn.commit()
                    found_category = True
                    #count += 1
#identify category
def find_category(word):
    for category in list(covid_keywords.items()):
        if word in category[1]:
            return category[0]
    return None      

def page_analysis(cur, conn):
    category_counts = {}
    for i in range(8):
        cur.execute('''SELECT Wikipedia.sentence FROM Wikipedia JOIN Categories ON Categories.id = Wikipedia.category_id 
            WHERE Wikipedia.category_id = ?''', (i, ))
        word_counts = {}
        num_rows = 0
        for row in cur:
            num_rows += 1
            sentence = row[0].split()
            for word in sentence:
                word_counts[word] = word_counts.get(word, 0) + 1
        cur.execute("SELECT category FROM Categories WHERE id = ?", (i, ))
        category = cur.fetchone()[0]
        counts_tpls = sorted(word_counts.items(), key = lambda x: x[1], reverse = True)
        word_counts_sorted = {k: v for k, v in counts_tpls}
        category_counts[category] = [{"Number of sentences": num_rows}, {"Word counts": word_counts_sorted}]
    return category_counts

def write_to_json(category_counts, filename):
    with open(filename, "w") as outfile:
        json.dump(category_counts, outfile, indent = 4)

def make_pie_chart(json_file, outfile):
    with open(json_file, "r") as f:
        data_dict = json.load(f)
        labels = data_dict.keys()
        total_num_sentences = 0
        for category in labels:
            total_num_sentences += data_dict[category][0]["Number of sentences"]
        sizes = []
        for category in labels:
            num = data_dict[category][0]["Number of sentences"]
            size = (num / total_num_sentences) * 100
            sizes.append(size)
    colors = ["red", "green", "purple", "yellow", "blue", "magenta", "gray", "orange"]
    #explode = (0.25, 0, 0.15, 0.1, 0, 0, 0, 0)
    plt.pie(sizes, labels = labels, colors = colors, autopct= '%1.1f%%')
    plt.legend()
    plt.axis("equal")
    plt.show()

        


    
#Table 1: Categories (Symptoms, Vaccination, Impact, Responses etc.)
#Give each an ID (primary key)
#Table 2: Row: sentences, category_id. JOIN. Sentences categorized based on words

path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + '/' + 'finalproject.db')
cur = conn.cursor()

category_lst = get_category_info(url)
sentence_lst = get_sentences(url)
filtered_sentences = parse_sentences(sentence_lst)
create_categories_table(category_lst, cur, conn)
create_text_table(filtered_sentences, cur, conn)

category_words = page_analysis(cur, conn)
write_to_json(category_words, "wikipedia_covid.json")

make_pie_chart("wikipedia_covid.json", "wikipedia_piechart.png")

conn.close()