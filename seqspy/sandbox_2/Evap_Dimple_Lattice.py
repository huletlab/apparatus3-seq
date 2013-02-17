__author__ = "Pedro M Duarte"

import sys
import os
import shutil

#Use this line to use the parameters in seq/benchmark/report_benchamr.INI and the output expseq.txt will located at the benchmark folder as well
#sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]+'/benchmark')


sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] )
import seqconf
for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)

import time
t0=time.time()

import math
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot, manta, lattice

#REPORT
report=gen.getreport()

    
#GET SECTION CONTENTS
DIMPLE = gen.getsection('DIMPLE')
EVAP   = gen.getsection('EVAP')
FB     = gen.getsection('FESHBACH')
ZC     = gen.getsection('ZEROCROSS')
ANDOR  = gen.getsection('ANDOR')
DL     = gen.getsection('DIMPLELATTICE')
MANTA  = gen.getsection('MANTA')

print '...Compilation = %.2f seconds\n' % (time.time()-t0)


#SEQUENCE
stepsize = float(report['SEQ']['stepsize'])
s=seq.sequence(stepsize)
s=gen.initial(s)
s.digichg('hfimg',1)
s.digichg('odt7595',0)

#Get hfimg ready
s.digichg('hfimg',1)

#If using analoghfimg get it ready
if ANDOR.analoghfimg == 1:
	s.digichg('analogimgttl',1)


print '...Compilation = %.2f seconds\n' % (time.time()-t0)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)


print '...Compilation = %.2f seconds\n' % (time.time()-t0)


# Evaporate into the dimple 
s, cpowend = odt.crossbeam_dimple_evap(s, toENDBFIELD)


print '...Compilation = %.2f seconds\n' % (time.time()-t0)


# Ramp up the lattice
s = lattice.dimple_to_lattice(s,cpowend)


print '...Compilation = %.2f seconds\n' % (time.time()-t0)


#########################################
## OTHER TTL EVENTS: probekill, braggkill, rf, quick2
#########################################
# Probe Kill
if DL.probekill == 1:
	s.wait(DL.probekilltime)
	
	s.wait(-10)
	s.digichg('prshutter',0)
	s.wait(10)
	s.digichg('probe',1)
	s.wait(DL.probekilldt)
	s.digichg('probe',0)

	s.digichg('prshutter',1)
	s.wait(-DL.probekilltime)

# Pulse RF
if DL.rf == 1:
	s.wait(DL.rftime)
	s.digichg('rfttl',1)
	s.wait(DL.rfpulsedt)
	s.digichg('rfttl',0)
	s.wait(-DL.rfpulsedt)
	s.wait(-DL.rftime)
	
# Braggkill
if DL.braggkill == 1:
	s.wait( DL.braggkilltime)
	
	s = manta.OpenShutterBragg(s,DL.shutterdelay)
	s.digichg('bragg',1)
	s.wait( DL.braggkilldt)
	s.digichg('brshutter',1) # to close shutter
	s.digichg('bragg',0)
	
	s.wait( -DL.braggkilldt)
	s.wait( -DL.braggkilltime )


# QUICK2
if DL.quick2 == 1:
    s.wait( DL.quick2time)
    s.digichg('quick2',1)
    s.wait(-DL.quick2time)
    


#########################################
## TTL RELEASE FROM ODT and LATTICE
#########################################
#RELEASE FROM LATICE
if DL.tof <= 0.:
    s.wait(1.0)
s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)
#RELEASE FROM IR TRAP
s.digichg('odtttl',0)
if DL.tof <= 0.:
    s.wait(-1.0)

s.wait(DL.tof)


#########################################
## PICTURES
#########################################

#INDICATE WHICH CHANNELS ARE TO BE CONSIDERED FOR THE BACKGROUND
bg = ['odtttl','irttl1','irttl2','irttl3','greenttl1','greenttl2','greenttl3']
bgdict={}
for ch in bg:
    bgdict[ch] = s.digistatus(ch)

print '...Compilation = %.2f seconds\n' % (time.time()-t0)

#TAKE PICTURES
#####light = this is 'probe', 'motswitch' or 'bragg'
#####camera = this is 'andor' or 'manta'
if DL.light == 'bragg':
    s = manta.OpenShutterBragg(s,DL.shutterdelay)

if DL.camera == 'andor':
	s,SERIESDT = andor.KineticSeries4_SmartBackground(s,ANDOR.exp, DL.light,ANDOR.noatoms, bg)
		
elif DL.camera == 'manta':
	#PICTURE OF ATOMS
	s=manta.MantaPicture(s, MANTA.exp, DL.light, 1)
	s.wait(MANTA.noatoms)
	#RELEASE FROM ODT AND LATTICE
	s.digichg('quick2',0)
	s.digichg('field',0)
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
	
	#RESTORE LIGHTS FOR BACKGROUND
	for key in bgdict.keys():
		s.digichg( key, bgdict[key])
		
	s.wait(20.0)

	#PICTURE OF BACKGROUND
	s=manta.MantaPicture(s, MANTA.exp, DL.light, 1)
	s.wait(MANTA.noatoms)
	
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
	s=manta.MantaPicture(s, MANTA.exp, DL.light, 0)
	s.wait(MANTA.noatoms)
	#REFERENCE #2
	s=manta.MantaPicture(s, MANTA.exp, DL.light, 0)
	s.wait(MANTA.noatoms)



#After taking a picture sequence returns at time of the last probe strobe
#Wait 50ms to get past the end
s.wait(50.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

print '...Compilation = %.2f seconds\n' % (time.time()-t0)


outputfile = seqconf.seqtxtout() 
s.save( outputfile )

shutil.copyfile( outputfile,  __file__.split('.')[0]+'.txt')

s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)