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
exp=2.0

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)
s.digichg('camerashut',0)
s.digichg('prshutter',1)
s.digichg('probe',0)


s.wait(15.0)

s=andor.OpenShuttersProbe(s)
light = 'probe'


#PICTURE OF ATOMS
s=andor.AndorKinetics(s,exp,light,1)
#SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
noatoms=200.0 #time for no atoms is given by max trigger period in Andor settings
s.wait(noatoms) 
s.wait(noatoms)
s.wait(noatoms)
#PICTURE OF BACKGROUND
s=andor.AndorKinetics(s,exp,light,1)


s.wait(30.0)

s.digichg('cameratrig',0)
s.digichg('camerashut',0)
s.digichg('prshutter',1)

s.save('L:/software/apparatus3/seq/seqstxt/testandor.txt')
