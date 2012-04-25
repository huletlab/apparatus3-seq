"""This sequence script is used to put a ramp in the bfield using the QUICK TTL for 
improved turn-on speed.  
     """

__author__ = "Pedro M Duarte"
__version__ = "$Revision: 0.5 $"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen



stepsize=0.01
s=seq.sequence(stepsize)

s.digichg('field',1)

s.wait(50.0)

bfield   = wfm.wave('bfield',0,stepsize)
bfield.appendhold(10.0)
bfield.linear(2.0,stepsize)
bfield.appendhold(50.0)
bfield.linear(0.0,stepsize)
bfield.appendhold(stepsize)
bfield.fileoutput( 'L:/software/apparatus3/seq/ramps/testcoils.txt')

#Add the load trap waveforms
duration = s.analogwfm(stepsize,[ \
{'name':'bfield',   'path':'L:/software/apparatus3/seq/ramps/testcoils.txt'} ])

dt=30.0
s.wait(-dt)
s.digichg('quick',1)
s.wait(dt+10.+5.)
s.digichg('quick',0)
#s.wait(dt+duration)
#s.digichg('quick',0)

s.wait(60.0)
#s=gen.shutdown(s)
#s.digichg('field',1)
#s.digichg('uvaom1',1)

s.digichg('field',0)

s.save('L:/software/apparatus3/seq/seqstxt/testquick.txt')
        
print time.time()-t0," seconds"