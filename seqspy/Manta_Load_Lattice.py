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
 
 
 
import seq, wfm, gen, cnc, odt, manta, highfield_uvmot
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
texp     = float(report['MANTA']['exp'])
noatoms  = float(report['MANTA']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)


s.digichg('hfimg',1)
s.digichg('odt7595',0)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)


# Evaporate in cross beam trap
s, endcrap = odt.crossbeam_evap(s, toENDBFIELD)


# Go to scattering length zero-crossing
evap_ss = float(report['EVAP']['evapss'])
buffer=20.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)
bias = float(report['FESHBACH']['bias'])
zcrampdt = float(report['ZEROCROSS']['zcrampdt'])
zcdt = float(report['ZEROCROSS']['zcdt'])
zcbias = float(report['ZEROCROSS']['zcbias'])
bfield = wfm.wave('bfield',bias,evap_ss)
bfield.linear(zcbias,zcrampdt)
bfield.appendhold(zcdt)
s.analogwfm_add(evap_ss,[bfield])
s.wait(zcdt+zcrampdt)


buffer=25.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)

# Ramp up IR and green beams
irramp1 = float(report['LATTICE']['irrampdt1'])
irramp2 = float(report['LATTICE']['irrampdt2'])
irramp3 = float(report['LATTICE']['irrampdt3'])
odtoverlap = float(report['LATTICE']['mantaodtoverlap'])
irdelay1 = float(report['LATTICE']['irdelay1'])
irdelay2 = float(report['LATTICE']['irdelay2'])
irdelay3 = float(report['LATTICE']['irdelay3'])

ir_ss = 0.5
ir1  = wfm.wave('ir1pow', 0., ir_ss)
ir2  = wfm.wave('ir2pow', 0., ir_ss)
ir3  = wfm.wave('ir3pow', 0., ir_ss)

ir1.appendhold(irdelay1)
ir2.appendhold(irdelay2)
ir3.appendhold(irdelay3)

ir1.linear(float(report['LATTICE']['irpow1']),irramp1)
ir2.linear(float(report['LATTICE']['irpow2']),irramp2)
ir3.linear(float(report['LATTICE']['irpow3']),irramp3)

gr1  = wfm.wave('greenpow1', 0., ir_ss)
gr2  = wfm.wave('greenpow2', 0., ir_ss)
gr3  = wfm.wave('greenpow3', 0., ir_ss)

grdelay1 = float(report['LATTICE']['grdelay1'])
grdelay2 = float(report['LATTICE']['grdelay2'])
grdelay3 = float(report['LATTICE']['grdelay3'])

gr1.appendhold(grdelay1)
gr2.appendhold(grdelay2)
gr3.appendhold(grdelay3)

grramp1 = float(report['LATTICE']['grrampdt1'])
grramp2 = float(report['LATTICE']['grrampdt2'])
grramp3 = float(report['LATTICE']['grrampdt3'])
gr1.linear(float(report['LATTICE']['grpow1']),grramp1)
gr2.linear(float(report['LATTICE']['grpow2']),grramp2)
gr3.linear(float(report['LATTICE']['grpow3']),grramp3)

dt_lattice_on = s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3])

# Turn on IR lattice beams
s.wait(irdelay1)
s.digichg('irttl1', float(report['LATTICE']['ir1']) )
s.wait(-irdelay1+irdelay2)
s.digichg('irttl2', float(report['LATTICE']['ir2']) )
s.wait(-irdelay2+irdelay3)
s.digichg('irttl3', float(report['LATTICE']['ir3']) )
s.wait(-irdelay3)


s.wait(grdelay1)
s.digichg('greenttl1', float(report['LATTICE']['gr1']) )
s.wait(-grdelay1+grdelay2)
s.digichg('greenttl2', float(report['LATTICE']['gr2']) )
s.wait(-grdelay2+grdelay3)
s.digichg('greenttl3', float(report['LATTICE']['gr3']) )
s.wait(-grdelay3)


# Wait some time in the lattice
s.wait(dt_lattice_on)
inlattice = float(report['LATTICE']['inlattice'])
s.wait(inlattice)


# Go to zero field so we can do fluorescence imaging with the MOT
evap_ss = float(report['EVAP']['evapss'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)
zerorampdt = 50.0
zerodt = 50.0

bfield = wfm.wave('bfield',zcbias,evap_ss)
bfield.linear(0.0,zerorampdt)
bfield.appendhold(zerodt)

repdet = wfm.wave('repdet', float(report['CNC']['repdetf']), evap_ss)
repdet.linear( float(report['MANTA']['imgdettrap']), zerorampdt )
repdet.appendhold(zerodt)

trapdet = wfm.wave('trapdet', float(report['CNC']['trapdetf']), evap_ss)
trapdet.linear( float(report['MANTA']['imgdettrap']), zerorampdt )
trapdet.appendhold(zerodt)

reppow = wfm.wave('reppow', float(report['CNC']['reppowf']), evap_ss)
reppow.linear( float(report['MANTA']['imgpowrep']), zerorampdt )
reppow.appendhold(zerodt)

trappow = wfm.wave('trappow', float(report['CNC']['trappowf']), evap_ss)
trappow.linear( float(report['MANTA']['imgpowtrap']), zerorampdt )
trappow.appendhold(zerodt)

motpow = wfm.wave('motpow', float(report['CNC']['motpowf']), evap_ss)
motpow.linear( 1.14, zerorampdt)
motpow.appendhold(zerodt)

s.analogwfm_add(evap_ss,[bfield,repdet,trapdet,reppow, trappow, motpow])

# Go to the end of ramp and change field TTL to zero
s.wait(zerorampdt)
s.digichg('field',0)
s.wait(-zerorampdt)


# Turn off ODT
s.wait(-buffer - inlattice - dt_lattice_on)
s.wait(odtoverlap)
s.digichg('odtttl',0)
s.digichg('odt7595',0)


odtoff = float(report['LATTICE']['mantaodtoff'])
if odtoff < (-odtoverlap + buffer + inlattice + dt_lattice_on + zerorampdt + zerodt ):
    print "----> CAUTION The field will not be zero when you take the image"
    print "----> Use a larger odtoff or a larger odtoverlap"
    exit(1)
s.wait(odtoff)
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])


s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)

latticetof = float(report['LATTICE']['latticetof'])
s.wait(latticetof)



#Select fluorescence probe
probe = 'motswitch'
s=manta.OpenShuttersFluorMOT(s)

#PICTURE OF ATOMS
s=manta.MantaPicture(s, texp, probe, 1)
s.wait(noatoms)
#RELEASE FROM ODT
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.wait(50.0)
s.digichg('odtttl',1)
s.digichg('odt7595',1)
s.wait(20.0)

#PICTURE OF BACKGROUND
s=manta.MantaPicture(s, texp, probe, 1)
s.wait(noatoms)
#REFERENCE #1
s=manta.MantaPicture(s, texp, probe, 0)
s.wait(noatoms)
#REFERENCE #2
s=manta.MantaPicture(s, texp, probe, 0)
s.wait(noatoms)


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