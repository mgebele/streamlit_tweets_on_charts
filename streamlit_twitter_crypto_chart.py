import streamlit as st
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
pd.set_option('display.max_columns', None)
st.set_page_config(layout="wide")

# Twitter API credentials
consumer_key = os.environ["twtr_consumer_key"]
consumer_secret = os.environ["twtr_consumer_secret"]
access_key = os.environ["twtr_access_key"]
access_secret = os.environ["twtr_access_secret"]
quandl_api_key = os.environ["quandl_api_key"]


# TODO STORE FILE CREATINO DATE IN CSV FILENAMES TO CHECK WHEN WAS CREATED AND 24 hours limit on updatin new tweets!


def _max_width_():
    max_width_str = f"max-width: 1300px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


_max_width_()

# / - for deployment and \\ for local testing
path='twitterdata/'

def get_all_stored_twitter_user_csvs():
    # get all csv file names - already scraped users
    extension = 'csv'
    all_twitter_user_scraped_csvs = glob.glob(
        r'{}*.{}'.format(path, extension))  # CHANGE FOR SHARE STREAMLIT to /
    # filter the price csv
    all_twitter_user_scraped_csvs = [
        k for k in all_twitter_user_scraped_csvs if 'BITFINEX' not in k]
    # filter the price csv
    all_twitter_user_scraped_csvs = [
        k for k in all_twitter_user_scraped_csvs if 'relevant_words' not in k]

    display_name_all_twitter_user_scraped_csvs = [
        i.split(' ', 1)[0].split("{}".format(path))[1] for i in all_twitter_user_scraped_csvs]

    return display_name_all_twitter_user_scraped_csvs, all_twitter_user_scraped_csvs


def get_all_tweets(screen_name):

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
        return

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


def main(user_selection_list_containing_twitter_user):

    display_name_all_twitter_user_scraped_csvs, all_twitter_user_scraped_csvs = get_all_stored_twitter_user_csvs()

    # st.write(user_selection_list_containing_twitter_user)
    # st.write(all_twitter_user_scraped_csvs)
    # map name back to filename:
    # empty space at the end to check if its the exact same name and
    # not matching until there like AltcoinGordon for AltcoinGordons
    # user_selection_list_containing_twitter_user = [
    #     k for k in all_twitter_user_scraped_csvs if user_selection_list_containing_twitter_user in k]

    # here we can get multiple files from different times of scraping the specific user
    # now we read all of those files and merge them together into one df
    list_of_dfs = []
    for user_file in user_selection_list_containing_twitter_user:
        tweet_data = pd.read_csv("{}".format(user_file))
        list_of_dfs.append(tweet_data)

    tweet_data = pd.concat(list_of_dfs)

    st.session_state.first_run = False

    # for the right naming we take the first entry
    user_selection_list_containing_twitter_user = user_selection_list_containing_twitter_user[0]

    # streamlit layout
    st.title("Tweets on charts - {}".format(
        user_selection_list_containing_twitter_user.split(" ")[0].split("{}".format(path))[1]))

    # # # start - read in BTC data # # #
    datasource_btcusd = "BITFINEX/BTCUSD.csv"
    btcusd_data = pd.read_csv("coindata/{}".format(
        datasource_btcusd.replace("/", " ")), index_col=0)
    btcusd_data.index = pd.to_datetime(btcusd_data.index)

    most_recent_stored_btcusd_date = btcusd_data.sort_index().tail(
        1).index[0].strftime("%Y-%m-%d")
    todays_date = datetime.date.today() - timedelta(days=1)
    todays_date = todays_date.strftime("%Y-%m-%d")

    # st.write(most_recent_stored_btcusd_date)
    # st.write(todays_date)

    if most_recent_stored_btcusd_date != todays_date:
        data = q.get(datasource_btcusd.split(".")[0],   start_date=most_recent_stored_btcusd_date,
                     end_date='{}'.format(todays_date),
                     api_key=quandl_api_key)
        data.info()
        data["First"] = data.Last.shift(1)
        data.dropna()
        btcusd_data = pd.concat([btcusd_data, data])
        btcusd_data = btcusd_data.sort_index()
        # store current df with up-to-date values
        btcusd_data.to_csv('coindata/{}'.format(
            datasource_btcusd.replace("/", " ")), index=True)
    # # # end - read in BTC data # # #

    # # # start - processing and cleaning of tweets # # #




    # Instantiate the sentiment intensity analyzer
    rel_tweet_data = tweet_data[tweet_data['text'].str.contains(
        '|'.join(option))]
    # rel_tweet_data = rel_tweet_data[~rel_tweet_data['text'].str.contains("@")]

    rel_tweet_data["created_at"] = pd.to_datetime(
        rel_tweet_data["created_at"], utc=True, errors='coerce')
    rel_tweet_data = rel_tweet_data[rel_tweet_data['created_at'].notna()]

    rel_tweet_data['created_at'] = rel_tweet_data['created_at'].dt.tz_localize(
        None)
    rel_tweet_data['created_at_day'] = rel_tweet_data['created_at'].dt.round(
        '1d')

    print(rel_tweet_data.columns)
    print(rel_tweet_data.head())
    if deactivate_retweets:
        rel_tweet_data = rel_tweet_data[~rel_tweet_data['text'].str.startswith("RT ") ]

    rel_tweet_data_incl_price = pd.merge(
        rel_tweet_data, btcusd_data, how="left", left_on=rel_tweet_data["created_at_day"], right_on=btcusd_data.index,)
    # # # end - processing and cleaning of tweets # # #

    print("tweets displayed", len(rel_tweet_data))

    # # # start - chart with tweets # # #
    fig = go.Figure(
        data=[go.Candlestick(x=btcusd_data.index,
                             open=btcusd_data['First'],
                             high=btcusd_data['High'],
                             low=btcusd_data['Low'],
                             close=btcusd_data['Last'],
                             name="{}".format(datasource_btcusd.split("/")
                                              [1].split(".")[0]),
                             )],
    )

    # add tweets to the candle - chart
    fig.add_trace(
        go.Scatter(mode="markers",
                   x=rel_tweet_data_incl_price["created_at"],
                   y=rel_tweet_data_incl_price["High"]*1.1,
                   name='tweets',
                   text=rel_tweet_data_incl_price["text"],
                   textposition="top center",
                   marker={'color': "#0d75f8",  # clear blue
                           'size': 4
                           }
                   )
    )
    fig.update_layout(
        # title="Plot Title",
        autosize=False,
        width=int(1400/1.3),
        height=int(800/1.3),
        xaxis_range=[rel_tweet_data_incl_price["created_at"].min(
        ), rel_tweet_data_incl_price["created_at"].max()]
        # fig.layout.xaxis.range[0]:fig.layout.xaxis.range[1]
    )
    st.plotly_chart(fig)
    # # # end - chart with tweets # # #

    # # # start - add word cloud # # #
    # get all the rows into one string
    complete_str = rel_tweet_data['text'].str.cat(sep=' ')

    stopwords = set(STOPWORDS)
    stopwords.update(["and", "or", "https", "year", "will", "post", "see",
                      "going", "now", "actually", "co", "go",  "look", "make", "right", "people",
                      "RT", "really", "first", "right", "week", "still", "twitter",
                      "even", "re", "lol", "new", "much", "day", "haha", "dont", "well", "us", "sure",
                      "don", "pretty", "looks", "Thank", "another", "thing", "view", "lot",
                      "next", "many", "way", "one", "Oh", "say", "im"])
    wordcloud = WordCloud(width=int(1200/1.5), stopwords=stopwords, height=int(800/1.5), max_font_size=200,
                          max_words=50, collocations=False, background_color='black').generate(complete_str)
    fig = plt.figure(figsize=(40, 30))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()
    st.pyplot(fig)
    # # # end - add word cloud # # #


run_it = st.sidebar.button('Show visualizations')

st.sidebar.text("")


display_name_all_twitter_user_scraped_csvs, all_twitter_user_scraped_csvs = get_all_stored_twitter_user_csvs()

display_name_user_selection_list_containing_twitter_user = st.sidebar.selectbox(
    "Select existing Twitter-User", list(set(display_name_all_twitter_user_scraped_csvs)), 0)

# map name back to filename:
user_selection_list_containing_twitter_user = [
    k for k in all_twitter_user_scraped_csvs if display_name_user_selection_list_containing_twitter_user in k]
user_selection_list_containing_twitter_user = user_selection_list_containing_twitter_user

allowed_user_input_characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D',
                                 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '$', '%', '_', '!', '§']


# add new twitter user data
twitter_name = ""

# update_selected_user = st.sidebar.button(
#     'Update tweets')

user_input_twitter_name = st.sidebar.text_input(
    "Add new Twitter-User data", twitter_name)


st.sidebar.text("")
st.sidebar.text("")

deactivate_retweets = st.sidebar.checkbox('no Retweets')

new_search_word = ""
user_input_new_search_word = st.sidebar.text_input(
    "Add new Searchword", new_search_word)

datasource = "relevant_words.csv"
relevant_words = []
with open("tmp/" + datasource, newline='') as inputfile:
    for row in csv.reader(inputfile):
        relevant_words.append(row)
relevant_words = relevant_words[0]

if user_input_new_search_word:
    button_add_new_searchword = st.sidebar.button('Add Searchword')
    if button_add_new_searchword:
        if user_input_new_search_word not in relevant_words:

            if any(x not in allowed_user_input_characters for x in user_input_new_search_word):
                st.error(
                    'Character not allowed, please dont use special characters')
            else:
                relevant_words.append(user_input_new_search_word)
                with open("tmp/" + datasource, 'w') as f:
                    write = csv.writer(f)
                    write.writerow(relevant_words)
                st.success('Searchword added')

        else:
            st.error('Searchword already there')


relevant_words = []
with open("tmp/" + datasource, newline='') as inputfile:
    for row in csv.reader(inputfile):
        relevant_words.append(row)
relevant_words = relevant_words[0]

# # # start - read in BTC data # # #
option = st.sidebar.multiselect(
    'Searchwords:', relevant_words, relevant_words
)


if user_input_twitter_name:
    # if user_input_twitter_name not in display_name_all_twitter_user_scraped_csvs:
    display_name_all_twitter_user_scraped_csvs, all_twitter_user_scraped_csvs = get_all_stored_twitter_user_csvs()
    # map name back to filename:
    user_selection_list_containing_twitter_user = [
        k for k in all_twitter_user_scraped_csvs if user_input_twitter_name+" " in k]
    has_user_been_scraped_last_24h = []
    for user in user_selection_list_containing_twitter_user:
        # if the file was created longer than 24 hours ago
        print("os.path.getmtime(user) {}".format(os.path.getmtime(user)))
        print("user".format(user))
        print("user_selection_list_containing_twitter_user")
        print(user_selection_list_containing_twitter_user)
        if os.path.getmtime(user) + 60*60*24 > time.time():

            has_user_been_scraped_last_24h.append(os.path.getmtime(user))

    # if len(has_user_been_scraped_last_24h) == 0:
    if any(x not in allowed_user_input_characters for x in user_input_twitter_name):
        st.error(
            'Character not allowed, please dont use special characters')
    else:
        button_get_twitter_name_data = st.button(
            'get last 3300 tweets of {}'.format(user_input_twitter_name))
        if button_get_twitter_name_data:
            get_all_tweets(user_input_twitter_name)
            # search for file with the name of user input
            main(user_input_twitter_name)
    # elif len(has_user_been_scraped_last_24h) == 1:
    #     st.error('Username has been already scraped in the last 24 hours.')
    # else:
    #     st.error('Error.')


# if update_selected_user:
#     user_input_twitter_name = display_name_user_selection_list_containing_twitter_user
#     print(user_input_twitter_name)
#     print(update_selected_user)
#     # if user_input_twitter_name not in display_name_all_twitter_user_scraped_csvs:
#     display_name_all_twitter_user_scraped_csvs, all_twitter_user_scraped_csvs = get_all_stored_twitter_user_csvs()
#     # map name back to filename:
#     user_selection_list_containing_twitter_user = [
#         k for k in all_twitter_user_scraped_csvs if user_input_twitter_name+" " in k]
#     has_user_been_scraped_last_24h = []
#     for user in user_selection_list_containing_twitter_user:
#         # if the file was created longer than 24 hours ago
#         print("os.path.getmtime(user) {}".format(os.path.getmtime(user)))
#         print("user".format(user))
#         print("user_selection_list_containing_twitter_user")
#         print(user_selection_list_containing_twitter_user)
#         if os.path.getmtime(user) + 60*60*24 > time.time():

#             has_user_been_scraped_last_24h.append(os.path.getmtime(user))

#     # if len(has_user_been_scraped_last_24h) == 0:
#     if any(x not in allowed_user_input_characters for x in user_input_twitter_name):
#         st.error(
#             'Character not allowed, please dont use special characters')
#     else:
#         button_get_twitter_name_data = st.button(
#             'get last 3300 tweets of {}'.format(user_input_twitter_name))
#         if button_get_twitter_name_data:
#             get_all_tweets(user_input_twitter_name)
#             # search for file with the name of user input
#             main(user_input_twitter_name)
    # elif len(has_user_been_scraped_last_24h) == 1:
    #     st.error('Username has been already scraped in the last 24 hours.')
    # else:
    #     st.error('Error.')


# add excluded_words
st.sidebar.text("")
st.sidebar.text("")
excluded_words = ["buy", "sell"]

# placeholder = st.sidebar.empty()

# click_clear = st.sidebar.button('clear text input', key=1)
# if click_clear:
#     added_excluded_words = st.sidebar.text_input(
#         'New searchword', value='', key=1)


if 'first_run' not in st.session_state:

    relevant_words = [
        "good", "stop",
        "think", "price", "buy",
        "take", "money", 'bitcoin',
        'BTC', 'long', 'trading',
        'trade', 'short', 'market',
        'BitMEX', 'money', 'position',
        'good', 'trader', 'buy',
        'low', 'ETH', 'price',
        'bullish', 'high', 'close',
        'buying', 'spot', 'ThinkingBitmex',
        'bear', 'level', 'chart',
        'range', 'profit', 'volume',
        'dip', 'bid', 'bottom',
        'liquidity', 'hedge', 'top',
        'coin', 'call', 'sell',
        'exchange', 'SNX', 'order'
        'DeFi', 'bought', 'volatility',
        'risk', 'bounce', 'ATH',
        'PnL', 'size', 'million',
        'selling', 'quarter', 'portfolio',
        'signal', 'bull', 'SOL',
        'FTT', 'shorting', '10k',
        'bearish', 'option', 'asset',
        'leverage', 'open', '5k',
        'bad']

    datasource = "relevant_words.csv"
    with open("tmp/" + datasource, 'w') as f:
        write = csv.writer(f)
        write.writerow(relevant_words)

    st.session_state.first_run = True

if run_it or st.session_state.first_run:
    main(user_selection_list_containing_twitter_user)
