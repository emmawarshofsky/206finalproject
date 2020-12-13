#facebook
import requests
import os
import sqlite3
from bs4 import BeautifulSoup
import re

group_id = '223351171575348'
group_url = 'https://mobile.facebook.com/groups/' + group_id

def save_to_database(post_dict_list, cur, conn):
    cur.execute("DROP TABLE IF EXISTS Facebook")
    cur.execute("CREATE TABLE Facebook (post_id INTEGER PRIMARY KEY, post_text TEXT, rent INTEGER, housing_type TEXT)")
    idnumber = 0
    for i in post_dict_list:
        if 'rent' in i and 'type' in i:
            idnumber +=1 
            cur.execute('''INSERT INTO Facebook (post_id, post_text, rent, housing_type) VALUES (?, ?, ?, ?)''', (idnumber, i['text'], i['rent'], i['type']))
        conn.commit()
    conn.close()


#returns list of posts
#are we supposed to be storing this all in database immediately?
def get_posts(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    print(soup.text)
    #print(soup.prettify())
    #posts = soup.find_all('p', id= "m_group_stories_container")
    posts = soup.find(id = "m_group_stories_container").find_all("p")
    post_contents = []
    for post in posts[0:101]:
        #p = post.find("p")
        post_contents.append(post.text)
    return post_contents

#returns rent of listing if included in post, returns empty string if not found
def get_price(post):
    x = re.search("\$\d{3,4}$", post)
    if x == None:
        return ''
    else:
        return int(x[1:])
        
#returns whether listing is for an apartment or house, returns empty string if not clarified
def get_type(post):
    if 'apartment' in post and 'house' in post:
        return ''
    elif 'apartment' in post:
        return 'apartment'
    elif 'house' in post:
        return 'house'
    else:
        return ''

#returns list of dictionaries for each post, keys post text, price, and housing type
def create_post_dict_list(post_contents):
    post_dict_list = []
    for item in post_contents:
        item_dict = {}
        item_dict['text'] = item
        if get_price(item) != '':
            item_dict['rent'] = get_price(item)
        if get_type(item) != '':
            item_dict['type'] = get_type(item)
        post_dict_list.append(item_dict)
    return post_dict_list



#create database file - not sure if we need this in both
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + '/' + 'finalproject.db')
cur = conn.cursor()

post_dict_list = create_post_dict_list(get_posts(group_url))
print(post_dict_list)