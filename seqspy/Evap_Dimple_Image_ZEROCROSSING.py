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

#REPORT
report=gen.getreport()

    
#GET SECTION CONTENTS
DIMPLE = gen.getsection('DIMPLE')
EVAP = gen.getsection('EVAP')
FB = gen.getsection('FESHBACH')
ZC   = gen.getsection('ZEROCROSS')
ANDOR= gen.getsection('ANDOR')


#SEQUENCE
stepsize = float(report['SEQ']['stepsize'])
s=seq.sequence(stepsize)
s=gen.initial(s)
s.digichg('hfimg',1)
s.digichg('odt7595',0)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)


# Evaporate into the dimple 
s, cpowend = odt.crossbeam_dimple_evap(s, toENDBFIELD)

ir_p0 = DIMPLE.ir_pow
gr_p0 = DIMPLE.gr_pow


#---Go to scattering length zero-crossing after
if DIMPLE.zct0 < 20:
    buffer = 20.0
    s.wait(buffer)
else:
    s.wait(DIMPLE.zct0)


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


fieldF = EVAP.fieldrampfinal if DIMPLE.image > EVAP.fieldrampt0 else FB.bias
bfield = wfm.wave('bfield', fieldF, EVAP.evapss)
bfield.linear(ZC.zcbias, ZC.zcrampdt)
bfield.appendhold(ZC.zcdt)
s.analogwfm_add(EVAP.evapss,[bfield])
s.wait(ZC.zcdt + ZC.zcrampdt)

	
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


#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
if DIMPLE.tof <= 0.0:
    trap_on_picture = 1
else:
    trap_on_picture = 0
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)
else:
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