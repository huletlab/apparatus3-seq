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
exp      = float(report['FINDLATTICE']['andorexp'])
noatoms  = float(report['ANDOR']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

# Set powers for ir beams
ir_ss = 0.5
ir1  = wfm.wave('ir1pow', float(report['FINDLATTICE']['irpow1']), ir_ss)
ir2  = wfm.wave('ir2pow', float(report['FINDLATTICE']['irpow2']), ir_ss)
ir3  = wfm.wave('ir3pow', float(report['FINDLATTICE']['irpow3']), ir_ss)
odt0 = wfm.wave('odtpow', float(report['FINDLATTICE']['odtpow']), ir_ss)
ir1.appendhold(5*ir_ss)
ir2.appendhold(5*ir_ss)
ir3.appendhold(5*ir_ss)
odt0.appendhold(5*ir_ss)
s.analogwfm_add(ir_ss,[ir1,ir2,ir3,odt0])
s.wait(5*ir_ss)
s.wait(10.0)

s.digichg('hfimg',1)
s.digichg('odt7595',0)

#flight = float(report['FINDLATTICE']['flight'])
#s.wait(flight)
s.digichg('irttl1',1)
s.digichg('irttl2',0)
s.digichg('irttl3',0)
#s.wait(-flight)

# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)



# Evaporate in cross beam trap
s, cpowend  = odt.crossbeam_evap(s, toENDBFIELD)


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
repdet.linear( float(report['ANDOR']['imgdettrap']), zerorampdt )
repdet.appendhold(zerodt)

trapdet = wfm.wave('trapdet', float(report['CNC']['trapdetf']), evap_ss)
trapdet.linear( float(report['ANDOR']['imgdettrap']), zerorampdt )
trapdet.appendhold(zerodt)

reppow = wfm.wave('reppow', float(report['CNC']['reppowf']), evap_ss)
reppow.linear( float(report['ANDOR']['imgpowrep']), zerorampdt )
reppow.appendhold(zerodt)

trappow = wfm.wave('trappow', float(report['CNC']['trappowf']), evap_ss)
trappow.linear( float(report['ANDOR']['imgpowtrap']), zerorampdt )
trappow.appendhold(zerodt)

motpow = wfm.wave('motpow', float(report['CNC']['motpowf']), evap_ss)
motpow.linear( 1.14, zerorampdt)
motpow.appendhold(zerodt)

s.analogwfm_add(evap_ss,[bfield,repdet,trapdet,reppow, trappow, motpow])
s.wait(zerorampdt)

s=andor.OpenShuttersFluor(s)
dt0=5.0
dt1=0.006
s.digichg('field',0)
s.wait(zerodt)

#RELEASE FROM IR TRAP
s.digichg('odtttl',0)
odttof = float(report['FINDLATTICE']['odttof'])
s.wait(odttof)


#TAKE PICTURES
#light = 'probe'
light = 'motswitch'
#light = 'bragg'
trap_on_picture = 1
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)


#s.digichg('motswitch',1)
s.wait(dt1)
#s.digichg('motswitch',0)
s.wait(dt0)
s.digichg('field',0)
s.wait(-dt0-dt1-dt0)

s.wait(zerodt)

s.digichg('field',0)
s.wait(zerorampdt)

s.wait(10.0)






#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
#print s.digital_chgs_str(0.,100000.)

import seqconf
s.save( seqconf.seqtxtout() )
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)