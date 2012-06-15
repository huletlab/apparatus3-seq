"""Make sure the report file at 'Savedir/reportRunNumber.INI'
   exists otherwise this code won't compile. 
   
   Savedir and RunNumber are specified in settings.INI
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
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


# Evaporate in cross beam trap
s, cpoend= odt.crossbeam_evap(s, toENDBFIELD)


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
s.wait(zcdt+zcrampdt)


buffer=25.0 #Time needed to re-latch the trigger for the AOUTS
s.wait(buffer)

# Ramp up IR and green beams
irramp1 = float(report['LATTICE']['irrampdt1'])
irramp2 = float(report['LATTICE']['irrampdt2'])
irramp3 = float(report['LATTICE']['irrampdt3'])
odtoverlap = float(report['LATTICE']['odtoverlap'])
irdelay1 = float(report['LATTICE']['irdelay1'])
irdelay2 = float(report['LATTICE']['irdelay2'])
irdelay3 = float(report['LATTICE']['irdelay3'])

ir_ss = 0.5
ir1  = wfm.wave('ir1pow', 0., ir_ss)
ir2  = wfm.wave('ir2pow', 0., ir_ss)
ir3  = wfm.wave('ir3pow', 0., ir_ss)

ir1.appendhold(irdelay1)
ir2.appendhold(irdelay2)
ir3.appendhold(irdelay3)

ir1.linear(float(report['LATTICE']['irpow1']),irramp1)
ir2.linear(float(report['LATTICE']['irpow2']),irramp2)
ir3.linear(float(report['LATTICE']['irpow3']),irramp3)

gr1  = wfm.wave('greenpow1', 0., ir_ss)
gr2  = wfm.wave('greenpow2', 0., ir_ss)
gr3  = wfm.wave('greenpow3', 0., ir_ss)

grdelay1 = float(report['LATTICE']['grdelay1'])
grdelay2 = float(report['LATTICE']['grdelay2'])
grdelay3 = float(report['LATTICE']['grdelay3'])

gr1.appendhold(grdelay1)
gr2.appendhold(grdelay2)
gr3.appendhold(grdelay3)

grramp1 = float(report['LATTICE']['grrampdt1'])
grramp2 = float(report['LATTICE']['grrampdt2'])
grramp3 = float(report['LATTICE']['grrampdt3'])
gr1.linear(float(report['LATTICE']['grpow1']),grramp1)
gr2.linear(float(report['LATTICE']['grpow2']),grramp2)
gr3.linear(float(report['LATTICE']['grpow3']),grramp3)

#Shut down ODT laser completely
#ipg = wfm.wave('ipganalog', 10., ir_ss)
#ipg.appendhold(odtoverlap)
#ipg.linear( 0.0, 10.0)
#s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3,ipg])

s.analogwfm_add(ir_ss,[ir1,ir2,ir3,gr1,gr2,gr3])

# Turn on IR lattice beams

s.wait(irdelay1)

s.digichg('irttl1', float(report['LATTICE']['ir1']) )

s.wait(-irdelay1+irdelay2)

s.digichg('irttl2', float(report['LATTICE']['ir2']) )

s.wait(irdelay3-irdelay2)

s.digichg('irttl3', float(report['LATTICE']['ir3']) )

s.wait(-irdelay3)



s.wait(grdelay1)

s.digichg('greenttl1', float(report['LATTICE']['gr1']) )

s.wait(-grdelay1+grdelay2)

s.digichg('greenttl2', float(report['LATTICE']['gr2']) )

s.wait(-grdelay2+grdelay3)

s.digichg('greenttl3', float(report['LATTICE']['gr3']) )

s.wait(-grdelay3)


# Wait in ODT
s.wait(odtoverlap)


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

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)