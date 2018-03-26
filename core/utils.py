import requests
from requests_oauthlib import OAuth1
import re
import math
import time
from textblob import TextBlob
from django.conf import settings

# Twitter settings
API_KEY = settings.API_KEY
API_SECRET = settings.API_SECRET
ACCESS_TOKEN = settings.ACCESS_TOKEN
ACCESS_TOKEN_SECRET = settings.ACCESS_TOKEN_SECRET
# Max limit set by twitter
MAX_TWEETS_PER_REQUEST = settings.MAX_TWEETS_PER_REQUEST

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

def user_exists(target_user, auth=auth):
    """ funciton to check if the user with given user_name exists on twitter"""
    BASE_URL = 'https://api.twitter.com/1.1/users/lookup.json'
    url = BASE_URL + '?screen_name=' + target_user
    res = requests.get(url, auth=auth)
    res_data = res.json()
    try:
        if res_data[0]['screen_name'].lower() == target_user.lower():
            return True
        else:
            return False
    except:
        return False


def get_target_user_meta(target_user, auth=auth, requested_meta = None):
    """ This return meta data for the given user """
    BASE_URL = 'https://api.twitter.com/1.1/users/show.json'
    url = BASE_URL + '?screen_name=' + target_user
    res = requests.get(url, auth=auth)
    if res.status_code == 200:
        target_user_meta = res.json()
        if requested_meta:
            return target_user_meta[requested_meta]
        else:
            return target_user_meta
    return False

def get_tweets_data(target_user, auth=auth, max_id=None):
    """ return 200 tweets of given user based on max_id. 200 is limit set by twitter api """
    BASE_URL = 'https://api.twitter.com/1.1/statuses/user_timeline.json?'
    if max_id:
        url = BASE_URL + 'screen_name=' + target_user + '&count=' + str(MAX_TWEETS_PER_REQUEST) + '&max_id=' + max_id
    else:
        url = BASE_URL + 'screen_name=' + target_user + '&count=' + str(MAX_TWEETS_PER_REQUEST)

    res = requests.get(url, auth=auth)
    if res.status_code == 200:
        return res.json()
    else:
        return False

def get_recent_tweet_mentioned(target_user, auth=auth):
    """ return list of dict with recent twitter_handles who mentioned the given twitter_handle and time of mentioning """
    url = 'https://api.twitter.com/1.1/search/tweets.json?q=' + target_user + '&count=10&result_type=recent'
    res = requests.get(url, auth=auth)
    if res.status_code == 200:
        tweets = res.json()['statuses']
        return [{'user_name': tweet['user']['screen_name'], 'created_at': time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))} for tweet in tweets]
    else:
        return False

def do_tweet_analysis(target_user, auth=auth):
    """ Main function which return the analysis of tweets for/of given user """
    from pprint import pprint
    total_tweet_count = get_target_user_meta(target_user=target_user, auth=auth, requested_meta='statuses_count')

    # this seemed better than using ceil function math
    total_requests = (total_tweet_count + MAX_TWEETS_PER_REQUEST - 1) // MAX_TWEETS_PER_REQUEST

    con_list = []
    con_dict = {}
    hashtag_list = []
    hashtag_dict = {}
    tweets = []
    max_tweet_id = None
    mentions_analysed = False

    sum_of_tweet_poliarity = 0
    sum_of_tweet_subjectivity = 0
    average_tweet_polarity = 0
    average_tweet_subjectivity = 0

    for i in range(1, total_requests):
        max_id = None
        tweets = get_tweets_data(target_user, auth, max_id)
        max_id = tweets[-1]['id']
        for tweet in tweets:
            created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))
            tweet_text = tweet['text']

            # sentimental analysis
            blob = TextBlob(tweet_text)
            sum_of_tweet_poliarity +=  blob.sentiment.polarity
            sum_of_tweet_subjectivity += blob.sentiment.subjectivity

            # to get all mentions using regex
            # REVIEW: How to seperate emails from mentions ?
            mentions = re.findall("@([a-zA-Z0-9]{1,15})", tweet_text)
            for mention in mentions:
                list_item = {'user_name': mention, 'created_at': created_at}
                # limiting at 10 because we will require maximum 10
                if  (len(con_list) <= 10) and (not list_item in con_list):
                    con_list.append(list_item)
                if mention in con_dict:
                    con_dict[str(mention)] += 1
                else:
                    con_dict[str(mention)] = 1
            # to get all hash tags
            hashtags = list(re.findall("(?i)(?<=\#)\w+", tweet_text))
            for hashtag in hashtags:
                if hashtag in hashtag_dict:
                    hashtag_dict[str(hashtag)] += 1
                else:
                    hashtag_dict[str(hashtag)] = 1

    # get top ten
    top_ten_connections = sorted(con_dict.keys(),key=con_dict.get,reverse=True)[:10]
    top_ten_hashtags = sorted(hashtag_dict.keys(),key=hashtag_dict.get,reverse=True)[:10]


    # top ten most active connection based on if the user was mentioned by others
    recent_tweet_mentioned = get_recent_tweet_mentioned(target_user=target_user, auth=auth)

    # add to get recent connection, duplicates are to be taken care of
    con_list = con_list + recent_tweet_mentioned
    # sort con_list
    con_list = sorted(con_list, key=lambda k: k['created_at'], reverse=True)
    ten_recent_connections = list(set([str(item['user_name']) for item in con_list]))[:10]

    # ten_most_active_connection
    ten_most_active_connection = [str(item['user_name']) for item in recent_tweet_mentioned]

    # average sentimental analysis
    average_tweet_polarity = sum_of_tweet_poliarity/total_tweet_count
    average_tweet_subjectivity = sum_of_tweet_subjectivity/total_tweet_count

    if average_tweet_polarity > 0:
        polarity = 'positive'
    elif average_tweet_polarity == 0:
        polarity = 'neutral'
    else:
        polarity = 'negative'

    if average_tweet_subjectivity > 0:
        subjectivity = 'positive'
    elif average_tweet_subjectivity == 0:
        subjectivity = 'neutral'
    else:
        subjectivity = 'negative'

    sentimental_analysis = {
        'polarity' : {
            'average_tweet_polarity': average_tweet_polarity,
            'polarity': polarity
        },
        'subjectivity' : {
            'average_tweet_subjectivity': average_tweet_polarity,
            'subjectivity': subjectivity
        }
    }

    return {
        'ten_recent_connections':ten_recent_connections,
        'top_ten_connections': top_ten_connections,
        'ten_most_active_connection': ten_most_active_connection,
        'top_ten_hashtags': top_ten_hashtags,
        'sentimental_analysis': sentimental_analysis
        }
