import constants
import time
import irc.bot
import requests
import json
from os import path

validCommands = [
    "game",
    "title",
    "poke",
    "points"
]


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel
        self.viewers = []
        # self.isFollowing = {} for later
        self.points = self.load_points()
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

    @staticmethod
    def save_points(points):
        f = open('points.json', 'w')
        json.dump(points, f)
        f.close()

    @staticmethod
    def load_points() -> dict:
        points = {}
        # Load points if they exist, otherwise return empty set
        if path.exists('points.json'):
            with open('points.json') as f:
                points = json.load(f)
        return points

    def start(self):
        self._connect()
        while self._active:
            self.reactor.process_once(timeout=0.2)
            cTime = time.time()
            if cTime > self.points_time:
                self.add_points()
                self.points_time = cTime + constants.POINTS_TIME_INCREMENT
                self.save_points(self.points)

    def add_points(self):
        print("Adding points!")
        for viewer in self.viewers:
            self.points[viewer] += constants.POINTS_TIME_REWARD

    def die(self, msg="Goodbye."):
        self.connection.disconnect(msg)
        self.save_points(self.points)
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

    def on_join(self, c, e):
        # Load user points from file and store it in the points dictionary
        nickname = _parse_nickname_from_twitch_user_id(e.source)
        self.viewers.append(nickname)
        print(f'Added {nickname} to viewers.')
        if nickname not in self.points.keys():
            self.points[nickname] = 0
            print(f'{nickname} not found in points. Added to points with 0.')
            self.save_points(self.points)

    def on_part(self, c, e):
        # Save user points to points.csv and remove from points dictionary
        nickname = _parse_nickname_from_twitch_user_id(e.source)
        self.viewers.remove(nickname)
        print(f'Removed {nickname} from viewers.')

    def cmd_game(self, c, e, url, headers):
        # Poll the API to get current game.
        r = requests.get(url, headers=headers).json()
        c.privmsg(self.channel, f"@{r['display_name']} is currently playing {r['game']}")

    def cmd_title(self, c, e, url, headers):
        # Poll the API the get the current status of the stream
        r = requests.get(url, headers=headers).json()
        c.privmsg(self.channel, f"@{r['display_name']} channel title is currently {r['status']}")

    def cmd_poke(self, c, e, url, headers):
        # Poke the streamer
        r = requests.get(url, headers=headers).json()
        c.privmsg(self.channel, f"@{r['display_name']} *poke*")

    def cmd_points(self, c, e, url, headers):
        #Get user points
        nickname = _parse_nickname_from_twitch_user_id(e.source)
        c.privmsg(self.channel, f"@{nickname} has {self.points[nickname]} points!")

    def do_command(self, e, cmd):
        c = self.connection
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        headers = {'Client-ID': self.client_id, 'Accept': 'application.vbd.twitchtv.v5+json'}
        if cmd in validCommands:
            # This may need to be changed, c might not get evaluated by eval
            eval("self.cmd_" + cmd + "(c, e, url, headers)")
            return
        # The command was not recognized
        c.privmsg(self.channel, f"Did not understand command: {cmd}")


def _parse_nickname_from_twitch_user_id(user_id):
    # nickname!username@nickname.tmi.twitch.tv
    return user_id.split('!', 1)[0]