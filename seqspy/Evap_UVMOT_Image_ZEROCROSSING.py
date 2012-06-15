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
#print s.digital_chgs_str(1000,100000., ['cameratrig','probe','odtttl','prshutter'])
s.digichg('odtttl',0)
odttof = float(report['ODT']['odttof'])
s.wait(odttof)
#print s.digital_chgs_str(1000,100000., ['cameratrig','probe','odtttl','prshutter'])

#TAKE PICTURES
light = 'probe'
#light = 'motswitch'
#light = 'bragg'
if odttof <= 0.0:
    trap_on_picture = 1
else:
    trap_on_picture = 0
kinetics = gen.bstr('Kinetics',report)
print '...kinetics = ' + str(kinetics)
if kinetics == True:
    s,SERIESDT = andor.KineticSeries4(s,exp,light,noatoms, trap_on_picture)
else:
    s,SERIESDT = andor.FKSeries2(s,stepsize,exp,light,noatoms, trap_on_picture)
#print s.digital_chgs_str(1000,100000.,['cameratrig','probe','odtttl','prshutter'])

#After taking a picture sequence returns at time of the last probe strobe
#Wait 30ms to get past the end
s.wait(30.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)
s.digichg('odt7595',0)

#print s.digital_chgs_str(500,100000., ['cameratrig','probe','odtttl','prshutter'])
#print s.digital_chgs_str(0.,100000.)

s.save('L:/software/apparatus3/seq/seqstxt/expseq.txt')
s.clear_disk()
        
print '...Compilation = %.2f seconds\n' % (time.time()-t0)