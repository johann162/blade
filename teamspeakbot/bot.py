# -*- coding: iso-8859-1 -*-
# teamspeakbot
from datetime import datetime
import time
import argparse
import threading
import telepot
from telepot.loop import MessageLoop
from data import *
from tsclient import *


class Bot(object):

    # init
    def __init__(self, data):

        # set debugmode
        # self.debug = sys.argv[0] == "-debug" or sys.argv[0] == "-d"
        # print self.debug, sys.argv[1]
        self.debug = True

        # parser = argparse.ArgumentParser(description='Process some integers.')
        # parser.add_argument("-foo", ..., required=True)
        # parser.parse_args()

        self.data = data

        ######################
        ### Ts Chat Format ###
        ######################
        self.userFormat = "[b]"
        self.chatFormat = "[/b][color=grey]"

        # start bot with bot_token
        try:
            self.bot = telepot.Bot(self.data.getToken())
        except Exception as e:
            print e
            print "failed to init Bot"
            print "start with --clean"

        print self.data.getToken()

        MessageLoop(self.bot, self.handle).run_as_thread()
        self.keepAlive()

        self.initTeamspeak(self.data.getChatId())

        print 'I am listening ...'

    # Telegram bot loop
    def handle(self, msg):

        # get chat id
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']

        # checks for textmessage
        if 'text' in msg:

            command = msg['text'].split('@')[0]
            full_command = msg['text'].split(' ')

            # debug output
            if self.debug: print msg
            print 'Got command: %s' % command

            if self.groupId == "0":
                self.initTeamspeak(chat_id)

            # do nothing for now
            elif chat_id != self.groupId:
                print "do nothing for now"

            # quitting teamspeak
            elif command == '/quit':
                self.teamspeak.tsQuit()

            # joining teamspeak
            elif command == '/join':
                self.teamspeak.tsStart()

            elif self.teamspeak.getTsRunning():

                # writes command for current channelclients
                if command == '/status':
                    self.teamspeak.sendStatus()

                # unlisten from teamspeakchat
                elif command == '/stfu':
                    self.teamspeak.setListen(False)
                    self.writeTelegram('stopped listening to TS3 Chat')

                # listen to teamspeakchat
                elif command == '/listen':
                    self.teamspeak.setListen(True)
                    self.writeTelegram("started listening to TS3 Chat")

                # set username for current id
                elif command.split(" ")[0] == '/setusername':
                    self.setUsername(user_id, full_command)

                # set usercolor for current id
                elif command.split(" ")[0] == '/setusercolor':
                    self.setUsercolor(user_id, full_command, msg)

                # builds textmessages and writes it into teamspeakchat
                else:
                    self.teamspeak.writeTeamspeak(
                        self.userFormat
                        + self.getUsernameWithColor(msg)
                        + ': '
                        + self.chatFormat
                        + msg['text']
                    )

#           else:
#               writeTelegram('bot is not in Teamspeak')

    def initTeamspeak(self, chatId):
        if not(chatId == "0"):
            self.teamspeak = Tsclient(
                 self.bot, chatId, self.data.getAuth())
        self.groupId = chatId
        self.data.setChatId(chatId)


    # write message into Telegram chat
    def writeTelegram(self, string):
        self.bot.sendMessage(self.groupId, string)

    # thread for keeping the connection
    def __keepAliveThread(self):
        while True:
            self.bot.getMe()
            x = datetime.today()
            print x
            if not(self.groupId == "0"):
                self.teamspeak.autoQuit()
            time.sleep(60)

    # builds a Thread for keeping the connection alive
    def keepAlive(self):
        t = threading.Thread(target=self.__keepAliveThread)
        t.daemon = True
        t.start()

    # gets username from msg
    def getUsername(self, msg):
        # if known then colorize it and make default name
        if 'id' in msg['from'] and self.data.isUser(msg['from']['id']):
            return self.data.getUsername(msg['from']['id'])
        elif 'username' in msg['from']:
            return msg['from']['username']
        elif 'first_name' in msg['from']:
            return msg['from']['first_name']
        return "no username found"

    def setUsername(self, user_id, command):
        if command.__len__() == 2:
            self.data.setUsername(user_id, command[1])
            self.writeTelegram("username set")
        else:
            self.writeTelegram(
                "only use following syntax: /setusername USERNAME")

    def setUsercolor(self, user_id, command, msg):
        if command.__len__() == 2:
            if self.data.setUsercolor(user_id, command[
                              1], self.getUsername(msg)):
                self.writeTelegram("usercolor set ")
        else:
            self.writeTelegram(
                "only use following syntax: /setusercolor ffffff")

    # gets username from msg with color
    def getUsernameWithColor(self, msg):
        # if known then colorize it and make default name
        if 'id' in msg['from'] and self.data.isUser(msg['from']['id']):
            return self.data.getUsercolor(msg['from']['id']) + self.getUsername(msg)
        return self.getUsername(msg)