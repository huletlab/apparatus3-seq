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
from convert import cnv
report=gen.getreport()


#PARAMETERS
stepsize = float(report['CNC']['cncstepsize'])
ss       = float(report['SEQ']['analogstepsize'])
intrap   = float(report['ODT']['intrap'])
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

# Cool and Compress MOT
# ENDCNC is defined as the time up to release from the MOT
motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()

trappow, reppow, bfield, ENDCNC = cnc.state_transfer(trappow, reppow, bfield)


# Set imaging values
camera = 'ANDOR'
motpow, repdet, trapdet, reppow, trappow, maxDT = cnc.imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow, camera)

#Switch bfield to FESHBACH
switchdt  = float(report['FESHBACH']['switchdt'])
bfield.linear(0.0,ss)
bfield.appendhold(4*switchdt)
bias  = float(report['FESHBACH']['bias'])
bfield.linear(cnv('bfield',bias),40.0)
#bfield.ExponentialTurnOn( bias, 20.0, 3.0, 'bfield')


# Add adiabatic ramp down to ODT
#odtpow = odt.odt_adiabaticDown(ss,ENDUVMOT)
	
#Add waveforms to sequence
s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow])
	
#wait normally rounds down using floor, here the duration is changed before so that
#the wait is rounded up
ENDCNC = ss*math.ceil(ENDCNC/ss)
	
#insert QUICK pulse  for fast ramping of the field gradient
s.wait(-10.0)
quickval = 1 if gen.bstr('CNC',report) == True else 0
s.digichg('quick',quickval)	
s.wait(10.0)

#Go to MOT release time and set QUICK back to low
s.wait(ENDCNC)
s.digichg('quick',0)

#RELEASE FROM MOT
s.digichg('motswitch',0) 
s.digichg('motshutter',0)
s.digichg('field',0)



#Go a little in the future to switch field from MOT to FESHBACH and to change HF probe detuning
s.digichg('field',0)
s.wait(switchdt)
s.digichg('feshbach',1)
s.digichg('hfimg',1)
s.wait(switchdt)
s.digichg('field',1)
s.wait(-2*switchdt)

#s.wait(intrap)
#wait for adiabatic ramp down
#tau = float(report['ODT']['tau'])
#s.wait( 2*tau )
#s.digichg('odtttl',0)
#s.wait(-2*tau)

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