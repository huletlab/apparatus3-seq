import os
import seqconf
import datetime
import shutil
import sys
import diff


now = datetime.datetime.now()

folder = '%d_%.2d_%.2d_%.2d_%.2d' % (now.year,now.month,now.day,now.hour,now.minute)

datapath = os.path.join(os.path.abspath(os.path.dirname(__file__)) , 'data', folder)
if not os.path.isdir(datapath):
   os.makedirs(datapath)
   
print "Saving benchmark to %s", datapath

folders = os.listdir( os.path.join(os.getcwd() , 'data') ) # acquire folders before benchmark 


try:
  base_seqspy = seqconf.base_seqspypath()
  seqlist = os.listdir( base_seqspy )
except:
  base_seqspy = seqconf.base_seqspypath().replace('L:','/lab')
  seqlist = os.listdir( base_seqspy )



dir_temp = dir()

for i, file  in enumerate(seqlist):
    
    if file.endswith('.py'):
        
        fpath = base_seqspy + '/' + file
        print '\nBenchmarking %s' % fpath
        print os.path.join( base_seqspy, file)

        try:        
            execfile( fpath )
            try: 
                shutil.copyfile(seqconf.seqtxtout(), datapath+'/'+file.split('.')[0]+'.txt')
            except:
                shutil.copyfile(seqconf.seqtxtout().replace('L:','/lab'), datapath+'/'+file.split('.')[0]+'.txt')
        except:
            print "!!File %s did NOT compile!!" % fpath
       
        # Clean up the scope 
        for n in dir():
            
            if (not (n in dir_temp)) & ( n[0] != '_') & (n != 'dir_temp'): 
                
                delattr(sys.modules[__name__], n) 
                
shutil.copyfile(seqconf.savedir()+'report'+seqconf.runnumber()+'.INI', datapath+'/report'+seqconf.runnumber()+'.INI')


#find latest folder and diff 

times = [os.path.getmtime(os.path.abspath(os.path.dirname(__file__))+ '/data/'+i)for i in os.listdir(os.path.abspath(os.path.dirname(__file__) )+ '/data/')]

times_and_folder = zip ( times, folders)

times_and_folder.sort()

sorttime , sortfolder = zip(*times_and_folder)

print datapath

diff.diff( datapath + '/' , os.path.abspath(os.path.dirname(__file__))+ '/data/' + sortfolder[-2]+ '/')
