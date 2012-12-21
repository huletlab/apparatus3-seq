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
latticeint  = gen.getsection('LATTICEINT')

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
irramp1 = float(report['LATTICEINT']['irrampdt1'])
irramp2 = float(report['LATTICEINT']['irrampdt2'])
irramp3 = float(report['LATTICEINT']['irrampdt3'])
irdelay1 = float(report['LATTICEINT']['irdelay1'])
irdelay2 = float(report['LATTICEINT']['irdelay2'])
irdelay3 = float(report['LATTICEINT']['irdelay3'])

ir_ss = 0.5
ir1  = wfm.wave('ir1pow', 0., ir_ss)
ir2  = wfm.wave('ir2pow', 0., ir_ss)
ir3  = wfm.wave('ir3pow', 0., ir_ss)

ir1.appendhold(irdelay1)
ir2.appendhold(irdelay2)
ir3.appendhold(irdelay3)

irservo = int(report['LATTICEINT']['irservo'])
# irservo = 0  --> -111  --> no conversion --> work in VOLTAGES
# irservo = 1  --> -11  --> conversion --> work in RECOILS
cnvflag = -11 if irservo==1 else -111 

ir1.linear(float(report['LATTICEINT']['irpow1']),irramp1, cnvflag )
ir2.linear(float(report['LATTICEINT']['irpow2']),irramp2, cnvflag )
ir3.linear(float(report['LATTICEINT']['irpow3']),irramp3, cnvflag )

gr1  = wfm.wave('greenpow1', 0., ir_ss)
gr2  = wfm.wave('greenpow2', 0., ir_ss)
gr3  = wfm.wave('greenpow3', 0., ir_ss)

grdelay1 = float(report['LATTICEINT']['grdelay1'])
grdelay2 = float(report['LATTICEINT']['grdelay2'])
grdelay3 = float(report['LATTICEINT']['grdelay3'])

gr1.appendhold(grdelay1)
gr2.appendhold(grdelay2)
gr3.appendhold(grdelay3)

grramp1 = float(report['LATTICEINT']['grrampdt1'])
grramp2 = float(report['LATTICEINT']['grrampdt2'])
grramp3 = float(report['LATTICEINT']['grrampdt3'])
gr1.linear(float(report['LATTICEINT']['grpow1']),grramp1)
gr2.linear(float(report['LATTICEINT']['grpow2']),grramp2)
gr3.linear(float(report['LATTICEINT']['grpow3']),grramp3)

ramptime = s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3])
print "...Lattice ramp time = " + str(ramptime) + " ms"

# Turn on IR lattice beams
s.wait(irdelay1)
s.digichg('irttl1', float(report['LATTICEINT']['ir1']) )
s.wait(-irdelay1+irdelay2)
s.digichg('irttl2', float(report['LATTICEINT']['ir2']) )
s.wait(irdelay3-irdelay2)
s.digichg('irttl3', float(report['LATTICEINT']['ir3']) )
s.wait(-irdelay3)

s.wait(grdelay1)
s.digichg('greenttl1', float(report['LATTICEINT']['gr1']) )
s.wait(-grdelay1+grdelay2)
s.digichg('greenttl2', float(report['LATTICEINT']['gr2']) )
s.wait(-grdelay2+grdelay3)
s.digichg('greenttl3', float(report['LATTICEINT']['gr3']) )
s.wait(-grdelay3)

# Go to the end of the lattice turn on
s.wait(ramptime)

# Wait after lattice is ramped up
inlattice = float(report['LATTICEINT']['inlattice'])
s.wait(inlattice)


# Go to scattering length zero-crossing
evap_ss = float(report['EVAP']['evapss'])
# Time needed to re-latch the trigger for the AOUTS
if inlattice < 20:
    buffer = 20.0
else:
    buffer = 0.
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





#Testing if field gradient is holding the atoms tightly in the Top/Bottom beam
#~ zcwait = 50.0
#~ zerorampdt = 50.0
#~ zerodt = 50.0
#~ bfield = wfm.wave('bfield',zcbias,evap_ss)
#~ bfield.linear(zcbias,zerorampdt)
#~ bfield.appendhold(zerodt)
#~ bfield.linear(zcbias,zerorampdt)
#~ s.wait(zcwait)
#~ s.analogwfm_add(evap_ss,[bfield])
#~ s.wait(-zcwait)

if latticeint.flicker == 1:
    s.wait(-latticeint.flickerdt)
    s.digichg('odtttl',0)
    s.wait(latticeint.flickerdt)
    s.digichg('odtttl',1)


#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
inzc = float(report['LATTICEINT']['inzc'])
s.wait(inzc)

#RELEASE FROM ODT
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])

odtoff = float(report['LATTICEINT']['odtoff'])
s.wait(odtoff)
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
if latticeint.flicker ==1:  
    s.digichg('greenttl1',0)
    s.digichg('greenttl2',0)
    s.digichg('greenttl3',0)
    s.digichg('irttl1',0)
    s.digichg('irttl2',0)
    s.digichg('irttl3',0)
s.wait(-odtoff)


s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)

latticetof = float(report['LATTICEINT']['latticetof'])
s.wait(latticetof)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
trap_on_picture = 0

kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)
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