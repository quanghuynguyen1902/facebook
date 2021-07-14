import requests
import os
from dotenv import load_dotenv
import datetime
from dateutil import parser
from datetime import datetime
from dateutil.tz import tzutc, tzlocal
from celery import Celery
from celery.schedules import crontab 
import pytz
from dateutil.tz import gettz

load_dotenv()

iid = os.getenv('profile_id')
token = os.getenv('my_access_token')
page_id = os.getenv('page_id')

#Your Access Keys
profile_crawl_id = iid
my_access_token = token


app = Celery('tasks', broker='amqp://admin:12345678@rabbit:5672')

app.conf.timezone = 'Asia/Ho_Chi_Minh'

app.conf.beat_schedule = {
    # executes every 
    'post-page': {
        'task': 'auto_tool.post_page',
        'schedule': crontab(minute=29, hour=22),
    },
    
}


@app.task
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

    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    # get today's date
    utc = parser.parse(datetime.now(tz).astimezone().isoformat())
    # create range time from 6h to 9h
    today_date = str(utc).split(' ')[0]
    upper_hour = '09:00:00+07:00'
    lower_hour = '06:00:00+07:00'

    message_posts = []

    VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

    # get the right data
    for data in datas:

        # get time of posts
        posts_time = parser.parse(parser.parse(data['created_time']).astimezone(VN_TZ).isoformat())
        print(posts_time)
        # get date of posts
        posts_date = str(posts_time).split(' ')[0]
        # get hour of posts
        posts_hour = str(posts_time).split(' ')[1]

        # check time of posts in the right range
        if (posts_date == today_date) and (posts_hour < upper_hour) and (posts_hour > lower_hour):
            # get message of posts
            message_posts.append(data['message'])

    return message_posts


@app.task
def process_new(st):
    res = st.replace('"', "")
    res = res.replace("'", "")
    res = res.replace("+)", "+")
    res = res.replace("+ )", "+")
    res = res.replace("...", " ")
    res = res.replace("..", " ")
    if res == '' or len(res) < 25:
        return ''
    if res[-1] in ['.', ';', ',']:
        res = res[:-1]
    return res.lstrip()

@app.task
def processing_text(message):
    lines = message.splitlines()
    lines = [x for x in lines if x != '']
    pre_categories = ['TIN COVID', 'TRONG NƯỚC', 'KINH DOANH', 'KHÁM PHÁ', 'THẾ GIỚI', 'GIẢI TRÍ - THỂ THAO', 'P.PHÁP HỌC', 'Ý TƯỞNG LÀM GIÀU']
    new_categories = [x for x in lines if x.isupper()]
    categories = list(set(pre_categories + new_categories))
#     print(categories)
    
    cur_cat = 'TIN COVID'
    cur_news = []
    res = {}
    for line in lines:
        if line.isupper():
            if cur_news:
                res[cur_cat] = cur_news
            cur_news = []
            cur_cat = line
        else:
            if line == '':
                continue
            pline = process_new(line)
            if pline == '':
                continue
            if pline[0] == '+':
                if pline.find('+ ') == -1:
                    pline = pline.replace('+', '+ ')
                pline = pline.replace('+', '🎶')
                cur_news.append(pline)
    return res

@app.task
def kinhdoanh(news):
    today = datetime.today().strftime('%d/%m')
    message = f'🚨 BẢN TIN KINH DOANH NGÀY {today} 💥\n\n' + '\n'.join(news['KINH DOANH'])
    if 'Ý TƯỞNG LÀM GIÀU' in news:
        message += '\n 💵 Ý TƯỞNG LÀM GIÀU \n \n' + '\n'.join(news['Ý TƯỞNG LÀM GIÀU'])
    
    message += '\n\n💠 📢 Làm gì làm ngày nào cũng vào kênh 𝑷𝒊𝒈𝑩𝒊𝒓𝒅 cập nhật tin tức nhé mọi người! 📢 🤟 ' 
    return message

@app.task
def tinnong(news):
    today = datetime.today().strftime('%d/%m')
    message = f'🌋🌋 TIN NÓNG NGÀY {today} 🔥🔥\n\n'
    message += f'🌡 TIN COVID 🛬\n' + '\n'.join(news['TIN COVID'])
    if 'TRONG NƯỚC' in news:
        message += '\n\n🚈 TRONG NƯỚC 🏖\n' + '\n'.join(news['TRONG NƯỚC'])
    if 'THẾ GIỚI' in news:
        message += '\n\n🌎 THẾ GIỚI 🛸\n' + '\n'.join(news['THẾ GIỚI'])
    
    message += '\n\n💠 📢 Làm gì làm ngày nào cũng vào kênh 𝑷𝒊𝒈𝑩𝒊𝒓𝒅 cập nhật tin tức nhé mọi người! 📢 🤟 ' 
    return message

@app.task
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

@app.task
def post_page():
    '''
        post status on page

        Parameters:

        page_id: id of page on facebook
        
    '''

    # get page_token 
    page_token = get_page_token(my_access_token, page_id)
    # get data from specific profile facebook
    message_crawl = crawl_post(my_access_token, profile_crawl_id)
    message = ''
    for mess in message_crawl:
        if 'Tin nóng' in mess:
            message = mess 

    if(message != ''):
        res = processing_text(message)
    
        # post status on page
        kinhdoanh_post = kinhdoanh(res)
        url = f'https://graph.facebook.com/{page_id}/feed?message={kinhdoanh_post}!&access_token={page_token}'
        requests.post(url)
    
        tinnong_post = tinnong(res)
        url = f'https://graph.facebook.com/{page_id}/feed?message={tinnong_post}!&access_token={page_token}'
        requests.post(url)
