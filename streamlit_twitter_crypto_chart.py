from datetime import datetime
import plotly.graph_objects as go
import datetime
import pandas as pd
import streamlit as st


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
global widthfig
widthfig = 950

twitter_user = "new_ThinkingUSD_tweets"
datasource = "BITFINEX/BTCUSD"

tweet_data = pd.read_csv("{}.csv".format(
    twitter_user))
# Preview the first 5 lines of the loaded data

current_time = datetime.datetime.today().strftime('%Y-%m-%d')

data = pd.read_csv("{}.csv".format(
    datasource.replace("/", "_")), index_col=0)


fig = go.Figure(
    data=[go.Candlestick(x=data.index,
                         open=data['First'],
                         high=data['High'],
                         low=data['Low'],
                         close=data['Last'],
                         name="{}".format(datasource),
                         )],

)

fig.add_trace(
    # go.Scatter(mode = "markers+text",
    go.Scatter(mode="markers",
               x=tweet_data["created_at"],
               y=[0] * len(tweet_data["created_at"]),
               name="{}".format(twitter_user),
               text=tweet_data["text"],
               textposition="top center"

               ))

fig.update_layout(
    # title="Plot Title",
    autosize=False,
    width=1200,
    height=600,)

# fig.add_trace(
#     go.Scatter(mode = "lines",
#         x=data.index,
#         y=data["100movingaverage"],
#         name='100movingaverage'
#     ))

# fig.add_trace(
#     go.Scatter(mode = "lines",
#         x=data.index,
#         y=data["200movingaverage"],
#         name='200movingaverage'
#     ))


st.title("Tweets on charts")

# TODO add NLP to filter tweets, make search of tweets by text available?
st.plotly_chart(fig)
