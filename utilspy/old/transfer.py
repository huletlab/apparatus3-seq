""" transfer: build ramps for transfer into lowest hyperfine state turn off MOT/UV and prepare AOMs for imaging"""

def IMGvalues(params,aos,camera):
	if camera=='ANDOR':
		#PARAMETERS FOR IMAGING SAMPLES AT THE END OF RAMPS
		motIMGpow = aos.motpow(float(params['ANDOR']['imgpow']))
		repIMGdet = aos.repdet(float(params['ANDOR']['imgdetrep']))
		trapIMGdet = aos.trapdet(float(params['ANDOR']['imgdettrap']))
		repIMGpow = aos.reppow(float(params['ANDOR']['imgpowrep']))
		trapIMGpow = aos.trappow(float(params['ANDOR']['imgpowtrap']))
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