#The functions here are used to return settings whenever needed
from configobj import ConfigObj

def ramps_dir():
	return "L:/software/apparatus3/ramps/"

def settings_INI_file():
	return ConfigObj("L:/software/apparatus3/main/settings.INI")

def clockrate():
    return float(settings_INI_file()["SEQUENCE"]["clockrate"])