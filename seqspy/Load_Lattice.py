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
L     = gen.getsection('LATTICE')

#---SEQUENCE
s=seq.sequence(SEQ.stepsize)
s=gen.initial(s)

#Get hfimg ready
s.digichg('hfimg',1)

#If using analoghfimg get it ready
if ANDOR.analoghfimg == 1:
	s.digichg('analogimgttl',1)


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


#---Go to scattering length zero-crossing
buffer=20.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)

fieldF = EVAP.fieldrampfinal if EVAP.image > EVAP.fieldrampt0 else FB.bias
bfield = wfm.wave('bfield', fieldF, EVAP.evapss)
bfield.linear(ZC.zcbias, ZC.zcrampdt)
bfield.appendhold(ZC.zcdt)

gradient = odt.gradient_wave('gradientfield', 0.0, bfield.ss,volt = 0.0)
gradient.follow( bfield)

s.analogwfm_add(EVAP.evapss,[bfield,gradient])
s.wait(ZC.zcdt + ZC.zcrampdt)


buffer=25.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)



# Ramp up IR and GR beams
ir_ss = 0.5
def rampup( ch, delay, pow, ramp):
    w = wfm.wave( ch, 0., ir_ss)
    w.appendhold( delay)
    w.linear( pow, ramp)
    return w
    
ir1 = rampup( 'ir1pow', L.irdelay1, L.irpow1, L.irrampdt1)
ir2 = rampup( 'ir2pow', L.irdelay2, L.irpow2, L.irrampdt2)
ir3 = rampup( 'ir3pow', L.irdelay3, L.irpow3, L.irrampdt3)

gr1 = rampup( 'greenpow1', L.grdelay1, L.grpow1, L.grrampdt1)
gr2 = rampup( 'greenpow2', L.grdelay2, L.grpow2, L.grrampdt2)
gr3 = rampup( 'greenpow3', L.grdelay3, L.grpow3, L.grrampdt3)


#---OPTIONAL: Shut down ODT laser completely
#ipg = wfm.wave('ipganalog', 10., ir_ss)
#ipg.appendhold(odtoverlap)
#ipg.linear( 0.0, 10.0)
#s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3,ipg])

s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3])


# Turn on IR, GR TTLs
def ttlon( delay, ch, bool):
    s.wait(delay)
    s.digichg( ch, bool)
    s.wait(-delay)

ttlon( L.irdelay1, 'irttl1', L.ir1)
ttlon( L.irdelay2, 'irttl2', L.ir2)
ttlon( L.irdelay3, 'irttl3', L.ir3)
ttlon( L.grdelay1, 'greenttl1', L.gr1)
ttlon( L.grdelay2, 'greenttl2', L.gr2)
ttlon( L.grdelay3, 'greenttl3', L.gr3)



# Wait in ODT
s.wait(L.odtoverlap)


#RELEASE FROM ODT
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)


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


odtoff = float(report['LATTICE']['odtoff'])
s.wait(odtoff)
#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])

#Perform consistency checks
#if irramp < 0. or grramp < 0. or grdelay < 0. or grdelay > odtoff + odtoverlap:
#   print "----> Verify LATTICE section parameters, they have values that are not allowed"
#   exit(1)


s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)

latticetof = float(report['LATTICE']['latticetof'])
s.wait(latticetof)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
if odtoff <= 0.0:
    trap_on_picture = 1
else:
    trap_on_picture = 0

kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,SEQ.stepsize,ANDOR.exp,light,ANDOR.noatoms, trap_on_picture)
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