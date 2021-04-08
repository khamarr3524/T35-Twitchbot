#!/usr/bin/env python3

'''
Twitch Bot - Features to be Added
    -Points System
        Viewers accumulate points to be redeemed by the bot by:
            - Being in Chat
                How to check for users in chat? How often to check?
                How many points/min? Do followers get a bonus? Subs (eventually? :])
                    -Not following: 50 points / 6 minutes => 500 points / hour
                    -Following: 150 points / 6 minutes => 1500 points / hour
            - Following the Channel
                One time Payout - Retroactive listing.
                    If you're already following, but didn't get points, we need to track that.
                    How?
                        Does follow -> unfollow -> (Wait) -> follow count again??

            - Mini-games

'''
import constants
import time
import irc.bot
import requests
import threading
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget

tbThread = 0
validCommands = [
    "game",
    "title",
    "poke"
]


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel
        self.viewers = []
        self.points = {}
        self.points_time = int(time.time()) + constants.POINTS_TIME_INCREMENT
        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/kraken/users?login=' + channel
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print(f"Connecting to {server} on port {port}...")
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, token)], username, username)
        self._active = True

    def start(self):
        self._connect()
        while self._active:
            self.reactor.process_once(timeout=0.2)
            cTime = time.time()
            if cTime > self.points_time:
                self.add_points()
                self.points_time = cTime + constants.POINTS_TIME_INCREMENT

    def add_points(self):
        # Iterate self.viewers and add points.
        pass

    def die(self, msg="Goodbye."):
        self.connection.disconnect(msg)
        self._active = False

    def on_welcome(self, c, e):
        print(f'Joining {self.channel}')
        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        # c.privmsg(self.channel, "Hello ^.^")

    def on_pubmsg(self, c, e):
        # If a chat message starts with an exclamation point, try to run it as a command
        if e.arguments[0][:1] == '!':
            cmd = e.arguments[0].split(' ')[0][1:]
            print(f"Received command: {cmd}")
            self.do_command(e, cmd)
        return

    def on_join(self, c, e):
        # Load user points from file and store it in the points dictionary
        nickname = _parse_nickname_from_twitch_user_id(e.source)
        self.viewers.append(nickname)

    def on_part(self, c, e):
        # Save user points to points.csv and remove from points dictionary
        nickname = _parse_nickname_from_twitch_user_id(e.source)
        self.viewers.remove(nickname)

    def cmd_game(self, c):
        # Poll the API to get current game.
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        c.privmsg(self.channel, f"@{r['display_name']} is currently playing {r['game']}")

    def cmd_title(self, c):
        # Poll the API the get the current status of the stream
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        c.privmsg(self.channel, f"@{r['display_name']} channel title is currently {r['status']}")

    def cmd_poke(self, c):
        # Poke the streamer
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        headers = {'Client-ID': self.client_id, 'Accept': 'application.vbd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        c.privmsg(self.channel, f"@{r['display_name']} *poke*")

    def do_command(self, e, cmd):
        c = self.connection
        if cmd in validCommands:
            # This may need to be changed, c might not get evaluated by eval
            eval("self.cmd_" + cmd + "(c)")
        else:
            # The command was not recognized
            c.privmsg(self.channel, f"Did not understand command: {cmd}")


def _parse_nickname_from_twitch_user_id(user_id):
    # nickname!username@nickname.tmi.twitch.tv
    return user_id.split('!', 1)[0]


def cmd_test():
    print("Test")


def cmd_exit():
    print("Attempting to exit bot thread.")
    tbThread.stop_task()
    print("Bot thread exited.")


class BotThread(threading.Thread):
    def __init__(self, target):
        threading.Thread.__init__(self)
        self.target = target

    def run(self):
        # noinspection PyUnresolvedReferences
        self.target.start()
        print("Exiting BotThread...")

    def stop_task(self):
        # noinspection PyUnresolvedReferences
        self.target.die()


def _exit_click():
    tbThread.stop_task()
    sys.exit()


class TwitchBotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Twitch Bot - T35')
        self.setFixedSize(250, 250)
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._create_buttons()

    def _create_buttons(self):
        self.buttons = {
            "exit": QPushButton("Exit")
        }
        self.buttons["exit"].setFixedSize(100, 40)
        self.buttons["exit"].move(75, 105)
        self.buttons["exit"].setParent(self)
        self.buttons["exit"].clicked.connect(_exit_click)


# noinspection PyTypeChecker
def main():
    args = []
    f = open('args.txt', 'r')
    for line in f:
        args.append(line.rstrip())
    global tbThread
    tb = TwitchBot(args[0], args[1], args[2], args[3])
    tbThread = BotThread(tb)
    tbThread.start()

    tbgui = QApplication([])
    view = TwitchBotGUI()
    view.show()
    sys.exit(tbgui.exec_())


if __name__ == "__main__":
    main()
