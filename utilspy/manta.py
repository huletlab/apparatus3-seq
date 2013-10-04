import math,andor

def MantaPicture(s, texp, probe, signal=1): 
    #signal = 0 for background picture

    # Set exposure pulse
    s.digichg(probe,signal)
    s.wait(texp)
    s.digichg(probe,0)
    s.wait(-texp)

    # Set MANTA trigger
    trigdt = 0.006*16
    trigadvance = 0.006*4
    s.wait(-trigadvance)
    s.digichg('manta',1)
    s.wait(trigdt)
    s.digichg('manta',0)
    s.wait(-trigdt)
    s.wait(trigadvance)
    return s
    
def OpenShuttersFluorMOT(s):
	#open camera and probe beam shutters  (back in time)
	#for test purposes give it an extra 1.0ms
	test=200.0
	motSHUT=3.5+test#full-on time for the probe shutter
	s.wait(-motSHUT)
	s.digichg('motshutter',0)
	s.wait(motSHUT)
	return s


def OpenShutterBragg(s, delay):
	#open camera and probe beam shutters  (back in time)
	test=delay
	s.wait(-test)
	s.digichg('brshutter',0)
	s.wait(test)
	return s


def Manta2_SmartBackground(s, exp, light, noatoms, bglist, bgdictPRETOF=None, enforcelight=1):
    #Takes a kinetic series of 4 exposures:  atoms, noatoms, atomsref, noatomsref
    
    #print s.digital_chgs_str(1000,100000.,['cameratrig','probe','odtttl','prshutter'])
    
    t0 = s.tcur
    
    #OPEN SHUTTERS
    if light == 'probe':
        s=andor.OpenShuttersProbe(s)
    elif light == 'motswitch':
        s=andor.OpenShuttersFluor(s)
    
    #print s.digital_chgs_str(1000,100000.,['cameratrig','probe','odtttl','prshutter'])

    bgdict={}
    for ch in bglist:
        bgdict[ch] = s.digistatus(ch)
        
    
    #PICTURE OF ATOMS
    if enforcelight == 0: 
        print "USE ARB FOR PICTURES? = YES" 
        s.wait(-0.006) 
        s.digichg(light,1)
        s.wait(+0.006)
        s.digichg(light,0)
    else:
        print "USE ARB FOR PICTURES? = NO"
    s=MantaPicture(s, exp, light, enforcelight) 


    #print s.digital_chgs_str(1000,100000.,['cameratrig','probe','odtttl','prshutter'])
    
    #SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
    #minimum time for no atoms is given by max trigger period in Andor settings
    
    
    s.wait(noatoms)
    s.digichg('quick2',0)
    s.digichg('field',0)
    s.digichg('odtttl',0)
    s.digichg('irttl1',0)
    s.digichg('irttl2',0)
    s.digichg('irttl3',0)
    s.digichg('greenttl1',0)
    s.digichg('greenttl2',0)
    s.digichg('greenttl3',0)
    s.wait(noatoms)
    
    if bgdictPRETOF is not None:
        #RESTORE LIGHTS FOR BACKGROUND - PRETOF
        for key in bgdictPRETOF.keys():
            if key is not 'tof':
                s.digichg( key, bgdictPRETOF[key])
        s.wait(noatoms)
    
        tof = bgdictPRETOF['tof']
        if tof > 0:
            s.wait( -tof )
            for key in bgdict.keys():
                s.digichg( key, bgdict[key])
            s.wait( tof )
    else:
        #RESTORE LIGHTS FOR BACKGROUND
        for key in bgdict.keys():
            s.digichg( key, bgdict[key])
        s.wait(noatoms)
        

    #PICTURE OF BACKGROUND
    if enforcelight == 0:
        print "USE ARB FOR PICTURES? = YES" 
        s.wait(-0.006) 
        s.digichg(light,1)
        s.wait(+0.006)
        s.digichg(light,0)
    else:
        print "USE ARB FOR PICTURES? = NO"
    s=MantaPicture(s, exp, light, enforcelight) 
    
    s.wait(noatoms*1)
    s.digichg('odtttl',0)
    s.digichg('irttl1',0)
    s.digichg('irttl2',0)
    s.digichg('irttl3',0)
    s.digichg('greenttl1',0)
    s.digichg('greenttl2',0)
    s.digichg('greenttl3',0)

    tf = s.tcur
    return s, tf-t0
