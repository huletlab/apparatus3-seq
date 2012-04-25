"""Basler Fluoresence: To test this custom sequence make sure the report file given by
	(L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI
     exists otherwise this code won't compile. 
     """

__author__ = "Pedro M Duarte"
__version__ = "$Revision: 0.5 $"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, uvcooling, basler
report=gen.getreport()


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
s, duration = uvcooling.run(s,'BASLER')

#Go back and turn on the probe beam to do photoionization measurement
probepulse =float(report['UV']['uvhold'])-5
shutter = 5
s.wait(-probepulse -shutter)
s.digichg('prshutter',0)
s.wait(shutter)
s.digichg('probe',1)
s.wait(probepulse)
s.digichg('probe',0)


#Take fluorescence imaging shot with the MOT beams. 
#LET MOT EXPAND
s.digichg('field',0)
s.digichg('motswitch',0) 
s.wait(tof)
#PICTURE OF ATOMS
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)
#PICTURE OF BACKGROUND
s.wait(noatoms)
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)

s.wait(2.0)
s=gen.shutdown(s)
s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
        
print time.time()-t0," seconds"
