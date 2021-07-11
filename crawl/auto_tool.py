import requests
import os
from dotenv import load_dotenv
import datetime
from dateutil import parser
from datetime import datetime
from dateutil.tz import tzutc, tzlocal


load_dotenv()

iid = os.getenv('profile_id')
token = os.getenv('my_access_token')
page_id = os.getenv('page_id')

#Your Access Keys
profile_crawl_id = iid
my_access_token = token


def crawl_post(my_access_token, profile_crawl_id):
    url = f"https://graph.facebook.com/{profile_crawl_id}?fields=feed.limit(5)&access_token={my_access_token}"

    posts = requests.get(url).json()['feed']['data']

    utc = parser.parse(datetime.now(tzutc()).astimezone().isoformat())

    day_now = str(utc).split(' ')[0]

    hour_upper = '09:00:00+0000'
    hour_lower = '06:00:00+0000'

    message_post = []

    for post in posts:
        time_post = parser.parse(parser.parse(post['created_time']).astimezone().isoformat())
        day_post = str(time_post).split(' ')[0]
        hour_post = str(time_post).split(' ')[1]
        if (day_post == day_now) and (hour_post < hour_upper) and (hour_post > hour_lower) :
            message_post.append(post['message'])

    return message_post


def processing_post():
    pass

def get_page_token(my_access_token, page_id):
    url = f'https://graph.facebook.com/{page_id}?fields=access_token&access_token={my_access_token}'

    data = requests.get(url).json()

    page_token = data['access_token']

    return page_token


def post_page(page_id):
    page_token = get_page_token(my_access_token, page_id)
    message_crawl = crawl_post(my_access_token, profile_crawl_id)
    message = message_crawl[0]
    url = f'https://graph.facebook.com/{page_id}/feed?message={message}!&access_token={page_token}'
    requests.post(url)

post_page(page_id)