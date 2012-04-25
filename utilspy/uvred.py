"""Constructs the ramps for doing UV cooling and fluorescence imaging

"""


import wfm, gen, math, cnc
report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])

def uvcoolRamps(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC):
	ss=f('CNC','cncstepsize')
	uvfppiezo= wfm.wave('uvfppiezo',0.0,ss)
	uvfppiezo.extend( ENDCNC)
	
	#Put pulse on uvfppiezo
	uvfppiezo.linear( f('UVRED','pulsedet'), 0.0)
	
	uvfppiezo.appendhold( f('UVRED','dtpulse'))
	uvfppiezo.linear( 0.0, f('UVRED','dtpulseramp'))
	#uvfppiezo.dither( f('UVRED','dtpulse'), 3)
	#uvfppiezo.lineardither( 0.0, f('UVRED','dtpulseramp'),3)

	
	#Ramp down things quickly to UV values
	uvdt = f('UVRED','dt')
	motpow.linear(  f('UVRED','uvmotpow'), uvdt)
	reppow.linear(  f('UVRED','uvreppow'), uvdt)
	trappow.linear( 0.0               , uvdt)
	repdet.linear(  f('UVRED','uvrepdet'), uvdt)
	trapdet.linear( f('UVRED','uvtrapdet'),uvdt)
	bfield.linear(  f('UVRED','uvbfield'), uvdt)
	
	#Hold UV MOT bfield for uvmotdt 
	uvmotdt = f('UVRED','uvmotdt')
	bfield.appendhold(uvmotdt)

	#Ramp up the bfield during uvramp
	uvramp = f('UVRED','uvramp')
	bfield.linear( f('UVRED','uvbfieldf'), uvramp)
	
	#Hold lasers for uvdelayrep and then ramp lasers to optimal cool&compress values
	uvdelayrep = f('UVRED','uvdelayrep')
	uvpowfdt = f('UVRED','uvpowfdt')
	repdet.appendhold(uvdelayrep)
	motpow.appendhold(uvdelayrep)

	uvlramp = f('UVRED','uvlramp')
	motpow.linear( f('UVRED','uvmotpowf'), uvlramp)
	repdet.linear( f('UVRED','uvrepdetf'), uvlramp)
	
	#Hold everything for a little more
	uvhold = f('UVRED','uvhold')
	bfield.appendhold(uvhold)	
	
	ENDUVMOT = max( motpow.dt(), reppow.dt(), trappow.dt(), repdet.dt(), trapdet.dt(), bfield.dt() )
	
	#Insert ramps that are referenced from the end
	uvpowfdt = f('UVRED','uvpowfdt')
	uvpowrampdt = f('UVRED','uvpowrampdt')	
	uvpowf = f('UVRED','uvpowf')
	uvpow= wfm.wave('uvpow', f('UVRED','uvpow'),ss)
	#~ uvpow.extend( ENDUVMOT)
	uvpow.extend( ENDUVMOT-uvpowfdt) 
	uvpow.linear( uvpowf, uvpowrampdt)
	uvpow.extend( ENDUVMOT)
	
	reppowf= f('UVRED','uvreppowf')
	reppow.extend( ENDUVMOT-uvpowfdt)
	reppow.linear(reppowf, uvpowrampdt)
	reppow.extend (ENDUVMOT)

	reppowpump= f('UVRED','uvreppowpump')
	trappowpump= f('UVRED','uvtrappowpump')
	pumptime = f('UVRED','pumptime')
	reppow.chop(ENDUVMOT-pumptime,extra=0)
	trappow.extend(ENDUVMOT-pumptime)
	reppow.linear( reppowpump, ss)
	trappow.linear( trappowpump, ss)
	#
	#
	uvfppiezo.extend(ENDUVMOT)
	#~ overlapdt = f('ODT','overlapdt')
	#~ uvfppiezo.extend(ENDUVMOT-overlapdt)
	#~ uvfppiezo.linear( f('UVRED','cooldet'), 0.0)
	#~ uvfppiezo.appendhold( overlapdt + 3.0 )
	#~ uvfppiezo.linear( 0.0 , 0.0 ) 
	#
	#
	reppow.extend(ENDUVMOT)
	trappow.extend(ENDUVMOT)
	motpow.extend(ENDUVMOT)
	repdet.extend(ENDUVMOT)
	trapdet.extend(ENDUVMOT)
	bfield.extend(ENDUVMOT)
	uvpow.extend(ENDUVMOT)
	
	
	
	#Make sure everything has the same length before imaging
	#print motpow.dt(), repdet.dt(), trapdet.dt(), bfield.dt(), reppow.dt(), trappow.dt(), uvfppiezo.dt()
	#print motpow.N(), repdet.N(), trapdet.N(), bfield.N(), reppow.N(), trappow.N(), uvfppiezo.N()
	
	return uvfppiezo, uvpow, motpow,repdet, trapdet, reppow, trappow, bfield, ENDUVMOT
	

def run(s,camera):
	global report
	ss=f('CNC','cncstepsize')
	
	# Cool and Compress MOT
	# DURATION is defined as the time up to release from the MOT
	motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()
	
	# Load UVMOT from CNCMOT
	uvfppiezo, uvpow, motpow, repdet, trapdet, reppow, trappow, bfield, ENDUVMOT = uvcoolRamps(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC)

	# Imaging
	motpow, repdet, trapdet, reppow, trappow, bfield, maxDT = cnc.imagingRamps(motpow, repdet, trapdet, reppow, trappow, bfield,camera)

	uvfppiezo.extend(maxDT)
	uvpow.extend(maxDT)
	
	
	#Add the waveforms
	s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow])
	
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
	#insert QUICK pulse  for fast ramping of the field gradient
	s.wait(-10.0)
	quickval = 1 if gen.bstr('CNC',report) == True else 0
	s.digichg('quick',quickval)
	s.wait(10.0)
	
	#insert UV pulse
	s.wait(ENDCNC)
	s.wait(f('UVRED','uvtime'))
	#Shut down the UVAOM's and open the shutter
	s.wait(-50.0)
	s.digichg('uvaom1',0)
	s.digichg('uvaom2',0)
	s.digichg('uvshutter',1)
	s.wait(50.0)
	#Turn on UVAOM
	s.digichg('uvaom1',1)
	s.wait(-f('UVRED','uvtime') - ENDCNC)
	
	
	#Go to MOT release time turn off UV and set QUICK back to low
	s.wait(ENDUVMOT)
	s.digichg('uvaom1',0)
	s.digichg('quick',0)
	
	#print s.tcur
	
	return s, ENDUVMOT



