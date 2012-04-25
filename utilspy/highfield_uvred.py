""" Does CNCMOT then loads UVMOT and then ramps up to high field.
    Atoms in the trap at high field are the starting point for many experiments"""


import wfm, gen, math, cnc, uvred, odt
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
	uvfppiezo, uvpow, motpow, repdet, trapdet, reppow, trappow, bfield, ENDUVMOT = uvred.uvcoolRamps(motpow, repdet, trapdet, reppow, trappow, bfield, ENDCNC)

	# Set imaging values
	camera = 'ANDOR'
	motpow, repdet, trapdet, reppow, trappow, maxDT = cnc.imagingRamps_nobfield(motpow, repdet, trapdet, reppow, trappow, camera)

	# Switch bfield to FESHBACH
	overlapdt    = float(report['ODT']['overlapdt'])
	rampdelay    = float(report['FESHBACH']['rampdelay'])
	rampbf       = float(report['FESHBACH']['rampbf'])
	bf           = float(report['FESHBACH']['bf'])
	feshbachdt   = float(report['FESHBACH']['feshbachdt'])
	switchondt  = float(report['FESHBACH']['switchondt'])
	switchdelay  = float(report['FESHBACH']['switchdelay'])
	bias         = float(report['FESHBACH']['bias'])
	biasrampdt   = float(report['FESHBACH']['rampdt'])

	bfield.chop(ENDUVMOT-overlapdt)
	bfield.appendhold(rampdelay)
	bfield.linear( bf, rampbf)
	bfield.extend(ENDUVMOT+feshbachdt)
	bfield.linear(0.0, 0.0)
	ENDBFIELD = feshbachdt
	bfield.appendhold( switchondt + switchdelay)
	bfield.linear(bias,biasrampdt)

	#---Ramp up ODT
	odtpow0 = odt.odt_wave('odtpow', f('ODT','odtpow0'), ss)
	odtpow0.extend(ENDUVMOT)



	#Add waveforms to sequence
	s.analogwfm_add(ss,[ motpow, repdet, trapdet, bfield, reppow, trappow, uvfppiezo, uvpow, odtpow0])
	
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	ENDUVMOT = ss*math.ceil(ENDUVMOT/ss)
	
	#insert QUICK pulse  for fast ramping of the field gradient
	s.wait(-10.0)
	quickval = 1 if gen.bstr('CNC',report) == True else 0
	s.digichg('quick',quickval)	
	s.wait(10.0)

	#insert UV pulse
	uvtime  = float(report['UVRED']['uvtime'])
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
	s.wait(-uvtime - ENDCNC)
	
	#Go to MOT release time and set QUICK back to low
	s.wait(ENDUVMOT)
	s.digichg('quick',0)

	#CAREFUL: State transfer should be programmed in uvred.py, as it is done un uvmot.py
	s.digichg('uvaom1',0)


	#RELEASE FROM MOT
	waitshutter=5.0
	s.wait(waitshutter)
	s.digichg('uvshutter',0)
	#~ s.wait(20.0)
	#~ s.digichg('uvaom1',0)
	#~ s.digichg('uvaom2',0)
	#~ s.wait(-20.0)
	s.wait(-waitshutter)

	s.digichg('motswitch',0) 
	s.digichg('motshutter',1)
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
	
	return s, toENDBFIELD 