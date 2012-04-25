"""Constructs the ramps for CNC of the MOT.

"""


import wfm, gen, math

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])


def cncRamps():
	# Initialize channels to MOT SS values and with cncstepsize
	ss=f('CNC','cncstepsize')
	motpow   = wfm.wave('motpow', f('MOT','motpow')   ,ss)
	repdet   = wfm.wave('repdet', f('MOT','repdetSS') ,ss)
	trapdet  = wfm.wave('trapdet',f('MOT','trapdetSS'),ss)
	reppow   = wfm.wave('reppow', f('MOT','reppowSS') ,ss)
	trappow  = wfm.wave('trappow',f('MOT','trappowSS'),ss)
	bfield   = wfm.wave('bfield', f('MOT','bfield')   ,ss)
	
	CNC = gen.bstr('CNC',report)
	#If CNC is selected in the report then insert necessary linear ramps
	
	#First ramp bfield
	SINH = gen.bstr('sinh',report)
	if SINH == True:
		bfield.sinhRise(f('CNC','bfieldf') if CNC == True else  f('MOT','bfield'),  f('CNC','dtbfield'), f('CNC','dtbfield')*f('CNC','taubfield'))
	else:
		bfield.linear(  f('CNC','bfieldf') if CNC == True else  f('MOT','bfield'),  f('CNC','dtbfield'))
	
	#Hold off start of laser ramps
	delay = f('CNC','delay')
	motpow.appendhold( delay )
	repdet.appendhold( delay )
	trapdet.appendhold( delay )
	reppow.appendhold( delay )
	trappow.appendhold( delay )
	
	#Do laser ramps
	motpow.linear(  f('CNC','motpowf')  if CNC == True else  f('MOT','motpow')    , f('CNC','dtmotpow'))
	repdet.linear(  f('CNC','repdetf')  if CNC == True else  f('MOT','repdetSS')  , f('CNC','dtrepdet'))
	trapdet.linear( f('CNC','trapdetf') if CNC == True else  f('MOT','trapdetSS'),  f('CNC','dttrapdet'))
	reppow.linear(  f('CNC','reppowf')  if CNC == True else  f('MOT','reppowSS')  , f('CNC','dtreppow'))
	trappow.linear( f('CNC','trappowf') if CNC == True else  f('MOT','trappowSS'),  f('CNC','dttrappow'))
	
	#print motpow.dt()
	#Extend all ramps to match current total duration
	print '...CNC = ' + str(CNC)
	ht = (f('CNC','holdtime') if CNC == True else 0.0)
	#print "holdtime = " + str(ht)
	ENDCNC = max( motpow.dt(), repdet.dt(), trapdet.dt(), reppow.dt(), trappow.dt(), bfield.dt() ) + ht
	
	motpow.extend( ENDCNC)
	#print motpow.dt()
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
	bfdt = 0.0
	bfield.linear(f(camera,'imgbfield'),bfdt)
	
	#Insert AOM imaging values 30us after release
	imgdt=0.03
	motpow.appendhold(imgdt)
	repdet.appendhold(imgdt)
	trapdet.appendhold(imgdt)
	reppow.appendhold(imgdt)
	trappow.appendhold(imgdt)
	
	motpow.linear( f(camera,'imgpow'),    0.0)
	#repdet.linear( f(camera,'imgdetrep'), 0.0)
	repdet.linear( f(camera,'imgdettrap'), 0.0)
	trapdet.linear(f(camera,'imgdettrap'),0.0)
	reppow.linear( f(camera,'imgpowrep'), 0.0)
	trappow.linear(f(camera,'imgpowtrap'),0.0)

	maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

	motpow.extend(maxDT)
	repdet.extend(maxDT)
	trapdet.extend(maxDT)
	bfield.extend(maxDT)
	reppow.extend(maxDT)
	trappow.extend(maxDT)
	
	return motpow, repdet, trapdet, reppow, trappow, bfield, maxDT


def uvzsload_imaging():
	# Initialize channels to MOT SS values and with cncstepsize
	ss=f('CNC','cncstepsize')
	motpow   = wfm.wave('motpow', f('MOT','motpow')   ,ss)
	repdet   = wfm.wave('repdet', f('MOT','repdetSS') ,ss)
	trapdet  = wfm.wave('trapdet',f('MOT','trapdetSS'),ss)
	reppow   = wfm.wave('reppow', f('MOT','reppowSS') ,ss)
	trappow  = wfm.wave('trappow',f('MOT','trappowSS'),ss)
	bfield   = wfm.wave('bfield', f('MOT','bfield')   ,ss)
	
	sec='ZSLOAD'
	
	#Insert bfield imaging value at release
	bfdt = 0.0
	bfield.linear(f(sec,'imgbfield'),bfdt)
	
	#Insert AOM imaging values 30us after release
	imgdt=0.03
	motpow.appendhold(imgdt)
	repdet.appendhold(imgdt)
	trapdet.appendhold(imgdt)
	reppow.appendhold(imgdt)
	trappow.appendhold(imgdt)
	
	motpow.linear( f(sec,'imgpow'),    0.0)
	#repdet.linear( f(sec,'imgdetrep'), 0.0)
	repdet.linear( f(sec,'imgdettrap'), 0.0)
	trapdet.linear(f(sec,'imgdettrap'),0.0)
	reppow.linear( f(sec,'imgpowrep'), 0.0)
	trappow.linear(f(sec,'imgpowtrap'),0.0)

	maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

	motpow.extend(maxDT)
	repdet.extend(maxDT)
	trapdet.extend(maxDT)
	bfield.extend(maxDT)
	reppow.extend(maxDT)
	trappow.extend(maxDT)
	
	return motpow, repdet, trapdet, reppow, trappow, bfield

def imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow,camera):
	ss=f('CNC','cncstepsize')
	
	#Insert AOM imaging values 100us after release
	imgdt=0.1
	motpow.appendhold(imgdt)
	repdet.appendhold(imgdt)
	trapdet.appendhold(imgdt)
	reppow.appendhold(imgdt)
	trappow.appendhold(imgdt)
	
	motpow.linear( f(camera,'imgpow'),    0.0)
	#repdet.linear( f(camera,'imgdetrep'), 0.0)
	repdet.linear( f(camera,'imgdettrap'), 0.0)
	trapdet.linear(f(camera,'imgdettrap'),0.0)
	reppow.linear( f(camera,'imgpowrep'), 0.0)
	trappow.linear(f(camera,'imgpowtrap'),0.0)

	maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), reppow.dt(), trappow.dt())

	motpow.extend(maxDT)
	repdet.extend(maxDT)
	trapdet.extend(maxDT)
	reppow.extend(maxDT)
	trappow.extend(maxDT)
	
	return motpow, repdet, trapdet, reppow, trappow, maxDT

#~ def statetransfer_wprobe(motpow, repdet, trapdet, reppow, trappow, bfield):
	#~ ss=f('CNC','cncstepsize')
	
	#~ fsrepdet = f('ODT','fsrepdet')
	#~ fstrapdet = f('ODT','fstrapdet')
	#~ fsreppow = f('ODT','fsreppow')
	#~ fstrappow = f('ODT','fstrappow')
	
	#~ bfield.appendhold(0.1)

	#~ maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

	#~ motpow.extend(maxDT)
	#~ repdet.extend(maxDT)
	#~ trapdet.extend(maxDT)
	#~ bfield.extend(maxDT)
	#~ reppow.extend(maxDT)
	#~ trappow.extend(maxDT)
	
	#~ bfield.linear(0,ss)
	#~ repdet.linear( fsrepdet, ss)
	#~ trapdet.linear( fstrapdet, ss)
	#~ reppow.linear( fsreppow, ss)
	#~ trappow.linear( fstrappow, ss)
	
	#~ fstatedt = f('ODT','fstatedt')
	#~ repdet.appendhold(0.1 + fstatedt)
	
	#~ maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

	#~ motpow.extend(maxDT)
	#~ repdet.extend(maxDT)
	#~ trapdet.extend(maxDT)
	#~ bfield.extend(maxDT)
	#~ reppow.extend(maxDT)
	#~ trappow.extend(maxDT)
	
	#~ return motpow, repdet, trapdet, reppow, trappow, bfield, maxDT

#~ def statetransfer_F32(motpow, repdet, trapdet, reppow, trappow, bfield):
	#~ ss=f('CNC','cncstepsize')
	
	#~ # Turn off repump for 100 us to transfer everything to the F=3/2 state
	#~ bfield.linear(0,0.0)
	#~ trappow.linear( 0, 0.0 )
	#~ trappow.appendhold(0.5)
	
	#~ maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

	#~ motpow.extend(maxDT)
	#~ repdet.extend(maxDT)
	#~ trapdet.extend(maxDT)
	#~ bfield.extend(maxDT)
	#~ reppow.extend(maxDT)
	#~ trappow.extend(maxDT)
	
	#~ return motpow, repdet, trapdet, reppow, trappow, bfield, maxDT
	
#~ def statetransfer_F12(motpow, repdet, trapdet, reppow, trappow, bfield):
	#~ ss=f('CNC','cncstepsize')
	
	#~ # Turn off repump for 100 us to transfer everything to the F=3/2 state
	#~ trapdet.linear( -12.0, ss)
	#~ repdet.linear( -35.0, ss)
	#~ reppow.linear( 0, 0.0 )
	#~ reppow.appendhold(1.6)
	
	#~ maxDT = max( motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt())

	#~ motpow.extend(maxDT)
	#~ repdet.extend(maxDT)
	#~ trapdet.extend(maxDT)
	#~ bfield.extend(maxDT)
	#~ reppow.extend(maxDT)
	#~ trappow.extend(maxDT)
	
	#~ return motpow, repdet, trapdet, reppow, trappow, bfield, maxDT
	



	
def run(s,camera):
	global report
	ss=f('CNC','cncstepsize')
	
	# Cool and Compress MOT
	# ENDCNC is defined as the time up to release from the MOT
	motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cncRamps()

	# Set imaging values
	motpow, repdet, trapdet, reppow, trappow, bfield, maxDT = imagingRamps(motpow, repdet, trapdet, reppow, trappow, bfield, camera)
	
	#Add waveforms to sequence
	s.analogwfm_add(ss,[motpow,repdet,trapdet,bfield,reppow,trappow])
	
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	ENDCNC = ss*math.ceil(ENDCNC/ss)
	
	#insert QUICK pulse  for fast ramping of the field gradient
	s.wait(-10.0)
	quickval = 1 if gen.bstr('CNC',report) == True else 0
	s.digichg('quick',quickval)
	s.wait(10.0)
	
	#Go to MOT release time and set QUICK back to low
	s.wait(ENDCNC)
	s.digichg('quick',0)
	
	#print s.tcur

	return s, ENDCNC


def goto_imaging_values(s,camera):
	global report
	ss=f('CNC','cncstepsize')
	
	#Set up channels
	motpow, repdet, trapdet, reppow, trappow, bfield = uvzsload_imaging()
	
	#Add waveforms to sequence
	s.analogwfm_add(ss,[motpow,repdet,trapdet,bfield,reppow,trappow])
	
	#Remeber, wait at least 50us before taking the picture
	return s
	
	
