"""Constructs the ramps for changing the MOT values to imaging
	
	motpow
	repdet
	trapdet
	trappow
	reppow

	
"""
import wfm, gen, math
#Import the conversion function
from convert import cnv

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])



def constructLoadRamps():
	global report

	# Initialize channels to ZSLOAD values and with cncstepsize
	ss=f('CNC','cncstepsize')
	motpow   = wfm.wave(cnv('motpow',f('ZSLOAD','motpow'))     ,ss)
	repdet   = wfm.wave(cnv('repdet',f('ZSLOAD','repdet'))   ,ss)
	trapdet  = wfm.wave(cnv('trapdet',f('ZSLOAD','trapdet')) ,ss)
	reppow   = wfm.wave(cnv('reppow',f('ZSLOAD','reppow'))   ,ss)
	trappow  = wfm.wave(cnv('trappow',f('ZSLOAD','trappow')) ,ss)
	
	#Insert AOM imaging values in one analogstepsize
	motpow.linear( cnv('motpow' ,f('ZSLOAD','imgpow')),    0.0)
	repdet.linear( cnv('repdet' ,f('ZSLOAD','imgdetrep')), 0.0)
	trapdet.linear(cnv('trapdet',f('ZSLOAD','imgdettrap')),0.0)
	reppow.linear( cnv('reppow' ,f('ZSLOAD','imgpowrep')), 0.0)
	trappow.linear(cnv('trappow',f('ZSLOAD','imgpowtrap')),0.0)

	maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), reppow.dt(), trappow.dt())

	motpow.extend(maxDT)
	repdet.extend(maxDT)
	trapdet.extend(maxDT)
	reppow.extend(maxDT)
	trappow.extend(maxDT)

	motpow.fileoutput( 'L:/software/apparatus3/seq/ramps/motpow.txt')
	repdet.fileoutput( 'L:/software/apparatus3/seq/ramps/repdet.txt')
	trapdet.fileoutput('L:/software/apparatus3/seq/ramps/trapdet.txt')
	reppow.fileoutput( 'L:/software/apparatus3/seq/ramps/reppow.txt')
	trappow.fileoutput( 'L:/software/apparatus3/seq/ramps/trappow.txt')

	return max( motpow.dt(), repdet.dt(), trapdet.dt(), reppow.dt(), trappow.dt())

def run(s):
	duration = constructLoadRamps()
	seqstepsize = f('SEQ','stepsize')
	#Add the load trap waveforms
	s.analogwfm(f('CNC','cncstepsize'),[ 	\
	{'name':'motpow',   'path':'L:/software/apparatus3/seq/ramps/motpow.txt'},\
	{'name':'repdet','path':'L:/software/apparatus3/seq/ramps/repdet.txt'},\
	{'name':'trapdet',  'path':'L:/software/apparatus3/seq/ramps/trapdet.txt'},\
	{'name':'reppow','path':'L:/software/apparatus3/seq/ramps/reppow.txt'},\
	{'name':'trappow',  'path':'L:/software/apparatus3/seq/ramps/trappow.txt'},\
			                                 ])
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	duration = seqstepsize*math.ceil(duration/seqstepsize)

	#Go to end, where motaos are ready for imaging
	s.wait(duration)
	return s, duration

