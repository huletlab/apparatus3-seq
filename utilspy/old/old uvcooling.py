"""Constructs the ramps for doing UV cooling and fluorescence imaging:

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
#Import the polynomial interpolator
from convert import cnv

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])



def constructLoadRamps(cam):
	global report

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
	lifetime = gen.bstr('Lifetime',report)
	ht = (f('CNC','holdtime') if CNC == True or lifetime == True else 0.0)
	print "holdtime = " + str(ht)
	DURATION = max( motpow.dt(), repdet.dt(), trapdet.dt(), reppow.dt(), trappow.dt(), bfield.dt() ) + ht
	#DURATION = DURATION + ht
	motpow.extend( DURATION)
	print motpow.dt()
	repdet.extend( DURATION)
	trapdet.extend(DURATION)
	bfield.extend( DURATION)
	reppow.extend( DURATION)
	trappow.extend( DURATION)
	maxN=int(math.floor( (DURATION)/ss))+1
	
	#print motpow.dt()
	#print reppow.dt()
	#print trappow.dt()
	#print repdet.dt()
	#print trapdet.dt()
	#print bfield.dt()
	#print uvdet.dt()
	
	#Up to here you have a Cooled and Compressed MOT
	#
	
	#Ramp down things quickly to UV values
	uvdt = f('UV','dt')
	motpow.linear(  cnv('motpow', f('UV','uvmotpow')), uvdt)
	reppow.linear(  cnv('reppow', f('UV','uvreppow')), uvdt)
	trappow.linear( 0.0                               ,uvdt)
	repdet.linear(  cnv('repdet', f('UV','uvrepdet')), uvdt)
	trapdet.linear( cnv('trapdet',f('UV','uvtrapdet')),uvdt)
	bfield.linear(  cnv('bfield', f('UV','uvbfield')), uvdt)
	
	#Hold UV MOT for uvmotdt 
	uvmotdt = f('UV','uvmotdt')
	motpow.appendhold(uvmotdt)
	reppow.appendhold(uvmotdt)
	trappow.appendhold(uvmotdt)
	repdet.appendhold(uvmotdt)
	trapdet.appendhold(uvmotdt)
	bfield.appendhold(uvmotdt)

	#Ramp up the bfield during uvramp
	uvramp = f('UV','uvramp')
	motpow.appendhold(uvramp)
	reppow.appendhold(uvramp)
	trappow.appendhold(uvramp)
	repdet.appendhold(uvramp)
	trapdet.appendhold(uvramp)
	bfield.linear( cnv('bfield', f('UV','uvbfieldf')), uvramp)
	
	#Hold everything for a little more
	uvhold = f('UV','uvhold')
	motpow.appendhold(uvhold)
	reppow.appendhold(uvhold)
	trappow.appendhold(uvhold)
	repdet.appendhold(uvhold)
	trapdet.appendhold(uvhold)
	bfield.appendhold(uvhold)
	
	CNCDURATION = DURATION
	UVMOTDURATION = DURATION + uvdt + uvmotdt + uvramp
	DURATION = UVMOTDURATION + uvhold	


	#Insert bfield imaging value at release
	bfield.linear(cnv('bfield',f(cam,'imgbfield')),0.0)
	
	#Insert AOM imaging values 30us after release
	imgdt=0.03
	motpow.appendhold(imgdt)
	repdet.appendhold(imgdt)
	trapdet.appendhold(imgdt)
	reppow.appendhold(imgdt)
	trappow.appendhold(imgdt)
	
	motpow.linear( cnv('motpow' ,f(cam,'imgpow')),    0.0)
	repdet.linear( cnv('repdet' ,f(cam,'imgdetrep')), 0.0)
	trapdet.linear(cnv('trapdet',f(cam,'imgdettrap')),0.0)
	reppow.linear( cnv('reppow' ,f(cam,'imgpowrep')), 0.0)
	trappow.linear(cnv('trappow',f(cam,'imgpowtrap')),0.0)

	maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

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

	return CNCDURATION, DURATION

def doLOAD(s,camera):
	cncduration, duration = constructLoadRamps(camera)
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
	
	#insert UV pulse
	s.wait(cncduration)
	s.wait(f('UV','uvtime'))
	s.digichg('uvaom1',1)
	s.wait(-f('UV','uvtime') - cncduration)
	
	
	#Go to MOT release time and set QUICK back to low
	s.wait(duration)
	s.digichg('uvaom1',0)
	s.digichg('quick',0)
	
	print s.tcur
			


	
	return s, duration

