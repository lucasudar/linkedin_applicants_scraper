from jproperties import Properties

configs = Properties()
with open('../config/app-config.properties', 'rb') as config_file:
    configs.load(config_file)

username = configs.get('username').data
password = configs.get('password').data
url = configs.get('url').data
