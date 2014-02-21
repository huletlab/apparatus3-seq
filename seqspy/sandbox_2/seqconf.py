#The functions here are used to return settings whenever needed
from configobj import ConfigObj
import os

if os.name == 'posix':
    lab = '/lab/'
else:
    lab = 'L:/'
    
def ramps_dir():
	return lab+"software/apparatus3/seq/seqspy/sandbox_2/ramps/"

def settings_INI_file():
	return ConfigObj(lab+"software/apparatus3/settings.INI")

def clockrate():
    return float(settings_INI_file()["SEQUENCE"]["clockrate"])

def base_txtpath():
    return lab+'software/apparatus3/seq/seqstxt'

def base_seqspypath():
    return lab+'software/apparatus3/seq/seqspy'

def savedir():
    return lab+'software/apparatus3/seq/seqspy/sandbox_2/'

def runnumber():
    return '_sandbox_2'
   
def systemtxt():
    return lab+'software/apparatus3/seq/system.txt'

def import_paths():
	paths=[]
	if os.name == 'posix':
	    #paths.append(lab+'software/apparatus3/convert')
	    paths.append(lab+'software/apparatus3/seq/utilspy')
	    paths.append(lab+'software/apparatus3/seq')
	else:
	    #paths.append('L:\\software\\apparatus3\\convert')
	    paths.append('L:\\software\\apparatus3\\seq\\utilspy')
	    paths.append('L:\\software\\apparatus3\\seq')
	return paths


def seqtxtout():
        return lab+'software/apparatus3/seq/seqspy/sandbox_2/expseq.txt'
