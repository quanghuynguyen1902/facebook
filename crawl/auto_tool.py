import requests
import os
from dotenv import load_dotenv
import datetime
from dateutil import parser
from datetime import datetime
from dateutil.tz import tzutc, tzlocal
from crontab import CronTab

load_dotenv()

iid = os.getenv('profile_id')
token = os.getenv('my_access_token')
page_id = os.getenv('page_id')

#Your Access Keys
profile_crawl_id = iid
my_access_token = token


def crawl_post(my_access_token, profile_crawl_id):

    '''
        crawl data from specific profile facebook

        Parameters:

        profile_crawl_id: id of the profile facebook to crawl data
        my_access_token: access_token of your account facebook
        
    '''
    
    # get posts from profile facebook
    url = f"https://graph.facebook.com/{profile_crawl_id}?fields=feed.limit(5)&access_token={my_access_token}"
    datas = requests.get(url).json()['feed']['data']

    # get today's date
    utc = parser.parse(datetime.now(tzutc()).astimezone().isoformat())

    # create range time from 6h to 9h
    today_date = str(utc).split(' ')[0]
    upper_hour = '09:00:00+07:00'
    lower_hour = '06:00:00+07:00'

    message_posts = []

    # get the right data
    for data in datas:

        # get time of posts
        posts_time = parser.parse(parser.parse(data['created_time']).astimezone().isoformat())
        # get date of posts
        posts_date = str(posts_time).split(' ')[0]
        # get hour of posts
        posts_hour = str(posts_time).split(' ')[1]

        # check time of posts in the right range
        if (posts_date == today_date) and (posts_hour < upper_hour) and (posts_hour > lower_hour):
            # get message of posts
            message_posts.append(data['message'])

    return message_posts


def processing_text(message_array):
    '''
        process text to get desired text

        Parameters:

        message_array: 
        
    '''
    pass

def get_page_token(my_access_token, page_id):
    '''
        get token of page on facebook

        Parameters:

        page_id: id of page on facebook
        my_access_token: access_token of your account facebook
        
    '''

    url = f'https://graph.facebook.com/{page_id}?fields=access_token&access_token={my_access_token}'

    data = requests.get(url).json()

    page_token = data['access_token']

    return page_token


def post_page(page_id):
    '''
        post status on page

        Parameters:

        page_id: id of page on facebook
        
    '''

    # get page_token 
    page_token = get_page_token(my_access_token, page_id)

    # get data from specific profile facebook
    message_crawl = crawl_post(my_access_token, profile_crawl_id)
    message = message_crawl[0]

    # post status on page
    url = f'https://graph.facebook.com/{page_id}/feed?message={message}!&access_token={page_token}'
    requests.post(url)

# schedule run program
# cron = CronTab()
# job = cron.new(command='python auto_tool.py')
# job.minute.every(1)
