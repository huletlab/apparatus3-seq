"""Constructs ramps relevant to the ODT
	
"""
import wfm, gen, math, cnc
#Import the polynomial interpolator
from convert import cnv

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])
	
def odt_evap(image):
	evap_ss = f('EVAP','evapss')

	p0   = f('ODT','odtpow')
	p1   = f('EVAP','p1')
	t1   = f('EVAP','t1')
	tau  = f('EVAP','tau')
	beta = f('EVAP','beta')
		
	odtpow = wfm.wave('odtpow', cnv('odtpow',p0), evap_ss)
	odtpow.Evap(p0, p1, t1, tau, beta, image)
	
	#~ odtpow.Exponential(pow0,powf,evap_dt,tau)
	#~ odtpow.linear( cnv('odtpow',powf), evap_ss)
	#~ odtpow.appendhold( evap_dt)
	
	maxDT = odtpow.dt()
	
	return odtpow, maxDT
	
def odt_lightshift(image):
	evap_ss = f('EVAP','evapss')

	p0   = f('ODT','odtpow')
	p1   = f('EVAP','p1')
	t1   = f('EVAP','t1')
	tau  = f('EVAP','tau')
	beta = f('EVAP','beta')
	
	waitdt = f('UVLS','waitdt')
	waitdt2 = f('UVLS', 'waitdt2')
	
	cdt = f('UVLS','cdt')
	cpow = f('UVLS','cpow')
	
	b0  = f('FESHBACH','bias')
	bf  = 0.0
	bdt = f('UVLS','bdt')
	bpulse = cnv('bfield',f('UVLS','bpulse'))
	dtpulse = f('UVLS','pulse')
	bimg = 0.0
	
	uvfreq = f('UVLS','uvfreq')
	det = cnv('uvdet',f('UVLS','uvdet'))
	power = f('UVLS','uvpow2')
		
	odtpow = wfm.wave('odtpow', cnv('odtpow',p0), evap_ss)
	bfield = wfm.wave('bfield', cnv ('bfield',b0), evap_ss)
	uv1freq = wfm.wave('uv1freq', 5.905, evap_ss)
	uvdet = wfm.wave('uvdet', 2.9, evap_ss)
	uvpow= wfm.wave('uvpow', cnv('uvpow',f('UV','uvpow')),evap_ss)
	#uvpow2= wfm.wave('uvpow2', power, evap_ss)
	
	uv1freq.linear( uvfreq, 10.0)
	uvdet.linear( det, 100 )
	uvpow.linear(  cnv('uvpow', f('UVLS','lspow')), 10.0)
	
	odtpow.Evap(p0, p1, t1, tau, beta, image)
	bfield.extend( odtpow.dt() )
	bfield.linear( bpulse , bdt )
	bfield.appendhold(waitdt)
	odtpow.extend( bfield.dt())
	
	odtpow.linear( cnv('odtpow',cpow), cdt)
	odtpow.appendhold( waitdt2)
	bfield.extend( odtpow.dt() )
		
	ENDC = max(odtpow.dt(), bfield.dt())
	
	
	hframpdt = f('UVLS','hframpdt')
	bfield.appendhold( dtpulse) 
	
	bfield.linear( cnv ('bfield',b0) , hframpdt)
	#bfield.linear( 0.0, evap_ss)
	
	totalDT = bfield.dt()
	
	
	odtpow.extend(totalDT)
	uv1freq.extend(totalDT)
	uvdet.extend(totalDT)
	
	return odtpow, bfield, uv1freq, uvdet, uvpow, ENDC
	
def odt_adiabaticDown(ss,STARTDELAY):	
	maxpow = f('ODT','odtpow')
	tau = f('ODT','tau')
	dt = 2*tau
	odtpow = wfm.wave('odtpow', cnv('odtpow',maxpow),ss)
	odtpow.extend(STARTDELAY +  f('ODT','intrap'))
	odtpow.AdiabaticRampDown(dt,tau,'odtpow')
	return odtpow
	

def odt_modulationRamps(ss,STARTDELAY):
	maxpow = f('ODT','odtpow')
	moddt = f('TRAPFREQ','moddt')
	modfreq = f('TRAPFREQ','modfreq')
	moddepth = f('TRAPFREQ','moddepth')

	odtpow = wfm.wave( 'odtpow',cnv('odtpow',maxpow),ss)
	odtpow.extend(STARTDELAY +  f('TRAPFREQ','intrapdt'))
	odtpow.SineMod( maxpow, moddepth, moddt, modfreq, 'odtpow')
	odtpow.linear( cnv('odtpow',maxpow) , ss )

	return odtpow 



