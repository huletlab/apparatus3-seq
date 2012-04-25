"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, uvcooling_repump, basler
report=gen.getreport()

print "\n----- basler_probe_repump.py -----"

#PARAMETERS
stepsize    =float(report['SEQ']['stepsize'])
tof         =float(report['BASLER']['tof'])
preexp      =float(report['BASLER']['preexp'])
texp        =float(report['BASLER']['exp'])
postexp     =float(report['BASLER']['postexp'])
noatoms     = 200.0


#Use MOT beams for fluorescence imaging
probe = 'motswitch'

#SEQUENCE

s=seq.sequence(stepsize)
s=gen.initial(s)

s.wait(20.0)


#LoadRamps refers to everything done up to loading the optical trap
#Edit loadtrap.py to change any of this
s, duration = uvcooling_repump.run_proberepump(s,'BASLER')


#RELEASE FROM MOT
s.digichg('motswitch',0) 
s.digichg('motshutter',1)
s.digichg('field',0)

s.wait(tof)

#Take fluorescence imaging shot with the MOT beams. 
#PICTURE OF ATOMS
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)
#PICTURE OF BACKGROUND
s.wait(noatoms)
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)

s.wait(2.0)
s=gen.shutdown(s)
s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)
