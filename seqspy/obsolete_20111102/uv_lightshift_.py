"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

print "\n----- uv_lightshift.py -----"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, cnc, uvcooling, odt, andor

global report

report=gen.getreport()

#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

s.digichg('hfimg',1)
s.digichg('odt7595',1)

#Keep ODT on
ODT = gen.bstr('ODT',report)
if ODT == True:
    s.digichg('odtttl',1)
s.wait(20.0)

ss = float(report['SEQ']['analogstepsize'])

# Cool and Compress MOT
# ENDCNC is defined as the time up to release from the MOT
motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()

# Load UVMOT from CNCMOT
uvfppiezo, uvpow, motpow, repdet, trapdet, reppow, trappow, bfield, ENDUVMOT = uvcooling.uvcoolRamps(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC)

# Set imaging values
camera = 'ANDOR'
motpow, repdet, trapdet, reppow, trappow, maxDT = cnc.imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow, camera)

# Switch bfield to FESHBACH while UV cools in trap
overlapdt    = float(report['ODT']['overlapdt'])
rampdelay    = float(report['ODT']['rampdelay'])
rampbf       = float(report['ODT']['rampbf'])
bf           = float(report['ODT']['bf'])
holdbf       = float(report['ODT']['holdbf'])
switchdt     = float(report['FESHBACH']['switchdt'])
offdelay     = float(report['FESHBACH']['offdelay'])
quickdelay   = float(report['FESHBACH']['quickdelay'])
switchdelay  = float(report['FESHBACH']['switchdelay'])
bias         = float(report['FESHBACH']['bias'])
biasrampdt   = float(report['FESHBACH']['rampdt'])

bfield.chop(ENDUVMOT-overlapdt)
bfield.appendhold(rampdelay)
bfield.linear( bf, rampbf)
bfield.appendhold(holdbf)
bfield.linear(0.0, 0.0)
ENDBFIELD=(rampdelay+rampbf+holdbf-overlapdt)
bfield.appendhold(-ENDBFIELD+offdelay+2*switchdt+quickdelay+switchdelay)
bfield.linear(bias,biasrampdt)

#Add waveforms to sequence
s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow])
	
#wait normally rounds down using floor, here the duration is changed before so that
#the wait is rounded up
ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
#insert QUICK pulse  for fast ramping of the field gradient
s.wait(-10.0)
quickval = 1 if gen.bstr('CNC',report) == True else 0
s.digichg('quick',quickval)	
s.wait(10.0)

#insert UV pulse
uvtime  = float(report['UV']['uvtime'])
s.wait(ENDCNC)
s.digichg('quick',0)
s.wait(uvtime)
s.digichg('uvaom1',1)
s.wait(-uvtime - ENDCNC)
	
#Go to MOT release time
s.wait(ENDUVMOT)
s.digichg('quick',0)

#Leave UVMOT on for state transfer
fstatedt  = float(report['ODT']['fstatedt'])
s.wait(fstatedt)
s.digichg('uvaom1',0)
s.wait(-fstatedt) 


#RELEASE FROM MOT
waitshutter=5.0
s.wait(waitshutter)
s.digichg('uvshutter',0)
s.wait(-waitshutter)

s.digichg('motswitch',0) 
s.digichg('motshutter',1)
s.digichg('field',0)

#Insert ODT overlap with UVMOT and switch field to FESHBACH
overlapdt = float(report['ODT']['overlapdt'])
s.wait(-overlapdt)
s.digichg('odtttl',1)
s.digichg('odt7595',1)
feshbachdt = rampdelay + rampbf + holdbf
s.wait( feshbachdt )
s.digichg('feshbach',1)
s.wait(overlapdt - feshbachdt)

s.wait(offdelay)
s.wait(2*switchdt)
s.wait(quickdelay)
do_quick=1
s.digichg('field',1)
s.digichg('hfquick',do_quick)
s.digichg('quick',do_quick)
#Can't leave quick ON for more than quickmax
quickmax=100.
s.wait(quickmax)
s.digichg('hfquick',0)
s.digichg('quick',0)
s.wait(-quickmax)
s.wait(switchdelay+biasrampdt)
s.digichg('quick',0)
s.wait(-biasrampdt)
s.wait(-switchdelay-quickdelay-2*switchdt-offdelay)

#At this point the time sequence is at ENDUVMOT

#This is the time until the end of the bfield ramp
toENDBFIELD = biasrampdt + switchdelay + quickdelay + 2*switchdt + offdelay

# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
image= float(report['UVLS']['evapdt'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
    exit(1)
s.wait(free)

#uvdet change is included in evap so the lock has time to respond
odtpow, uvdet, ENDEVAP = odt.odt_lightshift_evap(image)
evap_ss = float(report['EVAP']['evapss'])
s.analogwfm_add(evap_ss,[odtpow,uvdet])
# ENDEVAP should be equal to image
s.wait(image)

#Trigger new waveform to do LIGHTSHIFT measurement
buffer=10.0
s.wait(buffer)

odtpow2, bfield2, uv1freq, uvpow, END2 = odt.odt_lightshift(odtpow.last())
ls_ss = float(report['UVLS']['ls_ss'])
s.analogwfm_add(ls_ss,[odtpow2, bfield2, uv1freq, uvpow])

# Goes to when the UV should be pulsed
s.wait(END2)

#OPEN UV SHUTTERS
#s.wait(-1000.0)
#s.digichg('uvprobe',0)
#s.wait(1000.0)
s.wait(-30.0)
s.digichg('uvshutter',1)
s.wait(30.0)

#PULSE UV LIGHT
pulse = float(report['UVLS']['dtpulse'])
uv = int(report['UVLS']['uv'])
if uv !=1:
    uv=0
s.digichg('uvaom1',uv)
s.digichg('uvaom2',uv)
s.wait(pulse)
s.digichg('uvaom1',0)
s.digichg('uvaom2',0)

#ADD QUICK TO BE ABLE TO RAMP FIELD BACK UP
s.wait(-15.0) #Give QUICKS 15.0ms head start
s.digichg('quick',1)
s.digichg('hfquick',1)
s.wait( 15.0) 
hframpdt = float(report['UVLS']['hframpdt'])
s.wait( hframpdt)
s.digichg('quick',0)
s.digichg('hfquick',0)
s.wait(-hframpdt)


#WAIT IN TRAP AND THEN RELEASE FROM IR TRAP
trapdt = float(report['UVLS']['trapdt'])
s.wait( trapdt)
lstof = float(report['UVLS']['lstof'])
s.digichg('odtttl',0)
s.wait(lstof)
    

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
trap_on_picture = 1
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)


#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)


s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
s.clear_disk()

print '...Compilation = %.2f seconds\n' % (time.time()-t0)