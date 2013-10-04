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


#---GET SECTION CONTENTS
SEQ   = gen.getsection('SEQ')
EVAP  = gen.getsection('EVAP')
ANDOR = gen.getsection('ANDOR')
ODT   = gen.getsection('ODT')
FB    = gen.getsection('FESHBACH')
ZC    = gen.getsection('ZEROCROSS')
LI     = gen.getsection('LATTICEINT')

#---SEQUENCE
s=seq.sequence(SEQ.stepsize)
s=gen.initial(s)

#Get hfimg ready
s.digichg('hfimg',1)

#If using analoghfimg get it ready
if ANDOR.analoghfimg == 1:
	s.digichg('analogimgttl',1)


s.digichg('odt7595',0)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)


# Evaporate in cross beam trap
if EVAP.lattice == 1:
    s, cpowend = odt.crossbeam_evap_field_into_lattice(s, toENDBFIELD)
    ir_p0 = EVAP.irpow
    gr_p0 = EVAP.grpow
else:
    s, cpowend = odt.crossbeam_evap_field(s, toENDBFIELD)
    ir_p0 =0.
    gr_p0 =0.



buffer=25.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)


# Ramp up IR and GR beams
ir_ss = 0.5
def rampupcnv( ch, delay, pow, ramp, cnvflag):
    w = wfm.wave( ch, 0., ir_ss)
    w.appendhold( delay)
    w.linear( pow, ramp, cnvflag)
    return w
    
def rampup( ch, delay, pow, ramp):
    w = wfm.wave( ch, 0., ir_ss)
    w.appendhold( delay)
    w.linear( pow, ramp)
    return w
    
irservo = int(LI.irservo)
# irservo = 0  --> -111  --> no conversion --> work in VOLTAGES
# irservo = 1  --> -11  --> conversion --> work in RECOILS
cnvflag = -11 if irservo==1 else -111 
    
ir1 = rampupcnv( 'ir1pow', LI.irdelay1, LI.irpow1, LI.irrampdt1, cnvflag)
ir2 = rampupcnv( 'ir2pow', LI.irdelay2, LI.irpow2, LI.irrampdt2, cnvflag)
ir3 = rampupcnv( 'ir3pow', LI.irdelay3, LI.irpow3, LI.irrampdt3, cnvflag)

gr1 = rampup( 'greenpow1', LI.grdelay1, LI.grpow1, LI.grrampdt1)
gr2 = rampup( 'greenpow2', LI.grdelay2, LI.grpow2, LI.grrampdt2)
gr3 = rampup( 'greenpow3', LI.grdelay3, LI.grpow3, LI.grrampdt3)


ramptime = s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3])
print "...Lattice ramp time = " + str(ramptime) + " ms"


# Turn on IR, GR TTLs
def ttlon( delay, ch, bool):
    s.wait(delay)
    s.digichg( ch, bool)
    s.wait(-delay)

ttlon( LI.irdelay1, 'irttl1', LI.ir1)
ttlon( LI.irdelay2, 'irttl2', LI.ir2)
ttlon( LI.irdelay3, 'irttl3', LI.ir3)
ttlon( LI.grdelay1, 'greenttl1', LI.gr1)
ttlon( LI.grdelay2, 'greenttl2', LI.gr2)
ttlon( LI.grdelay3, 'greenttl3', LI.gr3)


# Go to the end of the lattice turn on
s.wait(ramptime)

# Wait after lattice is ramped up
s.wait(LI.inlattice)


#---Go to scattering length zero-crossing
if LI.inlattice < 20:
    buffer = 20.0
else:
    buffer = 0.
s.wait(buffer)


fieldF = EVAP.fieldrampfinal if EVAP.image > EVAP.fieldrampt0 else FB.bias
bfield = wfm.wave('bfield', fieldF, EVAP.evapss)
bfield.linear(ZC.zcbias, ZC.zcrampdt)
bfield.appendhold(ZC.zcdt)

gradient = odt.gradient_wave('gradientfield', 0.0, bfield.ss,volt = 0.0)
gradient.follow( bfield)

s.analogwfm_add(EVAP.evapss,[bfield,gradient])
s.wait(ZC.zcdt + ZC.zcrampdt)


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

if LI.flicker == 1:
    s.wait(-LI.flickerdt)
    s.digichg('odtttl',0)
    s.wait(LI.flickerdt)
    s.digichg('odtttl',1)


s.wait(LI.inzc)

#RELEASE FROM ODT
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])


s.wait(LI.odtoff)
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
if LI.flicker ==1:  
    s.digichg('greenttl1',0)
    s.digichg('greenttl2',0)
    s.digichg('greenttl3',0)
    s.digichg('irttl1',0)
    s.digichg('irttl2',0)
    s.digichg('irttl3',0)
s.wait(-LI.odtoff)


s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)

s.wait(LI.latticetof)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
trap_on_picture = 0

kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)
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