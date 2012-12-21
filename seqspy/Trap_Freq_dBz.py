"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import sys
import os
sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] )
import seqconf
for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)


import time
t0=time.time()

print "\n----- odt_dbz.py -----"

import sys, math
 
 
 
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

# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
evapdt= float(report['DBZ']['evapdt'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
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

odtpow2, bfield2, OFFDT = odt.odt_dbz(odtpow.last())
dbz_ss = float(report['DBZ']['dbz_ss'])
s.analogwfm_add(dbz_ss,[odtpow2,bfield2])

# Goes to when the field turns off for the first time
s.wait(OFFDT)
s.digichg('field',0)
dbz_switchdt = float(report['DBZ']['switchdt'])
s.wait(dbz_switchdt)
s.digichg('feshbach',0)
s.wait(dbz_switchdt)
s.digichg('field',1)
s.wait(dbz_switchdt)

s.wait(float(report['DBZ']['rampdt']))
s.wait(float(report['DBZ']['holddt']))
s.digichg('field',0)


#WAIT IN TRAP AND THEN RELEASE FROM IR TRAP
trapdt = float(report['DBZ']['trapdt'])
s.wait( trapdt)

tf_tof = float(report['DBZ']['tf_tof'])
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


import seqconf
s.save( seqconf.seqtxtout() )
s.save( __file__.split('.')[0]+'.txt')
s.clear_disk()

print '...Compilation = %.2f seconds\n' % (time.time()-t0)