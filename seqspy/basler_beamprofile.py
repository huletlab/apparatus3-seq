"""Basler Fluoresence: To test this custom sequence make sure the report file given by
	(L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI
     exists otherwise this code won't compile. 
     """

__author__ = "Pedro M Duarte"
__version__ = "$Revision: 0.5 $"

import pprint
import sys
import os
sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] )
import seqconf
for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)


import time
t0=time.time()


import math

try:
  import seq, wfm, gen, cnc, basler
except:
  print "Could not import"
  exit(1)



#PARAMETERS
preexp   = .1
texp     = 0.1
postexp  = .1


#Beam that you are profiling
probe = 'odtttl'

#SEQUENCE
stepsize=0.01
s=seq.sequence(stepsize)
s=gen.initial(s)

s.digichg(probe,0)
s.wait(750.0)


#PICTURE OF BEAM
s=basler.BaslerPicture(s,preexp,texp,postexp,probe)
s.wait(800.0)
s=basler.BaslerBackground(s,preexp,texp,postexp)
s.wait(800.0)
s=gen.shutdown(s)
s.digichg(probe,1)
import seqconf
s.save( seqconf.seqtxtout() )
s.save( __file__.split('.')[0]+'.txt')
print time.time()-t0," seconds"
