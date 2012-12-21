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

print "\n----- odt_uv_hf_tof.py -----"

import sys, math
 
 
 
import seq, wfm, gen, cnc, highfield_uvred, odt, andor
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

#Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvred.go_to_highfield(s)

#At this point the time sequence is at ENDUVMOT
s.wait(tof)

#RELEASE FROM IR TRAP
s.digichg('odtttl',0)
odttof = float(report['ODT']['odttof'])
s.wait(odttof)

#~ braggtime=0.15
#~ waittime=1.0
#~ s.wait(-braggtime-waittime)
#~ s.digichg('bragg',1)
#~ s.wait(braggtime)
#~ s.digichg('bragg',0)
#~ s.wait(waittime)

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
trap_on_picture = 0
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
s.digichg('odt7595',0)

import seqconf
s.save( seqconf.seqtxtout() )
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)