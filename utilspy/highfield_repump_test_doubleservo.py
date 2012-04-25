""" Does CNCMOT then loads UVMOT and then ramps up to high field.
    Atoms in the trap at high field are the starting point for many experiments"""


import wfm_test, gen, math, cnc, uvcooling_repump
report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])
	
	
def  go_to_highfield(s):

	#Keep ODT on
	ODT = gen.bstr('ODT',report)
	if ODT == True:
		s.digichg('odtttl',1)
	s.wait(20.0)

	ss = float(report['SEQ']['analogstepsize'])

	# Cool and Compress MOT
	# ENDCNC is defined as the time up to release from the MOT
	motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC = cnc.cncRamps()

	# Load UVMOT from CNCMOT
	uvfppiezo, uvpow2, uvpow, motpow, repdet, trapdet, reppow, trappow, bfield, ENDUVMOT = uvcooling_repump.uvcoolRamps_repump(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC)

	# Set imaging values
	camera = 'ANDOR'
	motpow, repdet, trapdet, reppow, trappow, maxDT = cnc.imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow, camera)

	# Switch bfield to FESHBACH 
	overlapdt    = float(report['ODT']['overlapdt'])
	rampdelay    = float(report['ODT']['rampdelay'])
	rampbf       = float(report['ODT']['rampbf'])
	bf           = float(report['ODT']['bf'])
	#holdbf       = float(report['ODT']['holdbf'])
	feshbachdt   = float(report['ODT']['feshbachdt'])
	switchondt  = float(report['FESHBACH']['switchondt'])
	#switchdt     = float(report['FESHBACH']['switchdt'])
	#offdelay     = float(report['FESHBACH']['offdelay'])
	#quickdelay   = float(report['FESHBACH']['quickdelay'])
	switchdelay  = float(report['FESHBACH']['switchdelay'])
	bias         = float(report['FESHBACH']['bias'])
	biasrampdt   = float(report['FESHBACH']['rampdt'])
	bias2         = float(report['FESHBACH']['bias2'])
	biasrampdt2   = float(report['FESHBACH']['rampdt2'])	

	bfield.chop(ENDUVMOT-overlapdt)
	bfield.appendhold(rampdelay)
	bfield.linear( bf, rampbf)
	#bfield.appendhold(holdbf)
	bfield.extend(ENDUVMOT+feshbachdt)
	bfield.linear(0.0, 0.0)
	#ENDBFIELD=(rampdelay+rampbf+holdbf-overlapdt)
	ENDBFIELD = feshbachdt
	#bfield.appendhold(-ENDBFIELD+offdelay+2*switchdt+quickdelay+switchdelay)
	bfield.appendhold( switchondt + switchdelay)
	bfield.linear(bias,biasrampdt)
	bfield.linear(bias2,biasrampdt2)
	
	
	rampupdt = float(report['ODT']['rampupdt'])
	updt = float(report['ODT']['updt'])
	overshootdt = float(report['ODT']['overshootdt'])
	
	#~ odtpow0 = wfm.wave('odtpow', 0.0, ss)
	#~ odtpow0.extend(ENDUVMOT-overlapdt-updt-rampupdt)
	#~ odtpow0.odt_linear( 0.0 , f('ODT','odtpow0'), rampupdt)
	#~ odtpow0.appendhold( updt)
	#~ odtpow0.odt_linear(f('ODT','odtpow0'), f('ODT','odtpow'), overshootdt)

	odtpow0 = wfm_test.wave('odtpow', f('ODT','odtpow0'), ss)
	odtpow0.extend(ENDUVMOT-overlapdt)
	odtpow0.odt_linear(f('ODT','odtpow0'), f('ODT','odtpow'), overshootdt)

	
	EXTRA = max( overshootdt - (bfield.dt() - (ENDUVMOT-overlapdt-updt-rampupdt)) , 0.0) 
	print "...EXTRA time to allow for ODT overshoot = %f"  % EXTRA


	#Add waveforms to sequence
	s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow, uvpow2,odtpow0])
	
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
	#insert QUICK pulse  for fast ramping of the field gradient
	s.wait(-10.0)
	quickval = 1 if gen.bstr('CNC',report) == True else 0
	s.digichg('quick',quickval)	
	s.wait(10.0)

	#insert UV pulse
	uvtime  = float(report['UV']['uvtime'])
	s.wait(ENDCNC)
	s.digichg('quick',0)
	s.wait(uvtime)
	#Shut down the UVAOM's and open the shutter
	s.wait(-50.0)
	s.digichg('uvaom1',0)
	s.digichg('uvaom2',0)
	s.digichg('uvshutter',1)
	s.wait(50.0)
	#Turn on UVAOM
	s.digichg('uvaom1',1)
	s.wait(-uvtime)
	
	# Turn off Red Light Completly and turn UV repump after uvramp
	uvrepswitchdt = float(report['UV']['uvrepswitchdt'])
	s.wait(uvrepswitchdt)
	s.digichg('uvaom2',1)
	s.digichg('motswitch',0) 
	s.digichg('motshutter',1)
	s.wait(-uvrepswitchdt)
	
	s.wait(-ENDCNC)

	
	#Go to MOT release time turn off UV and set QUICK back to low
	s.wait(ENDUVMOT)
	s.digichg('quick',0)

	#Turn off UV repump before optical pumping
	pumpdelay =float(report['UV']['pumpdelay'])
	uvhold = float(report['UV']['uvhold'])
	s.wait(pumpdelay-uvhold)
	s.digichg('uvaom2',0)
	s.wait(-pumpdelay+uvhold)
	
	
	#Leave UVMOT on for state transfer
	fstatedt  = float(report['ODT']['fstatedt'])
	s.wait(fstatedt)
	s.digichg('uvaom1',0)
	s.wait(-fstatedt) 


	#RELEASE FROM MOT
	waitshutter=5.0
	s.wait(waitshutter)
	s.digichg('uvshutter',0)
	s.wait(100.0)
	s.digichg('uvaom1',0)
	s.digichg('uvaom2',0)
	s.wait(-100.0)
	s.wait(-waitshutter)
	
	

	# s.digichg('motswitch',0) 
	# s.digichg('motshutter',1) 
	s.digichg('field',0)

	#Insert ODT overlap with UVMOT and switch field to FESHBACH
	overlapdt = float(report['ODT']['overlapdt'])
	servodt = float(report['ODT']['servodt'])
	s.wait(-overlapdt-servodt)
	s.digichg('odt7595',1)
	s.wait(servodt)
	s.digichg('odtttl',1)
	#feshbachdt = rampdelay + rampbf + holdbf
	s.wait(overlapdt)
	s.wait( feshbachdt )
	s.digichg('feshbach',1)
	#s.wait(overlapdt - feshbachdt)
	#s.wait( -feshbachdt)
	

	#s.wait(offdelay)
	#s.wait(2*switchdt)
	#s.wait(quickdelay)
	s.wait(switchondt)
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
	s.wait(switchdelay+biasrampdt)
	s.digichg('quick',0)
	s.wait(-biasrampdt)
	#s.wait(-switchdelay-quickdelay-2*switchdt-offdelay)
	s.wait(-switchdelay - switchondt - feshbachdt - ss)

	#At this point the time sequence is at ENDUVMOT
	
	#This is the time until the end of the bfield ramp
	#toENDBFIELD = biasrampdt + switchdelay + quickdelay + 2*switchdt + offdelay
	toENDBFIELD = biasrampdt + switchdelay + switchondt + feshbachdt
	
	return s, toENDBFIELD + EXTRA
