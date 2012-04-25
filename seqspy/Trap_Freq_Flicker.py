"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

print "\n----- odt_flicker.py -----"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, cnc, highfield_uvmot, odt, andor

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
s.digichg('odt7595',0)

#Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)

print toENDBFIELD

# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
evapdt= float(report['FLICKER']['evapdt'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at list %.3f ms of free evap before evaporation can be triggered' % (buffer+toENDBFIELD)
    exit(1)
s.wait(free)
odtpow, ENDEVAP, cpowend, ipganalog = odt.odt_evap(evapdt)
evap_ss = float(report['EVAP']['evapss'])
s.analogwfm_add(evap_ss,[odtpow])
# ENDEVAP should be equal to image
s.wait(evapdt)

#Trigger new waveform to do trap frequency measurement
buffer=10.0
s.wait(buffer)

odtpow2, bfield2, ENDFLICK = odt.odt_flicker(odtpow.last())
flicker_ss = float(report['FLICKER']['flicker_ss'])
s.analogwfm_add(flicker_ss,[odtpow2,bfield2])

# Goes to when the modulation is finished
s.wait(ENDFLICK)

#
dt =float(report['FLICKER']['flickdt'])
ch =report['FLICKER']['channel']
if ch == 'odtttl' or ch == 'odt7595':
    s.digichg(ch, 0)
    s.wait(dt)
    s.digichg(ch, 1)
elif ch == 'odt7580':
    s.digichg(ch, 1)
    s.wait(dt)
    s.digichg(ch, 0)
else:
    exit(2)

#WAIT IN TRAP AND THEN RELEASE FROM IR TRAP
trapdt = float(report['FLICKER']['trapdt'])
s.wait( trapdt)

tf_tof = float(report['FLICKER']['tf_tof'])
s.digichg('odtttl',0)
s.wait(tf_tof)
    

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