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


#GET SECTION CONTENTS
SEQ = gen.getsection('SEQ')
EVAP  = gen.getsection('EVAP')
ANDOR = gen.getsection('ANDOR')
ODT = gen.getsection('ODT')
FESHBACH = gen.getsection('FESHBACH')
ZEROCROSS = gen.getsection('ZEROCROSS')
RF = gen.getsection('RF')

if EVAP.andor2 == 1:
	print "\n...SEQ:camera will be modified  in report"
	print "\tNEW  SEQ:camera = andor,andor2\n" 
	gen.save_to_report('SEQ','camera', 'andor,andor2') 


#SEQUENCE
s=seq.sequence(SEQ.stepsize)
s=gen.initial(s)
s.wait(0.0)

#Get hfimg ready
s.digichg('hfimg',1)

#If using analoghfimg get it ready
if ANDOR.analoghfimg == 1:
	s.digichg('analogimgttl',1)


####REMOVAL PENDING
#This is T-eed and used to enable/disable the ODT servo
s.digichg('odt7595',0)


#Turn on lattice channels if they are used in evap
if EVAP.lattice == 1.0:
	s.digichg('irttl1', EVAP.irttl1)
	s.digichg('irttl2', EVAP.irttl2)
	s.digichg('irttl3', EVAP.irttl3)

#Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)

#Allow time for free evaporation (also helps provide buffer to reload the analog chs)
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if EVAP.free < buffer + toENDBFIELD :
    print 'Need at list ' + str(buffer) + 'ms of EVAP.free evap before evaporation can be triggered'
    print 'Currently ramps end at %f , and EVAP.free is %f' % (toENDBFIELD,EVAP.free)
    exit(1)
s.wait(EVAP.free)


#Do Evap
if int(EVAP.use_field_ramp) == 1:
    bfield, odtpow, ENDEVAP, cpowend, ipganalog= odt.odt_evap_field(EVAP.scale)
else:
    odtpow, ENDEVAP, cpowend, ipganalog = odt.odt_evap(EVAP.scale)
    bfield = wfm.wave('bfield',FESHBACH.bias,EVAP.evapss)
    bfield.extend(odtpow.dt())
#Use the EVAP.image time equal to EVAP.image times EVAP.scale for the sequence after the part.
EVAP.image = EVAP.image *EVAP.scale    


#Ramp the field to the zerocrossing
bfield.linear(ZEROCROSS.zcbias,ZEROCROSS.zcrampdt)
bfield.appendhold(ZEROCROSS.zcdt)
odtpow.extend(bfield.dt())
ipganalog.extend(bfield.dt())


#Recompress with the ODT
if int(EVAP.use_odt_lock) == 1: 
    
    if EVAP.odtlockpow == -1: 
        odtpow.appendhold(EVAP.odtlockpowdt)        
        bfield.extend(odtpow.dt())
        ipganalog.extend(bfield.dt())
        
    else:
        odtpow.linear( EVAP.odtlockpow, EVAP.odtlockpowdt)
        bfield.extend(odtpow.dt())
        ipganalog.extend(bfield.dt())
        #Here, go ahead and save the finalcpow to the report
        gen.save_to_report('EVAP','finalcpow', odtlockpow)


waveforms = [odtpow,bfield,ipganalog]

#ADD rf ramp
if int(RF.rf) == 1: 
    rfmod  = wfm.wave('rfmod', 0., EVAP.evapss)
    rfmod.extend(bfield.dt())
    rfdelay_probe = 0

    if int(RF.probekill) == 1:
        rfdelay_probe = rfdelay_probe +  RF.probekilldt + RF.probewait
    
    rfmod.appendhold(rfdelay_probe)
    rfmod.linear(RF.rfvoltf, RF.rfpulsedt)
    rfmod.appendhold(RF.rfwait)
    for i in waveforms:
        i.extend(rfmod.dt())
    waveforms = [odtpow,bfield,ipganalog,rfmod]


#Add waveforms and go to the end of evaporation
s.analogwfm_add(EVAP.evapss,waveforms)


#Add quick jump to help go to final evaporation field
if ( EVAP.use_field_ramp == 1 and  EVAP.image > EVAP.fieldrampt0):
    s.wait( EVAP.fieldrampt0 )
    s.wait(-25.0)
    s.digichg('hfquick',1)
    s.digichg('quick',1)
    s.wait(75.0)
    s.digichg('hfquick',0)
    s.digichg('quick',0)
    s.wait(-50.0)
    s.wait(-EVAP.fieldrampt0)
    

s.wait(EVAP.image)


#If ZC ramp needs to go up, then help it with a quick
if ( EVAP.use_field_ramp != 1 or  EVAP.image < EVAP.fieldrampt0):
    s.wait(-12.0)
    s.digichg('quick2',1)
    s.wait(12.0)
    
#Go to the end of ZC ramp
s.wait(ZEROCROSS.zcrampdt)
s.wait(ZEROCROSS.zcdt)

# Add time if recompressing with ODT
if int(EVAP.use_odt_lock) == 1: 
    s.wait(EVAP.odtlockpowdt)


#Pulse the probekill if required
if int(RF.probekill) == 1:
	s.wait(-10)
	s.digichg('prshutter',0)
	s.wait(10)
	s.digichg('probe',1)
	s.wait(RF.probekilldt)
	s.digichg('probe',0)
	s.digichg('prshutter',1)
	s.digichg('hfimg2',RF.hfimg2)
	s.wait(RF.probewait)
	
#Pulse RF
if int(RF.rf) == 1: 
	s.digichg('rfttl',1)
	s.wait(RF.rfpulsedt)
	s.digichg('rfttl',0)
	s.wait(RF.rfwait)


# This part below is used to characterize the ODT mode in a real evaporation scenario
# If a beam profile is taken send trigger to Basler:
if EVAP.beamprofile == 'yes' and EVAP.thermaltest != 'yes': 
    print "...Will trigger basler for beam profile."
    postbaslerdt = 5.0
    s.wait( - EVAP.baslerexp - postbaslerdt )
    s.digichg('basler',1)
    s.wait( EVAP.baslerexp)
    s.digichg('basler',0)
    s.wait( postbaslerdt)
if EVAP.beamprofile == 'yes' and EVAP.thermaltest == 'yes': 
    image0 = 50.0
    postbaslerdt = 100.0
    Nimages = 5
    delta = (EVAP.image - image0 - postbaslerdt) / (Nimages-1)
    ANDOR.exposures = [0.5, 8.0, 40.0, 40.0,40.0, 40.0, 40.0, 40.0, 40.0, 40.0]
    
    print ""
    print "----- Setting up basler triggers for ODT thermal test -----"
    print "\tEVAP.image       = %.1f" % EVAP.image
    print "\tEVAP.image0      = %.1f" % EVAP.image0
    print "\tdelta       = %.1f" % delta
    
    for i in range(Nimages):
        s.wait( -(EVAP.image-image0) + delta*i )
        s.digichg('basler', 1)
        s.wait( ANDOR.exposures[i] )
        s.digichg('basler', 0)
        s.wait( -ANDOR.exposures[i])
        s.wait( (EVAP.image-image0) - delta*i )


#RELEASE FROM IR TRAP
s.digichg('odtttl',0)
s.wait(ODT.odttof)


#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
if ODT.odttof <= 0.0:
    trap_on_picture = 1
else:
    trap_on_picture = 0
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
	s,SERIESDT = andor.KineticSeries4(s,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)
	if EVAP.andor2 == 1:
		s.wait(-SERIESDT)
		s,SERIESDT = andor.KineticSeries4(s,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture,trigger="cameratrig2")
else:
	if EVAP.andor2 == 1:
		sys.exit("Warning! The part of code with andor2 and kinetcs off has not been done.")
	s,SERIESDT = andor.FKSeries2(s,SEQ.stepsize,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)

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
