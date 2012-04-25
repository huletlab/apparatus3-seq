"""Make sure the report file given by 
   (L:/data/app3/Savedir)report(L:/data/app3/RunNumber).INI 
   exists otherwise this code won't compile. 
"""
__author__ = "Pedro M Duarte"

import time
t0=time.time()

print "\n----- Evap_UVMOT_Image_ZEROCROSSING.py -----\n"

import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot
report=gen.getreport()


#PARAMETERS
stepsize = float(report['SEQ']['stepsize'])
tof      = float(report['ANDOR']['tof'])
exp      = float(report['ANDOR']['exp'])
noatoms  = float(report['ANDOR']['noatoms'])

#SEQUENCE
s=seq.sequence(stepsize)
s=gen.initial(s)

s.wait(0.0)


s.digichg('hfimg',1)
s.digichg('odt7595',0)

#Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)

# Add evaporation ramp to ODT
free = float(report['EVAP']['free'])
image= float(report['EVAP']['image'])
buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
if free < buffer + toENDBFIELD :
    print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
    print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,free)
    exit(1)
s.wait(free)
odtpow, ENDEVAP, cpowend, ipganalog = odt.odt_evap(image)
evap_ss = float(report['EVAP']['evapss'])

bias = float(report['FESHBACH']['bias'])
zcrampdt = float(report['ZEROCROSS']['zcrampdt'])
zcdt = float(report['ZEROCROSS']['zcdt'])
zcbias = float(report['ZEROCROSS']['zcbias'])


bfield = wfm.wave('bfield',bias,evap_ss)

#~ bfield.extend(odtpow.dt()-zcdt-zcrampdt)
#~ bfield.linear(zcbias,zcrampdt)
#~ bfield.extend(odtpow.dt())

bfield.extend(odtpow.dt())
bfield.linear(zcbias,zcrampdt)
bfield.appendhold(zcdt)
odtpow.extend(bfield.dt())
ipganalog.extend(bfield.dt())

#s.analogwfm_add(evap_ss,[odtpow,bfield])
s.analogwfm_add(evap_ss,[odtpow,bfield,ipganalog])
# ENDEVAP should be equal to image

#~ s.wait(image)

s.wait(image+zcdt+zcrampdt)

#RELEASE FROM IR TRAP
s.digichg('odtttl',0)
odttof = float(report['ODT']['odttof'])
s.wait(odttof)

#Shine probe multiple times before taking the final picture
#Test for how far detuned is the phase-contrast imaging
multiN     = int(report['ANDOR']['multiN'])
multiDelta = float(report['ANDOR']['multiDelta'])
multidt    = float(report['ANDOR']['multidt'])
s = andor.multiProbe(s, 'probe', multiN, multiDelta, multidt)



#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
trap_on_picture = 1
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)


#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)