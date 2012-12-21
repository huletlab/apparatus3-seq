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
 
 
 
import seq, wfm, gen, cnc, odt, manta, highfield_uvmot, andor
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


# Go to zero field so we can do fluorescence imaging with the MOT
evap_ss = float(report['EVAP']['evapss'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)
bias = float(report['FESHBACH']['bias'])
zerorampdt = 50.0
zerodt = 50.0

bfield = wfm.wave('bfield',bias,evap_ss)
bfield.linear(0.0,zerorampdt)
bfield.appendhold(zerodt)
#zcbias = float(report['ZEROCROSS']['zcbias'])
#bfield.linear(0.0,zerorampdt)

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

s.wait(zerorampdt)
s.digichg('field',0)
s.wait(zerodt)

s=manta.OpenShuttersFluorMOT(s)
s.wait(100.0) #wait 50.0 at zero field to stabilize



#RELEASE FROM ODT
s.digichg('odtttl',0)
s.digichg('odt7595',0)

odttof = float(report['MANTA']['tof'])
s.wait(odttof)
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])

#Select fluorescence probe
probe = 'motswitch'


#~ #TAKE PICTURES
#~ #light = 'probe'
#~ light = 'motswitch'
#~ #light = 'bragg'
#~ trap_on_picture = 1
#~ kinetics = gen.bstr('Kinetics',report)
#~ print '...kinetics = ' + str(kinetics)
#~ if kinetics == True:
    #~ s,SERIESDT = andor.KineticSeries4(s,texp,light,noatoms, trap_on_picture)
#~ else:
    #~ s,SERIESDT = andor.FKSeries2(s,stepsize,texp,light,noatoms, trap_on_picture)

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