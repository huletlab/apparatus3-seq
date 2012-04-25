"""Constructs ramps relevant to the ODT
	
"""
import wfm_test, gen, math, cnc

report=gen.getreport()

def f(sec,key):
	global report
	return float(report[sec][key])
	
def odt_evap(image,servo=1):
	evap_ss = f('EVAP','evapss')

	p0   = f('ODT','odtpow')
	p1   = f('EVAP','p1')
	t1   = f('EVAP','t1')
	tau  = f('EVAP','tau')
	beta = f('EVAP','beta')
	
	offset = f('EVAP','offset')
	t2     = f('EVAP','t2')
	tau2   = f('EVAP','tau2')
	channel = 'odtpow' if servo else 'odtpow_nonservo'
	odtpow = wfm_test.wave(channel, p0, evap_ss)
	#odtpow.Evap(p0, p1, t1, tau, beta, image)
	#odtpow.Evap2(p0, p1, t1, tau, beta, offset, t2, tau2, image)
	odtpow.Evap3(p0, p1, t1, tau, beta, offset, t2, tau2, image,servo)
	
	#~ odtpow.Exponential(pow0,powf,evap_dt,tau)
	#~ odtpow.linear( powf, evap_ss)
	#~ odtpow.appendhold( evap_dt)
	
	maxDT = odtpow.dt()
	
	return odtpow, maxDT
	
def odt_lightshift_evap(image):
	evap_ss = f('EVAP','evapss')

	p0   = f('ODT','odtpow')
	p1   = f('EVAP','p1')
	t1   = f('EVAP','t1')
	tau  = f('EVAP','tau')
	beta = f('EVAP','beta')
	
	odtpow = wfm.wave('odtpow', p0, evap_ss)
	odtpow.Evap(p0, p1, t1, tau, beta, image)
	
	uvdet = wfm.wave('uvdet', None , evap_ss, volt=3.744)
	uvdet.linear( f('UVLS','uvdet'), 100 )
	
	maxDT = odtpow.dt()
	uvdet.extend(maxDT)
	
	return odtpow, uvdet, maxDT
	
def odt_lightshift(odtpow0):
	ls_ss = f('UVLS','ls_ss')

	odtpow  = wfm.wave('odtpow',  None, ls_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), ls_ss)
	uv1freq = wfm.wave('uv1freq', None , ls_ss, volt=7.600)
	uvpow   = wfm.wave('uvpow',   f('UV','uvpow'), ls_ss)
	
	uv1freq.linear( None, 10.0, volt=f('UVLS','uvfreq'))
	uvpow.linear(  f('UVLS','lspow'), 10.0)
		
	odtpow.linear( f('UVLS','cpow'), f('UVLS','cdt') )
	odtpow.appendhold( f('UVLS','waitdt'))
	bfield.extend(odtpow.dt())
	
	bfield.linear( f('UVLS','bpulse'), f('UVLS','bdt') )
	bfield.appendhold( f('UVLS','waitdt2'))
	bfield.appendhold( f('UVLS','waitdt3'))
	ENDC=bfield.dt()

	#~ bfield.linear( f('UVLS','bpulse') , f('UVLS','bdt') )
	#~ bfield.appendhold(f('UVLS','waitdt'))
	#~ odtpow.extend(bfield.dt())
	
	#~ odtpow.linear( f('UVLS','cpow'), f('UVLS','cdt') )
	#~ odtpow.appendhold( f('UVLS', 'waitdt2'))
	#~ ENDC = odtpow.dt()
	
	#~ bfield.extend( odtpow.dt() )
	
	odtpow.extend( bfield.dt() )
	bfield.appendhold( f('UVLS','dtpulse')) 
	

	bfield.linear( f('FESHBACH','bias') , f('UVLS','hframpdt'))
	#bfield.linear( 0.0, f('UVLS','hframpdt'))
	
	totalDT = bfield.dt()
	
	odtpow.extend(totalDT)
	uv1freq.extend(totalDT)
	uvpow.extend(totalDT)
	
	return odtpow, bfield, uv1freq, uvpow, ENDC
	
def odt_trapfreq(odtpow0):
	mod_ss = f('TRAPFREQ','mod_ss')

	odtpow  = wfm.wave('odtpow',  None, mod_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), mod_ss)
	
	odtpow.linear( f('TRAPFREQ','cpow'), f('TRAPFREQ','cdt') )
	odtpow.appendhold( f('TRAPFREQ','waitdt'))
	bfield.extend(odtpow.dt())
	
	bfield.linear( f('TRAPFREQ','bmod'), f('TRAPFREQ','bdt') )
	bfield.appendhold( f('TRAPFREQ','waitdt2'))
	
	odtpow.extend( bfield.dt() )
	#odtpow.SineMod( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	#odtpow.SineMod2( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	odtpow.SineMod3( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	
	return odtpow, bfield, odtpow.dt()
	
def odt_flicker(odtpow0):
	flicker_ss = f('FLICKER','flicker_ss')

	odtpow  = wfm.wave('odtpow',  None, flicker_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), flicker_ss)
	
	odtpow.linear( f('FLICKER','cpow'), f('FLICKER','cdt') )
	odtpow.appendhold( f('FLICKER','waitdt'))
	bfield.extend(odtpow.dt())
	
	bfield.linear( f('FLICKER','bflick'), f('FLICKER','bdt') )
	bfield.appendhold( f('FLICKER','waitdt2'))
	
	odtpow.extend( bfield.dt() )
	
	return odtpow, bfield, odtpow.dt()
	
def odt_dbz(odtpow0):
	dbz_ss = f('DBZ','dbz_ss')

	odtpow  = wfm.wave('odtpow',  None, dbz_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), dbz_ss)
	
	odtpow.linear( f('DBZ','cpow'), f('DBZ','cdt') )
	odtpow.appendhold( f('DBZ','waitdt'))
	bfield.extend(odtpow.dt())
	
	#Field goes to zero
	bfield.linear( 0.0, f('DBZ','bdt') )
	bfield.appendhold( f('DBZ','waitdt2'))
	#Field TTL goes off here
	OFFDT1 = bfield.dt()
	bfield.appendhold( f('DBZ','switchdt'))
	#Field switches from feshbach to gradient here
	bfield.appendhold( f('DBZ','switchdt'))
	#Field TTL goes back on here
	bfield.appendhold( f('DBZ','switchdt'))
	bfield.linear( f('DBZ', 'dbz'), f('DBZ','rampdt'))
	bfield.appendhold( f('DBZ','holddt'))
	#Field goes off here (atoms should be oscillating in the trap)
	bfield.linear( 0.0, f('DBZ','dbz_ss'))
	
	odtpow.extend( bfield.dt() )
	return odtpow, bfield, OFFDT1
