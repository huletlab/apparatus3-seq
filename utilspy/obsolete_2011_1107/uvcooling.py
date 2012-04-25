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
	uvfppiezo.linear( f('UV','pulsedet'), 0.0)
	
	uvfppiezo.appendhold( f('UV','dtpulse'))
	uvfppiezo.linear( 0.0, f('UV','dtpulseramp'))
	#uvfppiezo.dither( f('UV','dtpulse'), 3)
	#uvfppiezo.lineardither( 0.0, f('UV','dtpulseramp'),3)

	
	#Ramp down things quickly to UV values
	uvdt = f('UV','dt')
	motpow.linear(  f('UV','uvmotpow'), uvdt)
	reppow.linear(  f('UV','uvreppow'), uvdt)
	trappow.linear( 0.0               , uvdt)
	repdet.linear(  f('UV','uvrepdet'), uvdt)
	trapdet.linear( f('UV','uvtrapdet'),uvdt)
	bfield.linear(  f('UV','uvbfield'), uvdt)
	
	#Hold UV MOT bfield for uvmotdt 
	uvmotdt = f('UV','uvmotdt')
	bfield.appendhold(uvmotdt)

	#Ramp up the bfield during uvramp
	uvramp = f('UV','uvramp')
	bfield.linear( f('UV','uvbfieldf'), uvramp)
	
	#Hold lasers for uvdelayrep and then ramp lasers to optimal cool&compress values
	uvdelayrep = f('UV','uvdelayrep')
	uvpowfdt = f('UV','uvpowfdt')
	repdet.appendhold(uvdelayrep)
	motpow.appendhold(uvdelayrep)

	uvlramp = f('UV','uvlramp')
	motpow.linear( f('UV','uvmotpowf'), uvlramp)
	repdet.linear( f('UV','uvrepdetf'), uvlramp)
	
	#Hold everything for a little more
	uvhold = f('UV','uvhold')
	bfield.appendhold(uvhold)	
	
	ENDUVMOT = max( motpow.dt(), reppow.dt(), trappow.dt(), repdet.dt(), trapdet.dt(), bfield.dt() )
	
	#Insert ramps that are referenced from the end
	uvpowfdt = f('UV','uvpowfdt')
	uvpowrampdt = f('UV','uvpowrampdt')	
	uvpowf = f('UV','uvpowf')
	uvpow= wfm.wave('uvpow', f('UV','uvpow'),ss)
	#~ uvpow.extend( ENDUVMOT)
	uvpow.extend( ENDUVMOT-uvpowfdt) 
	uvpow.linear( uvpowf, uvpowrampdt)
	uvpow.extend( ENDUVMOT)
	
	reppowf= f('UV','uvreppowf')
	reppow.extend( ENDUVMOT-uvpowfdt)
	reppow.linear(reppowf, uvpowrampdt)
	reppow.extend (ENDUVMOT)

	reppowpump= f('UV','uvreppowpump')
	trappowpump= f('UV','uvtrappowpump')
	pumptime = f('UV','pumptime')
	reppow.chop(ENDUVMOT-pumptime,extra=0)
	trappow.extend(ENDUVMOT-pumptime)
	reppow.linear( reppowpump, ss)
	trappow.linear( trappowpump, ss)
	#
	#
	uvfppiezo.extend(ENDUVMOT)
	#~ overlapdt = f('ODT','overlapdt')
	#~ uvfppiezo.extend(ENDUVMOT-overlapdt)
	#~ uvfppiezo.linear( f('UV','cooldet'), 0.0)
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
	s.wait(f('UV','uvtime'))
	#Shut down the UVAOM's and open the shutter
	s.wait(-50.0)
	s.digichg('uvaom1',0)
	s.digichg('uvaom2',0)
	s.digichg('uvshutter',1)
	s.wait(50.0)
	#Turn on UVAOM
	s.digichg('uvaom1',1)
	s.wait(-f('UV','uvtime') - ENDCNC)
	
	
	#Go to MOT release time turn off UV and set QUICK back to low
	s.wait(ENDUVMOT)
	s.digichg('uvaom1',0)
	s.digichg('quick',0)
	
	#print s.tcur
	
	return s, ENDUVMOT



