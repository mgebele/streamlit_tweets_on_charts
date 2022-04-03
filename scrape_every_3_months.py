# %% [markdown]
# # 1. Scrape all tweets every 3 months!
# # 2. Store in csvs locally
# # 3. push csvs automatically into repo here!

# %%
from git import Repo
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from datetime import datetime, timedelta
import plotly.graph_objects as go
import datetime
import pandas as pd
import tweepy
import csv
import os
import time
from dateutil import tz
import glob
import quandl as q
import re
import streamlit as st
st.set_page_config(layout="wide")

# %%
# Twitter API credentials
consumer_key = os.environ["twtr_consumer_key"]
consumer_secret = os.environ["twtr_consumer_secret"]
access_key = os.environ["twtr_access_key"]
access_secret = os.environ["twtr_access_secret"]
quandl_api_key = os.environ["quandl_api_key"]


# %%
def get_all_stored_twitter_user_csvs():
    # get all csv file names - already scraped users
    extension = 'csv'
    all_twitter_user_scraped_csvs = glob.glob(
        r'twitterdata/*.{}'.format(extension))  # CHANGE FOR SHARE STREAMLIT to /
    # filter the price csv
    all_twitter_user_scraped_csvs = [
        k for k in all_twitter_user_scraped_csvs if 'BITFINEX' not in k]
    # filter the price csv
    all_twitter_user_scraped_csvs = [
        k for k in all_twitter_user_scraped_csvs if 'relevant_words' not in k]
    display_name_all_twitter_user_scraped_csvs = [
        i.split(' ', 1)[0].split("twitterdata\\")[1] for i in all_twitter_user_scraped_csvs]

    return display_name_all_twitter_user_scraped_csvs, all_twitter_user_scraped_csvs


display_name_all_twitter_user_scraped_csvs, all_twitter_user_scraped_csvs = get_all_stored_twitter_user_csvs()
unique_display_name_all_twitter_user_scraped_csvs = list(
    set(display_name_all_twitter_user_scraped_csvs))
unique_display_name_all_twitter_user_scraped_csvs

# %%
for screen_name in unique_display_name_all_twitter_user_scraped_csvs:
    try:

        print(screen_name)
        # Twitter only allows access to a users most recent 3240 tweets with this method
        # authorize twitter, initialize tweepy
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_key, access_secret)
        api = tweepy.API(auth)

        # initialize a list to hold all the tweepy Tweets
        alltweets = []

        try:
            # make initial request for most recent tweets (200 is the maximum allowed count)
            new_tweets = api.user_timeline(screen_name=screen_name, count=200)
        except:
            st.error('Username does not exist')

        # save most recent tweets
        alltweets.extend(new_tweets)

        # save the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1

        my_bar = st.progress(0)
        progress_complete = 0

        # keep grabbing tweets until there are no tweets left to grab
        while len(new_tweets) > 0:

            progress_complete += 7
            if progress_complete >= 100:
                progress_complete = 100
            my_bar.progress(progress_complete)

            # all subsiquent requests use the max_id param to prevent duplicates
            new_tweets = api.user_timeline(
                screen_name=screen_name, count=200, max_id=oldest)

            # save most recent tweets
            alltweets.extend(new_tweets)

            # update the id of the oldest tweet less one
            oldest = alltweets[-1].id - 1

            print(f"...{len(alltweets)} tweets downloaded so far")

        # transform the tweepy tweets into a 2D array that will populate the csv
        outtweets = [[tweet.id_str, tweet.created_at, tweet.text]
                     for tweet in alltweets]

        # remove progress bar now after completion
        my_bar.empty()
        with open(r'twitterdata/{0} {1}.csv'.format(screen_name, oldest), 'w',  encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "created_at", "text"])
            writer.writerows(outtweets)

    except:
        print("error for {}".format(screen_name))

# now update git:
# # make sure .git folder is properly configured

PATH_OF_GIT_REPO = r'C:\Users\mg\github\\streamlit_tweets_on_charts\.git'
now = datetime.datetime.now()
COMMIT_MESSAGE = 'new game update htdatan {}'.format(now.date())

repo = Repo(PATH_OF_GIT_REPO)
repo.git.add(update=True)
repo.index.commit(COMMIT_MESSAGE)
origin = repo.remote(name='origin')
origin.push()
