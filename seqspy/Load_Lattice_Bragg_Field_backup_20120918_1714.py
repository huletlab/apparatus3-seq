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

import math
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot, manta

#REPORT
report=gen.getreport()

#MOST USED SECTION
SEC = report['LATTICEBRAGGFIELD']
def fval( key ):
    return float(SEC[key])
    


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


buffer=25.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)

#This step size is used in all ramps from here on
ir_ss = 0.01

# Ramp B Field to intermediate value 
bias = float(report['EVAP']['fieldrampfinal'])
bfield = wfm.wave('bfield',bias,ir_ss)
bfield.appendhold( fval('brampdelay1') )
bfield.linear( fval('bstage1'), fval('brampdt1') )

# With respect to the start of the sequence, set QUICK2 pulse
quick2time = float(report['LATTICEBRAGGFIELD']['quick2time'])
s.wait(-quick2time + fval('brampdelay1') )
s.digichg('quick2',1)
s.wait( quick2time - fval('brampdelay1') )



IR1Param = 'ir1'
IR2Param = 'ir2' if int(fval('bindir')) == 0 else 'ir1'
IR3Param = 'ir3' if int(fval('bindir')) == 0 else 'ir1'
GR1Param = 'gr1'
GR2Param = 'gr2' if int(fval('bindgr')) == 0 else 'gr1'
GR3Param = 'gr3' if int(fval('bindgr')) == 0 else 'gr1'


# Ramp up IR and green beams to intermediate value 
ir1ramp1  = float(report['LATTICEBRAGGFIELD'][IR1Param + 'rampdt1'])
ir2ramp1  = float(report['LATTICEBRAGGFIELD'][IR2Param + 'rampdt1'])
ir3ramp1  = float(report['LATTICEBRAGGFIELD'][IR3Param + 'rampdt1'])
ir1delay1 = float(report['LATTICEBRAGGFIELD'][IR1Param + 'delay1'])
ir2delay1 = float(report['LATTICEBRAGGFIELD'][IR2Param + 'delay1'])
ir3delay1 = float(report['LATTICEBRAGGFIELD'][IR3Param + 'delay1'])
ir1pow1   = float(report['LATTICEBRAGGFIELD'][IR1Param + 'pow1'])
ir2pow1   = float(report['LATTICEBRAGGFIELD'][IR2Param + 'pow1'])
ir3pow1   = float(report['LATTICEBRAGGFIELD'][IR3Param + 'pow1'])


ir1  = wfm.wave('ir1pow', 0., ir_ss,volt=-11)
ir2  = wfm.wave('ir2pow', 0., ir_ss,volt=-11)
ir3  = wfm.wave('ir3pow', 0., ir_ss,volt=-11)
ir1.appendhold( fval(IR1Param + 'delay1') )
ir2.appendhold( fval(IR2Param + 'delay1') )
ir3.appendhold( fval(IR3Param + 'delay1') )
ir1.linear(fval(IR1Param + 'pow1'),fval(IR1Param + 'rampdt1'), volt=-11)
ir2.linear(fval(IR2Param + 'pow1'),fval(IR2Param + 'rampdt1'), volt=-11)
ir3.linear(fval(IR3Param + 'pow1'),fval(IR3Param + 'rampdt1'), volt=-11)


gr1delay1 = float(report['LATTICEBRAGGFIELD'][GR1Param + 'delay1'])
gr2delay1 = float(report['LATTICEBRAGGFIELD'][GR2Param + 'delay1'])
gr3delay1 = float(report['LATTICEBRAGGFIELD'][GR3Param + 'delay1'])
gr1ramp1 = float(report['LATTICEBRAGGFIELD'][GR1Param + 'rampdt1'])
gr2ramp1 = float(report['LATTICEBRAGGFIELD'][GR2Param + 'rampdt1'])
gr3ramp1 = float(report['LATTICEBRAGGFIELD'][GR3Param + 'rampdt1'])
gr1pow1 = float(report['LATTICEBRAGGFIELD'][GR1Param + 'pow1'])
gr2pow1 = float(report['LATTICEBRAGGFIELD'][GR2Param + 'pow1'])
gr3pow1 = float(report['LATTICEBRAGGFIELD'][GR3Param + 'pow1'])


gr1  = wfm.wave('greenpow1', 0., ir_ss)
gr2  = wfm.wave('greenpow2', 0., ir_ss)
gr3  = wfm.wave('greenpow3', 0., ir_ss)
gr1.appendhold(gr1delay1)
gr2.appendhold(gr2delay1)
gr3.appendhold(gr3delay1)
gr1.linear(gr1pow1,gr1ramp1)
gr2.linear(gr2pow1,gr2ramp1)
gr3.linear(gr3pow1,gr3ramp1)

# Bfield, IR, and Green are at intermediate value. Time elapsed is == intermediate_dt
intermediate_dt = max( fval(GR1Param + 'delay1') + fval(GR1Param + 'rampdt1'), \
                    fval(GR2Param + 'delay1') + fval(GR2Param + 'rampdt1'), \
                    fval(GR3Param + 'delay1') + fval(GR3Param + 'rampdt1'), \
                    fval(IR1Param + 'delay1') + fval(IR1Param + 'rampdt1'), \
                    fval(IR2Param + 'delay1') + fval(IR2Param + 'rampdt1'), \
                    fval(IR2Param + 'delay1') + fval(IR2Param + 'rampdt1'), \
                    fval('brampdt1')  + fval('brampdelay1'))

# Make them all equal length
bfield.extend(intermediate_dt)
ir1.extend(intermediate_dt)
ir2.extend(intermediate_dt)
ir3.extend(intermediate_dt)
gr1.extend(intermediate_dt)
gr2.extend(intermediate_dt)
gr3.extend(intermediate_dt)



#Ramp IR, Green and field to final value

ir1ramp2 = float(report['LATTICEBRAGGFIELD'][IR1Param + 'rampdt2'])
ir2ramp2 = float(report['LATTICEBRAGGFIELD'][IR2Param + 'rampdt2'])
ir3ramp2= float(report['LATTICEBRAGGFIELD'][IR3Param + 'rampdt2'])
ir1delay2 = float(report['LATTICEBRAGGFIELD'][IR1Param + 'delay2'])
ir2delay2 = float(report['LATTICEBRAGGFIELD'][IR2Param + 'delay2'])
ir3delay2 = float(report['LATTICEBRAGGFIELD'][IR3Param + 'delay2'])
ir1pow2 = float(report['LATTICEBRAGGFIELD'][IR1Param + 'pow2'])
ir2pow2 = float(report['LATTICEBRAGGFIELD'][IR2Param + 'pow2'])
ir3pow2 = float(report['LATTICEBRAGGFIELD'][IR3Param + 'pow2'])

ir1.appendhold(ir1delay2)
ir2.appendhold(ir2delay2)
ir3.appendhold(ir3delay2)
ir1.linear(ir1pow2,ir1ramp2 )
ir2.linear(ir2pow2,ir2ramp2)
ir3.linear(ir3pow2,ir3ramp2)

gr1delay2 = float(report['LATTICEBRAGGFIELD'][GR1Param + 'delay2'])
gr2delay2 = float(report['LATTICEBRAGGFIELD'][GR2Param + 'delay2'])
gr3delay2 = float(report['LATTICEBRAGGFIELD'][GR3Param + 'delay2'])
gr1ramp2 = float(report['LATTICEBRAGGFIELD'][GR1Param + 'rampdt2'])
gr2ramp2 = float(report['LATTICEBRAGGFIELD'][GR2Param + 'rampdt2'])
gr3ramp2 = float(report['LATTICEBRAGGFIELD'][GR3Param + 'rampdt2'])
gr1pow2 = float(report['LATTICEBRAGGFIELD'][GR1Param + 'pow2'])
gr2pow2 = float(report['LATTICEBRAGGFIELD'][GR2Param + 'pow2'])
gr3pow2 = float(report['LATTICEBRAGGFIELD'][GR3Param + 'pow2'])

gr1.appendhold(gr1delay2)
gr2.appendhold(gr2delay2)
gr3.appendhold(gr3delay2)
gr1.linear(gr1pow2,gr1ramp2)
gr2.linear(gr2pow2,gr2ramp2)
gr3.linear(gr3pow2,gr3ramp2)


brampdt2 = float(report['LATTICEBRAGGFIELD']['brampdt2'])
brampdelay2 = float(report['LATTICEBRAGGFIELD']['brampdelay2'])
bstage2 = float(report['LATTICEBRAGGFIELD']['bstage2'])
bfield.appendhold(brampdelay2)
bfield.linear(bstage2,brampdt2)
bfile2rampdt = bfield.dt()

# Bfield, IR, and Green are at final value. Time elapsed is == intermediate_dt2
intermediate_dt2 = max(gr1delay2+gr1ramp2,gr2delay2+gr2ramp2,gr3delay2+gr3ramp2,ir1delay2+ir1ramp2,ir2delay2+ir2ramp2,ir2delay2+ir2ramp2,brampdt2+brampdelay2)
# Make them all equal length
bfield.extend(intermediate_dt+intermediate_dt2)
ir1.extend(intermediate_dt+intermediate_dt2)
ir2.extend(intermediate_dt+intermediate_dt2)
ir3.extend(intermediate_dt+intermediate_dt2)
gr1.extend(intermediate_dt+intermediate_dt2)
gr2.extend(intermediate_dt+intermediate_dt2)
gr3.extend(intermediate_dt+intermediate_dt2)

#Bfield, IR, and Green are all equal length == intermediate_dt + intermediate_dt2

#Wait in lattice
inlattice = float(report['LATTICEBRAGGFIELD']['inlattice'])\
#This is when we take the picture or probe with the Bragg beam
imagetime = intermediate_dt + intermediate_dt2 + inlattice

if inlattice < 200:
	separate_ramps_cuttof = 500.
else:
	separate_ramps_cuttof = 100.


imgzc = int( report['LATTICEBRAGGFIELD']['imgzc'] )

if inlattice < separate_ramps_cuttof:
	ir1.appendhold(inlattice)
	ir2.appendhold(inlattice)
	ir3.appendhold(inlattice)
	gr1.appendhold(inlattice)
	gr2.appendhold(inlattice)
	gr3.appendhold(inlattice)
	
	# Ramp field quickly down to zero crossing for imaging
	
	if imgzc == 1 : 
		bfield.extend( ir1.dt() ) 
		bfield.insertlin_cnv( float(report['ZEROCROSS']['zcbias']), 1.0, -5.0)
	
	##Ramp-down lattice to do band mapping
	# bandrampdt = float(report['LATTICEBRAGGFIELD']['bandrampdt'])
	# ir1.linear( 0., bandrampdt)
	# ir2.linear( 0., bandrampdt)
	# ir3.linear( 0., bandrampdt)
	# gr1.linear( 0., bandrampdt)
	# gr2.linear( 0., bandrampdt)
	# gr3.linear( 0., bandrampdt)

	irlockpow = float(report['LATTICEBRAGGFIELD']['irlockpow'])
	irlockpowdt = float(report['LATTICEBRAGGFIELD']['irlockpowdt'])
	ir1.insertlin_cnv( irlockpow, irlockpowdt, -irlockpowdt)
	ir2.insertlin_cnv( irlockpow, irlockpowdt, -irlockpowdt)
	ir3.insertlin_cnv( irlockpow, irlockpowdt, -irlockpowdt)

	#IR and Green have been extended with inlattice and with the lock ramp

	odtpow = odt.odt_wave('odtpow', cpowend, ir_ss)
	odtpow.appendhold( imagetime + float(report['LATTICEBRAGGFIELD']['odtdelay']))
	if int( report['LATTICEBRAGGFIELD']['odtzero'] ) == 1:
		odtpow.linear( 0.0,  float(report['LATTICEBRAGGFIELD']['odtrampdt']))

	waveforms = [ir1,ir2,ir3,gr1,gr2,gr3,bfield, odtpow]

	#ADD rf ramp
	if int(report['LATTICEBRAGGFIELD']['rf']) == 1:   
		rfmod  = wfm.wave('rfmod', 0., ir_ss)
		rfmod.appendhold( imagetime + float(report['LATTICEBRAGGFIELD']['rftime']) )
		rfmod.linear(float(report['LATTICEBRAGGFIELD']['rfvoltf']),float(report['LATTICEBRAGGFIELD']['rfpulsedt']))
		waveforms = [rfmod,ir1,ir2,ir3,gr1,gr2,gr3,bfield, odtpow]


	endtime = s.analogwfm_add(ir_ss,waveforms)
	print "...Lattice ramp time = " + str(endtime) + " ms"
else:
	# FINISH OUT FIRST SET OF RAMPS
	waveforms = [ir1,ir2,ir3,gr1,gr2,gr3,bfield]
	endtime = s.analogwfm_add(ir_ss,waveforms)
	print "...Lattice ramp time = " + str(endtime) + " ms"
	
	
	odtdelay = float(report['LATTICEBRAGGFIELD']['odtdelay'])
	odtrampdt = float(report['LATTICEBRAGGFIELD']['odtrampdt'])
	irlockpow = float(report['LATTICEBRAGGFIELD']['irlockpow'])
	irlockpowdt = float(report['LATTICEBRAGGFIELD']['irlockpowdt'])
	# PUT IN THE SECOND SET OF RAMPS, WHEN INLATTICE IS LONG
	#
	# The second set of ramps is going to contain the odt rampdown
	# and the lattice locking
	#
	if inlattice - (-odtdelay) < separate_ramps_cuttof + 50.0:
		print "---> ERROR: attempted to put ramps in the dead region, no time to load second set of ramps"
		exit(1)
	
	# Ramps start at the earliest of odtramp and irlockramp
	start2time =  min(  inlattice - (-odtdelay), inlattice - irlockpowdt )

	if start2time < separate_ramps_cuttof + 50.0:
		print "---> ERROR: attempted to put ramps in the dead region, no time to load second set of ramps"
		exit(1)
	if inlattice - start2time > 2000.0:
		print "---> ERROR: probably not enough buffer time to put in second set of ramps"
		exit(1)

	if abs(endtime - (intermediate_dt+intermediate_dt2)) > 3*ir_ss:
		print "---> ERROR: endtime for the first ramps is different that the sum of intermediate times",(endtime - (intermediate_dt+intermediate_dt2))
		exit(1)

	s.wait(endtime + start2time)
	
	print "...Building second set of ramps:"
	print "...  inlattice = %.3f " % inlattice
	print "...  start2time = %.3f " % start2time
	
	
	print "...odt ramp"
	
	odtpow = odt.odt_wave('odtpow', cpowend, ir_ss)
	odtpow.appendhold( inlattice - (-odtdelay) - start2time)
	if int( report['LATTICEBRAGGFIELD']['odtzero'] ) == 1:
		odtpow.linear(0.0, odtrampdt)
	odtpow.extend( inlattice - start2time)
	
	print "...ir ramps"
	
	ir1  = wfm.wave(IR1Param + 'pow', ir1pow2, ir_ss)
	ir2  = wfm.wave(IR2Param + 'pow', ir2pow2, ir_ss)
	ir3  = wfm.wave(IR3Param + 'pow', ir3pow2, ir_ss)
	
	ir1.appendhold( inlattice -start2time)
	ir2.appendhold( inlattice -start2time)
	ir3.appendhold( inlattice -start2time)

	
	ir1.insertlin_cnv( irlockpow, irlockpowdt, -irlockpowdt)
	ir2.insertlin_cnv( irlockpow, irlockpowdt, -irlockpowdt)
	ir3.insertlin_cnv( irlockpow, irlockpowdt, -irlockpowdt)
	
	print "...bfield ramp"
	
	bfield = wfm.wave('bfield', bstage2, ir_ss)
	bfield.extend( ir1.dt())
	
	if imgzc == 1: 
		bfield.insertlin_cnv( float(report['ZEROCROSS']['zcbias']), 1.0, -5.0)
	
	
	waveforms = [ir1,ir2,ir3,odtpow,bfield]

	endtime2 = s.analogwfm_add(ir_ss,waveforms)
	s.wait( -endtime-start2time)
	print "...Lattice ramp time (second set) = " + str(endtime) + " ms"
	

# Turn on IR lattice beams
ttldelay = 0.9
s.wait(-ttldelay)
s.wait(ir1delay1)
s.digichg('irttl1', float(report['LATTICEBRAGGFIELD'][IR1Param]) )
s.wait(-ir1delay1+ir2delay1)
s.digichg('irttl2', float(report['LATTICEBRAGGFIELD'][IR2Param]) )
s.wait(ir3delay1-ir2delay1)
s.digichg('irttl3', float(report['LATTICEBRAGGFIELD'][IR3Param]) )
s.wait(-ir3delay1)

s.wait(gr1delay1)
s.digichg('greenttl1', float(report['LATTICEBRAGGFIELD'][GR1Param]) )
s.wait(-gr1delay1+gr2delay1)
s.digichg('greenttl2', float(report['LATTICEBRAGGFIELD'][GR2Param]) )
s.wait(-gr2delay1+gr3delay1)
s.digichg('greenttl3', float(report['LATTICEBRAGGFIELD'][GR3Param]) )
s.wait(-gr3delay1)
s.wait(ttldelay)

# Go to the time of the second bfield ramp
s.wait(bfile2rampdt)
s.digichg('select2', float(report['LATTICEBRAGGFIELD']['select2']))
s.wait(-bfile2rampdt)

# Go 100 ms after the end of the second bfield ramp and turn quick2 off
s.wait(bfile2rampdt + 10.)
s.digichg('quick2', 0)
s.wait(-bfile2rampdt-10.)

# Go to the time odt turn off
odtoff_time =imagetime+float(report['LATTICEBRAGGFIELD']['odtdelay'])+float(report['LATTICEBRAGGFIELD']['odtrampdt'])
s.wait(odtoff_time)
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
s.wait(-odtoff_time)

# Go to where we take the image / probe with Brag beam
s.wait(imagetime)

# Probe Kill
if int(report['LATTICEBRAGGFIELD']['probekill']) == 1:

		
	probekilltime = float(report['LATTICEBRAGGFIELD']['probekilltime'])
	probe_kill_dt =  float(report['LATTICEBRAGGFIELD']['probekilldt'])
	s.wait(probekilltime)
	
	if int(report['LATTICEBRAGGFIELD']['probekill_hfimg2'])==1:
		s.wait(-20)
		s.digichg('hfimg2',1)
		s.wait(20)
	
	s.wait(-10)
	s.digichg('prshutter',0)
	s.wait(10)
	s.digichg('probe',1)
	s.wait(probe_kill_dt)
	s.digichg('probe',0)
	
	if int(report['LATTICEBRAGGFIELD']['probekill_hfimg2'])==1:
		s.digichg('hfimg2',0)

	s.digichg('prshutter',1)
	s.wait(-probekilltime)

# PULSE RF
if int(report['LATTICEBRAGGFIELD']['rf']) == 1: 
	rftime = float(report['LATTICEBRAGGFIELD']['rftime'])
	rfpulsedt = float(report['LATTICEBRAGGFIELD']['rfpulsedt'])
	s.wait(rftime)
	s.digichg('rfttl',1)
	s.wait(rfpulsedt)
	s.digichg('rfttl',0)
	s.wait(-rfpulsedt)
	s.wait(-rftime)
	
#BLOW AWAY SHOT WITH BRAGG
if int(report['LATTICEBRAGGFIELD']['braggkill']) == 1:
	braggkilltime = float(report['LATTICEBRAGGFIELD']['braggkilltime'])
	braggkilldt = float(report['LATTICEBRAGGFIELD']['braggkilldt'])
	s.wait( braggkilltime)
	s = manta.OpenShutterBragg(s,float(report['LATTICEBRAGGFIELD']['shutterdelay']))
	s.digichg('bragg',1)
	s.wait( braggkilldt)
	s.digichg('brshutter',1) # to close shutter
	s.digichg('bragg',0)
	s.digichg('hfimg2',int(report['LATTICEBRAGGFIELD']['hfimg2']))
	s.wait( -braggkilldt)
	s.wait( -braggkilltime )
	
	
#RELEASE FROM LATICE
latticeoff = float(report['LATTICEBRAGGFIELD']['latticeoff'])
s.wait(latticeoff)
s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)
s.wait(-latticeoff)


#TAKE PICTURES
trap_on_picture = 0

light = report['LATTICEBRAGGFIELD']['light']  # this is 'probe', 'motswitch' or 'bragg'
camera = report['LATTICEBRAGGFIELD']['camera']  # this is 'andor' or 'manta'

if light == 'bragg':
    delay = float(report['LATTICEBRAGGFIELD']['shutterdelay'])
    s = manta.OpenShutterBragg(s,delay)

if camera == 'andor':
	tof      = float(report['ANDOR']['tof'])
	exp      = float(report['ANDOR']['exp'])
	noatoms  = float(report['ANDOR']['noatoms'])
	kinetics = gen.bstr('Kinetics',report)
	print '...kinetics = ' + str(kinetics)
	if kinetics == True:
		s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
	else:
		s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)
		
elif camera == 'manta':
	texp     = float(report['MANTA']['exp'])
	noatoms  = float(report['MANTA']['noatoms'])
	#PICTURE OF ATOMS
	s=manta.MantaPicture(s, texp, light, 1)
	s.wait(noatoms)
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
	s.digichg('greenttl1',latticeon_picture*float(report['LATTICEBRAGGFIELD'][GR1Param]) )
	s.digichg('greenttl2',latticeon_picture*float(report['LATTICEBRAGGFIELD'][GR1Param]) )
	s.digichg('greenttl3',latticeon_picture*float(report['LATTICEBRAGGFIELD'][GR3Param]) )
	s.digichg('irttl1',latticeon_picture*float(report['LATTICEBRAGGFIELD'][IR1Param]) )
	s.digichg('irttl2',latticeon_picture*float(report['LATTICEBRAGGFIELD'][IR2Param]) )
	s.digichg('irttl3',latticeon_picture*float(report['LATTICEBRAGGFIELD'][IR3Param]) )
	s.wait(20.0)

	#PICTURE OF BACKGROUND
	s=manta.MantaPicture(s, texp, light, 1)
	s.wait(noatoms)
	
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
	s=manta.MantaPicture(s, texp, light, 0)
	s.wait(noatoms)
	#REFERENCE #2
	s=manta.MantaPicture(s, texp, light, 0)
	s.wait(noatoms)


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
