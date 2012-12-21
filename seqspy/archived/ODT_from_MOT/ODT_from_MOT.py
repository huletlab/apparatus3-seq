"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
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

print "\n----- odt_load_mot.py -----"

import sys, math
 
 
 
import seq, wfm, gen, cnc, andor
report=gen.getreport()

#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

#Keep ODT on
ODT = gen.bstr('ODT',report)
if ODT == True:
    s.digichg('odtttl',1)
s.wait(20.0)

#LOAD ODT
s, ENDCNC=cnc.run(s,'ANDOR')

#Insert ODT overlap 
overlapdt = float(report['ODT']['overlapdt'])
s.wait(-overlapdt)
s.digichg('odtttl',1)
s.wait(overlapdt)

#Flash UVMOT for state transfer
#~ fstatedt  = float(report['ODT']['fstatedt'])
#~ s.digichg('uvaom1',1)
#~ s.wait(fstatedt)
#~ s.digichg('uvaom1',0)
#~ s.wait(-fstatedt) 

#RELEASE FROM MOT
s.digichg('motswitch',0) 
s.digichg('motshutter',1)
s.digichg('field',0)

s.wait(tof)

#TAKE PICTURES
light = 'probe'
trap_on_picture = 1
#light = 'motswitch'
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)

import seqconf
s.save( seqconf.seqtxtout() )
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)