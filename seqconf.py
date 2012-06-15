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
    f=open('L:/data/app3/comms/SaveDir')
    savedir=f.readline()
    f.close()
    return savedir

def runnumber():
    f=open('L:/data/app3/comms/RunNumber')
    shotnum=f.readline()
    f.close()
    return shotnum
   
def systemtxt():
    return 'L:/software/apparatus3/conf/system.txt'

def import_paths():
    paths=[]
    paths.append('L:\\software\\apparatus3\\convert')
    paths.append('L:\\software\\apparatus3\\seq\\utilspy')
    return paths


def seqtxtout():
        return 'L:/software/apparatus3/seq/seqstxt/expseq.txt'
