""" Create a bunch of TRAPFREQ ramps in advance to minimize 
    sequence compilation time during a Vary Param """

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')

import wfm, numpy

import time


mod_ss = 0.02
cpow = 5.0
moddt = 200.0
moddepth = 40.0


freq_0 = 6600
step  = 10
freq_f = 7000

odtpow  = wfm.wave('odtpow',  None, mod_ss, volt=cpow)

set = numpy.arange(freq_0 , freq_0 +  step*(numpy.fix((freq_f-freq_0)/step)+1), step)
print set 
print

for modfreq in set:
    t0=time.time()
    print "...Creating SineMod (cpow=%.2f, moddt=%.2f, modfreq=%.2f, moddepth=%.2f" % (cpow, moddt, modfreq, moddepth) 
    odtpow.SineMod( cpow, moddt, modfreq, moddepth)
    print '...Time used = %.2f seconds\n' % (time.time()-t0)
    print ""