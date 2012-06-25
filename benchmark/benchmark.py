import os
import seqconf
import datetime
import shutil
import sys
import diff

now = datetime.datetime.now()

folder = '%d_%.2d_%.2d_%.2d_%.2d' % (now.year,now.month,now.day,now.hour,now.minute)

datapath = os.getcwd() + '\\data\\' + folder

folders = os.listdir(os.getcwd() + '\\data\\') # acquire folders before benchmark 

if not os.path.isdir(datapath):
    
   os.makedirs(datapath)
   
seqlist =  os.listdir(seqconf.base_seqspypath())

dir_temp = dir()

for i, file  in enumerate(seqlist):
    
    if file.endswith('.py'):
        
        print 'Benchmarking %s' % file
        
        try:        
            
            execfile(seqconf.base_seqspypath()+'/'+file)
            
        except:
        
            print "File not be able to compile" 
        
        shutil.copyfile(seqconf.seqtxtout(), datapath+'/'+file.split('.')[0]+'.txt')
        
        for n in dir():
            
            if (not (n in dir_temp)) & ( n[0] != '_') & (n != 'dir_temp'): 
                
                delattr(sys.modules[__name__], n) 
                
shutil.copyfile(seqconf.savedir()+'report'+seqconf.runnumber()+'.INI', datapath+'/report'+seqconf.runnumber()+'.INI')


#find latest folder and diff 

times = [os.path.getmtime(os.getcwd() + '\\data\\'+i) for i in os.listdir(os.getcwd() + '\\data\\')]

times_and_folder = zip ( times, folders)

times_and_folder.sort()

sorttime , sortfolder = zip(*times_and_folder)

print datapath

diff.diff( datapath + '\\' , os.getcwd() + '\\data\\' + sortfolder[-1]+ '\\')