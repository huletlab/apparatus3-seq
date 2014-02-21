__author__ = "Pedro M Duarte"

import sys
import os
import shutil

#Use this line to use the parameters in seq/benchmark/report_benchamr.INI and the output expseq.txt will located at the benchmark folder as well
#sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]+'/benchmark')


sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] )
import seqconf
for p in seqconf.import_paths():
	print "...adding path " + p
	sys.path.append(p)

import time
t0=time.time()

import math
 
import seq, wfm, gen, cnc, odt, andor, highfield_uvmot, manta, lattice, roundtrip

#REPORT
report=gen.getreport()
    
#GET SECTION CONTENTS
DIMPLE = gen.getsection('DIMPLE')
EVAP   = gen.getsection('EVAP')
FB     = gen.getsection('FESHBACH')
ZC     = gen.getsection('ZEROCROSS')
ANDOR  = gen.getsection('ANDOR')
DL     = gen.getsection('DIMPLELATTICE')
MANTA  = gen.getsection('MANTA')
LATTICEMOD = gen.getsection('LatticeMod')
RT     = gen.getsection('ROUNDTRIP')




print "\n...SEQ:camera will be modified  in report"
print "\tNEW  SEQ:camera = %s\n" % ( DL.camera )
# When only use one camera the reading of DL.camera will be a string instead of a list of string. As a consequence we need to check the type.
gen.save_to_report('SEQ','camera', DL.camera if type(DL.camera) == type("string") else ",".join(DL.camera)) 



#SEQUENCE
stepsize = float(report['SEQ']['stepsize'])
s=seq.sequence(stepsize)
s=gen.initial(s)
s.digichg('hfimg',1)
s.digichg('odt7595',0)

#Get hfimg ready
s.digichg('hfimg',1)

#If using analoghfimg get it ready
if ANDOR.analoghfimg == 1:
	s.digichg('analogimgttl',1)


# Do CNC, UVMOT, and field ramps
s, toENDBFIELD = highfield_uvmot.go_to_highfield(s)

analoghfimg = []
# THis section used to resolve the issue we have probe or bragg kill in dimple section
if DL.probekill ==1:
    if (-DL.probekilltime) > DL.image:
        analoghfimg = [wfm.wave('analogimg', DL.probekill_hfimg, EVAP.evapss)]
elif DL.braggkill == 1:
    if (-DL.braggkilltime) > DL.image:
        print "...braggkill will be inserted in DIMPLE part of sequence"
        hfimgwfm = wfm.wave('analogimg', DL.braggkill_hfimg, EVAP.evapss)
        
        
        analoghfimg = [hfimgwfm]

    
    
    
# Evaporate into the dimple 
s, cpowend = odt.crossbeam_dimple_evap(s, toENDBFIELD,analoghfimg)


# Ramp up the lattice
s, noatomswfms, lockwfms, bgdictPRETOF, wfms = lattice.dimple_to_lattice(s,cpowend)


if RT.enable == 1:
    s, noatomswfms, bgdictPRETOF = roundtrip.do_roundtrip(s, wfms)
#








#########################################
## PICTURES
## For the background pictures one needs to consider what is the noatoms time
#########################################

#INDICATE WHICH CHANNELS ARE TO BE CONSIDERED FOR THE BACKGROUND
bglist = ['odtttl','irttl1','irttl2','irttl3','greenttl1','greenttl2','greenttl3']
bgdict={}
bgdictPast={}
for ch in bglist:
    bgdict[ch] = s.digistatus(ch)
    bgdictPast[ch] = s.get_pastdigichgs( DL.bgRetainDT, ch )


#TAKE PICTURES
#####light = this is 'probe', 'motswitch' or 'bragg'
#####camera = this is 'andor' or 'manta'
if DL.light == 'bragg':
    s = manta.OpenShutterBragg(s,DL.shutterdelay)

cameras = DL.camera
# This is for backward comptibility for old syntax:
if "both" in cameras:
	cameras.remove("both")
	cameras.append("manta")
	cameras.append("andor")


if 'manta' in cameras:
    noatomsdt = MANTA.noatoms
else:
    noatomsdt = ANDOR.noatoms
	
# The noatomswfms that replicate the conditions of the last part
# of the experiment wfms are added here
print
print "ADDING COPY OF RAMPS FOR BACKGROUND PICTURE"
pic1time = s.tcur
print "tcur = ", pic1time
s.wait( 3.*noatomsdt - DL.bgRetainDT)
if (DL.bgRetainDT - noatomswfms[0].dt()) > DL.ss:
    print " Possible time slip due to difference in DL.bgRetainDT and wfms.dt()"
    print " time slip =", (DL.bgRetainDT-noatomswfms[0].dt())
bufferdt = 5.0
if DL.locksmooth == 1 and DL.lock == 0:
    s.wait(-bufferdt)
    s.wait(-lockwfms[0].dt()) 
duration0 = s.analogwfm_add(DL.ss,noatomswfms)
if DL.locksmooth == 1 and DL.lock == 0:
    s.wait(duration0)
    s.wait(bufferdt)
    duration = s.analogwfm_add( DL.lockss, lockwfms)
    s.wait(lockwfms[0].dt())
    s.wait(-duration0)
s.wait( -3.*noatomsdt + DL.bgRetainDT)
print "tcur = ",s.tcur
#if pic1time != s.tcur:
if abs(pic1time - s.tcur) > 1e-6:
    print "pic1time = ",pic1time
    print "s.tcur   = ",s.tcur
    s =  "A time slip has occured and sequence did not"
    s += "\nreturn to correct time for picture1"
    
    raise Exception(s)
    exit(1)
print


# Find out if ARB is being used to control timing 
notusearb =  not ( (LATTICEMOD.enable == 1) and (LATTICEMOD.arb == 1) )
if notusearb == True: 
    notusearb = 1 
else:  
    notusearb = 0
print "notusearb =",notusearb


# Start taking the pictures
imagetime = s.tcur
if "manta" in cameras:
    (s,SERIESDT) = \
          manta.Manta2_SmartBackground( s, MANTA.exp, DL.light, \
                                        noatomsdt, bglist,  bgdictPRETOF, \
                                        enforcelight = notusearb)

if 'andor' in cameras:
    s.tcur = imagetime 
    print "Current time before Andor1 = ", s.tcur
    (s,SERIESDT) = \
          andor.KineticSeries4_SmartBackground( s, ANDOR.exp, DL.light, \
                                                noatomsdt, bglist,  bgdictPRETOF, \
                                                trigger='cameratrig',\
                                                enforcelight = notusearb,\
                                                bgdictPAST= bgdictPast )
    print "Current time after Andor1 =", s.tcur

if 'andor2' in cameras:
    s.tcur = imagetime
    print "Current time before Andor2 = ", s.tcur
    s,SERIESDT =  \
         andor.KineticSeries4_SmartBackground( s, ANDOR.exp, DL.light, \
                                               noatomsdt, bglist, bgdictPRETOF, \
                                               trigger='cameratrig2',\
                                               enforcelight = notusearb,\
                                               bgdictPAST= bgdictPast )
    print "Current time after Andor2 = ", s.tcur	

		
s.wait(20.0)

#HERE TURN OFF ALL LIGHT THAT COULD GET TO THE MANTA
s.digichg('odtttl',0)
s.digichg('odt7595',0)
s.digichg('ipgttl',0)
s.digichg('greenttl1',0)
s.digichg('greenttl2',0)
s.digichg('greenttl3',0)
s.digichg('irttl1',0)
s.digichg('irttl2',0)
s.digichg('irttl3',0)
s.wait(20.0)



#After taking a picture sequence returns at time of the last probe strobe
#Wait 50ms to get past the end
s.wait(50.0)
s=gen.shutdown(s)
s.digichg('odtttl',0)


outputfile = seqconf.seqtxtout() 
s.save( outputfile )

shutil.copyfile( outputfile,  __file__.split('.')[0]+'.txt')

s.clear_disk()
        
__author__ = "Pedro M Duarte"
print "This is the very end of the sequence file."
