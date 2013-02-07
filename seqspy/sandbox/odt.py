"""Constructs ramps relevant to the ODT
	
"""
import sys
sys.path.append('L:/software/apparatus3/seq')
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seqconf, wfm, gen, math, cnc, time, os, numpy, hashlib, evap, lattice, physics, errormsg
report=gen.getreport()

#GET SECTION CONTENTS
ODT  = gen.getsection('ODT')
EVAP = gen.getsection('EVAP')
DIMPLE = gen.getsection('DIMPLE')
FB   = gen.getsection('FESHBACH')
LBF  = gen.getsection('LATTICEBRAGGFIELD')
IL   = gen.getsection('INTOLATTICE')


def f(sec,key):
	global report
	return float(report[sec][key])
	


def odt_evap(scale=1.0):
	odtpow = odt_wave('odtpow', ODT.p0, ODT.evapss)
	### SELECT EVAP TRAJECTORY HERE###
	finalcpow = odtpow.Evap8(\
							ODT.odtpow, \
							EVAP.p1, \
							EVAP.t1, 
							EVAP.tau, \
							EVAP.beta, \
							EVAP.offset, \
							EVAP.t2, \
							EVAP.tau2, \
							EVAP.smoothdt, \
							EVAP.image, \
							EVAP.scale \
							)
	#---Here, go ahead and save the finalcpow to the report
	gen.save_to_report('EVAP','finalcpow', finalcpow)
	
	#---Setup ipganalog ramp
	ipganalog = ipg_wave('ipganalog', 10., evap_ss)
	if ODT.use_servo == 0:
		ipganalog.extend( odtpow.dt() )
	elif ODT.use_servo == 1:
		ipganalog.follow( odtpow )
	
	maxDT = odtpow.dt()
	return odtpow, maxDT, finalcpow, ipganalog
	


def odt_evap_field(scale =1.0):
	field_ramp_time = EVAP.fieldrampt0*scale
	field_ramp_dt   = EVAP.fieldrampdt*scale
	
	ramp=[]
	hashbase = ''
	hashbase = hashbase + '%.8f' % EVAP.image
	hashbase = hashbase + '%.8f' % EVAP.evapss
	hashbase = hashbase + '%.8f' % field_ramp_time
	hashbase = hashbase + '%.8f' % field_ramp_dt
	hashbase = hashbase + '%.8f' % FB.bias
	hashbase = hashbase + '%.8f' % EVAP.fieldrampfinal
	hashbase = hashbase + '%.8f' % scale
	hashbase = hashbase + wfm.rawcalibdat( 'bfield' ) 

	
	#---Here, go ahead and save the trajectory path to the report
	ramphash = seqconf.ramps_dir() +'Evap_field_withscale'+ hashlib.md5( hashbase).hexdigest()
	gen.save_to_report('EVAP','ramp_field', ramphash)

	#---Setup field ramp
	bfield = wfm.wave('bfield', FB.bias, EVAP.evapss)
	if not os.path.exists(ramphash) or True:
		print '\t...Making new Evap_field'
		bfield.extend(field_ramp_time)
		bfield.linear(EVAP.fieldrampfinal,field_ramp_dt)
		if((field_ramp_time+field_ramp_dt)<EVAP.image*scale):
			bfield.extend(EVAP.image*scale)
		else:
			bfield.chop(EVAP.image*scale)
		ramp = bfield.y
		#ramp.tofile(ramphash,sep=',',format="%.4f")
	else:
		print '\t...Recycling previously calculated Evap_field'
		ramp = numpy.fromfile(ramphash,sep=',')
		bfield.y=ramp

	#---Setup ODT ramp
	odtpow = odt_wave('odtpow', ODT.odtpow, EVAP.evapss)
	### SELECT EVAP TRAJECTORY HERE###
	finalcpow = odtpow.Evap8(\
							ODT.odtpow, \
							EVAP.p1, \
							EVAP.t1, 
							EVAP.tau, \
							EVAP.beta, \
							EVAP.offset, \
							EVAP.t2, \
							EVAP.tau2, \
							EVAP.smoothdt, \
							EVAP.image, \
							EVAP.scale \
							)
	#Here, go ahead and save the finalcpow to the report
	gen.save_to_report('EVAP','finalcpow', finalcpow)
	
	#---Setup ipganalog ramp
	ipganalog = ipg_wave('ipganalog', 10., EVAP.evapss)
	if ODT.use_servo == 0:
		ipganalog.extend( odtpow.dt() )
	elif ODT.use_servo == 1:
		ipganalog.follow( odtpow )

	maxDT = odtpow.dt()
	return bfield, odtpow, maxDT, finalcpow, ipganalog








def odt_evap_patch():
	odtpow = odt_wave('odtpow', p0, evap_ss)
	### SELECT EVAP TRAJECTORY HERE###
	finalcpow = odtpow.Evap6(\
							EVAP.patch_cuttime, \
							EVAP.patch_m, \
							EVAP.patch_y, \
							EVAP.patch_t0, \
							EVAP.patch_kink1, \
							EVAP.patch_kink2, \
							EVAP.patch_m_t0, \
							EVAP.patch_m_t0_2, \
							EVAP.image)
	
	#Here, go ahead and save the finalcpow to the report
	gen.save_to_report('EVAP','finalcpow', finalcpow)
	
	#---Setup ipganalog ramp
	ipganalog = ipg_wave('ipganalog', 10., EVAP.evapss)
	if ODT.use_servo == 0:
		ipganalog.extend( odtpow.dt() )
	elif ODT.use_servo == 1:
		ipganalog.follow( odtpow )

	maxDT = odtpow.dt()	
	return odtpow, maxDT, finalcpow, ipganalog
	
	
	
	
def crossbeam_evap(s, toENDBFIELD):
	# Add evaporation ramp to ODT, returns sequence right at the end of evaporation
	buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
	if EVAP.free < buffer + toENDBFIELD :
		print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
		print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,EVAP.free)
		exit(1)
	s.wait(EVAP.free)
	odtpow, ENDEVAP, cpowend, ipganalog = odt_evap()
	
	# Set LCR preset value in the begining of evap 1 is lattice 0 is dimple
	lcr1  = lattice.lattice_wave('lcr1', EVAP.lcr_preset, EVAP.evapss)
	lcr2  = lattice.lattice_wave('lcr2', EVAP.lcr_preset, EVAP.evapss)
	lcr3  = lattice.lattice_wave('lcr3', EVAP.lcr_preset, EVAP.evapss)
	lcr1.extend(ENDEVAP)
	lcr2.extend(ENDEVAP)
	lcr3.extend(ENDEVAP)
	
	s.analogwfm_add(EVAP.evapss,[odtpow,ipganalog,lcr1,lcr2,lcr3])
	# ENDEVAP should be equal to image
	s.wait(EVAP.image)
	return s, cpowend
	
	
def crossbeam_evap_into_lattice(s, toENDBFIELD):
	# Add evaporation ramp to ODT, returns sequence right at the end of evaporation
	buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
	if EVAP.free < buffer + toENDBFIELD :
		print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
		print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD, EVAP.free)
		exit(1)
	s.wait(EVAP.free)
	odtpow, ENDEVAP, cpowend, ipganalog = odt_evap()
	# ENDEVAP should be equal to image
	
	# Set LCR preset value in the begining of evap 1 is lattice 0 is dimple
	lcr1  = lattice.lattice_wave('lcr1', EVAP.lcr_preset, EVAP.evapss)
	lcr2  = lattice.lattice_wave('lcr2', EVAP.lcr_preset, EVAP.evapss)
	lcr3  = lattice.lattice_wave('lcr3', EVAP.lcr_preset, EVAP.evapss)
	lcr1.extend(ENDEVAP)
	lcr2.extend(ENDEVAP)
	lcr3.extend(ENDEVAP)
	
	#---Ramp up IR and green beams
	def rampup(ch, ss, END, load, delay, pow, dt):
		w = wfm.wave(ch, 0., ss) 
		w.appendhold( END - load)
		w.appendhold( delay)
		w.linear( pow, dt)
		return w 
	
	ir1 = rampup('ir1pow', EVAP.evapss, ENDEVAP, IL.loadtime, IL.irdelay1, IL.irpow1, IL.irrampdt1)
	ir2 = rampup('ir2pow', EVAP.evapss, ENDEVAP, IL.loadtime, IL.irdelay2, IL.irpow2, IL.irrampdt1)
	ir3 = rampup('ir3pow', EVAP.evapss, ENDEVAP, IL.loadtime, IL.irdelay3, IL.irpow3, IL.irrampdt1)
	
	gr1 = rampup('greenpow1', EVAP.evapss, ENDEVAP, IL.loadtime, IL.grdelay1, IL.grpow1, IL.grrampdt1)
	gr2 = rampup('greenpow2', EVAP.evapss, ENDEVAP, IL.loadtime, IL.grdelay2, IL.grpow2, IL.grrampdt1)
	gr3 = rampup('greenpow3', EVAP.evapss, ENDEVAP, IL.loadtime, IL.grdelay3, IL.grpow3, IL.grrampdt1)

	end = s.analogwfm_add(EVAP.evapss,[odtpow,ir1,ir2,ir3,gr1,gr2,gr3,lcr1,lcr2,lcr3])
	s.wait(EVAP.image-IL.loadtime)
	
	#---Turn on IR lattice beams
	def ttlon( s, delay, ch, bool ):
		s.wait(delay)
		s.digichg( ch, bool)
		s.wait(-delay)
		
	ttlon( s, IL.irdelay1, 'irttl1', IL.ir1)
	ttlon( s, IL.irdelay2, 'irttl2', IL.ir2)
	ttlon( s, IL.irdelay3, 'irttl3', IL.ir3)
	ttlon( s, IL.grdelay1, 'grttl1', IL.gr1)
	ttlon( s, IL.grdelay2, 'grttl2', IL.gr2)
	ttlon( s, IL.grdelay3, 'grttl3', IL.gr3)
	
	
	s.wait( IL.loadtime + end - EVAP.image)	
	
	return s
	
	
def crossbeam_evap_field(s, toENDBFIELD):
	# Add evaporation ramp to ODT, returns sequence right at the end of evaporation
	buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
	if EVAP.free < buffer + toENDBFIELD :
		print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
		print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,EVAP.free)
		exit(1)
	s.wait(EVAP.free)
	
	bfield, odtpow, ENDEVAP, cpowend, ipganalog = odt_evap_field()
	
	# Set LCR preset value in the begining of evap 1 is lattice 0 is dimple
	lcr1  = lattice.lattice_wave('lcr1', EVAP.lcr_preset, EVAP.evapss)
	lcr2  = lattice.lattice_wave('lcr2', EVAP.lcr_preset, EVAP.evapss)
	lcr3  = lattice.lattice_wave('lcr3', EVAP.lcr_preset, EVAP.evapss)
	lcr1.extend(ENDEVAP)
	lcr2.extend(ENDEVAP)
	lcr3.extend(ENDEVAP)
	
	s.analogwfm_add(EVAP.evapss,[odtpow,ipganalog, bfield,lcr1,lcr2,lcr3])
	
	#Add quick jump to help go to final evaporation field
	if ( EVAP.use_field_ramp == 1 and  EVAP.image > EVAP.fieldrampt0):
		s.wait( EVAP.fieldrampt0 )
		s.wait(-25.0)
		s.digichg('hfquick',1)
		s.digichg('quick',1)
		s.wait(75.0)
		s.digichg('hfquick',0)
		s.digichg('quick',0)
		s.wait(-50.0)
		s.wait(-EVAP.fieldrampt0)
	
	s.wait(EVAP.image)
	return s, cpowend
	

def crossbeam_evap_field_into_lattice(s, toENDBFIELD):
	# Add evaporation ramp to ODT, returns sequence right at the end of evaporation
	buffer=10.0 #Time needed to re-latch the trigger for the AOUTS
	if EVAP.free < buffer + toENDBFIELD :
		print 'Need at list ' + str(buffer) + 'ms of free evap before evaporation can be triggered'
		print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,EVAP.free)
		exit(1)
	s.wait(EVAP.free)
	bfield, odtpow, ENDEVAP, cpowend, ipganalog = odt_evap_field()
	
	#---Set LCR preset value in the begining of evap 1 is lattice 0 is dimple
	lcr1  = lattice.lattice_wave('lcr1', EVAP.lcr_preset, EVAP.evapss)
	lcr2  = lattice.lattice_wave('lcr2', EVAP.lcr_preset, EVAP.evapss)
	lcr3  = lattice.lattice_wave('lcr3', EVAP.lcr_preset, EVAP.evapss)
	lcr1.extend(ENDEVAP)
	lcr2.extend(ENDEVAP)
	lcr3.extend(ENDEVAP)
	
	#---Ramp up IR, GR beams
	def rampup( ch, pow ):
		w = lattice.lattice_wave(ch, 0., EVAP.evapss)
		w.appendhold( EVAP.latticet0 )
		w.tanhRise( pow, EVAP.latticedt, EVAP.tanhtau, EVAP.tanhshift )
		
	ir1 = rampup('ir1pow', EVAP.irpow)
	ir2 = rampup('ir2pow', EVAP.irpow)
	ir3 = rampup('ir3pow', EVAP.irpow)
	gr1 = rampup('greenpow1', EVAP.grpow)
	gr2 = rampup('greenpow2', EVAP.grpow)
	gr3 = rampup('greenpow3', EVAP.grpow)
	
	#---Turn on TTLs
	s.wait(EVAP.latticet0)
	s.digichg( 'irttl1', EVAP.irttl1)
	s.digichg( 'irttl2', EVAP.irttl2)
	s.digichg( 'irttl3', EVAP.irttl3)
	s.digichg( 'greenttl1', EVAP.irttl1)
	s.digichg( 'greenttl2', EVAP.irttl2)
	s.digichg( 'greenttl3', EVAP.irttl3)
	s.wait(-EVAP.latticet0)
	
	
	s.analogwfm_add(EVAP.evapss,[odtpow,ipganalog, bfield,ir1,ir2,ir3,gr1,gr2,gr3,lcr1,lcr2,lcr3])
	
	#Add quick jump to help go to final evaporation field
	if ( EVAP.use_field_ramp == 1 and  EVAP.image > EVAP.fieldrampt0):
		s.wait( EVAP.fieldrampt0 )
		s.wait(-25.0)
		s.digichg('hfquick',1)
		s.digichg('quick',1)
		s.wait(75.0)
		s.digichg('hfquick',0)
		s.digichg('quick',0)
		s.wait(-50.0)
		s.wait(-EVAP.fieldrampt0)
	
	s.wait(EVAP.image)
	
	return s, cpowend
	
	

def odt_evap_field_free(toENDBFIELD, scale =1.0):
	
	
	odtfree = EVAP.free - EVAP.buffer - toENDBFIELD
	
	#---Setup ODT ramp
	odtpow = odt_wave('odtpow', ODT.odtpow, EVAP.evapss)
	odtpow.appendhold( odtfree )
	### SELECT EVAP TRAJECTORY HERE###
	finalcpow = odtpow.Evap8(\
							ODT.odtpow, \
							EVAP.p1, \
							EVAP.t1, 
							EVAP.tau, \
							EVAP.beta, \
							EVAP.offset, \
							EVAP.t2, \
							EVAP.tau2, \
							EVAP.smoothdt, \
							EVAP.image, \
							EVAP.scale \
							)
	#Here, go ahead and save the finalcpow to the report
	gen.save_to_report('EVAP','finalcpow', finalcpow)
	

	#---Setup field ramp
	field_ramp_time = EVAP.fieldrampt0*scale
	field_ramp_dt   = EVAP.fieldrampdt*scale

	print '\t...Making new Evap_field'
	bfield = wfm.wave('bfield', FB.bias, EVAP.evapss)
	bfield.extend(field_ramp_time + odtfree)
	bfield.linear(EVAP.fieldrampfinal,field_ramp_dt)
	
	if((field_ramp_time+field_ramp_dt)<EVAP.image*scale):
		bfield.extend(EVAP.image*scale)
	else:
		bfield.chop(EVAP.image*scale)
	ramp = bfield.y
	
	
	#---Setup ipganalog ramp
	ipganalog = ipg_wave('ipganalog', 10., EVAP.evapss)
	if ODT.use_servo == 0:
		ipganalog.extend( odtpow.dt() )
	elif ODT.use_servo == 1:
		ipganalog.follow( odtpow )

	maxDT = odtpow.dt()
	return bfield, odtpow, maxDT, finalcpow, ipganalog


	
	
def crossbeam_dimple_evap(s, toENDBFIELD):
	# Add evaporation ramp to ODT, returns sequence right at the end of evaporation
	# EVAP.buffer is the time needed to re-latch the trigger for the AOUTS
	
	print "toENDBFIELD = %f " % toENDBFIELD
	
	if EVAP.free < EVAP.buffer + toENDBFIELD :
		print 'Need at list ' + str(EVAP.buffer + toENDBFIELD) + 'ms of free evap before evaporation can be triggered'
		print 'Currently ramps end at %f , and free is %f' % (toENDBFIELD,EVAP.free)
		exit(1)
		
	s.wait(toENDBFIELD + EVAP.buffer)
	
	

	bfield, odtpow, ENDEVAP, cpowend, ipganalog = odt_evap_field_free(toENDBFIELD)
	
	#---Set LCR preset value in the begining of evap 1 is lattice 0 is dimple
	def dimpleset(ch):
		w = lattice.lattice_wave(ch, 0., EVAP.evapss)
		w.extend(ENDEVAP)
		return w
		
	lcr1 = dimpleset('lcr1')
	lcr2 = dimpleset('lcr2')
	lcr3 = dimpleset('lcr3')
	
	#---Ramp up IR, GR beams
	def rampup( ch ):
		w = lattice.lattice_wave(ch, 0., EVAP.evapss)
		if 'ir' in ch:
			w.appendhold( DIMPLE.ir_t0 )
			w.tanhRise( DIMPLE.ir_pow, DIMPLE.ir_dt, DIMPLE.ir_tau, DIMPLE.ir_shift)
		elif 'green' in ch:
			w.appendhold( DIMPLE.gr_t0 )
			w.tanhRise( DIMPLE.gr_pow, DIMPLE.gr_dt, DIMPLE.gr_tau, DIMPLE.gr_shift)
		else:
			print "Error ramping up IR,GR beams in crossbeam_dimple_evap"
		return w
	
	ir1 = rampup('ir1pow')
	ir2 = rampup('ir2pow')
	ir3 = rampup('ir3pow')
	gr1 = rampup('greenpow1')
	gr2 = rampup('greenpow2')
	gr3 = rampup('greenpow3')
	
	#---Turn on TTLs
	s.wait( DIMPLE.ir_t0 )
	s.digichg( 'irttl1', DIMPLE.ir1)
	s.digichg( 'irttl2', DIMPLE.ir2)
	s.digichg( 'irttl3', DIMPLE.ir3)
	s.wait(-DIMPLE.ir_t0 )
	
	s.wait( DIMPLE.gr_t0 )
	s.digichg( 'greenttl1', DIMPLE.gr1)
	s.digichg( 'greenttl2', DIMPLE.gr2)
	s.digichg( 'greenttl3', DIMPLE.gr3)
	s.wait(-DIMPLE.gr_t0 )
	
	
	s.analogwfm_add(EVAP.evapss,[odtpow,ipganalog, bfield,ir1,ir2,ir3,gr1,gr2,gr3,lcr1,lcr2,lcr3])

	extrafree = EVAP.free - EVAP.buffer - toENDBFIELD
	
	#Add quick jump to help go to final evaporation field
	if ( EVAP.use_field_ramp == 1 and  EVAP.image > EVAP.fieldrampt0):
		s.wait( EVAP.fieldrampt0 + extrafree )
		s.wait(-25.0)
		s.digichg('hfquick',1)
		s.digichg('quick',1)
		s.wait(75.0)
		s.digichg('hfquick',0)
		s.digichg('quick',0)
		s.wait(-50.0)
		s.wait(-EVAP.fieldrampt0 - extrafree)
	
	s.wait(EVAP.free - EVAP.buffer - toENDBFIELD)
	s.wait(EVAP.image)
	
	if DIMPLE.image >= EVAP.image:
		s.wait( DIMPLE.image - EVAP.image)
	else:
		s.wait( DIMPLE.image - EVAP.image)
		s.stop_analog() 
		#trajectory = numpy.loadtxt( report['EVAP']['ramp'], delimiter=',')
		#cpowend = trajectory[ numpy.floor(DIMPLE.image/EVAP.evapss) ]
	
	print "...Evap cpowend  = %f" % cpowend
	
	
	return s, cpowend

	
	
def odt_trapfreq(odtpow0):
	mod_ss = f('TRAPFREQ','mod_ss')

	odtpow  = odt_wave('odtpow',  None, mod_ss, volt=odtpow0)
	bfield  = wfm.wave('bfield',  f('FESHBACH','bias'), mod_ss)
	
	odtpow.linear( f('TRAPFREQ','cpow'), f('TRAPFREQ','cdt') )
	odtpow.appendhold( f('TRAPFREQ','waitdt'))
	bfield.extend(odtpow.dt())
	
	bfield.linear( f('TRAPFREQ','bmod'), f('TRAPFREQ','bdt') )
	bfield.appendhold( f('TRAPFREQ','waitdt2'))
	
	odtpow.extend( bfield.dt() )
	#odtpow.SineMod( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	#odtpow.SineMod2( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	#odtpow.SineMod3( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	odtpow.SineMod4( f('TRAPFREQ','cpow'), f('TRAPFREQ','moddt'), f('TRAPFREQ','modfreq'), f('TRAPFREQ','moddepth'))
	
	return odtpow, bfield, odtpow.dt()
	
def odt_flicker(odtpow0):
	flicker_ss = f('FLICKER','flicker_ss')

	odtpow  = odt_wave('odtpow',  None, flicker_ss, volt=odtpow0)
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

	odtpow  = odt_wave('odtpow',  None, dbz_ss, volt=odtpow0)
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


###########################################
#### IPG ANALOG WAVEFORM ###
###########################################


class ipg_wave(wfm.wave):
	"""The ipg_wave class helps construct the waveform that 
		will be used to reduce the 50 Watt ipg power during
		evaporation. 
		
		The main method is 'follow', which allows the 
		ipg to be reduced as evaporation proceeds, always putting
		out enough power to let the servo be in control and also
		taking care not to go below 20% ipg output power, where
		the noise spectrum of the laser is increased.
		"""
	def follow(self, odtpow):
		ipgmargin =  10.; #  5% margin for ipg
		ipgmin    = 50.; # 20% minimum output power for ipg 
		# Change to 50 ( 03022012 by Ernie, since we see 20 is noisey on light)
		self.y = numpy.copy(odtpow.y)
		
		print "...Setting IPG to follow the evap ramp"
		
		for i in range(self.y.size):
			odt = physics.inv( 'odtpow', self.y[i] )
			ipg =  odt + 10.*ipgmargin/100.
			if ipg > 10.0:  #can't do more than 10.0 Volts
				ipg = 10.0
			if ipg < 10.*ipgmin/100.:  #should not do less than ipgmin
				ipg = 10.*ipgmin/100.
			self.y[i] = ipg
			#print "%.3f -> %.3f\t" % (odt,ipg)


###########################################
#### LOWER LEVEL CODE FOR ODT WAVEFORMS ###
###########################################


class odt_wave(wfm.wave):
	"""The odt_wave class helps construct arbitrary waveforms
		that will be ouutput to the odtpow channel. 
		It inherits from the base wave class defined in wfm 
		and adds further functionality for evaporation, etc."""
	def __init__(self,name,val,stepsize,N=1,volt=-11):
		"""Initialize the waveform  """
		self.idnum = time.time()*100
		self.name = name
		if volt != -11:
			val=volt
		else:
			val=physics.cnv('odtpow', val)
				
		self.y= numpy.array(N*[val])
		self.ss=stepsize
		#print ("...Initialized waveform %s, idnum=%s" % ( self.name, self.wfm_id()))
		
	def odt_linear(self,p0,pf,dt):
		"""Adds linear ramp to waveform, starts at 'p0' 
			value and goes to 'pf' in 'dt' 
			CAREFUL: This uses OdtpowConvert and is only valid for odtpow"""
		print "...ODT Linear from %.3f to %.3f" % (p0,pf)
		if dt == 0.0:
			self.y[ self.y.size -1] = physics.cnv('odtpow', pf)
			return
		else:
			N = int(math.floor(dt/self.ss))
			for i in range(N):
				self.y=numpy.append(self.y, [ physics.cnv('odtpow',  p0 + (pf-p0)*(i+1)/N )])
		return 




	def Evap8(self, p0, p1, t1, tau, beta, offset, t2, tau2, smoothdt, duration,scale = 1.0):
		"""Evaporation ramp v8 same as v7 with scale"""
		if True:
			print ""
			print "----- EVAPORATION RAMP Version 8-----"
			
		if duration <=0:
			return
		else:
			N=int(round(duration*scale/self.ss))
			print '\t...Evap nsteps = ' + str(N)
			ramp_phys=numpy.array([])
			ramp=numpy.array([])
			
			hashbase = ''
			hashbase = hashbase + '%.s' % self.name
			hashbase = hashbase + '%.8f' % self.ss
			hashbase = hashbase + '%.8f' % duration
			hashbase = hashbase + '%.8f' % p0
			hashbase = hashbase + '%.8f' % p1
			hashbase = hashbase + '%.8f' % t1
			hashbase = hashbase + '%.8f' % tau
			hashbase = hashbase + '%.8f' % beta
			hashbase = hashbase + '%.8f' % offset
			hashbase = hashbase + '%.8f' % t2
			hashbase = hashbase + '%.8f' % tau2
			hashbase = hashbase + '%.8f' % smoothdt
			hashbase = hashbase + '%.8f' % scale

			ramphash = seqconf.ramps_dir() +'Evap8_' \
						+ hashlib.md5( hashbase).hexdigest()
						
			#Here, go ahead and save the trajectory path to the report
			gen.save_to_report('EVAP','ramp', ramphash+'_phys')
			
			if not os.path.exists(ramphash) or True:
				print '\t...Making new Evap8 ramp'
				for xi in range(N):
					t = (xi+1)*self.ss/scale
					phys = evap.v6(t,p0,p1,t1,tau,beta, offset,t2,tau2,smoothdt)                    
					volt = physics.cnv( 'odtpow', phys)
					
					ramp_phys = numpy.append( ramp_phys, [ phys])
					ramp = numpy.append( ramp, numpy.around([ volt],decimals=4))
				ramp_phys.tofile(ramphash+'_phys',sep='\n',format="%.4f")
				#ramp.tofile(ramphash,sep=',',format="%.4f")
			
			else:
				print '\t...Recycling previously calculated Evap8 ramp'
				ramp = numpy.fromfile(ramphash,sep=',')

			self.y=numpy.append(self.y,ramp)

		#This returns the last value of the ramp
		print ""
		return evap.v6(N*self.ss/scale,p0,p1,t1,tau,beta,offset,t2,tau2,smoothdt)
		
	

