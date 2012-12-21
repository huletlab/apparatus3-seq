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

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)


s.digichg('hfimg',1)
s.digichg('odt7595',0)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)


# Evaporate in cross beam trap and into the lattice
s = odt.crossbeam_evap_into_lattice(s, toENDBFIELD)


# Wait after lattice is ramped up
inlattice = float(report['INTOLATTICE']['inlattice'])
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


#RELEASE FROM ODT
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])

odtoff = float(report['INTOLATTICE']['odtoff'])
s.wait(odtoff)
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
s.wait(-odtoff)


#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
inzc = float(report['INTOLATTICE']['inzc'])
s.wait(inzc)


s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)

latticetof = float(report['INTOLATTICE']['latticetof'])
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