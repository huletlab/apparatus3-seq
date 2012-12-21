"""Make sure the report file at 'Savedir/reportRunNumber.INI'
   exists otherwise this code won't compile. 
   
   Savedir and RunNumber are specified in settings.INI
"""
__author__ = "Pedro M Duarte"

import sys
import os

#Use this line to use the parameters in seq/benchmark/report_benchamr.INI and the output expseq.txt will located at the benchmark folder as well
sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]+'/benchmark')



sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] )
import seqconf
for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)

import time
t0=time.time()

import math
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot, manta

#REPORT
report=gen.getreport()

#MOST USED SECTION
SEC = report['LATTICEBRAGGFIELD']
def fval( key ):
    return float(SEC[key])
    
#GET SECTION CONTENTS
lbf  = gen.getsection('LATTICEBRAGGFIELD')
evap = gen.getsection('EVAP')
zc   = gen.getsection('ZEROCROSS')
Andor= gen.getsection('ANDOR')
Manta= gen.getsection('MANTA')


#SEQUENCE
stepsize = float(report['SEQ']['stepsize'])
s=seq.sequence(stepsize)
s=gen.initial(s)
s.digichg('hfimg',1)
s.digichg('odt7595',0)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)

# Evaporate in cross beam trap
s, cpowend = odt.crossbeam_evap_field(s, toENDBFIELD)




#########################################
## BIND LATTICE BEAMS TOGETHER
#########################################
if lbf.bindir:
    lbf.ir2 = lbf.ir1
    lbf.ir3 = lbf.ir1
    lbf.ir2pow1 = lbf.ir1pow1
    lbf.ir3pow1 = lbf.ir1pow1
    lbf.ir2delay1 = lbf.ir1delay1
    lbf.ir3delay1 = lbf.ir1delay1
    lbf.ir2rampdt1 = lbf.ir1rampdt1
    lbf.ir3rampdt1 = lbf.ir1rampdt1
    
    lbf.ir2pow2 = lbf.ir1pow2
    lbf.ir3pow2 = lbf.ir1pow2
    lbf.ir2delay2 = lbf.ir1delay2
    lbf.ir3delay2 = lbf.ir1delay2
    lbf.ir2rampdt2 = lbf.ir1rampdt2
    lbf.ir3rampdt2 = lbf.ir1rampdt2
    
if lbf.bindgr:
    lbf.gr2 = lbf.gr1
    lbf.gr3 = lbf.gr1
    lbf.gr2pow1 = lbf.gr1pow1
    lbf.gr3pow1 = lbf.gr1pow1
    lbf.gr2delay1 = lbf.gr1delay1
    lbf.gr3delay1 = lbf.gr1delay1
    lbf.gr2rampdt1 = lbf.gr1rampdt1
    lbf.gr3rampdt1 = lbf.gr1rampdt1
    
    lbf.gr2pow2 = lbf.gr1pow2
    lbf.gr3pow2 = lbf.gr1pow2
    lbf.gr2delay2 = lbf.gr1delay2
    lbf.gr3delay2 = lbf.gr1delay2
    lbf.gr2rampdt2 = lbf.gr1rampdt2
    lbf.gr3rampdt2 = lbf.gr1rampdt2


#This step size is used in all ramps from here on
ir_ss = 0.01
buffer=25.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)

#########################################
## RAMPS TO INTERMEDIATE VALUES
#########################################

# Ramp B Field to intermediate value 
bfield = wfm.wave('bfield', evap.fieldrampfinal ,ir_ss)
bfield.appendhold( lbf.brampdelay1 )
bfield.linear( lbf.bstage1, lbf.brampdt1 )
# With respect to the start of the sequence, set QUICK2 pulse
s.wait(-lbf.quick2time + lbf.brampdelay1 )
s.digichg('quick2',1)
s.wait( lbf.quick2time - lbf.brampdelay1 )
    
# Ramp up IR and green beams to intermediate value 
ir1  = wfm.wave('ir1pow', 0., ir_ss,volt=-11)
ir2  = wfm.wave('ir2pow', 0., ir_ss,volt=-11)
ir3  = wfm.wave('ir3pow', 0., ir_ss,volt=-11)
ir1.appendhold( lbf.ir1delay1 )
ir2.appendhold( lbf.ir2delay1 )
ir3.appendhold( lbf.ir3delay1 )
ir1.linear(lbf.ir1pow1,lbf.ir1rampdt1, volt=-11)
ir2.linear(lbf.ir2pow1,lbf.ir2rampdt1, volt=-11)
ir3.linear(lbf.ir3pow1,lbf.ir3rampdt1, volt=-11)

gr1  = wfm.wave('greenpow1', 0., ir_ss)
gr2  = wfm.wave('greenpow2', 0., ir_ss)
gr3  = wfm.wave('greenpow3', 0., ir_ss)
gr1.appendhold(lbf.gr1delay1)
gr2.appendhold(lbf.gr2delay1)
gr3.appendhold(lbf.gr3delay1)
gr1.linear(lbf.gr1pow1,lbf.gr1rampdt1)
gr2.linear(lbf.gr2pow1,lbf.gr2rampdt1)
gr3.linear(lbf.gr3pow1,lbf.gr3rampdt1)

# Bfield, IR, and Green are at intermediate value. Time elapsed is == intermediate_dt
intermediate_dt = max( [ lbf.__dict__[k] for k in lbf.__dict__.keys() if 'delay1' in k or 'rampdt1' in k] )
    
# Make them all equal length
bfield.extend(intermediate_dt)
ir1.extend(intermediate_dt)
ir2.extend(intermediate_dt)
ir3.extend(intermediate_dt)
gr1.extend(intermediate_dt)
gr2.extend(intermediate_dt)
gr3.extend(intermediate_dt)


#########################################
## RAMPS TO FINAL VALUES
#########################################
#Ramp IR, Green and field to final value
ir1.appendhold(lbf.ir1delay2)
ir2.appendhold(lbf.ir2delay2)
ir3.appendhold(lbf.ir3delay2)
ir1.linear(lbf.ir1pow2,lbf.ir1rampdt2 )
ir2.linear(lbf.ir2pow2,lbf.ir2rampdt2)
ir3.linear(lbf.ir3pow2,lbf.ir3rampdt2)

gr1.appendhold(lbf.gr1delay2)
gr2.appendhold(lbf.gr2delay2)
gr3.appendhold(lbf.gr3delay2)
gr1.linear(lbf.gr1pow2,lbf.gr1rampdt2)
gr2.linear(lbf.gr2pow2,lbf.gr2rampdt2)
gr3.linear(lbf.gr3pow2,lbf.gr3rampdt2)


bfield.appendhold(lbf.brampdelay2)
bfield.linear(lbf.bstage2,lbf.brampdt2)
bfield2rampdt = bfield.dt()

# Bfield, IR, and Green are at final value. Time elapsed is == intermediate_dt2
intermediate_dt2 = max( [ lbf.__dict__[k] for k in lbf.__dict__.keys() if 'delay2' in k or 'rampdt2' in k] )

# Make them all equal length
bfield.extend(intermediate_dt+intermediate_dt2)
ir1.extend(intermediate_dt+intermediate_dt2)
ir2.extend(intermediate_dt+intermediate_dt2)
ir3.extend(intermediate_dt+intermediate_dt2)
gr1.extend(intermediate_dt+intermediate_dt2)
gr2.extend(intermediate_dt+intermediate_dt2)
gr3.extend(intermediate_dt+intermediate_dt2)

#########################################
## END RAMPS: MAKE DECISION ABOUT CUTOFF
#########################################
#Bfield, IR, and Green are all equal length == intermediate_dt + intermediate_dt2
#This is when we take the picture or probe with the Bragg beam
imagetime = intermediate_dt + intermediate_dt2 + lbf.inlattice
if lbf.inlattice < 200:
	separate_ramps_cuttof = 500.
else:
	separate_ramps_cuttof = 100.

#########################################
## END RAMPS:  SHORT INLATTICE
## LOCK LATTICE, GO TO ZEROCROSS, RAMP DOWN ODT
#########################################
if lbf.inlattice < separate_ramps_cuttof:
	ir1.appendhold(lbf.inlattice)
	ir2.appendhold(lbf.inlattice)
	ir3.appendhold(lbf.inlattice)
	gr1.appendhold(lbf.inlattice)
	gr2.appendhold(lbf.inlattice)
	gr3.appendhold(lbf.inlattice)
	
	# Ramp field quickly down to zero crossing for imaging
	if lbf.imgzc == 1 : 
		bfield.extend( ir1.dt() ) 
		bfield.insertlin_cnv( zc.zcbias, 1.0, -5.0)
	
	# Insert lattice lock
	ir1.insertlin_cnv( lbf.irlockpow, lbf.irlockpowdt, -lbf.irlockpowdt)
	ir2.insertlin_cnv( lbf.irlockpow, lbf.irlockpowdt, -lbf.irlockpowdt)
	ir3.insertlin_cnv( lbf.irlockpow, lbf.irlockpowdt, -lbf.irlockpowdt)

	# Ramp down ODT
	odtpow = odt.odt_wave('odtpow', cpowend, ir_ss)
	odtpow.appendhold( imagetime + lbf.odtdelay )
	if lbf.odtzero == 1:
		odtpow.linear( 0.0,  lbf.odtrampdt)

	waveforms = [ir1,ir2,ir3,gr1,gr2,gr3,bfield, odtpow]

	# RF sweep
	if lbf.rf == 1:   
		rfmod  = wfm.wave('rfmod', 0., ir_ss)
		rfmod.appendhold( imagetime + lbf.rftime )
		rfmod.linear( lbf.rfvoltf, lbf.rfpulsedt)
		waveforms = [rfmod,ir1,ir2,ir3,gr1,gr2,gr3,bfield, odtpow]

	endtime = s.analogwfm_add(ir_ss,waveforms)
	print "...Lattice ramp time = " + str(endtime) + " ms"
	
#########################################
## END RAMPS:  LONG INLATTICE
## LOCK LATTICE, GO TO ZEROCROSS, RAMP DOWN ODT
#########################################	
else:
	# FINISH OUT FIRST SET OF RAMPS
	waveforms = [ir1,ir2,ir3,gr1,gr2,gr3,bfield]
	endtime = s.analogwfm_add(ir_ss,waveforms)
	print "...Lattice ramp time = " + str(endtime) + " ms"
	
	# PUT IN THE SECOND SET OF RAMPS, WHEN INLATTICE IS LONG
	#
	# The second set of ramps is going to contain the odt rampdown
	# and the lattice locking
	#
	if lbf.inlattice - (-lbf.odtdelay) < separate_ramps_cuttof + 50.0:
		print "---> ERROR: attempted to put ramps in the dead region, no time to load second set of ramps"
		exit(1)
	
	# Ramps start at the earliest of odtramp and irlockramp
	start2time =  min(  lbf.inlattice - (-lbf.odtdelay), lbf.inlattice - lbf.irlockpowdt )

	if start2time < separate_ramps_cuttof + 50.0:
		print "---> ERROR: attempted to put ramps in the dead region, no time to load second set of ramps"
		exit(1)
	if lbf.inlattice - start2time > 2000.0:
		print "---> ERROR: probably not enough buffer time to put in second set of ramps"
		exit(1)

	if abs(endtime - (intermediate_dt+intermediate_dt2)) > 3*ir_ss:
		print "---> ERROR: endtime for the first ramps is different that the sum of intermediate times",(endtime - (intermediate_dt+intermediate_dt2))
		exit(1)

	s.wait(endtime + start2time)
	
	print "...Building second set of ramps:"
	print "...  inlattice = %.3f " % lbf.inlattice
	print "...  start2time = %.3f " % start2time
	
	odtpow = odt.odt_wave('odtpow', cpowend, ir_ss)
	odtpow.appendhold( lbf.inlattice - (-lbf.odtdelay) - start2time)
	if lbf.odtzero  == 1:
		odtpow.linear(0.0, lbf.odtrampdt)
	odtpow.extend( lbf.inlattice - start2time)
	
	ir1  = wfm.wave(lbf.ir1pow, ir1pow2, ir_ss)
	ir2  = wfm.wave(lbf.ir2pow, ir2pow2, ir_ss)
	ir3  = wfm.wave(lbf.ir3pow, ir3pow2, ir_ss)
	ir1.appendhold( lbf.inlattice -start2time)
	ir2.appendhold( lbf.inlattice -start2time)
	ir3.appendhold( lbf.inlattice -start2time)
	ir1.insertlin_cnv( lbf.irlockpow, lbf.irlockpowdt, -lbf.irlockpowdt)
	ir2.insertlin_cnv( lbf.irlockpow, lbf.irlockpowdt, -lbf.irlockpowdt)
	ir3.insertlin_cnv( lbf.irlockpow, lbf.irlockpowdt, -lbf.irlockpowdt)
	
	bfield = wfm.wave('bfield', lbf.bstage2, ir_ss)
	bfield.extend( ir1.dt())
	
	#Go to zero crossing for imaging
	if lbf.imgzc == 1: 
		bfield.insertlin_cnv( zc.zcbias, 1.0, -5.0)

	waveforms = [ir1,ir2,ir3,odtpow,bfield]

	endtime2 = s.analogwfm_add(ir_ss,waveforms)
	s.wait( -endtime-start2time)
	print "...Lattice ramp time (second set) = " + str(endtime) + " ms"
	

#########################################
## TTL STATE CHANGES
#########################################	
# Turn on IR lattice beams
ttldelay = 0.0
s.wait(-ttldelay)
s.wait(lbf.ir1delay1)
s.digichg('irttl1', lbf.ir1 )
s.wait(-lbf.ir1delay1+lbf.ir2delay1)
s.digichg('irttl2', lbf.ir2 )
s.wait(lbf.ir3delay1-lbf.ir2delay1)
s.digichg('irttl3', lbf.ir3 )
s.wait(-lbf.ir3delay1)

s.wait(lbf.gr1delay1)
s.digichg('greenttl1', lbf.gr1 )
s.wait(-lbf.gr1delay1+lbf.gr2delay1)
s.digichg('greenttl2', lbf.gr2 )
s.wait(-lbf.gr2delay1+lbf.gr3delay1)
s.digichg('greenttl3', lbf.gr3 )
s.wait(-lbf.gr3delay1)
s.wait(ttldelay)

# Go to the time of the second bfield ramp
s.wait(bfield2rampdt)
s.digichg('select2', lbf.select2)
s.wait(-bfield2rampdt)

# Go 10 ms after the end of the second bfield ramp and turn quick2 off
s.wait(bfield2rampdt + 10.)
s.digichg('quick2', 0)
s.wait(-bfield2rampdt-10.)

# Go to the odt turn off time
odtoff_time =imagetime+ lbf.odtdelay + lbf.odtrampdt
s.wait(odtoff_time)
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
s.wait(-odtoff_time)

# Go to where we take the image / probe with Brag beam
s.wait(imagetime)


#########################################
## OTHER TTL EVENTS: probekill, braggkill, rf
#########################################
# Probe Kill
if lbf.probekill == 1:
	s.wait(lbf.probekilltime)
	
	if lbf.probekill_hfimg2 == 1 :
		s.wait(-20)
		s.digichg('hfimg2',1)
		s.wait(20)
	
	s.wait(-10)
	s.digichg('prshutter',0)
	s.wait(10)
	s.digichg('probe',1)
	s.wait(lbf.probe_kill_dt)
	s.digichg('probe',0)
	
	if lbf.probekill_hfimg2 == 1:
		s.digichg('hfimg2',0)

	s.digichg('prshutter',1)
	s.wait(-lbf.probekilltime)

# Pulse RF
if lbf.rf == 1:
	s.wait(lbf.rftime)
	s.digichg('rfttl',1)
	s.wait(lbf.rfpulsedt)
	s.digichg('rfttl',0)
	s.wait(-lbf.rfpulsedt)
	s.wait(-lbf.rftime)
	
# Braggkill
if lbf.braggkill == 1:
	s.wait( lbf.braggkilltime)
	s = manta.OpenShutterBragg(s,lbf.shutterdelay)
	s.digichg('bragg',1)
	s.wait( lbf.braggkilldt)
	s.digichg('brshutter',1) # to close shutter
	s.digichg('bragg',0)
	s.digichg('hfimg2', lbf.hfimg2)
	s.wait( -lbf.braggkilldt)
	s.wait( -lbf.braggkilltime )
	
#########################################
## TTL RELEASE FROM LATTICE
#########################################
#RELEASE FROM LATICE
s.wait(lbf.latticeoff)
s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)
s.wait(-lbf.latticeoff)


#########################################
## PICTURES
#########################################
#TAKE PICTURES
trap_on_picture = 0

#####light = this is 'probe', 'motswitch' or 'bragg'
#####camera = this is 'andor' or 'manta'
if lbf.light == 'bragg':
    s = manta.OpenShutterBragg(s,lbf.shutterdelay)

if lbf.camera == 'andor':
	kinetics = gen.bstr('Kinetics',report)
	print '...kinetics = ' + str(kinetics)
	if kinetics == True:
		s,SERIESDT = andor.KineticSeries4(s,Andor.exp, lbf.light,Andor.noatoms, trap_on_picture)
	else:
		s,SERIESDT = andor.FKSeries2(s,stepsize,Andor.exp, lbf.light,Andor.noatoms, trap_on_picture)
		
elif camera == 'manta':
	#PICTURE OF ATOMS
	s=manta.MantaPicture(s, Manta.texp, lbf.light, 1)
	s.wait(Manta.noatoms)
	#RELEASE FROM ODT AND LATTICE
	odton_picture = 0
	print "...ODTTTL for the picture = ", odton_picture
	latticeon_picture = 0 if latticeoff <= 0. else 1
	s.digichg('quick2',0)
	s.digichg('odtttl',0)
	s.digichg('odt7595',0)
	s.digichg('ipgttl',0)
	s.digichg('greenttl1',0)
	s.digichg('greenttl2',0)
	s.digichg('greenttl3',0)
	s.digichg('irttl1',0)
	s.digichg('irttl2',0)
	s.digichg('irttl3',0)
	s.wait(50.0)
	s.digichg('odtttl',odton_picture)
	s.digichg('odt7595',odton_picture)
	s.digichg('ipgttl',odton_picture)
	s.digichg('greenttl1',latticeon_picture*lbf.gr1)
	s.digichg('greenttl2',latticeon_picture*lbf.gr2)
	s.digichg('greenttl3',latticeon_picture*lbf.gr3)
	s.digichg('irttl1',latticeon_picture*lbf.ir1)
	s.digichg('irttl2',latticeon_picture*lbf.ir2)
	s.digichg('irttl3',latticeon_picture*lbf.ir3)
	s.wait(20.0)

	#PICTURE OF BACKGROUND
	s=manta.MantaPicture(s, Manta.texp, lbf.light, 1)
	s.wait(Manta.noatoms)
	
	#HERE TURN OFF ALL LIGHT THAT COULD GET TO THE MANTA
	s.digichg('odtttl',0)
	s.digichg('odt7595',0)
	s.digichg('ipgttl',0)
	s.digichg('greenttl1',0)
	s.digichg('greenttl2',0)
	s.digichg('greenttl3',0)
	s.digichg('irttl1',0)
	s.digichg('irttl2',0)
	s.digichg('irttl3',0)
	s.wait(20.0)
	
	#REFERENCE #1
	s=manta.MantaPicture(s, Manta.texp, lbf.light, 0)
	s.wait(Manta.noatoms)
	#REFERENCE #2
	s=manta.MantaPicture(s, Manta.texp, lbf.light, 0)
	s.wait(Manta.noatoms)


#print s.digital_chgs_str(500,100000.,['cameratrig','probe','odtttl','prshutter'])

#After taking a picture sequence returns at time of the last probe strobe
#Wait 50ms to get past the end
s.wait(50.0)
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