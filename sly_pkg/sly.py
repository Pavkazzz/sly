#!/usr/bin/python
# -*- coding: utf-8 -*-

import vk_api
import os
import json
from . import cli_player
from os.path import expanduser

sly_conf = os.path.join(expanduser("~"), '.sly')
config_file = os.path.join(sly_conf, 'config.json')
print(config_file)


class User:
    password = ''
    username = ''
    app_id = '4988819'

    def __init__(self, password='', username=''):
        self.password = password
        self.username = username

    @classmethod
    def fromJson(cls, json_file_name):

        try:
            with open(json_file_name) as data_file:
                data = json.load(data_file)
        except ValueError as e:
            print('Некоректный конфиг, {}'.format(e))

        print(data)
        return cls(data['password'], data['username'])

    def Login(self):

        self.vk = vk_api.VkApi(self.username, self.password)
        self.vk.authorization()

    def PlayMyPlaylist(self):
        tools = vk_api.VkTools(self.vk)
        owner_id = self.vk.settings['access_token']['user_id']
        audio = tools.get_all('audio.get', 100, {'owner_id': owner_id})
        print('Audio count:', audio['count'])
        # for song in audio['items']:
        # print(song['title'])
        song_list = [song['url'] for song in audio['items']]
        print(song_list)
        cli_player.play_range(audio['items'])


def main():
    print("Welcome to player.")
    print("config_file: {}".format(config_file))
    if os.path.exists(config_file):
        # Разбор файла
        user = User.fromJson(config_file)

    else:
        print("Введите e-mail и пароль")
        config = {}
        config['username'] = input("e-mail: ")
        config['password'] = input("Пароль: ")

        if not os.path.exists(sly_conf):
            os.makedirs(sly_conf)

        with open(config_file, 'w') as confp:
            json.dump(config, confp)

        user = User(config['username'], config['password'])

    user.Login()
    user.PlayMyPlaylist()

if __name__ == '__main__':
    main()
