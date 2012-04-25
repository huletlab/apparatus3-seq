"""Basler Fluoresence: To test this custom sequence make sure the report file given by
	(L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI
     exists otherwise this code won't compile. 
     """

__author__ = "Pedro M Duarte"
__version__ = "$Revision: 0.5 $"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, cnc, basler, andor
from convert import cnv

report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['BASLER']['tof'])
preexp   = float(report['BASLER']['preexp'])
texp     = float(report['BASLER']['exp'])
postexp  = float(report['BASLER']['postexp'])
noatoms  = 200.

#~ tof      = float(report['ANDOR']['tof'])
#~ exp      = float(report['ANDOR']['exp'])
#~ noatoms  = float(report['ANDOR']['noatoms'])


#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)
s.wait(20.0)

ss=float(report['CNC']['cncstepsize'])
	
# Cool and Compress MOT
# ENDCNC is defined as the time up to release from the MOT
motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()
#motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.statetransfer_F32(motpow, repdet, trapdet, reppow, trappow, bfield)
motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.statetransfer_F12(motpow, repdet, trapdet, reppow, trappow, bfield)

#camera='ANDOR'
camera='BASLER'
# Set imaging values
motpow, repdet, trapdet, reppow, trappow, bfield, maxDT = cnc.imagingRamps(motpow, repdet, trapdet, reppow, trappow, bfield, camera)

# Set uv1freq for lightshift probing
freq=float(report['UVLIGHTSHIFT']['freq'])
uv1freq = wfm.wave('uv1freq',cnv('uv1freq',freq),ss)
uv1freq.extend(maxDT)
	
#Add waveforms to sequence
s.analogwfm_add(ss,[motpow,repdet,trapdet,bfield,reppow,trappow,uv1freq])
	
#wait normally rounds down using floor, here the duration is changed before so that
#the wait is rounded up
ENDCNC = ss*math.ceil(ENDCNC/ss)
	
#insert QUICK pulse  for fast ramping of the field gradient
s.wait(-10.0)
quickval = 1 if gen.bstr('CNC',report) == True else 0
s.digichg('quick',quickval)
s.wait(10.0)
	
#Go to MOT release time and set QUICK back to low
s.wait(ENDCNC)
s.digichg('quick',0)

#RELEASE FROM MOT
s.digichg('motswitch',0) 
s.digichg('motshutter',1)
s.digichg('field',0)

freedt=float(report['UVLIGHTSHIFT']['freedt'])
pulse  = float(report['UVLIGHTSHIFT']['pulse'])
s.wait(freedt)
s.digichg('uvaom1',0)
s.wait(pulse)
s.digichg('uvaom1',0)
s.wait(tof-freedt-pulse)

#TAKE PICTURES
#probe = 'motswitch'
probe = 'probe'
#OPEN SHUTTERS
if probe == 'probe':
    s=andor.OpenShuttersProbe(s)
elif light == 'motswitch':
    s=andor.OpenShuttersFluor(s)
#PICTURE OF ATOMS
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)
#PICTURE OF BACKGROUND
s.wait(noatoms)
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)

#TAKE PICTURES
#~ light = 'probe'
#~ #light = 'motswitch'
#~ kinetics = gen.bstr('Kinetics',report)
#~ print 'kinetics = ' + str(kinetics)
#~ if kinetics == True:
    #~ s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms)
#~ else:
    #~ s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms)

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
        
print time.time()-t0," seconds"