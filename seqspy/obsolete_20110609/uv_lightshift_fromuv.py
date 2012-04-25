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
import seq, wfm, gen, cnc, uvcooling, odt, andor
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

#Keep ODT on
ODT = gen.bstr('ODT',report)
if ODT == True:
    s.digichg('odtttl',1)
s.wait(20.0)

#LOAD ODT
s, ENDUVMOT = uvcooling.run(s,'ANDOR')

#Insert ODT overlap with UVMOT
overlapdt = float(report['ODT']['overlapdt'])
s.wait(-overlapdt)
s.digichg('odtttl',1)
s.wait(overlapdt)

#Leave UVMOT on for state transfer
fstatedt  = float(report['ODT']['fstatedt'])
s.wait(fstatedt)
s.digichg('uvaom1',0)
s.wait(-fstatedt) 

#RELEASE FROM MOT
s.digichg('motswitch',0) 
s.digichg('motshutter',1)
s.digichg('field',0)

intrapdt  = float(report['UVLIGHTSHIFT']['intrapdt'])
pulse  = float(report['UVLIGHTSHIFT']['pulse'])
postdt  = float(report['UVLIGHTSHIFT']['postdt'])
s.wait(intrapdt)
s, ENDANALOG2 = uvcooling.lightshift_ramp(s)
s.wait(ENDANALOG2)
print "time before light shift pulse = " + str(intrapdt+ENDANALOG2)
s.digichg('uvaom1',1)
s.wait(pulse)
s.digichg('uvaom1',0)
s.wait(postdt) 

s.wait(tof)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
kinetics = gen.bstr('Kinetics',report)
print 'kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms)

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')