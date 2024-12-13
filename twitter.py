import os
import requests
import json

from __init__ import *
from requests_oauthlib import OAuth1Session

print("Welcome to the Twitter Scraper")


class Tokens(object):
    @property
    def API(self):
        return os.getenv("api_key")

    @property
    def API_SECRET(self):
        return os.getenv("api_key_secret")

    @property
    def BEARER(self):
        return os.getenv("bearer_token")

    @property
    def ACCESS(self):
        return os.getenv("access_token")

    @property
    def ACCESS_SECRET(self):
        return os.getenv("access_token_secret")


class Scraper(object):
    def __init__(self, tier):
        self.base_url = X_API_URL
        self.tokens = Tokens()
        self.headers = {"Authorization": "Bearer %s" % self.tokens.BEARER}
        self.token_expired_message = "TOKEN_EXPIRED"
        self.tmr_message = "TOO_MANY_REQUESTS"
        self.subscription_tier = tier

    def _request(self, method, url, params=None, data=None, json=None, oauth=None):
        if oauth:
            response = oauth.get(url, params=params)
        else:
            response = requests.request(method, url, headers=self.headers,
                                        params=params, data=data, json=json)
        if response:
            if response.status_code == 401:
                self.refresh_token()
                return self.token_expired_message
            if response.status_code == 429:
                return self.tmr_message
            if response.status_code == 200:
                return response.json()

            raise Exception("Unknown status code returned")

        raise Exception("Could not get the response from X API")

    def get_recent_tweets(self, query):
        endpoint = "%s/2/tweets/search/recent" % self.base_url
        response = self._request("GET", endpoint, params=query)
        if response == "TOKEN_EXPIRED":
            response = self._request("GET", endpoint, params=query)
        print(response.json())

    def get_profile(self, oauth):
        endpoint = "%s/2/users/me" % self.base_url
        response = self._request("GET", endpoint, oauth=oauth, params=PROFILE_PARAMS)
        if response == "TOKEN_EXPIRED":
            response = self._request("GET", endpoint)
        print(response.json())

    def refresh_token(self):
        pass

    def initialize_oauth(self):
        oauth = OAuth1Session(self.tokens.API,
                              client_secret=self.tokens.API_SECRET)
        fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        authorization_url = oauth.authorization_url(BASE_AUTHORIZATION_URL)
        print("Please go here and authorize: %s" % authorization_url)
        verifier = input("Paste the PIN here: ")
        oauth = OAuth1Session(
            self.tokens.API,
            client_secret=self.tokens.API_SECRET,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]
        return OAuth1Session(
            self.tokens.API,
            client_secret=self.tokens.API_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

    def run(self, query=None):
        if self.subscription_tier != "free":
            recent_tweets = self.get_recent_tweets(query)
        else:
            profile_data = self.get_profile(oauth=self.initialize_oauth())


if __name__ == "__main__":
    subscription_tier = os.getenv("subscription_tier")
    scraper = Scraper(subscription_tier)
    if subscription_tier != "free":
        with open("queries.json") as f:
            queries = json.load(f)
            for query in queries:
                scraper.run(query)
    else:
        scraper.run()

    print("Scraping completed")
