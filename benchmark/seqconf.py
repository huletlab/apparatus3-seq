#The functions here are used to return settings whenever needed
from configobj import ConfigObj
import os 

labfolder = '/lab/' if os.name == 'posix' else 'L:/'

def ramps_dir():
	return labfolder +"software/apparatus3/ramps/"

def settings_INI_file():
	return ConfigObj(labfolder +"software/apparatus3/main/settings.INI")

def clockrate():
    return float(settings_INI_file()["SEQUENCE"]["clockrate"])

def base_txtpath():
    return labfolder +'software/apparatus3/seq/seqstxt'
    
    
def base_seqspypath():
    return labfolder +'software/apparatus3/seq/seqspy'

def savedir():
    return labfolder +'software/apparatus3/seq/benchmark/'

def runnumber():
    return '_benchmark'
   
def systemtxt():
    return labfolder +'software/apparatus3/conf/system.txt'

def import_paths():
    paths=[]
    paths.append(labfolder +'software/apparatus3/convert')
    paths.append(labfolder +'software/apparatus3/seq/utilspy')
    return paths

def seqtxtout():
        return labfolder +'/software/apparatus3/seq/benchmark/expseq.txt'
