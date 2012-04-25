"""Take fluorescence image with Andor
"""

__author__ = "Pedro M Duarte and Ted Corcovilos"
__version__ = "$Revision: 0.5 $"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
import seq, wfm, motaos, gen, andor, cnc
#AO calibration interpolator
aos=motaos.calib()



#The parameters are loaded from params.txt
#Declare params as global inside methods.
from configobj import ConfigObj
params=ConfigObj('L:/software/apparatus3/params/params.INI')

#PARAMETERS
stepsize=float(params['SEQ']['stepsize'])
tof=float(params['ANDOR']['tof'])
exp=float(params['ANDOR']['exp'])
kexp=float(params['ANDOR']['kexp'])



#SEQUENCE
s=seq.sequence(stepsize)
# set initial values for TTL lines
s=gen.initial(s)
s.digichg('iraom1',0)
s.digichg('iraom2',0)
s.digichg('iraom3',0)
s.wait(10.0)

s=cnc.doCNC(s,aos,params,'ANDOR')

#Release MOT
s=gen.releaseMOT(s)
s.wait(tof)

#Here t=0, the time where the atoms shot is taken
s=andor.OpenShuttersFluor(s)

#Delay between shots is limited by the camera exposure (kexp) and the number of rows being shifted
shotdelay=float(params['ANDOR']['kexp'])/1000.+float(params['ANDOR']['rows'])*0.5/1000.+100./1000.

###Clear CCD trigger
###s.wait(-2.0*shotdelay)
###s=andor.AndorPictureExternal(s,kexp,0.0,'motswitch')
###s.wait(shotdelay)

###First junk shot
s.wait(-shotdelay)
s=andor.AndorPictureExternal(s,kexp,0.0,'motswitch')
s.wait(shotdelay)

###t=0 ATOMS###
###s=andor.AndorPictureExternal(s,kexp,exp,'motswitch')
s=andor.AndorPictureExternal(s,0.0,exp,'motswitch')
NoAtomsDelay=float(params['ANDOR']['noatoms'])
s.wait(NoAtomsDelay)

###Clear CCD again
s.wait(-shotdelay)
s=andor.AndorPictureExternal(s,kexp,0.0,'motswitch')
s.wait(shotdelay)

###t=0 NOATOMS###
##s=andor.AndorPictureExternal(s,kexp,exp,'motswitch')
s=andor.AndorPictureExternal(s,0.0,exp,'motswitch')

#After taking a picture sequence returns at time of the last probe strobe
#Wait 2ms to get past the end
s.wait(2.0)

s=gen.shutdown(s)
s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')


