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
import seq, wfm, gen, cnc, andor
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
s, duration=cnc.run(s,'ANDOR')

#RELEASE
s=gen.releaseMOT(s)

#UV LIGHT SHIFT PARAMETERS
intrapdt = float(report['UVLIGHTSHIFT']['intrapdt'])
pulse = float(report['UVLIGHTSHIFT']['pulse'])
postdt = float(report['UVLIGHTSHIFT']['postdt'])

s.wait(intrapdt)
s.digichg('uvaom1',1)
s.wait(pulse)
s.digichg('uvaom1',0)
s.wait(postdt) 


#OPEN SHUTTERS
s=andor.OpenShuttersFluor(s)

light='motswitch'
    
#PICTURE OF ATOMS
s,dt=andor.AndorPictureWithClear(s,stepsize,exp,light,1)

#CHECK THAT BACKGROUND PICTURE IS NOT TAKEN TOO FAST
if noatoms < dt:
    print "Error:  need to wait longer between shots, clear trigger of NoAtoms will overlap with\
    \n end of accumulation trigger of Atoms"
    exit(1)    

#SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
s.wait(noatoms)
s.digichg('odtttl',0)
s.wait(noatoms)
s.digichg('odtttl',1)
s.wait(noatoms)
    
#PICTURE OF BACKGROUND
s,dt=andor.AndorPictureWithClear(s,stepsize,exp,light,1)

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')


