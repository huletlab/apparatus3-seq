""" Does CNCMOT then loads UVMOT and then ramps up to high field.
    Atoms in the trap at high field are the starting point for many experiments"""


import wfm, gen, math, cnc, uvmot, odt
report=gen.getreport()

#GET SECTION CONTENTS
SEQ = gen.getsection('SEQ')
UV = gen.getsection('UV')
SHUNT = gen.getsection('SHUNT')
FB = gen.getsection('FESHBACH')
ODT = gen.getsection('ODT')

	
def  go_to_highfield(s):

	#---Keep ODT on
	odton = gen.bstr('ODT',report)
	if odton == True:
		s.digichg('odtttl',1)
	s.wait(20.0)

	ss = SEQ.analogstepsize

	#---Cool and Compress MOT
	#---ENDCNC is defined as the time up to release from the MOT
	motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()

	#---Load UVMOT from CNCMOT
	uvpow2, uvpow, motpow, bfield, ENDUVMOT = uvmot.uvRamps(motpow, bfield, ENDCNC)

	repdet.extend(ENDUVMOT)
	trapdet.extend(ENDUVMOT)
	reppow.extend(ENDUVMOT)
	trappow.extend(ENDUVMOT)
	
	#---Make sure everything has the same length before setting imaging values
	#--- Set imaging values
	camera = 'ANDOR'
	motpow, repdet, trapdet, reppow, trappow, maxDT = cnc.imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow, camera)


	#---Switch bfield to FESHBACH 
	bfield.appendhold(FB.rampdelay)
	bfield.linear( FB.bf, FB.rampbf)
	bfield.appendhold( FB.feshbachdt)
	bfield.linear(0.0, 0.0)
	bfield.appendhold( FB.switchondt + FB.switchdelay + UV.extradt)
	bfield.linear(FB.bias,FB.rampdt)


	#---Set the starting voltage for the ODT
	odtpow0 = odt.odt_wave('odtpow', ODT.odtpow0, ss)
	odtpow0.extend(ENDUVMOT)
	
	#---Change shunt value from motV to hfV before going to highfield
	shunt = wfm.wave('gradientfield', SHUNT.motV, ss, volt = SHUNT.motV)
	shunt.extend(ENDUVMOT + FB.rampdelay + FB.rampbf + FB.feshbachdt + UV.extradt) 
	#shunt.linear(SHUNT.hfV, 0.0,volt =SHUNT.hfV)	
	shunt.linear(SHUNT.hfV, 0.0,volt =0.0)	
	
	
	wfms = [ motpow, repdet, trapdet, bfield, reppow, trappow, uvpow, uvpow2,odtpow0, shunt]

	
	#---Add waveforms to sequence
	s.analogwfm_add(ss,wfms)
	
		
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
	#---Insert QUICK pulse for fast ramping of the field gradient during CNC
	s.wait(-10.0)
	quickval = 1 if gen.bstr('CNC',report) == True else 0
	s.digichg('quick',quickval)	
	s.wait(10.0)
	s.wait(ENDCNC)
	s.digichg('quick',0)
	
	#---Go back in time, shut down the UVAOM's 
	#---UVAOM's were on to keep them warm
	s.wait(UV.clearaoms)
	s.digichg('uvaom1',0)
	s.digichg('uvaom2',0)
	s.wait(-UV.clearaoms)
	
	#---Insert ODT overlap 
	s.wait(-ODT.overlapdt-ODT.servodt)
	s.digichg('odt7595',1)
	s.wait(ODT.servodt)
	s.digichg('odtttl',1)
	s.wait(ODT.overlapdt)
	
	#---Turn OFF red light
	s.wait(UV.delay_red)
	s.digichg('motswitch',0) 
	s.digichg('motshutter',1)
	s.wait(-UV.delay_red)
	
	#---Turn ON UVAOM's
	s.wait(UV.delay_uv)
        #---make sure to open the shutter:
        s.wait(UV.openshutter)
	s.digichg('uvshutter',1)
        s.wait(-UV.openshutter)

	s.digichg('uvaom1',1)
	s.digichg('uvaom2',1)
	s.wait(-UV.delay_uv)
	

	#---Go to MOT release time
	s.wait(-ENDCNC)
	s.wait(ENDUVMOT)
	

	#---Go to end of field rampdown and set QUICK back to low
	s.wait(FB.rampdelay+FB.rampbf) 
	s.digichg('quick',0)
	

	#---Wait in the UVMOT and then do optical pumping
	s.wait(UV.extradt) 
	s.wait(-UV.pumptime)
	s.digichg('uvaom2',0)
	s.wait(UV.pumptime)
	#---Turn OFF UVAOM
	s.digichg('uvaom1',0)
	#---Close UV shutter
	waitshutter=UV.closeshutter
	s.wait(waitshutter)
	s.digichg('uvshutter',0)
	s.wait(-waitshutter)

	#---Turn OFF MOT magnetic field and switch it to FESHBACH
	s.digichg('field',0)
	s.wait( FB.feshbachdt )
	s.digichg('feshbach',1)
	s.wait(FB.switchondt)
	do_quick=1
	s.digichg('field',1)
	s.digichg('hfquick',do_quick)
	s.digichg('quick',do_quick)
	#Can't leave quick ON for more than quickmax
	quickmax=100.
	s.wait(quickmax)
	s.digichg('hfquick',0)
	s.digichg('quick',0)
	s.wait(-quickmax)
	#
	s.wait(FB.switchdelay+FB.rampdt)
	s.digichg('quick',0)
	s.wait(-FB.rampdt)
	s.wait(-FB.switchdelay - FB.switchondt - FB.feshbachdt - ss)


	#---At this point the time sequence is at ENDUVMOT
	#---Leave the sequence at the end of the UVMOT, but provide the amount
	#---of time that it needs to wait to go to ENDBFIELD
	toENDBFIELD = FB.rampdt + FB.switchdelay + FB.switchondt + FB.feshbachdt
	
	return s, toENDBFIELD
