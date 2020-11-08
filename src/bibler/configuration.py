
import configparser

config = configparser.ConfigParser()
config.read("bibler.ini")
default_conf = config["DEFAULT"]
