"""Test andor timing
"""

__author__ = "Pedro M Duarte and Ted Corcovilos"
__version__ = "$Revision: 0.5 $"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
import seq,  gen, andor


#PARAMETERS
stepsize=0.05
exp=0.05
noatoms=100.0

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)
s.digichg('camerashut',0)
s.digichg('prshutter',1)
s.digichg('probe',0)

s.wait(15.0)

s=andor.OpenShuttersProbe(s)
s.digichg('cameratrig',1)
trigpulse=0.2
s.wait(trigpulse)
s.digichg('cameratrig',0)

s.digichg('probe',1)
s.wait(exp)
s.digichg('probe',0)

s.wait(60.0)

s=andor.OpenShuttersProbe(s)
s.digichg('cameratrig',1)
trigpulse=0.2
s.wait(trigpulse)
s.digichg('cameratrig',0)

s.digichg('probe',1)
s.wait(exp)
s.digichg('probe',0)





s.wait(30.0)

s.digichg('cameratrig',0)
s.digichg('camerashut',0)
s.digichg('prshutter',1)

s.save('L:/software/apparatus3/seq/seqstxt/testandor.txt')



	
