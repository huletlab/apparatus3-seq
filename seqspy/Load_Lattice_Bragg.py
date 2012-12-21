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

# Ramp up IR and green beams
irramp1 = float(report['LATTICEBRAGG']['irrampdt1'])
irramp2 = float(report['LATTICEBRAGG']['irrampdt2'])
irramp3 = float(report['LATTICEBRAGG']['irrampdt3'])
irdelay1 = float(report['LATTICEBRAGG']['irdelay1'])
irdelay2 = float(report['LATTICEBRAGG']['irdelay2'])
irdelay3 = float(report['LATTICEBRAGG']['irdelay3'])

ir_ss = 0.1


bias = float(report['FESHBACH']['bias'])
zcrampdt = float(report['LATTICEBRAGG']['zcrampdt'])
zcbias = float(report['ZEROCROSS']['zcbias'])
bfield = wfm.wave('bfield',bias,ir_ss)
zcdelay = float(report['LATTICEBRAGG']['zcdelay'])
bfield.appendhold( zcdelay) 
bfield.linear(zcbias,zcrampdt)

odtpow = odt.odt_wave('odtpow', cpowend, ir_ss)
odtpow.appendhold( float(report['LATTICEBRAGG']['odtdelay']))
odtpow.linear( 0.0,  float(report['LATTICEBRAGG']['odtrampdt']))

ir1  = wfm.wave('ir1pow', 0., ir_ss)
ir2  = wfm.wave('ir2pow', 0., ir_ss)
ir3  = wfm.wave('ir3pow', 0., ir_ss)

ir1.appendhold(irdelay1)
ir2.appendhold(irdelay2)
ir3.appendhold(irdelay3)

ir1.linear(float(report['LATTICEBRAGG']['irpow1']),irramp1)
ir2.linear(float(report['LATTICEBRAGG']['irpow2']),irramp2)
ir3.linear(float(report['LATTICEBRAGG']['irpow3']),irramp3)

gr1  = wfm.wave('greenpow1', 0., ir_ss)
gr2  = wfm.wave('greenpow2', 0., ir_ss)
gr3  = wfm.wave('greenpow3', 0., ir_ss)

grdelay1 = float(report['LATTICEBRAGG']['grdelay1'])
grdelay2 = float(report['LATTICEBRAGG']['grdelay2'])
grdelay3 = float(report['LATTICEBRAGG']['grdelay3'])

gr1.appendhold(grdelay1)
gr2.appendhold(grdelay2)
gr3.appendhold(grdelay3)

grramp1 = float(report['LATTICEBRAGG']['grrampdt1'])
grramp2 = float(report['LATTICEBRAGG']['grrampdt2'])
grramp3 = float(report['LATTICEBRAGG']['grrampdt3'])
gr1.linear(float(report['LATTICEBRAGG']['grpow1']),grramp1)
gr2.linear(float(report['LATTICEBRAGG']['grpow2']),grramp2)
gr3.linear(float(report['LATTICEBRAGG']['grpow3']),grramp3)


#Wait in lattice
inlattice = float(report['LATTICEBRAGG']['inlattice'])
ir1.appendhold(inlattice)
ir2.appendhold(inlattice)
ir3.appendhold(inlattice)
gr1.appendhold(inlattice)
gr2.appendhold(inlattice)
gr3.appendhold(inlattice)

##Ramp-down lattice to do band mapping
# bandrampdt = float(report['LATTICEBRAGG']['bandrampdt'])
# ir1.linear( 0., bandrampdt)
# ir2.linear( 0., bandrampdt)
# ir3.linear( 0., bandrampdt)
# gr1.linear( 0., bandrampdt)
# gr2.linear( 0., bandrampdt)
# gr3.linear( 0., bandrampdt)



#endtime = s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3,bfield, odtpow])
endtime = s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3,bfield])
print "...Lattice ramp time = " + str(endtime) + " ms"

# Turn on IR lattice beams
s.wait(irdelay1)
s.digichg('irttl1', float(report['LATTICEBRAGG']['ir1']) )
s.wait(-irdelay1+irdelay2)
s.digichg('irttl2', float(report['LATTICEBRAGG']['ir2']) )
s.wait(irdelay3-irdelay2)
s.digichg('irttl3', float(report['LATTICEBRAGG']['ir3']) )
s.wait(-irdelay3)

s.wait(grdelay1)
s.digichg('greenttl1', float(report['LATTICEBRAGG']['gr1']) )
s.wait(-grdelay1+grdelay2)
s.digichg('greenttl2', float(report['LATTICEBRAGG']['gr2']) )
s.wait(-grdelay2+grdelay3)
s.digichg('greenttl3', float(report['LATTICEBRAGG']['gr3']) )
s.wait(-grdelay3)

# Go to the end of the lattice turn on
s.wait(endtime)

#RELEASE FROM ODT
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
odtoff = float(report['LATTICEBRAGG']['odtoff'])
s.wait(odtoff)
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
s.wait(-odtoff)

#RELEASE FROM LATICE
latticeoff = float(report['LATTICEBRAGG']['latticeoff'])
s.wait(latticeoff)
s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)
s.wait(-latticeoff)

#BLOW AWAY SHOT WITH BRAGG
if int(report['LATTICEBRAGG']['braggkill']) == 1:
	braggkilltime = float(report['LATTICEBRAGG']['braggkilltime'])
	braggkilldt = float(report['LATTICEBRAGG']['braggkilldt'])
	s.wait( braggkilltime)
	s = manta.OpenShutterBragg(s,float(report['LATTICEBRAGG']['shutterdelay']))
	s.digichg('bragg',1)
	s.wait( braggkilldt)
	s.digichg('bragg',0)
	s.wait( -braggkilldt)
	s.wait( -braggkilltime )
	



#TAKE PICTURES
trap_on_picture = 0

light = report['LATTICEBRAGG']['light']  # this is 'probe', 'motswitch' or 'bragg'
camera = report['LATTICEBRAGG']['camera']  # this is 'andor' or 'manta'

if light == 'bragg':
    delay = float(report['LATTICEBRAGG']['shutterdelay'])
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
	odton_picture = 0 if odtoff <= 0.  else 1 
	latticeon_picture = 0 if latticeoff <= 0. else 1
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
	s.digichg('greenttl1',0)
	s.digichg('greenttl2',0)
	s.digichg('greenttl3',0)
	s.digichg('irttl1',latticeon_picture)
	s.digichg('irttl2',latticeon_picture)
	s.digichg('irttl3',latticeon_picture)
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
s.save( __file__.split('.')[0]+'.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)