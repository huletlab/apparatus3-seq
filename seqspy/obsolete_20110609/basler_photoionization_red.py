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
import seq, wfm, gen, basler, photoion

report=gen.getreport()


#PARAMETERS
stepsize    =float(report['SEQ']['stepsize'])
tof         =float(report['BASLER']['tof'])
preexp      =float(report['BASLER']['preexp'])
texp        =float(report['BASLER']['exp'])
postexp     =float(report['BASLER']['postexp'])
backdt      =float(report['BASLER']['backdt'])


#Use MOT beams for fluorescence imaging
probe = 'motswitch'

#SEQUENCE

s=seq.sequence(stepsize)
s=gen.initial(s)

uvmotdt = float(report['UV']['uvmotdt'])

s.wait(20.0)
ionize = gen.bstr('ionize',report)

s.digichg('uvaom1',1 if ionize == True else 0)
s.wait(-1.0)
s.wait(uvmotdt)

s, duration = photoion.run(s,'BASLER')
print "Duration = " + str(duration)
s.digichg('uvaom1',0)

#Take fluorescence imaging shot with the MOT beams. 
#LET MOT EXPAND
s.digichg('field',0)
s.digichg('motswitch',0) 
s.wait(tof)
#PICTURE OF ATOMS
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)
#PICTURE OF BACKGROUND
s.wait(backdt)
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)

s.wait(2.0)
s=gen.shutdown(s)
s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
        
print time.time()-t0," seconds"
