__author__ = "Pedro M Duarte"

import sys
import os

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
from bfieldwfm import gradient_wave
#REPORT
report=gen.getreport()

    
#GET SECTION CONTENTS
DIMPLE = gen.getsection('DIMPLE')
EVAP = gen.getsection('EVAP')
FB = gen.getsection('FESHBACH')
ZC   = gen.getsection('ZEROCROSS')
ANDOR= gen.getsection('ANDOR')
SHUNT= gen.getsection('SHUNT')


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

if EVAP.andor2 == 1:
	print "\n...SEQ:camera will be modified  in report"
	print "\tNEW  SEQ:camera = andor,andor2\n" 
	gen.save_to_report('SEQ','camera', 'andor,andor2') 



# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)


# Evaporate into the dimple 
s, cpowend = odt.crossbeam_dimple_evap(s, toENDBFIELD)




buffer = 20.
s.wait(buffer)



# Go to scattering length zero-crossing
fieldF = EVAP.fieldrampfinal if DIMPLE.image > EVAP.fieldrampt0 else FB.bias
bfield = wfm.wave('bfield', fieldF, DIMPLE.analogss)
if DIMPLE.zct0 > buffer:
    bfield.appendhold( DIMPLE.zct0 - buffer)
bfield.linear(ZC.zcbias, ZC.zcrampdt)
bfield.appendhold(ZC.zcdt)

#~ shunt = wfm.wave('gradientfield', DIMPLE.finalV, DIMPLE.analogss)
#~ shunt.extend( odtpow.dt() ) 
#~ shunt.appendhold( DIMPLE.zct0 )
#~ shunt.linear( DIMPLE.zcV, ZC.zcrampdt)
#~ shunt.appendhold(ZC.zcdt)

# Add waveforms
gradient = gradient_wave('gradientfield', 0.0, bfield.ss,volt=0)
gradient.follow( bfield)
s.analogwfm_add(DIMPLE.analogss,[bfield,gradient])

s.wait( bfield.dt())

if math.fabs(DIMPLE.odt_pow) < 0.001:
    s.digichg('odtttl',0)

s.wait( DIMPLE.zct0 )

#At this point turn on the shunt servoing
#~ s.wait(5.0)
#~ s.digichg('gradientfieldttl', SHUNT.shuntttl)
#~ s.wait(-5.0)

#If ZC ramp needs to go up, then help it with a quick
if ( EVAP.use_field_ramp != 1 or  DIMPLE.image < EVAP.fieldrampt0):
	
	s.wait(-12.0)
	s.digichg('hfquick',1)
	s.digichg('quick',1)
	s.wait(12.0)
	
	#for safety turn this back off a little later
	s.wait(150.0)
	s.digichg('hfquick',0)
	s.digichg('quick',0)
	s.wait(-150.0)

s.wait(ZC.zcrampdt + ZC.zcdt)





	
#########################################
## TTL RELEASE FROM ODT and LATTICE
#########################################
#RELEASE FROM LATICE
s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)
#RELEASE FROM IR TRAP
s.digichg('odtttl',0)
s.wait(DIMPLE.tof)


#########################################
## PICTURES
#########################################

#INDICATE WHICH CHANNELS ARE TO BE CONSIDERED FOR THE BACKGROUND
bg = ['odtttl','irttl1','irttl2','irttl3','greenttl1','greenttl2','greenttl3']
bgdict={}
for ch in bg:
    bgdict[ch] = s.digistatus(ch)


#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'

kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
	s,SERIESDT = andor.KineticSeries4_SmartBackground(s,ANDOR.exp, light,ANDOR.noatoms, bg,trigger='cameratrig')
	if EVAP.andor2 == 1:
		s.wait(-SERIESDT)
		s,SERIESDT = andor.KineticSeries4_SmartBackground(s,ANDOR.exp, light,ANDOR.noatoms, bg,trigger='cameratrig2')
else:
	if EVAP.andor2 == 1:
		sys.exit("Warning! The part of code with andor2 and kinetcs off has not been done.")
	s,SERIESDT = andor.FKSeries2(s,SEQ.stepsize,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)


#After taking a picture sequence returns at time of the last probe strobe
#Wait 50ms to get past the end
s.wait(50.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)


import seqconf
s.save( seqconf.seqtxtout() )
s.save( __file__.split('.')[0]+'.txt')

s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)