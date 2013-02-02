"""Make sure the report file at 'Savedir/reportRunNumber.INI'
   exists otherwise this code won't compile. 
   
   Savedir and RunNumber are specified in settings.INI
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

import sys, math
 
 
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])

#GET SECTION CONTENTS
evapsec  = gen.getsection('EVAP')

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

s.wait(0.0)


s.digichg('hfimg',1)
#s.digichg('hfimg2',0)
s.digichg('odt7595',0)

if evapsec.lattice == 1.0:
	s.digichg('irttl1', evapsec.irttl1)
	s.digichg('irttl2', evapsec.irttl2)
	s.digichg('irttl3', evapsec.irttl3)

#Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)

# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
image= float(report['EVAP']['image'])
evapscale = float(report['EVAP']['image'])

buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
    print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,free)
    exit(1)
s.wait(free)


evap_ss = float(report['EVAP']['evapss'])
bias = float(report['FESHBACH']['bias'])
zcrampdt = float(report['ZEROCROSS']['zcrampdt'])
zcdt = float(report['ZEROCROSS']['zcdt'])
zcbias = float(report['ZEROCROSS']['zcbias'])

#add bfield ramp up during evap#
if (int(report['EVAP']['use_field_ramp'])):
    bfield, odtpow, ENDEVAP, cpowend, ipganalog= odt.odt_evap_field(image)#,odtpow_test,odtpow_test2 
    
else:
    odtpow, ENDEVAP, cpowend, ipganalog = odt.odt_evap(image)
    bfield = wfm.wave('bfield',bias,evap_ss)
    bfield.extend(odtpow.dt())
    

bfield.linear(zcbias,zcrampdt)
bfield.appendhold(zcdt)
odtpow.extend(bfield.dt())
ipganalog.extend(bfield.dt())


#add odt ramp up#
if int(report['EVAP']['use_odt_lock']) == 1: 
    odtlockpow = float(report['EVAP']['odtlockpow'])
    odtlockpowdt = float(report['EVAP']['odtlockpowdt'])
    
    if odtlockpow == -1: 
        odtpow.appendhold(odtlockpowdt)        
        bfield.extend(odtpow.dt())
        ipganalog.extend(bfield.dt())
        
    else:

        odtpow.linear( odtlockpow, odtlockpowdt)
        bfield.extend(odtpow.dt())
        ipganalog.extend(bfield.dt())
        #Here, go ahead and save the finalcpow to the report
        gen.save_to_report('EVAP','finalcpow', odtlockpow)

waveforms = [odtpow,bfield,ipganalog]#,odtpow_test,odtpow_test2]


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
    waveforms = [odtpow,bfield,ipganalog,rfmod]#,odtpow_test,odtpow_test2]

    
#s.analogwfm_add(evap_ss,[odtpow,bfield])
s.analogwfm_add(evap_ss,waveforms)
# ENDEVAP should be equal to image

#~ s.wait(image+zcrampdt+zcdt)

s.wait(image)

s.wait(-12.0)

s.digichg('quick2',1)

s.wait(12.0)

s.wait(zcrampdt)


s.digichg('select2',0)

s.wait(zcdt)

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


# If a beam profile is taken send trigger to Basler:
if report['EVAP']['beamprofile'] == 'yes' and report['EVAP']['thermaltest'] != 'yes': 
    print "...Will trigger basler for beam profile."
    baslerexp = float(report['EVAP']['baslerexp'])
    postbaslerdt = 5.0
    s.wait( - baslerexp - postbaslerdt )
    s.digichg('basler',1)
    s.wait( baslerexp)
    s.digichg('basler',0)
    s.wait( postbaslerdt)
if report['EVAP']['beamprofile'] == 'yes' and report['EVAP']['thermaltest'] == 'yes': 
    image = float(report['EVAP']['image'])
    image0 = 50.0
    postbaslerdt = 100.0
    Nimages = 5
    delta = (image - image0 - postbaslerdt) / (Nimages-1)
    
    exposures = [0.5, 8.0, 40.0, 40.0,40.0, 40.0, 40.0, 40.0, 40.0, 40.0]
    
    print ""
    print "----- Setting up basler triggers for ODT thermal test -----"
    print "\timage       = %.1f" % image
    print "\timage0      = %.1f" % image0
    print "\tdelta       = %.1f" % delta
    
    #~ s.wait( -(image-image0) - Nimages*10 -100)
    
    #~ for i in range(Nimages):
        #~ s.wait( 10*i )
        #~ s.digichg('basler', 1)
        #~ s.wait( 1)
        #~ s.digichg('basler', 0)
        #~ s.wait( -1)
        #~ s.wait( -10*i )
    
    #~ s.wait( -(-(image-image0) - Nimages*10 -100) )
    
    for i in range(Nimages):
        s.wait( -(image-image0) + delta*i )
        s.digichg('basler', 1)
        s.wait( exposures[i] )
        s.digichg('basler', 0)
        s.wait( -exposures[i])
        s.wait( (image-image0) - delta*i )
        
        
    
# add time for odt rampup

if int(report['EVAP']['use_odt_lock']) == 1: 
    odtlockpowdt = float(report['EVAP']['odtlockpowdt'])
    s.wait(odtlockpowdt)

#RELEASE FROM IR TRAP
#print s.digital_chgs_str(1000,100000., ['cameratrig','probe','odtttl','prshutter'])
s.digichg('odtttl',0)
odttof = float(report['ODT']['odttof'])
s.wait(odttof)
#print s.digital_chgs_str(1000,100000., ['cameratrig','probe','odtttl','prshutter'])


#~ s.wait(-200.)
#~ s.digichg('hfimg2',0)
#~ s.wait(200.)

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
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)
