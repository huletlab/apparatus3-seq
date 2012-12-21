"""Make sure the report file at 'Savedir/reportRunNumber.INI'
   exists otherwise this code won't compile. 
   
   Savedir and RunNumber are specified in settings.INI
"""
__author__ = "Pedro M Duarte"

import sys
import os

#Use this line to use the parameters in seq/benchmark/report_benchamr.INI and the output expseq.txt will located at the benchmark folder as well
#~ sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]+'/benchmark')


sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0])
import seqconf


for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)


import time
t0=time.time()

import sys, math
 
 
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

s.wait(0.0)


s.digichg('hfimg',1)
s.digichg('odt7595',0)

#Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)

# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
image= float(report['EVAP']['image'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
    print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,free)
    exit(1)
s.wait(free)


evap_ss = float(report['EVAP']['evapss'])
bias = float(report['FESHBACH']['bias'])
evap_ss = float(report['EVAP']['evapss'])
b1 = float(report['FESH_LIFETIME']['field1'])
b2 = float(report['FESH_LIFETIME']['field2'])
bdt1 = float(report['FESH_LIFETIME']['fielddt1'])
bdt2 = float(report['FESH_LIFETIME']['fielddt1'])
bwait1 = float(report['FESH_LIFETIME']['wait1'])
bwait2 = float(report['FESH_LIFETIME']['wait1'])

#add bfield ramp up during evap#
if (int(report['EVAP']['use_field_ramp'])):
    bfield,odtpow, ENDEVAP, cpowend, ipganalog = odt.odt_evap_field(image)
    
else:
    odtpow, ENDEVAP, cpowend, ipganalog = odt.odt_evap(image)
    bfield = wfm.wave('bfield',bias,evap_ss)
    bfield.extend(odtpow.dt())



bfield.linear(b1,bdt1)
bfield.appendhold(bwait1)
bfield.linear(b2,bdt2)
bfield.appendhold(bwait2)
odtpow.extend(bfield.dt())
ipganalog.extend(bfield.dt())

waveforms = [odtpow,bfield,ipganalog]


#ADD rf ramp
if int(report['RF']['rf']) == 1: 
    
    rfmod  = wfm.wave('rfmod', 0., evap_ss)
    rfmod.extend(bfield.dt())
    rfdelay_probe = 0

    if int(report['RF']['probekill']) == 1:
    
        rfdelay_probe = rfdelay_probe +  float(report['RF']['probekilldt'])+float(report['RF']['probewait'])
    
    rfmod.appendhold(rfdelay_probe)
    rfmod.linear(float(report['RF']['rfvoltf']),float(report['RF']['rfpulsedt']))
    rfmod.appendhold(float(report['RF']['rfwait']))
    for i in waveforms:
        i.extend(rfmod.dt())
    waveforms = [odtpow,bfield,ipganalog,rfmod]

    
#s.analogwfm_add(evap_ss,[odtpow,bfield])
s.analogwfm_add(evap_ss,waveforms)
# ENDEVAP should be equal to image

#~ s.wait(image+zcrampdt+zcdt)

s.wait(image)

s.wait(-12.0)

s.digichg('quick2',1)

s.wait(12.0)

s.wait(bdt1+bdt1+bwait1+bwait2)

# Pulse Probe and RF

if int(report['RF']['probekill']) == 1:
	
	probe_kill_dt =  float(report['RF']['probekilldt'])
	
	s.wait(-10)
	
	s.digichg('prshutter',0)
	
	s.wait(10)
	
	s.digichg('probe',1)
	
	s.wait(probe_kill_dt)
	
	s.digichg('probe',0)
	
	s.digichg('prshutter',1)
	
	s.digichg('hfimg2',float(report['RF']['hfimg2']))
	
	probe_wait = float(report['RF']['probewait'])
	
	s.wait(probe_wait)
	
	
if int(report['RF']['rf']) == 1: 

	rfpulsedt = float(report['RF']['rfpulsedt'])

	s.digichg('rfttl',1)

	s.wait(rfpulsedt)

	s.digichg('rfttl',0)

	s.wait(float(report['RF']['rfwait']))

        

#RELEASE FROM IR TRAP
#print s.digital_chgs_str(1000,100000., ['cameratrig','probe','odtttl','prshutter'])
s.digichg('odtttl',0)
odttof = float(report['ODT']['odttof'])
s.wait(odttof)
#print s.digital_chgs_str(1000,100000., ['cameratrig','probe','odtttl','prshutter'])

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
if odttof <= 0.0:
    trap_on_picture = 1
else:
    trap_on_picture = 0
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)
#print s.digital_chgs_str(1000,100000.,['cameratrig','probe','odtttl','prshutter'])

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
#print s.digital_chgs_str(0.,100000.)

import seqconf
s.save( seqconf.seqtxtout() )
s.save( __file__.split('.')[0]+'.txt')
s.save( __file__.split('.')[0]+'.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)
