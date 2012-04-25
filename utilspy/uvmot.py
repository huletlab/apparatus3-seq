"""Constructs the ramps for doing UV cooling and fluorescence imaging

"""


import wfm, gen, math, cnc
report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])

def uvRamps(motpow, bfield, ENDCNC):
	ss=f('CNC','cncstepsize')
	
	#---Put pulse on uvfppiezo
	uvfppiezo= wfm.wave('uvfppiezo',0.0,ss)
	uvfppiezo.extend( ENDCNC)
	uvfppiezo.linear( f('UV','pulsedet'), 0.0)	
	uvfppiezo.appendhold( f('UV','dtpulse'))
	uvfppiezo.linear( 0.0, f('UV','dtpulseramp'))
	#uvfppiezo.dither( f('UV','dtpulse'), 3)
	#uvfppiezo.lineardither( 0.0, f('UV','dtpulseramp'),3)


	uvdt = f('UV','dt')
	#---Ramp down red power
	motpow.linear(  0.002, uvdt) #0.002 is max attenuation before RF switch
	
	#---Bfield ramp
	dtload = f('UV','dtload_bfield')
	dtcnc = f('UV','dtcnc_bfield')
	uvhold = f('UV','uvhold')
	bfield.linear(  f('UV','uvbfield'), uvdt)
	bfield.appendhold(dtload)
	bfield.linear( f('UV','uvbfieldf'), dtcnc)
	#bfield.appendhold(uvhold)	
	
	ENDUVMOT = max( motpow.dt(), bfield.dt() )
	
	#---UVPOW ramps
	dtload_uvpow = f('UV','dtload_uvpow')
	dtcnc_uvpow = f('UV','dtcnc_uvpow')
	#
	uvpow= wfm.wave('uvpow', f('UV','uvpow'),ss)
	uvpow2= wfm.wave('uvpow2',f('UV','uvpow2'),ss)
	#
	uvpow.extend(ENDCNC+uvdt+dtload)
	uvpow2.extend(ENDCNC+uvdt+dtload)
	#
	uvpow.linear( f('UV','uvpowf'), dtcnc_uvpow)
	uvpow2.linear( f('UV','uvpow2f') , dtcnc_uvpow)	
	
	#---ENDUVMOT is defined as the point where the longest of bfield 
	#---or uvpow ramps ends
	maxramp = max( motpow.dt(), bfield.dt(), uvpow.dt(), uvpow2.dt() )
	ENDUVMOT = maxramp + uvhold
	bfield.extend(ENDUVMOT)
	uvpow.extend(ENDUVMOT)
	uvpow2.extend(ENDUVMOT)	
	
	uvfppiezo.extend(ENDUVMOT)
	motpow.extend(ENDUVMOT)
	bfield.extend(ENDUVMOT)
	uvpow.extend(ENDUVMOT)
	uvpow2.extend(ENDUVMOT)

	return uvfppiezo, uvpow2, uvpow, motpow, bfield, ENDUVMOT
	
def run(s,camera):
	global report
	ss=f('CNC','cncstepsize')
	
	# Cool and Compress MOT
	# DURATION is defined as the time up to release from the MOT
	motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()
	
	# Load UVMOT from CNCMOT
	uvfppiezo, uvpow2, uvpow, motpow, bfield, ENDUVMOT = uvRamps(motpow, bfield, ENDCNC)

	repdet.extend(ENDUVMOT)
	trapdet.extend(ENDUVMOT)
	reppow.extend(ENDUVMOT)
	trappow.extend(ENDUVMOT)


	# Imaging
	motpow, repdet, trapdet, reppow, trappow, bfield, maxDT = cnc.imagingRamps(motpow, repdet, trapdet, reppow, trappow, bfield,camera)

	uvfppiezo.extend(maxDT)
	uvpow.extend(maxDT)
	uvpow2.extend(maxDT)
	
	
	#---Add waveforms to sequence
	s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow, uvpow2])
	
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
	#---Insert QUICK pulse for fast ramping of the field gradient during CNC
	s.wait(-10.0)
	quickval = 1 if gen.bstr('CNC',report) == True else 0
	s.digichg('quick',quickval)
	s.wait(10.0)
	s.wait(ENDCNC)
	#s.digichg('quick',0)
	
	#---Go back in time, shut down the UVAOM's and open the shutter
	s.wait(-50.0)
	s.digichg('uvaom1',0)
	s.digichg('uvaom2',0)
	s.digichg('uvshutter',1)
	s.wait(50.0)
	
	#---Turn OFF red light
	delay_red = float(report['UV']['delay_red'])
	s.wait(delay_red)
	s.digichg('motswitch',0) 
	#s.digichg('motshutter',1)
	s.wait(-delay_red)
	
	#---Turn ON UVAOM's
	delay_uv = float(report['UV']['delay_uv'])
	s.wait(delay_uv)
	s.digichg('uvaom1',1)
	s.digichg('uvaom2',1)
	s.wait(-delay_uv)
	
	s.wait(-ENDCNC)
	
	#---Go to MOT release time and set QUICK back to low, turn off UV
	s.wait(ENDUVMOT)
	s.digichg('quick',0)
	s.digichg('uvaom1',0)
	s.digichg('uvaom2',0)
	
	#---Turn red light back on for imaging.
	s.digichg('motswitch',1)
	
	#print s.tcur
	
	return s, ENDUVMOT
	


