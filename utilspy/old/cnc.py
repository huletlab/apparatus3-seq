"""Build ramps for cooling and compressing the MOT
"""

import wfm, math, gen
#Import the polynomial interpolator
from convert import cnv


def IMGvalues(params,camera):
	if camera=='ANDOR':
		#PARAMETERS FOR IMAGING SAMPLES AT THE END OF RAMPS
		motIMGpow = aos.motpow(float(params['ANDOR']['imgpow']))
		trapIMGdet = aos.trapdet(float(params['ANDOR']['imgdettrap']))
		repIMGdet = aos.repdet(float(params['ANDOR']['imgdetrep']))
		trapIMGpow = aos.trappow(float(params['ANDOR']['imgpowtrap']))
		repIMGpow = aos.reppow(float(params['ANDOR']['imgpowrep']))
		biascurrentIMG = aos.biascurrent(float(params['ANDOR']['imgbiascurrent']))
	elif camera=='BASLER':
		#PARAMETERS FOR IMAGING SAMPLES AT THE END OF RAMPS
		motIMGpow = aos.motpow(float(params['BASLER']['imgpow']))
		trapIMGdet = aos.trapdet(float(params['BASLER']['imgdettrap']))
		repIMGdet = aos.repdet(float(params['BASLER']['imgdetrep']))
		trapIMGpow = aos.trappow(float(params['BASLER']['imgtrappow']))
		repIMGpow = aos.reppow(float(params['BASLER']['imgreppow']))
		biascurrentIMG = aos.biascurrent(float(params['BASLER']['imgbiascurrent']))
	return [motIMGpow,trapIMGdet,repIMGdet,trapIMGpow,repIMGpow,biascurrentIMG]



def buildramps(aos,params,camera):
	
	[motIMGpow,trapIMGdet,repIMGdet,trapIMGpow,repIMGpow,biascurrentIMG]=IMGvalues(params,aos,camera)
	
	seqstepsize=float(params['SEQ']['stepsize'])
	analogstepsize=float(params['SEQ']['analogstepsize'])
	
	#PARAMETERS FOR CNC RAMPS
	
	motpowSS = aos.motpow(float(params['MOT']['motpow'])) #initial MOT power
	motpowCNC = aos.motpow(float(params['CNC']['motpowf'])) #final MOT power
	motpowDT = float(params['CNC']['dtmotpow']) #MOT ramp time
	motN = int(math.floor(motpowDT/analogstepsize)) #MOT N of samples
	motramp='L:/software/apparatus3/seq/ramps/motpow_CNC.txt'

	repdetSS = aos.repdet(float(params['MOT']['repdetSS'])) #initial rep det
	repdetCNC= aos.repdet(float(params['CNC']['repdetf']))#final rep det
	repdetDT=float(params['CNC']['dtrepdet'])# rep ramp time
	repdetN=int(math.floor(repdetDT/analogstepsize))#rep N of samples
	repramp='L:/software/apparatus3/seq/ramps/repdet_CNC.txt'

	trapdetSS = aos.trapdet(float(params['MOT']['trapdetSS'])) #initial trap det
	trapdetCNC= aos.trapdet(float(params['CNC']['trapdetf']))#final trap det
	trapdetDT=float(params['CNC']['dttrapdet'])# trap ramp time
	trapdetN=int(math.floor(trapdetDT/analogstepsize))#trap N of samples
	trapramp='L:/software/apparatus3/seq/ramps/trapdet_CNC.txt'

	biascurrentSS = aos.biascurrent(float(params['MOT']['biascurrent'])) #initial bias current
	biascurrentCNC = aos.biascurrent(float(params['CNC']['biascurrentf'])) #final bias current
	biascurrentDT = float(params['CNC']['dtbiascurrent']) #bias current ramp time
	biascurrentN = int(math.floor(biascurrentDT/analogstepsize)) #bias current N of samples
	biascurrentramp='L:/software/apparatus3/seq/ramps/biascurrent_CNC.txt'
	
	#PARAMETERS FOR UV COOLING RAMPS
	
	#uvpow=aos.uvpow(float(params['UV']['uvpow']))
	#time constraints means no calibration to start with
	#uvpow=float(params['UV']['uvpow'])
	#uvpowDT=float(params['UV']['dtuvpow'])
	#uvpowN=int(math.floor(motpowDT/analogstepsize))
	#uvpowramp='L:/software/apparatus3/seq/ramps/uvpow.txt'
	#uvpowrampA='L:/software/apparatus3/seq/ramps/uvpow_A.txt'
	
	motpowUV=aos.motpow(float(params['UV']['motpow']))
	uvmotpowDT=float(params['UV']['dtmot'])
	uvmotN=int(math.floor(uvmotpowDT/analogstepsize))
	uvmotramp='L:/software/apparatus3/seq/ramps/motramp_UV.txt'
	
	reppowSS = aos.reppow(float(params['MOT']['reppow'])) #initial rep pow
	reppowUV= aos.reppow(float(params['UV']['reppow']))#final rep pow
	reppowDT=float(params['UV']['dtmot'])# rep ramp time
	reppowN=int(math.floor(repdetDT/analogstepsize))#rep N of samples
	repPowRamp='L:/software/apparatus3/seq/ramps/reppow_CNC.txt'
	uvrepPowRamp='L:/software/apparatus3/seq/ramps/reppow_UV.txt'
	
	trappowSS = aos.trappow(float(params['MOT']['trappow'])) #initial trap pow
	trappowUV= aos.trappow(float(params['UV']['trappow']))#final trap pow
	trappowDT=float(params['UV']['dtmot'])# trap ramp time
	trappowN=int(math.floor(trappowDT/analogstepsize))#trap N of samples
	trapPowRamp='L:/software/apparatus3/seq/ramps/trappow_CNC.txt'
	uvtrapPowRamp='L:/software/apparatus3/seq/ramps/trappow_UV.txt'
	
	#uvdetI=aos.uvdet(float(params['UV']['uvdeti']))
	#uvdetF=aos.uvdet(float(params['UV']['uvdetf']))
	#again need to do calibrations for now use straight voltage
	uvdetI=float(params['UV']['uvdeti'])
	uvdetF=float(params['UV']['uvdetf'])
	uvdetDT=float(params['UV']['dtuvdet'])
	uvdetN=int(math.floor(uvdetDT/analogstepsize))
	uvdetramp='L:/software/apparatus3/seq/ramps/uvdet.txt'
	uvdetrampA='L:/software/apparatus3/seq/ramps/uvdet_A.txt'
	
	uvrepdet=aos.repdet(float(params['UV']['repdet']))
	uvrepdetDT=float(params['UV']['dtmot'])
	uvrepdetN=int(math.floor(uvrepdetDT/analogstepsize))
	uvrepramp='L:/software/apparatus3/seq/ramps/repdet_UV.txt'
	
	biascurrentUV=float(params['UV']['uvbiascurrent'])
	uvbiascurrentDT=float(params['UV']['dtmot'])
	uvbiascurrentN=int(math.floor(uvbiascurrentDT/analogstepsize))
	uvbiascurrentramp='L:/software/apparatus3/seq/ramps/biascurrent_UV.txt'
	
		
	#PARAMETERS FOR TRANSFER RAMPS
	#not ready for prime time
	#motpowTR=aos.motpow(float(params['TRANSFER']['motpow'])
	#trmotpowDT=float(params['TRANSFER']['detmotpow']
	#trmotN=int(math.floor(trmotpowDT/analogstepsize))
	#trmotramp='L:software/apparatus3/seq/ramps/motpow_TR.txt'
	
	maxDT=max(motpowDT,repdetDT,trapdetDT,reppowDT,trappowDT,biascurrentDT)
	maxN=int(math.floor(maxDT/analogstepsize))
	#uvmaxDT=max(uvmotpowDT,reppowDT,trappowDT,uvpowDT,uvdetDT)
	uvmaxDT=max(uvmotpowDT,reppowDT,trappowDT,uvdetDT,uvrepdetDT,uvbiascurrentDT)
	uvmaxN=int(math.floor(uvmaxDT/analogstepsize))
	
	holdtime=float(params['CNC']['holdtime']) 
	uvholdtime=float(params['UV']['holdtime'])
	transtime=float(params['TRANSFER']['holdtime'])
	
	duration=maxDT+holdtime+transtime

	#CREATE CNC RAMP FILES --->     MOT POWER,  REP 

	 #MOT POWER
	f=open(motramp,'w')
	for i in range(motN+1): 
		sample = '%.4f' % (motpowSS + (motpowCNC-motpowSS)*i/motN) #linear ramp
		f.write(sample)
		if i != motN:
			f.write(',')
	f.write('\n')
	f.close()

	#REPUMP DETUNING
	f=open(repramp,'w')
	for i in range(repdetN+1): 
		sample = '%.4f' % (repdetSS + (repdetCNC-repdetSS)*i/repdetN) #linear ramp
		f.write(sample)
		if i != repdetN:
			f.write(',')
	f.write('\n')
	f.close()

	#TRAP DETUNING
	f=open(trapramp,'w')
	for i in range(trapdetN+1): 
		sample = '%.4f' % (trapdetSS + (trapdetCNC-trapdetSS)*i/trapdetN) #linear ramp
		f.write(sample)
		if i != trapdetN:
			f.write(',')
	f.write('\n')
	f.close()
	
	#REPUMP POWER
	f=open(repPowRamp,'w')
	for i in range(maxN+1): 
		sample = '%.4f' % (reppowSS) #held constant
		f.write(sample)
		if i != maxN:
			f.write(',')
	f.write('\n')
	f.close()

	#TRAP POWER
	f=open(trapPowRamp,'w')
	for i in range(maxN+1):
		sample = '%.4f' % (trappowSS)  #held constant
		f.write(sample)
		if i != maxN:
			f.write(',')
	f.write('\n')
	f.close()

	 #BIAS CURRENT
	f=open(biascurrentramp,'w')
	for i in range(biascurrentN+1): #linear ramp
		sample = '%.4f' % (biascurrentSS + (biascurrentCNC-biascurrentSS)*i/biascurrentN)
		f.write(sample)
		if i != biascurrentN:
			f.write(',')
	f.write('\n')
	f.close()
	
	#UV POWER
	#f=open(uvpowramp,'w')
	#for i in range(maxN+1):
	#	sample = '%.4f'%(0.0000)
	#	f.write(sample)
	#	if i !=maxN:
	#		f.write(',')
	#f.write('\n')
	#f.close()

	#UV DETUNING
	f=open(uvdetramp,'w')
	for i in range(maxN+1):
		sample = '%.4f'%(uvdetI) #held constant
		f.write(sample)
		if i !=maxN:
			f.write(',')
	f.write('\n')
	f.close()

	# Append all ramps to longest length	
	wfm.appendhold(motramp, maxDT-motpowDT, analogstepsize)
	wfm.appendhold(trapramp, maxDT-trapdetDT, analogstepsize)
	wfm.appendhold(repramp, maxDT-repdetDT, analogstepsize)
	wfm.appendhold(biascurrentramp, maxDT-biascurrentDT, analogstepsize)
	
	#The rest of the holdtime values are appended to the waveforms
	wfm.appendhold(repramp, holdtime-uvholdtime, analogstepsize)
	wfm.appendhold(trapramp, holdtime-uvholdtime, analogstepsize)
	wfm.appendhold(motramp, holdtime-uvholdtime, analogstepsize)
	wfm.appendhold(biascurrentramp, holdtime-uvholdtime, analogstepsize)
	wfm.appendhold(repPowRamp, holdtime-uvholdtime, analogstepsize)
	wfm.appendhold(trapPowRamp, holdtime-uvholdtime, analogstepsize)
	#wfm.appendhold(uvpowramp, holdtime-uvholdtime, analogstepsize)
	wfm.appendhold(uvdetramp, holdtime-uvholdtime, analogstepsize)
	
	#BUILD UV RAMPS

	#MOT POWER UV
	f=open(uvmotramp,'w')
	for i in range(uvmotN+1): 
		sample = '%.4f' % (motpowCNC + (motpowUV-motpowCNC)*i/uvmotN) #linear ramp
		f.write(sample)
		if i != uvmotN:
			f.write(',')
	f.write('\n')
	f.close()

	#REPUMP POWER
	f=open(uvrepPowRamp,'w')
	for i in range(reppowN+1): 
		sample = '%.4f' % (reppowSS + (reppowUV-reppowSS)*i/reppowN) #linear ramp
		f.write(sample)
		if i != reppowN:
			f.write(',')
	f.write('\n')
	f.close()

	#TRAP POWER
	f=open(uvtrapPowRamp,'w')
	for i in range(trappowN+1):
		sample = '%.4f' % (trappowSS + (trappowUV-trappowSS)*i/trappowN)
		f.write(sample)
		if i != trappowN:
			f.write(',')
	f.write('\n')
	f.close()

	#UV DETUNING
	f=open(uvdetrampA,'w')
	for i in range(uvdetN+1):
		sample = '%.4f'%(uvdetI+(uvdetF-uvdetI)*i/uvdetN)
		f.write(sample)
		if i !=uvdetN:
			f.write(',')
	f.write('\n')
	f.close()
	
	#UV REPUMP DETUNING
	f=open(uvrepramp,'w')
	for i in range(uvrepdetN+1):
		sample = '%.4f'%(repdetCNC+(uvrepdet-repdetCNC)*i/uvrepdetN)
		f.write(sample)
		if i !=uvrepdetN:
			f.write(',')
	f.write('\n')
	f.close()
	
	#UV BIAS FIELD
	f=open(uvbiascurrentramp,'w')
	for i in range(biascurrentN+1): #linear ramp
		sample = '%.4f' % (biascurrentCNC + (biascurrentUV-biascurrentCNC)*i/uvbiascurrentN)
		f.write(sample)
		if i != uvbiascurrentN:
			f.write(',')
	f.write('\n')
	f.close()
	
	#UV POWER
	#f=open(uvpowrampA,'w')
	#for i in range(uvpowN+1):
	#	sample = '%.4f'%(uvpow*i/uvpowN)
	#	f.write(sample)
	#	if i !=uvpowN:
	#		f.write(',')
	#f.write('\n')
	#f.close()	
	
	# Append all ramps to longest length
	wfm.appendhold(uvmotramp, uvmaxDT-uvmotpowDT, analogstepsize)
	wfm.appendhold(uvrepPowRamp, uvmaxDT-reppowDT, analogstepsize)
	wfm.appendhold(uvtrapPowRamp, uvmaxDT-trappowDT, analogstepsize)
	wfm.appendhold(uvrepramp, uvmaxDT-uvrepdetDT, analogstepsize)
	wfm.appendhold(uvdetrampA, uvmaxDT-uvdetDT, analogstepsize)
	
	#The rest of the holdtime values are appended to the waveforms
	wfm.appendhold(uvmotramp, uvholdtime-uvmaxDT, analogstepsize)
	wfm.appendhold(uvrepPowRamp, uvholdtime-uvmaxDT, analogstepsize)
	wfm.appendhold(uvtrapPowRamp, uvholdtime-uvmaxDT, analogstepsize)
	wfm.appendhold(uvrepramp, uvholdtime-uvmaxDT, analogstepsize)
	wfm.appendhold(uvdetrampA, uvholdtime-uvmaxDT, analogstepsize)
	
	if gen.bstr('UV on',params)==True:
		#Ramps are combined
		wfm.appendramp(motramp,uvmotramp)
		wfm.appendramp(repPowRamp,uvrepPowRamp)
		wfm.appendramp(trapPowRamp,uvtrapPowRamp)
		wfm.appendramp(repramp,uvrepramp)
		wfm.appendramp(uvdetramp,uvdetrampA)
		wfm.appendramp(biascurrentramp,uvbiascurrentramp)
		#Remaining ramps are filled
		wfm.appendhold(trapramp, uvholdtime, analogstepsize)
	else:
		wfm.appendhold(motramp,uvholdtime,analogstepsize)
		wfm.appendhold(repPowRamp,uvholdtime,analogstepsize)
		wfm.appendhold(trapPowRamp,uvholdtime,analogstepsize)
		wfm.appendhold(repramp,uvholdtime,analogstepsize)
		wfm.appendhold(uvdetramp,uvholdtime,analogstepsize)
		wfm.appendhold(biascurrentramp,uvholdtime,analogstepsize)
		wfm.appendhold(trapramp,uvholdtime,analogstepsize)
	
	
	#10 more sample is appended before turning the MOT power  and trap/rep detuning/power to its imaging values
	#Thiese samples are not counted in the duration of the cncramps so the MOT AOM will be switched off at this point
	wfm.appendhold(motramp, 10*analogstepsize, analogstepsize)
	wfm.appendhold(trapramp, 10*analogstepsize, analogstepsize)
	wfm.appendhold(repramp, 10*analogstepsize, analogstepsize)
	wfm.appendhold(biascurrentramp, 10*analogstepsize, analogstepsize)
	wfm.appendhold(repPowRamp, 10*analogstepsize, analogstepsize)
	wfm.appendhold(trapPowRamp, 10*analogstepsize, analogstepsize)
	#wfm.appendhold(uvpowramp, 10*analogstepsize, analogstepsize)
	wfm.appendhold(uvdetramp, 10*analogstepsize, analogstepsize)
	
	#Then 10 samples are appended with the imaging value
	wfm.appendvalue(motramp,10*analogstepsize,analogstepsize,motIMGpow)
	wfm.appendvalue(trapramp,10*analogstepsize,analogstepsize,trapIMGdet)
	wfm.appendvalue(repramp,10*analogstepsize,analogstepsize,repIMGdet)
	wfm.appendvalue(repPowRamp, 10*analogstepsize, analogstepsize,repIMGpow)
	wfm.appendvalue(trapPowRamp, 10*analogstepsize, analogstepsize,trapIMGpow)
	wfm.appendvalue(biascurrentramp, 10*analogstepsize, analogstepsize, biascurrentIMG)
	#wfm.appendhold(uvpowramp, 10*analogstepsize, analogstepsize)
	wfm.appendhold(uvdetramp, 10*analogstepsize, analogstepsize)


	#END OF RAMP BUILDING
	return duration


def doCNC(s,aos,params,camera):
	#cool and compress mot
	duration = buildramps(aos,params,camera)
	seqstepsize=float(params['SEQ']['stepsize'])
	analogstepsize=float(params['SEQ']['analogstepsize'])
	
	motramp='L:/software/apparatus3/seq/ramps/motpow_CNC.txt'
	repramp='L:/software/apparatus3/seq/ramps/repdet_CNC.txt'
	trapramp='L:/software/apparatus3/seq/ramps/trapdet_CNC.txt'
	repPowRamp='L:/software/apparatus3/seq/ramps/reppow_CNC.txt'
	trapPowRamp='L:/software/apparatus3/seq/ramps/trappow_CNC.txt'
	biascurrentramp='L:/software/apparatus3/seq/ramps/biascurrent_CNC.txt'
	#uvpowramp='L:/software/apparatus3/seq/ramps/uvpow.txt'
	uvdetramp='L:/software/apparatus3/seq/ramps/uvdet.txt'
	
	s.analogwfm(analogstepsize,[ {'name':'motpow','path':motramp},\
						{'name':'repdet','path':repramp},\
						{'name':'trapdet','path':trapramp},\
						{'name':'reppow','path':repPowRamp},\
						{'name':'trappow','path':trapPowRamp},\
						{'name':'bfield','path':biascurrentramp},
						#{'name':'uvpow','path':uvpowramp},
						{'name':'uvdet','path':uvdetramp},\
			                                 ])
	#wait normally rounds down using floor, here the duration is changed before so that
	#the wait is rounded up
	duration = seqstepsize*math.ceil(duration/seqstepsize)
	s.wait(duration)
	return s


                
        



