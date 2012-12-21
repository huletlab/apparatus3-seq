#The functions here are used to return settings whenever needed
from configobj import ConfigObj

def ramps_dir():
	return "L:/software/apparatus3/ramps/"

def settings_INI_file():
	return ConfigObj("L:/software/apparatus3/main/settings.INI")

def clockrate():
    return float(settings_INI_file()["SEQUENCE"]["clockrate"])

def base_txtpath():
    return 'L:/software/apparatus3/seq/seqstxt'

def savedir():
    return ''

def runnumber():
    return '_ODT_from_UVRED'
   
def systemtxt():
    return 'L:/software/apparatus3/conf/system.txt'

def import_paths():
    paths=[]
    paths.append('L:\\software\\apparatus3\\convert')
    paths.append('L:\\software\\apparatus3\\seq\\utilspy')
    paths.append('L:\\software\\apparatus3\\seq')
    return paths


def seqtxtout():
        return 'expseq.txt'
