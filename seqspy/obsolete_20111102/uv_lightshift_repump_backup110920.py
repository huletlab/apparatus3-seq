"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

print "\n----- uv_lightshift_repump.py -----"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, cnc, uvcooling_repump, odt, andor, highfield_repump
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
s, toENDBFIELD = highfield_repump.go_to_highfield(s)


# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
image= float(report['UVLS']['evapdt'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
    exit(1)
s.wait(free)

#uvdet change is included in evap so the lock has time to respond
odtpow2, uvdet, ENDEVAP = odt.odt_lightshift_evap(image)
evap_ss = float(report['EVAP']['evapss'])
s.analogwfm_add(evap_ss,[uvdet,odtpow2])
# ENDEVAP should be equal to image
s.wait(image)

#Trigger new waveform to do LIGHTSHIFT measurement
buffer=10.0
s.wait(buffer)

odtpow3, bfield2, uv1freq, uvpow2, ENDC = odt.odt_lightshift(odtpow2.last())
ls_ss = float(report['UVLS']['ls_ss'])
s.analogwfm_add(ls_ss,[odtpow3, bfield2, uv1freq, uvpow2])

# Goes to when the UV should be pulsed
s.wait(ENDC)

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
    
waitdt3=float(report['UVLS']['waitdt3'])
s.wait(-waitdt3)
s.digichg('field',0)
s.wait(waitdt3)

s.digichg('uvaom1',0)
s.digichg('uvaom2',uv)
s.wait(pulse)
s.digichg('field',1)
s.digichg('uvaom1',0)
s.digichg('uvaom2',0)

#ADD QUICK TO BE ABLE TO RAMP FIELD BACK UP
HS=20.0
s.wait(-HS) #Give QUICKS HS ms head start
s.digichg('quick',1)
s.digichg('hfquick',1)
s.wait( HS) 
hframpdt = float(report['UVLS']['hframpdt'])
s.wait( hframpdt+10.0)
s.digichg('quick',0)
s.digichg('hfquick',0)
s.wait(-hframpdt-10.0)


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