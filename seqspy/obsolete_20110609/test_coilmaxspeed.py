"""This sequence script is used to test the max coil turn-on speed by opening the FET's fully
     """

__author__ = "Pedro M Duarte"
__version__ = "$Revision: 0.5 $"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, loadtrap



stepsize=0.01
s=seq.sequence(stepsize)

s.digichg('field',1)

s.wait(10.0)

s.digichg('quick',1)
s.wait(50.0)
s.digichg('d-23',0)
s.wait(6.0)
s.digichg('d-23',1)
s.wait(5.0)
s.digichg('quick',0)
s.wait(10.0)

s=gen.shutdown(s)
s.digichg('field',1)
s.digichg('uvaom1',1)

s.save('L:/software/apparatus3/seq/seqstxt/testquick.txt')
        
print time.time()-t0," seconds"