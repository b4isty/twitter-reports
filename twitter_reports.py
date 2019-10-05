import itertools
import re
from collections import Counter
from datetime import timedelta

import requests
from requests.exceptions import TooManyRedirects
from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener

import twitter_credentials
from helpers import custom_time_now

keyword = input("Enter a keyword: ")


class TwitterAuthenticator(object):
    """
    class for twitter authentication
    """

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.API_kEY, twitter_credentials.API_SECRET_KEY)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth


class TwitterStreamer:
    """
    Class for streaming and processing live tweets
    """

    def __init__(self):
        self.twitter_auth = TwitterAuthenticator()

    def stream_tweets(self, keyword):
        listener = TwitterListener()
        auth = self.twitter_auth.authenticate_twitter_app()
        stream = Stream(auth, listener)
        stream.filter(track=[keyword])


class TwitterListener(StreamListener):
    """
    This is a listener that just prints received tweets to stdout
    """
    now = custom_time_now()

    def __init__(self):
        super(TwitterListener, self).__init__()

        self.content_text = ""
        self.raw_tweets = []
        self.tweet_list = []
        self.all_link_list = [[] for _ in range(5)]
        self.link_list = []
        self.error_link_list = []
        self.all_tweets = [[] for _ in range(5)]
        self.now = custom_time_now()
        self.user_list = []

    def get_user_report(self):
        """
        :return: blank string instead of None to make terminal clean
        """
        print("-------------------------------User Report--------------------------------")
        for user in self.user_list:
            print("User name: ", user.name)
            print("Tweet Counts: ", user.statuses_count)
        return ''

    def get_tweet_text(self, status):
        if hasattr(status, "retweeted_status"):  # Check if Retweetter
            try:
                text = status.retweeted_status.extended_tweet["full_text"]

            except AttributeError:
                text = status.retweeted_status.text
        else:
            try:
                text = status.extended_tweet["full_text"]
            except AttributeError:
                text = status.text
        self.tweet_list.append(text)
        return text

    def get_link(self, tweet):
        """
        finds link and store in a list
        :return: clean text without link
        """

        p2 = re.compile(
            r'(?:http|ftp|https)://(?:[\w_-]+(?:(?:\.[\w_-]+)+))(?:[\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?')
        links = p2.findall(tweet)
        content_text = ''

        for link in links:
            content_text = tweet.replace(link, '')
            try:
                expanded_link = requests.head(link, allow_redirects=True)
            except TooManyRedirects:
                self.error_list.append(link)
                continue
            if expanded_link.status_code != 404:
                splited_link = expanded_link.url.split("/")
                domain = f'{splited_link[0]}//{splited_link[2]}'
                self.link_list.append(domain)
            self.error_link_list.append(link)
        if content_text:
            return content_text
        return tweet

    def get_link_report(self):
        print("----------------------------Link Report---------------------")
        cleaned_links = itertools.chain.from_iterable(self.all_link_list)
        cnt = Counter(cleaned_links)
        print("Number of links", len(cnt))
        print("list of unique domains", sorted(cnt, key=cnt.get, reverse=True))

    def content_report(self):

        """
        function to create content report based
        on tweet list
        """
        print("----------------------------Content Report---------------------")
        content_list = []
        common_words = ["a", "an", "the", "of", "with", "at", "to", "into", "from", "in",
                        "on", "by", "for", "and", "but", "or", "so", "you", "i", "am", "is",
                        "are", "have", "has", "had", "was", "were", "will", "shall", "be", '']
        tweet_list = itertools.chain.from_iterable(self.all_tweets)

        words_list = ','.join(list(tweet_list)).split(' ')
        for word in words_list:
            if word.lower() not in common_words:
                content_list.append(word)
        counter = Counter(content_list)
        print("No of unique words:", len(counter))
        print("top words sorted by occurrence:", sorted(counter, key=counter.get, reverse=True)[:10])
        return ''

    def on_status(self, status):
        self.user_list.append(status.user)
        return self.runner(status)

    def on_error(self, status_code):
        if status_code == 420:
            return False
        print(status_code)

    def runner(self, status):
        full_text = self.get_tweet_text(status)
        content = self.get_link(full_text)
        self.tweet_list.append(content)

        cur_time = custom_time_now()
        if self.now + timedelta(seconds=60) == cur_time:
            self.now = custom_time_now()
            if self.tweet_list:
                self.all_tweets.insert(0, self.tweet_list)
                self.all_tweets = self.all_tweets[:5]
            if self.link_list:
                self.all_link_list.insert(0, self.link_list)
                self.all_link_list = self.all_link_list[:5]
            self.tweet_list = list()
            self.link_list = []
            self.get_user_report()
            self.get_link_report()
            self.content_report()


twitter_streamer = TwitterStreamer()
twitter_streamer.stream_tweets(keyword)