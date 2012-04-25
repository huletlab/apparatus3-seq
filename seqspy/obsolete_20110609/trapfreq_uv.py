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
import seq, wfm, gen, cnc, uvcooling, andor, odt
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

ss = float(report['CNC']['cncstepsize'])
camera = 'ANDOR'


# Cool and Compress MOT
# ENDCNC is defined as the time up to release from the MOT
motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()

# Load UVMOT from CNCMOT
uvfppiezo, uvpow, motpow, repdet, trapdet, reppow, trappow, bfield, ENDUVMOT = uvcooling.uvcoolRamps(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC)

# Set imaging values
motpow, repdet, trapdet, reppow, trappow, bfield, maxDT = cnc.imagingRamps(motpow, repdet, trapdet, reppow, trappow, bfield,camera)

uvfppiezo.extend(maxDT)
uvpow.extend(maxDT)
	
# Add modulation to odt
odtpow = odt.odt_modulationRamps(ss,ENDUVMOT)
	
#Add waveforms to sequence
s.analogwfm_add(ss,[motpow,repdet,trapdet,reppow,trappow,bfield,odtpow])

	
#wait normally rounds down using floor, here the duration is changed before so that
#the wait is rounded up
ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
#insert QUICK pulse  for fast ramping of the field gradient
s.wait(-10.0)
quickval = 1 if gen.bstr('CNC',report) == True else 0
s.digichg('quick',quickval)	
s.wait(10.0)

#insert UV pulse
s.wait(ENDCNC)
s.wait(f('UV','uvtime'))
s.digichg('uvaom1',1)
s.wait(-f('UV','uvtime') - ENDCNC)
	
#Go to MOT release time, turn off UV and set QUICK back to low
s.wait(ENDUVMOT)
s.digichg('uvaom1',0)
s.digichg('quick',0)

#RELEASE and go to the end of trap modulation
s=gen.releaseMOT(s)
s.wait( odtpow.dt() - ENDUVMOT )

s.wait(tof)

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