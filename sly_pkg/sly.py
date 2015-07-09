import vk_api
import os
import json
import cli_player

config_file = os.path.join(os.getcwd(), 'config.json')


class User:
    password = ''
    username = ''
    app_id = '4988819'

    def __init__(self, password='', username=''):
        self.password = password
        self.username = username

    @classmethod
    def fromJson(cls, json_file_name):

        with open(json_file_name) as data_file:
            data = json.load(data_file)

        print(data)
        return cls(data['password'], data['username'])

    def Login(self):
        vk = vk_api.VkApi(self.username, self.password)

        # vkapi.get_access_token()
        vk.authorization()
        tools = vk_api.VkTools(vk)
        owner_id = vk.settings['access_token']['user_id']
        audio = tools.get_all('audio.get', 100, {'owner_id': owner_id})
        print('Audio count:', audio['count'])
        # for song in audio['items']:
        # print(song['title'])
        song_list = [song['url'] for song in audio['items']]
        print(song_list)
        cli_player.play_range(audio['items'])


def main():
    print("Welcome to player.")
    if os.path.exists(config_file):
        # Разбор файла
        user = User.fromJson(config_file)
        user.Login()

    else:
        print("Введите логин и пароль")
        # Ввод логина и пароля с клавы и предложение запомнить
        pass


if __name__ == '__main__':
    main()
