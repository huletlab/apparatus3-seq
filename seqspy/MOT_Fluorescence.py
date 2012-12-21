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
 
 
 
import seq, wfm, gen, cnc, basler
report=gen.getreport()

print "\n----- basler_fluorescence.py -----"

#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['BASLER']['tof'])
preexp   = float(report['BASLER']['preexp'])
texp     = float(report['BASLER']['exp'])
postexp  = float(report['BASLER']['postexp'])
noatoms  = 200.


#Decides whether to shine on the probe beam or the MOT beams
##if gen.bstr('Fluor(T)/Abs(F)',report) == True:
##probe = 'motswitch'
##else:
##	probe = 'probe'
#At the moment we are just using the MOT beams for fluorescence imaging
probe = 'motswitch'

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)
s.wait(20.0)

#Edit cnc.py to change any of this
s, ENDCNC = cnc.run(s,'BASLER')

#Take fluorescence imaging shot with the MOT beams. 
#LET MOT EXPAND
#s.wait(-1.0)
s.digichg('field',0)
#s.wait(1.0)
s.digichg('motswitch',0) 

s.wait(tof)
#PICTURE OF ATOMS
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)
#PICTURE OF BACKGROUND
s.wait(noatoms)
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)

s.wait(2.0)
s=gen.shutdown(s)
import seqconf
s.save( seqconf.seqtxtout() )
s.save( __file__.split('.')[0]+'.txt')
s.save( __file__.split('.')[0]+'.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)
