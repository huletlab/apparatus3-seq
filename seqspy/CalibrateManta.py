"""Make sure the report file at 'Savedir/reportRunNumber.INI'
   exists otherwise this code won't compile. 
   
   Savedir and RunNumber are specified in settings.INI
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot, manta
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])


#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

s.wait(200.)

#TAKE PICTURES
trap_on_picture = 0

light = 'probe'
camera = 'manta'

s=andor.OpenShuttersProbe(s)

if light == 'bragg':
    s = manta.OpenShutterBragg(s)

if camera == 'manta':
	texp     = 0.006
	noatoms  = 200.0
	#PICTURE OF ATOMS
	s=manta.MantaPicture(s, texp, light, 1)
	s.wait(noatoms)

#print s.digital_chgs_str(500,100000.,['cameratrig','probe','odtttl','prshutter'])

#After taking a picture sequence returns at time of the last probe strobe
#Wait 50ms to get past the end
s.wait(50.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
#print s.digital_chgs_str(0.,100000.)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)