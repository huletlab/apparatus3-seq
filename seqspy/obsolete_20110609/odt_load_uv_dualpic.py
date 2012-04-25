""" Load ODT:  To test this sequence make sure the report file given by
	(L:/data/app3/comms/Savedir)report(L:/data/app3/comms/RunNumber).INI
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
import seq, wfm, gen, cnc, uvcooling, andor, basler
report=gen.getreport()

#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])
preexp   = float(report['BASLER']['preexp'])
postexp  = float(report['BASLER']['postexp'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

#Keep ODT on
ODT = gen.bstr('ODT',report)
if ODT == True:
    s.digichg('odtttl',1)
s.wait(20.0)

#LOAD ODT
s, duration = uvcooling.run(s,'ANDOR')

#RELEASE
s=gen.releaseMOT(s)
s.wait(tof)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
kinetics = gen.bstr('Kinetics',report)
print 'kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms)
    s.wait(-SERIESDT)
    s,BASLERDT = basler.Basler_AndorKineticSeries4(s,preexp,postexp,exp,light,noatoms)
    s.wait(SERIESDT-BASLERDT)
else:
    s,SERIESDT = andor.FKSeries4(s,stepsize,exp,light,noatoms)
    s.wait(-SERIESDT)
    s,BASLERDT = basler.Basler_FKSeries2(s,preexp,postexp,exp,light,noatoms)
    s.wait(SERIESDT-BASLERDT)

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')