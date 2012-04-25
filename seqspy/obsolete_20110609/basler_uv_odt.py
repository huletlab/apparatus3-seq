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
import seq, wfm, gen, cnc, uvcooling, odt, basler, andor
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['BASLER']['tof'])
preexp   = float(report['BASLER']['preexp'])
texp     = float(report['BASLER']['exp'])
postexp  = float(report['BASLER']['postexp'])
noatoms  = float(report['BASLER']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

#Keep ODT on
ODT = gen.bstr('ODT',report)
if ODT == True:
    s.digichg('odtttl',1)
s.wait(20.0)

#LOAD ODT
s, ENDUVMOT = uvcooling.run(s,'BASLER')
s.digichg('uvaom1',1)

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

s.wait(tof)

#TAKE PICTURES
#probe = 'motswitch'
probe = 'probe'
#OPEN SHUTTERS
if probe == 'probe':
    s=andor.OpenShuttersProbe(s)
elif light == 'motswitch':
    s=andor.OpenShuttersFluor(s)

#PICTURE OF ATOMS
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)
#SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
s.wait(noatoms)
s.digichg('odtttl',0)
s.wait(noatoms)
s.digichg('odtttl',0)
s.wait(noatoms)
#PICTURE OF BACKGROUND
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
        
print time.time()-t0," seconds"
