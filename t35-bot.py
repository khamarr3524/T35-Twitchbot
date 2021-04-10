#!/usr/bin/env python3

"""
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
"""


import threading
import sys
from twitchbot import TwitchBot
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel

tbThread = 0


def btn_test():
    print("Test")


def btn_exit():
    tbThread.stop_task()
    print("Exiting bot thread...")
    print("Exiting...")
    sys.exit()


class BotThread(threading.Thread):
    def __init__(self, target):
        threading.Thread.__init__(self)
        self.target = target

    def run(self):
        # noinspection PyUnresolvedReferences
        self.target.start()

    def stop_task(self):
        # noinspection PyUnresolvedReferences
        self.target.die()


class T35GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Twitch Bot - T35')
        self.setFixedSize(250, 250)
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._create_labels()
        self._create_buttons()

    def _create_labels(self):
        self.labels = {
            "viewers": QLabel()
        }

    def _create_buttons(self):
        self.buttons = {
            "exit": QPushButton("Exit")
        }
        self.buttons["exit"].setFixedSize(100, 40)
        self.buttons["exit"].move(0, 105)
        self.buttons["exit"].setParent(self)
        self.buttons["exit"].clicked.connect(btn_exit)


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
    view = T35GUI()
    view.show()
    sys.exit(tbgui.exec_())


if __name__ == "__main__":
    main()
