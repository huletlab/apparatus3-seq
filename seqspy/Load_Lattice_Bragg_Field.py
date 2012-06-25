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
 
 
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot, manta
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])


#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)


s.digichg('hfimg',1)
s.digichg('odt7595',0)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)


# Evaporate in cross beam trap
s, cpowend = odt.crossbeam_evap(s, toENDBFIELD)


buffer=25.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)


ir_ss = 0.1

# Ramp B Field to intermediate value 
bias = float(report['FESHBACH']['bias'])
brampdt1 = float(report['LATTICEBRAGGFIELD']['brampdt1'])
brampdelay1 = float(report['LATTICEBRAGGFIELD']['brampdelay1'])
bstage1 = float(report['LATTICEBRAGGFIELD']['bstage1'])
bfield = wfm.wave('bfield',bias,ir_ss)
bfield.appendhold(brampdelay1)
bfield.linear(bstage1,brampdt1)





# Ramp up IR and green beams to intermediate value 
ir1ramp1 = float(report['LATTICEBRAGGFIELD']['ir1rampdt1'])
ir2ramp1 = float(report['LATTICEBRAGGFIELD']['ir2rampdt1'])
ir3ramp1 = float(report['LATTICEBRAGGFIELD']['ir3rampdt1'])
ir1delay1 = float(report['LATTICEBRAGGFIELD']['ir1delay1'])
ir2delay1 = float(report['LATTICEBRAGGFIELD']['ir2delay1'])
ir3delay1 = float(report['LATTICEBRAGGFIELD']['ir3delay1'])
ir1pow1 = float(report['LATTICEBRAGGFIELD']['ir1pow1'])
ir2pow1 = float(report['LATTICEBRAGGFIELD']['ir2pow1'])
ir3pow1 = float(report['LATTICEBRAGGFIELD']['ir3pow1'])


ir1  = wfm.wave('ir1pow', 0., ir_ss)
ir2  = wfm.wave('ir2pow', 0., ir_ss)
ir3  = wfm.wave('ir3pow', 0., ir_ss)
ir1.appendhold(ir1delay1)
ir2.appendhold(ir2delay1)
ir3.appendhold(ir3delay1)
ir1.linear(ir1pow1,ir1ramp1)
ir2.linear(ir2pow1,ir2ramp1)
ir3.linear(ir3pow1,ir3ramp1)


gr1delay1 = float(report['LATTICEBRAGGFIELD']['gr1delay1'])
gr2delay1 = float(report['LATTICEBRAGGFIELD']['gr2delay1'])
gr3delay1 = float(report['LATTICEBRAGGFIELD']['gr3delay1'])
gr1ramp1 = float(report['LATTICEBRAGGFIELD']['gr1rampdt1'])
gr2ramp1 = float(report['LATTICEBRAGGFIELD']['gr2rampdt1'])
gr3ramp1 = float(report['LATTICEBRAGGFIELD']['gr3rampdt1'])
gr1pow1 = float(report['LATTICEBRAGGFIELD']['gr1pow1'])
gr2pow1 = float(report['LATTICEBRAGGFIELD']['gr2pow1'])
gr3pow1 = float(report['LATTICEBRAGGFIELD']['gr3pow1'])


gr1  = wfm.wave('greenpow1', 0., ir_ss)
gr2  = wfm.wave('greenpow2', 0., ir_ss)
gr3  = wfm.wave('greenpow3', 0., ir_ss)
gr1.appendhold(gr1delay1)
gr2.appendhold(gr2delay1)
gr3.appendhold(gr3delay1)
gr1.linear(gr1pow1,gr1ramp1)
gr2.linear(gr2pow1,gr2ramp1)
gr3.linear(gr3pow1,gr3ramp1)

# Find the time duration of this loading stage and ramp down odt
intermediate_dt = max(gr1delay1+gr1ramp1,gr2delay1+gr2ramp1,gr3delay1+gr3ramp1,ir1delay1+ir1ramp1,ir2delay1+ir2ramp1,ir2delay1+ir2ramp1,brampdt1+brampdelay1)

bfield.extend(intermediate_dt)
ir1.extend(intermediate_dt)
ir2.extend(intermediate_dt)
ir3.extend(intermediate_dt)
gr1.extend(intermediate_dt)
gr2.extend(intermediate_dt)
gr3.extend(intermediate_dt)

odtpow = odt.odt_wave('odtpow', cpowend, ir_ss)
odtpow.appendhold( intermediate_dt+float(report['LATTICEBRAGGFIELD']['odtdelay']))
odtpow.linear( 0.0,  float(report['LATTICEBRAGGFIELD']['odtrampdt']))

#Ramp IR, Green and field to final value

ir1ramp2 = float(report['LATTICEBRAGGFIELD']['ir1rampdt2'])
ir2ramp2 = float(report['LATTICEBRAGGFIELD']['ir2rampdt2'])
ir3ramp2= float(report['LATTICEBRAGGFIELD']['ir3rampdt2'])
ir1delay2 = float(report['LATTICEBRAGGFIELD']['ir1delay2'])
ir2delay2 = float(report['LATTICEBRAGGFIELD']['ir2delay2'])
ir3delay2 = float(report['LATTICEBRAGGFIELD']['ir3delay2'])
ir1pow2 = float(report['LATTICEBRAGGFIELD']['ir1pow2'])
ir2pow2 = float(report['LATTICEBRAGGFIELD']['ir2pow2'])
ir3pow2 = float(report['LATTICEBRAGGFIELD']['ir3pow2'])

ir1.appendhold(ir1delay2)
ir2.appendhold(ir2delay2)
ir3.appendhold(ir3delay2)
ir1.linear(ir1pow2,ir1ramp2)
ir2.linear(ir2pow2,ir2ramp2)
ir3.linear(ir3pow2,ir3ramp2)

gr1delay2 = float(report['LATTICEBRAGGFIELD']['gr1delay2'])
gr2delay2 = float(report['LATTICEBRAGGFIELD']['gr2delay2'])
gr3delay2 = float(report['LATTICEBRAGGFIELD']['gr3delay2'])
gr1ramp2 = float(report['LATTICEBRAGGFIELD']['gr1rampdt2'])
gr2ramp2 = float(report['LATTICEBRAGGFIELD']['gr2rampdt2'])
gr3ramp2 = float(report['LATTICEBRAGGFIELD']['gr3rampdt2'])
gr1pow2 = float(report['LATTICEBRAGGFIELD']['gr1pow2'])
gr2pow2 = float(report['LATTICEBRAGGFIELD']['gr2pow2'])
gr3pow2 = float(report['LATTICEBRAGGFIELD']['gr3pow2'])

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

# Find the time duration of this loading stage and ramp down odt

intermediate_dt2 = max(gr1delay2+gr1ramp2,gr2delay2+gr2ramp2,gr3delay2+gr3ramp2,ir1delay2+ir1ramp2,ir2delay2+ir2ramp2,ir2delay2+ir2ramp2,brampdt2+brampdelay2)

bfield.extend(intermediate_dt+intermediate_dt2)
ir1.extend(intermediate_dt+intermediate_dt2)
ir2.extend(intermediate_dt+intermediate_dt2)
ir3.extend(intermediate_dt+intermediate_dt2)
gr1.extend(intermediate_dt+intermediate_dt2)
gr2.extend(intermediate_dt+intermediate_dt2)
gr3.extend(intermediate_dt+intermediate_dt2)



#Wait in lattice
inlattice = float(report['LATTICEBRAGGFIELD']['inlattice'])
ir1.appendhold(inlattice)
ir2.appendhold(inlattice)
ir3.appendhold(inlattice)
gr1.appendhold(inlattice)
gr2.appendhold(inlattice)
gr3.appendhold(inlattice)

##Ramp-down lattice to do band mapping
# bandrampdt = float(report['LATTICEBRAGGFIELD']['bandrampdt'])
# ir1.linear( 0., bandrampdt)
# ir2.linear( 0., bandrampdt)
# ir3.linear( 0., bandrampdt)
# gr1.linear( 0., bandrampdt)
# gr2.linear( 0., bandrampdt)
# gr3.linear( 0., bandrampdt)



endtime = s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3,bfield, odtpow])
print "...Lattice ramp time = " + str(endtime) + " ms"

# Turn on IR lattice beams
s.wait(ir1delay1)
s.digichg('irttl1', float(report['LATTICEBRAGGFIELD']['ir1']) )
s.wait(-ir1delay1+ir2delay1)
s.digichg('irttl2', float(report['LATTICEBRAGGFIELD']['ir2']) )
s.wait(ir3delay1-ir2delay1)
s.digichg('irttl3', float(report['LATTICEBRAGGFIELD']['ir3']) )
s.wait(-ir3delay1)

s.wait(gr1delay1)
s.digichg('greenttl1', float(report['LATTICEBRAGGFIELD']['gr1']) )
s.wait(-gr1delay1+gr2delay1)
s.digichg('greenttl2', float(report['LATTICEBRAGGFIELD']['gr2']) )
s.wait(-gr2delay1+gr3delay1)
s.digichg('greenttl3', float(report['LATTICEBRAGGFIELD']['gr3']) )
s.wait(-gr3delay1)

# Go to the time odt turn off

s.wait(intermediate_dt+float(report['LATTICEBRAGGFIELD']['odtdelay'])+float(report['LATTICEBRAGGFIELD']['odtrampdt']))
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
s.wait(-(intermediate_dt+float(report['LATTICEBRAGGFIELD']['odtdelay'])+float(report['LATTICEBRAGGFIELD']['odtrampdt'])))

# Go to the end of the lattice turn on
s.wait(endtime)

#RELEASE FROM LATICE
s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)

#BLOW AWAY SHOT WITH BRAGG
if int(report['LATTICEBRAGGFIELD']['braggkill']) == 1:
	braggkilltime = float(report['LATTICEBRAGGFIELD']['braggkilltime'])
	braggkilldt = float(report['LATTICEBRAGGFIELD']['braggkilldt'])
	s.wait( braggkilltime)
	s = manta.OpenShutterBragg(s,float(report['LATTICEBRAGGFIELD']['shutterdelay']))
	s.digichg('bragg',1)
	s.wait( braggkilldt)
	s.digichg('bragg',0)
	s.wait( -braggkilldt)
	s.wait( -braggkilltime )
	



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
	#~ odton_picture = 0 if odtoff <= 0.  else 1 
	#~ latticeon_picture = 0 if latticeoff <= 0. else 1
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
	#~ s.digichg('odtttl',odton_picture)
	#~ s.digichg('odt7595',odton_picture)
	#~ s.digichg('ipgttl',odton_picture)
	#~ s.digichg('greenttl1',0)
	#~ s.digichg('greenttl2',0)
	#~ s.digichg('greenttl3',0)
	#~ s.digichg('irttl1',latticeon_picture)
	#~ s.digichg('irttl2',latticeon_picture)
	#~ s.digichg('irttl3',latticeon_picture)
	s.wait(20.0)

	#PICTURE OF BACKGROUND
	s=manta.MantaPicture(s, texp, light, 1)
	s.wait(noatoms)
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
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)