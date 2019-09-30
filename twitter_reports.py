import itertools
import re
import requests
import time
from collections import Counter
from requests.exceptions import TooManyRedirects
from tweepy import API, OAuthHandler

import twitter_credentials

keyword = input("Enter a keyword: ")


class TwitterAuthenticator(object):
    """
    class for twitter authentication
    """

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.API_kEY, twitter_credentials.API_SECRET_KEY)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth


class TwitterReports(object):
    """
    class for generating reports based on a given keyword
    """

    def __init__(self, keyword):
        self.keyword = keyword
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.api = API(self.auth)
        self.tweet_list = [[] for i in range(5)]
        self.all_tweets = []
        self.max_id = 0

    def tweets(self, with_since_id=False, since_id=None, max_id=None):
        """
        collecting tweets
        """
        # we need last 5(minutes) tweet list
        self.tweet_list = self.tweet_list[:5]
        if with_since_id:
            tweets = self.api.search(q=keyword, count=80, since_id=since_id, max_id=max_id)
        else:
            tweets = self.api.search(q=keyword, count=80, tweet_mode='extended')
        tweets = [i for i in tweets]
        if tweets:
            self.max_id = tweets[0].id
        else:
            self.max_id = self.max_id if self.max_id else 0

        self.all_tweets = tweets
        self.tweet_list.insert(0, self.all_tweets)

    def get_user_report(self):
        """
        :return: blank string instead of NOne to make terminal clean
        """
        print("-------------------------------User Report--------------------------------")
        for tweet in self.all_tweets:
            print("User name: ", tweet.user.name)
            print("Tweet Counts: ", tweet.user.statuses_count)
        return ''

    def get_link_report(self):
        print("-------------------------------Link Report--------------------------------")
        link_list = []
        error_list = []

        for tweet in itertools.chain.from_iterable(self.tweet_list):
            # finding links
            p2 = re.compile(
                r'(?:http|ftp|https)://(?:[\w_-]+(?:(?:\.[\w_-]+)+))(?:[\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?')
            links = p2.findall(tweet.full_text)
            for link in links:
                try:
                    expanded_link = requests.head(link, allow_redirects=True)
                except TooManyRedirects:
                    # handling too many redirects error
                    error_list.append(link)
                    continue

                if expanded_link.status_code != 404:
                    splited_link = expanded_link.url.split("/")
                    domain = f'{splited_link[0]}//{splited_link[2]}'
                    link_list.append(domain)
                error_list.append(link)
        cnt = Counter(link_list)
        print("Number of links", len(cnt))
        print("list of unique domains", sorted(cnt, key=cnt.get, reverse=True))
        return ''

    def content_report(self):
        print("-------------------------------Content Report--------------------------------")
        content_list = []
        common_words = ["a", "an", "the", "of", "with", "at", "to", "into", "from", "in",
                        "on", "by", "for", "and", "but", "am", "is", "are", "have", "has",
                        "had", "was", "were", "will", "shall", "be"]
        for tweet in itertools.chain.from_iterable(self.tweet_list):
            # print("text**", tweet.full_text)
            words_list = tweet.full_text.split()
            for word in words_list:
                if word.lower() not in common_words:
                    content_list.append(word)
        counter = Counter(content_list)
        print("No of unique words:", len(counter))
        print("top ten words sorted by occurrence:", sorted(counter, key=counter.get, reverse=True)[:10])
        return ''


if __name__ == '__main__':

    twitter_reports = TwitterReports(keyword)
    print(twitter_reports.tweets())
    print(twitter_reports.get_user_report())
    print(twitter_reports.get_link_report())
    print(twitter_reports.content_report())
    while True:
        # def scheduled_runner():
        """
        function to run scheduled job
        :return: blank string to keep the output clean
        """
        # waiting for 60 seconds
        time.sleep(60)
        twitter_reports.tweets(with_since_id=True, since_id=twitter_reports.max_id, max_id=twitter_reports.max_id + 100)
        print(twitter_reports.get_user_report())
        print(twitter_reports.get_link_report())
        print(twitter_reports.content_report())
