from datetime import datetime
import requests
import tweepy
from tweepy import NotFound
import json
from sty import fg
from random import randint

"""\
Gets Twitter username, date of next birthday and a number and sends the time remaining until the event.
    The number defines the maximum number of times the message will be sent per day.
It is possible not to give a username parameter and the calculation will be performed locally only.


Possible upgrades in the future:
- Possibility of a specific sending time for each user.
- Listening to DMs which are received with appropriate parameters and automatically adding them
    to the mailing list Or alternatively a one-time repeat message.
"""


class Countdown:
    """:)"""

    def __init__(self, year, month, day, username=None, max_in_day=0):
        self.username = username
        self.max_in_day = max_in_day
        self.next_birthday = datetime(year, month, day)
        self.__previous_birthday = datetime(year - 1, month, day)
        self.__time_til_next_birthday = self.next_birthday - datetime.today()
        self.__year_length = int(str(self.next_birthday - self.__previous_birthday)[0:3])

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, username):
        try:
            user = self.__twitter_api().get_user(screen_name=username)
            self.__username = username
        except NotFound:
            self.__username = None
            print("Invalid or nonexistent username")

    @staticmethod
    def randcolor(text: str):
        red = randint(100, 255)
        green = randint(100, 255)
        blue = randint(100, 255)
        colored = fg(red, green, blue) + text + fg.rs

        return colored

    # Sending HTTP requests to make sure there is internet available.
    # The loop stops only when the response is '200'.
    @staticmethod
    def internet_connection():
        sites = ['twitter', 'google', 'duckduckgo']
        response = ''
        while response != '<Response [200]>':
            for site in sites:
                response = str(requests.get(f'https://{site}.com')).strip()
                if response == '<Response [200]>':
                    break
                print(response == '<Response [200]>')

    # Setting up the Twitter API.
    def __twitter_api(self):
        __consumer_key = 'CONSUMER_KEY'
        __consumer_secret = 'CONSUMER_SECRET'
        __access_token = 'ACCESS_TOKEN'
        __access_token_secret = 'ACCESS_TOKEN_SECRET'

        __auth = tweepy.OAuthHandler(__consumer_key, __consumer_secret)
        __auth.set_access_token(__access_token, __access_token_secret)
        __api = tweepy.API(__auth)

        return __api

    # Calculate how many days have passed and remained until the event in percentages.
    # Returns:
    #     1. A string with the data.
    #     2. The time remaining until the event, in percentages to use in the "graph" function.
    def percents(self):
        left = round((100 / self.__year_length) * self.__time_til_next_birthday.days)
        passed = 100 - left
        str_percent_left_passed = f'Left: {left}%\nPassed: {passed}%'

        return str_percent_left_passed, left

    # Returns a visual representation of the time remaining and the elapsed time.
    def graph(self):
        black_square = '■'
        white_square = '□'
        left_in_single_digit = round(self.percents()[1] / 10)
        passed_in_single_digit = 10 - left_in_single_digit
        graph = (white_square * passed_in_single_digit) + (black_square * left_in_single_digit)

        return graph

    # Checking using the data in the Json document whether and how many times the message was sent today
    #   in relation to the number of times defined as the maximum.
    # Creates a new data block in the Json document in case of a new user.
    # Returns true if it is okay to send and false if not.
    def __permission_to_send(self):
        permission_to_send = False
        with open('data.json', 'r', encoding='utf8') as file:
            json_file = json.load(file)

        if str(self.username).lower() in json_file:
            last_time = json_file[str(self.username).lower()]['last_time']
            times_today = json_file[str(self.username).lower()]['times_today']

            if last_time != datetime.today().strftime('%Y/%m/%d'):
                json_file[str(self.username).lower()]['last_time'] = datetime.today().strftime('%Y/%m/%d')
                json_file[str(self.username).lower()]['times_today'] = 0

            if int(times_today) < self.max_in_day:
                permission_to_send = True
            elif int(times_today) >= self.max_in_day:
                permission_to_send = False

        else:
            permission_to_send = True if self.max_in_day != 0 else False
            username = str(self.username).lower()
            next_birthday = str(self.next_birthday.strftime('%Y/%m/%d'))
            last_time = datetime.today().strftime('%Y/%m/%d')
            times_today = 0
            json_file[username] = {'next_birthday': next_birthday, 'last_time': last_time, 'times_today': times_today}

        with open('data.json', 'w', encoding='utf8') as file:
            json.dump(json_file, file, indent=4)

        return permission_to_send

    # Updates the data in the Json document after each send (date and number of times).
    def __update_permission_to_send(self):
        with open('data.json', 'r', encoding='utf8') as file:
            json_file = json.load(file)
            json_file[str(self.username).lower()]['last_time'] = str(datetime.today().strftime('%Y/%m/%d'))
            json_file[str(self.username).lower()]['times_today'] = json_file[str(self.username).lower()]['times_today'] + 1

        with open('data.json', 'w', encoding='utf8') as file:
            json.dump(json_file, file, indent=4)

    # Defines the message that will be sent.
    # The information becomes more detailed in the last month before the event.
    def message(self):
        if self.__time_til_next_birthday.days > 30:
            time_til_next_birthday = self.__time_til_next_birthday.days
            message = f'--- automatic message ---\n\nDays left \'til next birthday: {time_til_next_birthday}\n{self.percents()[0]}\n{self.graph()}\n\n'
        else:
            message = f'--- automatic message ---\n\nTime left \'til next birthday: {self.__time_til_next_birthday}\n{self.percents()[0]}\n{self.graph()}\n\n'

        return message

    # The countdown function.
    def count(self):
        api = self.__twitter_api()

        if self.username is None:
            print('\n>>> No username. printing only:')
            print(self.message()[27:])

        elif self.__permission_to_send() is True:
            self.internet_connection()
            user = api.get_user(screen_name=self.username)
            recipient_id = user.id_str

            try:
                direct_message = api.send_direct_message(recipient_id, self.message())
                print(f'>>> sent to {self.randcolor(self.username)}:', datetime.now())
                print(direct_message.message_create['message_data']['text'])
                self.__update_permission_to_send()

            except Exception:
                print(f'\n>>> There was an error while sending to {self.username}:/\n\n')
                print(self.message())

        elif self.__permission_to_send() is False:
            print(f'\n>>> Sent to {self.randcolor(self.username)}: {self.max_in_day}/{self.max_in_day} already today')