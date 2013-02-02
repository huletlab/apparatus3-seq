"""Constructs the ramps for CNC of the MOT.
   This involves the following channels:
	
	motpow
	repdet
	trapdet
	trappow
	reppow
	bfield
	ir1
	ir2
	ir3
	
"""
import wfm, gen, math
#Import the conversion function
from convert import cnv

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])


def cncRamps():
	# Initialize channels to MOT SS values and with cncstepsize
	ss=f('CNC','cncstepsize')
	motpow   = wfm.wave(cnv('motpow',f('MOT','motpow'))     ,ss)
	repdet   = wfm.wave(cnv('repdet',f('MOT','repdetSS'))   ,ss)
	trapdet  = wfm.wave(cnv('trapdet',f('MOT','trapdetSS')) ,ss)
	reppow   = wfm.wave(cnv('reppow',f('MOT','reppowSS'))   ,ss)
	trappow  = wfm.wave(cnv('trappow',f('MOT','trappowSS')) ,ss)
	bfield   = wfm.wave(cnv('bfield',f('MOT','bfield'))     ,ss)
	
	CNC = gen.bstr('CNC',report)
	#If CNC is selected in the report then insert necessary linear ramps
	
	#First ramp bfield
	SINH = gen.bstr('sinh',report)
	if SINH == True:
		bfield.sinhRise(  cnv('bfield',  f('CNC','bfieldf'))    if CNC == True else  cnv('bfield',f('MOT','bfield'))    ,  f('CNC','dtbfield'), f('CNC','dtbfield')*f('CNC','taubfield'))
	else:
		bfield.linear(  cnv('bfield',  f('CNC','bfieldf'))    if CNC == True else  cnv('bfield',f('MOT','bfield'))    ,  f('CNC','dtbfield'))
	
	#Hold off start of laser ramps
	delay = f('CNC','delay')
	motpow.appendhold( delay )
	repdet.appendhold( delay )
	trapdet.appendhold( delay )
	reppow.appendhold( delay )
	trappow.appendhold( delay )
	
	#Do laser ramps
	motpow.linear(  cnv('motpow',  f('CNC','motpowf'))    if CNC == True else  cnv('motpow',f('MOT','motpow'))    ,  f('CNC','dtmotpow'))
	repdet.linear(  cnv('repdet',  f('CNC','repdetf'))    if CNC == True else  cnv('repdet',f('MOT','repdetSS'))  ,  f('CNC','dtrepdet'))
	trapdet.linear( cnv('trapdet', f('CNC','trapdetf'))   if CNC == True else  cnv('trapdet',f('MOT','trapdetSS')),  f('CNC','dttrapdet'))
	reppow.linear(  cnv('reppow',  f('CNC','reppowf'))    if CNC == True else  cnv('reppow',f('MOT','reppowSS'))  ,  f('CNC','dtreppow'))
	trappow.linear( cnv('trappow', f('CNC','trappowf'))   if CNC == True else  cnv('trappow',f('MOT','trappowSS')),  f('CNC','dttrappow'))
	
	print motpow.dt()
	#Extend all ramps to match current total duration
	print CNC
	ht = (f('CNC','holdtime') if CNC == True else 0.0)
	print "holdtime = " + str(ht)
	ENDCNC = max( motpow.dt(), repdet.dt(), trapdet.dt(), reppow.dt(), trappow.dt(), bfield.dt() ) + ht
	
	motpow.extend( ENDCNC)
	print motpow.dt()
	repdet.extend( ENDCNC)
	trapdet.extend(ENDCNC)
	bfield.extend( ENDCNC)
	reppow.extend( ENDCNC)
	trappow.extend( ENDCNC)
	maxN=int(math.floor( (ENDCNC)/ss))+1
	
	#print motpow.dt()
	#print reppow.dt()
	#print trappow.dt()
	#print repdet.dt()
	#print trapdet.dt()
	#print bfield.dt()
	#print uvdet.dt()
	
	#Up to here you have a Cooled and Compressed MOT
	#
	return motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC


    


def imagingRamps(motpow, repdet, trapdet, reppow, trappow, bfield,camera):
	ss=f('CNC','cncstepsize')
	#Insert bfield imaging value at release
	bfield.linear(cnv('bfield',f(camera,'imgbfield')),0.0)
	
	#Insert AOM imaging values 30us after release
	imgdt=0.03
	motpow.appendhold(imgdt)
	repdet.appendhold(imgdt)
	trapdet.appendhold(imgdt)
	reppow.appendhold(imgdt)
	trappow.appendhold(imgdt)
	
	motpow.linear( cnv('motpow' ,f(camera,'imgpow')),    0.0)
	#repdet.linear( cnv('repdet' ,f(camera,'imgdetrep')), 0.0)
	repdet.linear( cnv('repdet' ,f(camera,'imgdettrap')), 0.0)
	trapdet.linear(cnv('trapdet',f(camera,'imgdettrap')),0.0)
	reppow.linear( cnv('reppow' ,f(camera,'imgpowrep')), 0.0)
	trappow.linear(cnv('trappow',f(camera,'imgpowtrap')),0.0)

	maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

	motpow.extend(maxDT)
	repdet.extend(maxDT)
	trapdet.extend(maxDT)
	bfield.extend(maxDT)
	reppow.extend(maxDT)
	trappow.extend(maxDT)
	
	return motpow, repdet, trapdet, reppow, trappow, bfield, maxDT


def constructLoadRamps(camera):
	global report
	ss=f('CNC','cncstepsize')
	
	# Cool and Compress MOT
	# ENDCNC is defined as the time up to release from the MOT
	motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cncRamps()

	# Imaging
	motpow, repdet, trapdet, reppow, trappow, bfield, maxDT = imagingRamps(motpow, repdet, trapdet, reppow, trappow, bfield, camera)
	
	motpow.fileoutput( 'L:/software/apparatus3/seq/ramps/motpow.txt')
	repdet.fileoutput( 'L:/software/apparatus3/seq/ramps/repdet.txt')
	trapdet.fileoutput('L:/software/apparatus3/seq/ramps/trapdet.txt')
	bfield.fileoutput( 'L:/software/apparatus3/seq/ramps/bfield.txt')
	reppow.fileoutput( 'L:/software/apparatus3/seq/ramps/reppow.txt')
	trappow.fileoutput( 'L:/software/apparatus3/seq/ramps/trappow.txt')

	return ENDCNC

def run(s,camera):
	duration = constructLoadRamps(camera)
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
	
	#insert QUICK pulse  for fast ramping of the field gradient
	s.wait(-10.0)
	quickval = 1 if gen.bstr('CNC',report) == True else 0
	s.digichg('quick',quickval)
	s.wait(10.0)
	
	#Go to MOT release time and set QUICK back to low
	s.wait(duration)
	s.digichg('quick',0)
	
	print s.tcur
	
	#~ #IR On/Off
	#~ if gen.bstr('IR on',report) == True:
		#~ s.wait(-f('IRTRAP','dtirpow')-f('IRTRAP','irloadtime'))
		#~ s.digichg('iraom1',1)
		#~ s.digichg('iraom2',1)
		#~ s.digichg('iraom3',1)	
		#~ s.wait(f('IRTRAP','dtirpow')+f('IRTRAP','irloadtime'))
		

	
	return s, duration

