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
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot, manta, lattice, physics
from bfieldwfm import gradient_wave
#REPORT
report=gen.getreport()
gen.get_lattice_webcam_data()

    
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
if DIMPLE.Bramp == 1:
    fieldF = DIMPLE.B
else:
    fieldF = EVAP.fieldrampfinal if DIMPLE.image > EVAP.fieldrampt0 else FB.bias
bfield = wfm.wave('bfield', fieldF, DIMPLE.analogss)
if DIMPLE.zct0 > buffer:
    bfield.appendhold( DIMPLE.zct0 - buffer)
bfield.linear(ZC.zcbias, ZC.zcrampdt)
bfield.appendhold(ZC.zcdt)

# Proceed to change ANDOR:hfimg0 depending on the imaging bfield
bfieldG = physics.inv( 'bfield', bfield.y[-1] ) *6.8
hfimg0 = -1.*(100.0 + 163.7 - 1.414*bfieldG)
if ANDOR.hfimg0auto == 1: 
  gen.save_to_report('ANDOR','hfimg0', hfimg0)
  print "\tNEW  ANDOR:hfimg0 = %.2f MHz\n" %  hfimg0



#~ shunt = wfm.wave('gradientfield', DIMPLE.finalV, DIMPLE.analogss)
#~ shunt.extend( odtpow.dt() ) 
#~ shunt.appendhold( DIMPLE.zct0 )
#~ shunt.linear( DIMPLE.zcV, ZC.zcrampdt)
#~ shunt.appendhold(ZC.zcdt)

# Add waveforms
gradient = gradient_wave('gradientfield', 0.0, bfield.ss,volt=0)
gradient.follow( bfield)
s.analogwfm_add(DIMPLE.analogss,[bfield,gradient])

s.wait( bfield.dt() - ZC.zcrampdt - ZC.zcdt)

if math.fabs(DIMPLE.odt_pow) < 0.001:
    s.digichg('odtttl',0)

#s.wait( DIMPLE.zct0 )

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


#BELOW ONE CAN SELECT BETWEEN SEVERAL EXPERIMENTS ON THE DIMPLE AT ZERO INTERACTIONS


#--- Measure dimple frequencies by using gradient induced dipole oscillations
if DIMPLE.shuntnot == 1 :
    shuntval = 1 if DIMPLE.shuntttl == 0 else 0
    s.digichg('gradientfieldttl', shuntval)
    s.wait(DIMPLE.oscdt)
    
#--- Measure dimple frequencies by using a breathing mode obtained by flickering a beam
elif DIMPLE.flicker:
    s.digichg('irttl1', DIMPLE.ir1 if DIMPLE.ir1flick == 0 else 0 )
    s.digichg('irttl2', DIMPLE.ir2 if DIMPLE.ir2flick == 0 else 0 )
    s.digichg('irttl3', DIMPLE.ir3 if DIMPLE.ir3flick == 0 else 0 )
    s.wait( DIMPLE.flickdt)
    s.digichg('irttl1', 0 if DIMPLE.ir1off == 1 else DIMPLE.ir1)
    s.digichg('irttl2', 0 if DIMPLE.ir2off == 1 else DIMPLE.ir2)
    s.digichg('irttl3', 0 if DIMPLE.ir3off == 1 else DIMPLE.ir3)
    s.wait( DIMPLE.oscdt) 
    
#--- Measure dimple frequencies by using breathing mode obtained by squeezing atoms
#--- Squeezing is done using the Agilent function generator
elif DIMPLE.squeeze:
    s.digichg('latticemodttl', 1)
    agilentpulselen = 1.0
    s.wait(agilentpulselen)
    s.digichg('latticemodttl', 0)
    s.wait(-agilentpulselen)
    s.wait( DIMPLE.oscdt) 
    
#--- Measure lattice depth by lattice modulation
elif DIMPLE.latticemod == 1:
    
    #Add some buffer time to allow for ramp loading
    buffer = 20.0
    s.wait(buffer) 
    
    #First rotators are set
    lcr1  = lattice.lattice_wave('lcr1', DIMPLE.alpha1,  DIMPLE.analogss)
    lcr2  = lattice.lattice_wave('lcr2', DIMPLE.alpha2,  DIMPLE.analogss)
    lcr3  = lattice.lattice_wave('lcr3', DIMPLE.alpha3,  DIMPLE.analogss)
    
    lcr1.y = lcr1.y + DIMPLE.alphaV1
    
    
    print "...PREPARING LATTICE MOD:"
    #Then power is changed on the IR  and GR beams
    def latticepow(ch):
        ss = DIMPLE.analogss
        if 'gr' in ch:
            n=filter( str.isdigit, ch)[0]
            chname = 'greenpow' + n
            correction = DIMPLE.__dict__['gr'+n+'correct']
        else:
            chname = ch
            correction = 1.0
        #print "Start %s = %f" % (chname, DIMPLE.__dict__[ch])
        if 'gr' in ch:
            w = lattice.lattice_wave(chname, correction*DIMPLE.__dict__[ch+'2'], ss) 
        else:
            w = lattice.lattice_wave(chname, correction*DIMPLE.__dict__['allirpow'], ss) 
        
        w.appendhold( DIMPLE.lattice_t0)
        #print "Last voltage before tanhRise (%s) =  %f" % (ch,w.last())
        w.tanhRise( correction*DIMPLE.__dict__[ch+'_v0'], DIMPLE.lattice_dt, DIMPLE.ir_tau, DIMPLE.ir_shift)
        return w 

    ir1 = latticepow('ir1pow')
    ir2 = latticepow('ir2pow')
    ir3 = latticepow('ir3pow')
    
    gr1 = latticepow('gr1pow')
    gr2 = latticepow('gr2pow')
    gr3 = latticepow('gr3pow')
    
    lcr1.extend(ir1.dt())
    lcr2.extend(ir1.dt())
    lcr3.extend(ir1.dt())

    
    wfms = [lcr1,lcr2,lcr3,ir1,ir2,ir3,gr1,gr2,gr3]
    duration = s.analogwfm_add(DIMPLE.analogss,wfms)
    
    s.wait(duration) 
    
    #Modulate
    s.digichg('latticemodttl',DIMPLE.modTTL)
    s.wait(DIMPLE.latticemod_dt)
    s.digichg('latticemodttl',0)
    s.wait(DIMPLE.latticemod_hold)
    
    
    

	
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
