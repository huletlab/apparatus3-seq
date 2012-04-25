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
import seq, wfm, gen, cnc, basler, zsload 

report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
texp     = float(report['ZSLOAD']['texp'])
uvpow    = float(report['ZSLOAD']['uvpow'])

probe = 'motswitch'

#SEQUENCE
s=seq.sequence(stepsize)
s.digichg('motswitch',1)
s.digichg('motshutter',0)
s.digichg('field',1)
s.digichg('zsshutter',0)
s.digichg('beamflag',1)
if uvpow == 0:
    s.digichg('uvaom1',0)
else:
    s.digichg('uvaom1',1)

s.wait(1.0)

s, duration = zsload.run(s)


###Number calibration won't be ok because i'm not switching the lasers to imaging values

#Take fluorescence in situ of the MOT 
s=basler.BaslerInSitu(s,texp)

s.wait(10.0)
s=gen.shutdown(s)
s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
        
print time.time()-t0," seconds"
