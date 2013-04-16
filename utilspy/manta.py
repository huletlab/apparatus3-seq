import math

def MantaPicture(s, texp, probe, signal=1): 
    #signal = 0 for background picture
    trigdt = 0.1
    probedelay = 0.1
    s.wait(-probedelay)
    s.digichg('manta',1)
    s.wait(trigdt)
    s.digichg('manta',0)
    s.wait(-trigdt)
    s.wait(probedelay)
    s.digichg(probe,signal)
    s.wait(texp)
    s.digichg(probe,0)
    s.wait(-texp)
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
	#for test purposes give it an extra 1.0ms
	test=delay
	s.wait(-test)
	s.digichg('brshutter',0)
	s.wait(test)
	return s