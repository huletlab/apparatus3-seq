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
s , cpowend = odt.crossbeam_evap(s, toENDBFIELD)


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
s.wait(zcdt+zcrampdt+50.0)  #50.0 ms are added to allow field to stabilize


#RELEASE FROM ODT
s.digichg('odtttl',1)
s.digichg('odt7595',1)


odttof = float(report['MANTA']['tof'])
s.wait(odttof)
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])

#Use probe beam for fluorescence imaging
probe = 'probe'

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

s.wait(5.0)
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