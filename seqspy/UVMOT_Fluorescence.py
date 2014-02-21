"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import sys
import sys
import os
sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] )
import seqconf
for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)



import sys
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
 
 
 
import seq, wfm, gen, uvmot, basler, andor
report=gen.getreport()
#GET SECTION CONTENTS
UVSEC = gen.getsection('UV')
ODTSEC = gen.getsection('ODT')
BASLER = gen.getsection('BASLER')
ANDOR = gen.getsection('ANDOR')

print "\n----- basler_uv_repump.py -----\n"

#PARAMETERS
stepsize    =float(report['SEQ']['stepsize'])
tof         =float(report['BASLER']['tof'])
preexp      =float(report['BASLER']['preexp'])
texp        =float(report['BASLER']['exp'])
postexp     =float(report['BASLER']['postexp'])


#SEQUENCE
s=seq.sequence(stepsize)

s=gen.initial(s)
if UVSEC.odt == 1:
    s.digichg('odtttl', 1)
    odtss = 0.1
    from odt import odt_wave, ipg_wave 
    odtpow  = odt_wave('odtpow',  None, odtss, volt=10.0)
    ipganalog = ipg_wave('ipganalog', 10., odtss)
    odtpow.appendhold(5.0) 
    ipganalog.appendhold(10.0)
    s.analogwfm_add( odtss, [odtpow,ipganalog])

s.wait(20.0)
s, duration = uvmot.run(s,'BASLER')

#RELEASE FROM MOT
s.digichg('motswitch',0) 
s.digichg('uvshutter',0)
s.digichg('field',0)

s.wait(tof)

#Use MOT beams for fluorescence imaging
light = 'motswitch'
noatoms = 67.0
cameras = UVSEC.camera
imagetime = s.tcur

if 'andor' in cameras:
    new_seqcam = 'andor'
else:
    new_seqcam = 'none'  
print "\n...SEQ:camera will be modified  in report"
print "\tNEW  SEQ:camera = %s\n" % new_seqcam
# SEQ:camera needs to be a list of strings.
gen.save_to_report('SEQ','camera', new_seqcam)

print "Current time before BASLER = ", s.tcur
#Take fluorescence imaging shot with the MOT beams. 
#PICTURE OF ATOMS
s.tcur = imagetime
s=basler.BaslerPicture(s,preexp,texp,postexp,light)
#PICTURE OF BACKGROUND
s.wait(noatoms)
s.wait(noatoms)
s.wait(noatoms)
s=basler.BaslerPicture(s,preexp,texp,postexp,light)
print "Current time after BASLER = ", s.tcur

if 'andor' in cameras:
    s.tcur = imagetime 
    print "Current time before Andor1 = ", s.tcur
    trap_on_picture = 1
    s,SERIESDT = andor.KineticSeries4(s,ANDOR.exp,light,noatoms, trap_on_picture, mock=True)
    print "Current time after Andor1 =", s.tcur


#After taking a picture sequence returns at time of the last probe strobe
#Wait 50ms to get past the end
s.wait(50.0)
s=gen.shutdown(s)
import seqconf
s.save( seqconf.seqtxtout() )
s.save( __file__.split('.')[0]+'.txt')
s.save( __file__.split('.')[0]+'.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)
