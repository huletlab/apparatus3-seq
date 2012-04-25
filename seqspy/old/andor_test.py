"""Test andor timing
"""

__author__ = "Pedro M Duarte and Ted Corcovilos"
__version__ = "$Revision: 0.5 $"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
import seq, wfm, motaos, gen, andor, cnc


#PARAMETERS
stepsize=0.005
tof=10.0
exp=.500
kexp=10.
rows=128.

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)
s.digichg('camerashut',1)
s.digichg('motswitch',1)
s.digichg('motshutter',0)
s.digichg('prshutter',1)

s.wait(15.0)
#PICTURES
s=andor.OpenShuttersFluor(s)


light='probe'
#Atoms
s,dt=andor.AndorPictureWithClear(s,rows,stepsize,kexp,exp,light,1)
#NoAtoms
NoAtomsDelay=2.0
if NoAtomsDelay < dt:
    print "Error:  need to wait longer between shots, clear trigger of NoAtoms will overlap with\
    \n end of accumulation trigger of Atoms"
    exit(1)
s.wait(NoAtomsDelay)
s,dt=andor.AndorPictureWithClear(s,rows,stepsize,kexp,exp,light,1)


#Delay between shots is limited by the camera exposure (kexp) and the number of rows being shifted
#shotdelay=float(report['ANDOR']['kexp'])/1000.+float(report['ANDOR']['rows'])*0.5/1000.+100./1000.
shotdelay=4.0 #ms

#Thse timings work miraculously  because now ExternalStart is being used instead of external
#Check this later...
#~ ###First junk shot
#~ s.wait(-shotdelay)
#~ s=andor.AndorPictureExternal(s,kexp,exp,light,1)
#~ s.wait(shotdelay)
#~ ###t=0 ATOMS###
#~ s=andor.AndorPictureExternal(s,kexp,exp,light,1)

#~ NoAtomsDelay=10.0
#~ s.wait(NoAtomsDelay)
#~ ###Clear CCD again
#~ s.wait(-shotdelay)
#~ s=andor.AndorPictureExternal(s,kexp,exp,light,1)
#~ s.wait(shotdelay)
#~ ###t=0 NOATOMS###
#~ s=andor.AndorPictureExternal(s,kexp,exp,light,1)



#After taking a picture sequence returns at time of the last probe strobe
#Wait 2ms to get past the end
s.wait(30.0)

s.digichg('cameratrig',0)
s.digichg('camerashut',1)
s.digichg('prshutter',1)
s.digichg('motswitch',1)

#s=gen.shutdown(s)
s.save('L:/software/apparatus3/seq/seqstxt/testandor.txt')



	
