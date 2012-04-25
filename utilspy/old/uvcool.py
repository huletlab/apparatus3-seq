"""Constructs the ramps for doing UV spectroscopy
   This involves the following channels:
	
	motpow
	repdet
	trapdet
	trappow
	reppow
	bfield
"""
import wfm, gen, math
#Import the polynomial interpolator
from convert import cnv

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])


def constructUVCoolRamps(cam):
	global report

	# Initialize channels to MOT SS values and with cncstepsize
	ss=f('CNC','cncstepsize')
	motpow   = wfm.wave(cnv('motpow',f('MOT','motpow')), ss)
	repdet   = wfm.wave(cnv('repdet',f('MOT','repdetSS')),ss)
	trapdet  = wfm.wave(cnv('trapdet',f('MOT','trapdetSS')),ss)
	reppow   = wfm.wave(cnv('reppow',f('MOT','reppowSS')),ss)
	trappow  = wfm.wave(cnv('trappow',f('MOT','trappowSS')),ss)
	bfield   = wfm.wave(cnv('bfield',f('MOT','bfield')),ss)
	
	#Ramp down  bfield and trapping beam and motpow
	bfield.linear( cnv('bfield',f('UVCOOL','uvbfield')), ss)
	trappow.linear( cnv('trappow',f('UVCOOL','trapP')),ss)
	motpow.linear( cnv('motpow',f('UVCOOL','motP')),ss)
	bfield.appendhold(f('UVCOOL','cooldt')-ss)

	maxCNCdt = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt() )

	DURATION = maxCNCdt

	motpow.extend( DURATION)
	repdet.extend( DURATION)
	trapdet.extend(DURATION)
	reppow.extend(DURATION)
	trappow.extend(DURATION)
	bfield.extend( DURATION)

	maxN=int(math.floor( (DURATION)/ss))+1


	#Insert bfield imaging value at release
	bfield.linear(cnv('bfield',f(cam,'imgbfield')),0.0)
	
	#Insert AOM imaging values 50us after release
	imgdt=0.2
	motpow.appendhold(imgdt)
	repdet.appendhold(imgdt)
	trapdet.appendhold(imgdt)
	reppow.appendhold(imgdt)
	trappow.appendhold(imgdt)
	
	motpow.linear(cnv('motpow',f(cam,'imgpow')),0.0)
	repdet.linear(cnv('repdet',f(cam,'imgdetrep')),0.0)
	trapdet.linear(cnv('trapdet',f(cam,'imgdettrap')),0.0)
	reppow.linear(cnv('reppow',f(cam,'imgpowrep')),0.0)
	trappow.linear(cnv('trappow',f(cam,'imgpowtrap')),0.0)


	maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(),\
		reppow.dt(), trappow.dt())

	motpow.extend(maxDT)
	repdet.extend(maxDT)
	trapdet.extend(maxDT)
	bfield.extend(maxDT)
	reppow.extend(maxDT)
	trappow.extend(maxDT)

	
	motpow.fileoutput( 'L:/software/apparatus3/seq/ramps/motpow.txt')
	repdet.fileoutput( 'L:/software/apparatus3/seq/ramps/repdet.txt')
	trapdet.fileoutput('L:/software/apparatus3/seq/ramps/trapdet.txt')
	bfield.fileoutput( 'L:/software/apparatus3/seq/ramps/bfield.txt')
	reppow.fileoutput( 'L:/software/apparatus3/seq/ramps/reppow.txt')
	trappow.fileoutput('L:/software/apparatus3/seq/ramps/trappow.txt')
	return DURATION

def doUVCool(s,duration):
	seqstepsize = f('SEQ','stepsize')
	#Add the load trap waveforms
	s.analogwfm(f('CNC','cncstepsize'),[ 	\
	{'name':'motpow',   'path':'L:/software/apparatus3/seq/ramps/motpow.txt'},\
	{'name':'repdet','path':'L:/software/apparatus3/seq/ramps/repdet.txt'},\
	{'name':'trapdet',  'path':'L:/software/apparatus3/seq/ramps/trapdet.txt'},\
	{'name':'bfield',   'path':'L:/software/apparatus3/seq/ramps/bfield.txt'}, \
	{'name':'reppow','path':'L:/software/apparatus3/seq/ramps/reppow.txt'},\
	{'name':'trappow',  'path':'L:/software/apparatus3/seq/ramps/trappow.txt'},\
			                                 ])
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	duration = seqstepsize*math.ceil(duration/seqstepsize)
	#Go to MOT release time
	s.wait(duration)
	

	
	return s