import os, gen, math, numpy, hashlib, evap

from convert import cnv

report=gen.getreport()

#it=0

b=float(report['ODTCALIB']['b'])
m1=float(report['ODTCALIB']['m1'])
m2=float(report['ODTCALIB']['m2'])
kink=float(report['ODTCALIB']['kink'])     

b_nonservo=float(report['ODTCALIB']['b_nonservo'])
m1_nonservo=float(report['ODTCALIB']['m1_nonservo'])
m2_nonservo=float(report['ODTCALIB']['m2_nonservo'])
kink_nonservo=float(report['ODTCALIB']['kink_nonservo'])     

def OdtpowConvert(phys,servo=1):
	#Parameters for the odt servo calibration
	#Max odt power = 10.0
	if(servo):
		volt = b+m1*kink+m2*(phys-kink) if phys > kink else b+m1*phys	
	else:    
		volt = b_nonservo+m1_nonservo*kink_nonservo+m2_nonservo*(phys-kink_nonservo) if phys > kink_nonservo else b_nonservo+m1_nonservo*phys	
	#global it
	#if it  <10:
	#	print "phys=%.3f  ==> volt = %.3f" % (phys,volt)	
	#it = it + 1 

	return volt


class wave:
	"""The wave class helps construct the arbitrary waveform 
		that will be output to an analog output channel. 
		
		To prevent conflicts no conversions should be done outside 
		this module.   Outside of here all is in physical units, 
		conversion is done solely inside this module.  
		
		The volt optional parameter helps initializa a wfm
		with a voltage instead of a physical quantity"""
	def __init__(self,name,val,stepsize,N=1,volt=-11):
		"""Initialize the waveform  """
		self.name = name
		if volt != -11:
			val=volt
		else:
			if self.name == 'odtpow':
				val=OdtpowConvert(val)
			elif self.name =='odtpow_nonservo':
				val=OdtpowConvert(val,0)		
			else:
				val=cnv(self.name,val)
				
				
		self.y= numpy.array(N*[val])
		self.ss=stepsize
		
	def fileoutput(self,filename):
		self.y.tofile(filename,sep=',',format="%.4f")
		
	def __cmp__(self,other):
		"""Compares two waveforms"""
		return cmp(self.y,other.y)
		
	def __str__(self):
		"""When asked for a string returns all the array values"""
		return self.y.__str__()
		
	def last(self):
		"""Returns the last element in the array"""
		return self.y[-1]
		
	def dt(self):
		"""Returns the current duration of the wfm in ms"""
		return (self.y.size-1)*self.ss
		
	def N(self):
		"""Returns the number of samples on the wfm"""
		return (self.y.size)

	
	def linear(self,vf,dt,volt=-11):
		"""Adds linear ramp to waveform, starts at current last 
			value and goes to 'vf' in 'dt' 
			CAREFUL: This is linear in voltage, not in phys"""
		if volt != -11:
			vf=volt
		else:
			vf=cnv(self.name,vf)
		v0=self.last()
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			for i in range(N):
				self.y=numpy.append(self.y, [v0 + (vf-v0)*(i+1)/N])
		return


	def odt_linear(self,p0,pf,dt,servo=1):
		"""Adds linear ramp to waveform, starts at 'p0' 
			value and goes to 'pf' in 'dt' 
			CAREFUL: This uses OdtpowConvert and is only valid for odtpow"""
		print "...ODT Linear from %.3f to %.3f" % (p0,pf)
		if dt == 0.0:
			self.y[ self.y.size -1] = OdtpowConvert(pf,servo)
			return
		else:
			N = int(math.floor(dt/self.ss))
			for i in range(N):
				self.y=numpy.append(self.y, [OdtpowConvert( p0 + (pf-p0)*(i+1)/N ,servo)])
		return 
		
		
	def extend(self,dt):
		"""Extends the waveform so that it's total duration equals 'dt' """
		if self.dt() == dt:
			#print "0"
			return
		v=self.last()
		Ntotal=math.floor((dt+self.ss)/self.ss)
		Nextra=int(Ntotal-self.N())
		#print Nextra
		self.y = numpy.append(self.y, Nextra*[v])
		return
	
	def chop(self,dt,extra=0):
		"""Chops samples from the end of the waveform so that  it's total duration equals 'dt' """
		if self.dt() == dt:
			return
		dt0 = self.dt()
		self.y = self.y[: math.floor(dt/self.ss)+1+extra]
		dtf = self.dt()
		if round(self.dt(),4) != round(dt,4):
			print "-----> Chop error, ended up with the wrong number of samples in waveform"
			print "-----> %s : dt = %f,  selfdt = %f" % (self.name, dt, self.dt())
			print "-----> dt0 = %f,  dtf = %f" % (dt0, dtf)
		return
		
		
	def appendhold(self,dt):
		"""Appends the current last value enought times so that the 
			duration is increased by dt"""
		v=self.last()
		N=int(math.floor(dt/self.ss))
		if N >= 0 :
			self.y = numpy.append(self.y,N*[v])
			return
		elif -N < self.y.size :
			self.y = self.y[0:N-1]
			return
		else:
			print("Negative appendhold is larger than current length of waveform: " + str(-N) + " > " + str(self.y.size))
			exit(1)
			
		return
		
	def sinhRise(self,vf,dt,tau):
		"""Inserts a hyperbolic-sine-like ramp to the waveform.  
			tau is the ramp scale, it is understood in units of dt
			
			if tau is equal or greater to dt the ramp approaches a
			linear ramp
		
			as tau gets smaller than dt the ramp starts to deviate from 
			linear
			
			a real difference starts to be seen wheh tau = dt/3
			
			from tau=dt/20 it doesn't make a difference to keep making
			tau smaller
			
			good values to vary it are tau=dt/20, dt/5, dt/3, dt/2, dt"""
		### WARNING: in general the conversion should be done for every point
		### i.e. inside of the for loop below.
		### This one just does it on the endpoints.  It is ok because it is used
		### for the magnetic field which has a mostly linear relationship between
		### set voltage and current in the coils.  But don't use this as an example
		### for other things.   
		vf=cnv(self.name,vf)
		v0=self.last()
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			ramp=[]
			ramphash = seqconf.ramps_dir() + 'sinhRise_' \
			           + hashlib.md5(str(self.name)+str(vf)+str(v0)+str(N)+str(dt)+str(tau)).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new sinhRise ramp'
				for i in range(N):
					x=dt*(i+1)/N
					f=v0 + (vf-v0)*(x/tau+(x/tau)**3.0/6.0)/(dt/tau+(dt/tau)**3.0/6.0)
					ramp=numpy.append(ramp, [f])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated sinhRise ramp'
				ramp =  numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y, ramp)
		return

	def Evap(self, p0, p1, t1, tau, beta, duration):
		"""Evaporation ramp v1"""
		if duration <=0:
			return
		else:
			N=int(round(duration/self.ss))
			print '...Evap nsteps = ' + str(N)
			ramp=[]
			ramphash = seqconf.ramps_dir() + 'Evap_' \
					   + hashlib.md5(str(self.name)+str(self.ss)+str(duration)+str(p0)+str(p1)+str(t1)+str(tau)+str(beta)).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new Evap ramp'
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = evap.v1(t,p0,p1,t1,tau,beta)
					volt = cnv(self.name,phys)
					ramp = numpy.append( ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated Evap ramp'
				ramp = numpy.fromfile(ramphash,sep=',')

			self.y=numpy.append(self.y,ramp)
		return
		
	def Evap2(self, p0, p1, t1, tau, beta, offset, t2, tau2, duration):
		"""Evaporation ramp v2"""
		if duration <=0:
			return
		else:
			N=int(round(duration/self.ss))
			print '...Evap nsteps = ' + str(N)
			ramp=[]
			ramphash = seqconf.ramps_dir() + 'Evap2_' \
					   + hashlib.md5(str(self.name)+str(self.ss)+str(duration)+str(p0)+str(p1)+str(t1)+str(tau)+str(beta)\
					                  + str(offset)+str(t2)+str(tau2)).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new Evap2 ramp'
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = evap.v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)
					volt = cnv(self.name,phys)
					ramp = numpy.append( ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated Evap2 ramp'
				ramp = numpy.fromfile(ramphash,sep=',')

			self.y=numpy.append(self.y,ramp)
		return

	def Evap3(self, p0, p1, t1, tau, beta, offset, t2, tau2, duration,servo=1):
		"""Evaporation ramp v2"""
		if duration <=0:
			return
		else:
			N=int(round(duration/self.ss))
			print '...Evap nsteps = ' + str(N)
			ramp=[]
			hashbase = '%.8f,%.8f,%.8f,%.8f,%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f ' \
			           % ( b,m1,m2,kink, self.name, self.ss, duration, p0, p1, t1, tau, beta, offset, t2, tau2)
			ramphash = seqconf.ramps_dir()+'Evap3_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new Evap3 ramp'
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = evap.v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)
					volt = OdtpowConvert(phys,servo)
					ramp = numpy.append( ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated Evap3 ramp'
				ramp = numpy.fromfile(ramphash,sep=',')

			self.y=numpy.append(self.y,ramp)
		return

		
	def SineMod(self, p0, dt, freq, depth):
		"""Sine wave modulation on channel"""
		if dt <= 0.0:
			return
		else:
			N=int(math.floor(dt/self.ss))
			ramp=[]
			hashbase = '%s,%.3f,%.3f,%.3f,%.3f,%.3f ' % ( self.name, self.ss, p0, dt, freq, depth)
			ramphash = seqconf.ramps_dir()+'SineMod_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new SineMod ramp:  %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = p0 + (0.5*p0*depth/100.)* math.sin(  t * 2 * math.pi * freq/1000. )
					volt = cnv(self.name,phys)
					ramp = numpy.append(ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated SineMod ramp %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				ramp = numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y,ramp)
		return
		

		
		
	def SineMod2(self, p0, dt, freq, depth):
		"""Sine wave modulation on channel"""
		if dt <= 0.0:
			return
		else:
			N=int(math.floor(dt/self.ss))
			ramp=[]
			hashbase = '%s,%.3f,%.3f,%.3f,%.3f,%.3f ' % ( self.name, self.ss, p0, dt, freq, depth)
			ramphash = seqconf.ramps_dir()+'SineMod2_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new SineMod ramp:  %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = p0 + (0.5*p0*depth/100.)* math.sin(  t * 2 * math.pi * freq/1000. )
					volt = OdtpowConvert(phys)
					ramp = numpy.append(ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated SineMod ramp %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				ramp = numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y,ramp)
		return
		
	def SineMod3(self, p0, dt, freq, depth,servo=1):
		"""Sine wave modulation on channel"""
		if dt <= 0.0:
			return
		else:
			N=int(math.floor(dt/self.ss))
			ramp=[]
			hashbase = '%.8f,%.8f,%.8f,%.8f,%s,%.3f,%.3f,%.3f,%.3f,%.3f ' % ( b,m1,m2,kink, self.name, self.ss, p0, dt, freq, depth)
			ramphash = seqconf.ramps_dir()+'SineMod3_' \
						+ hashlib.md5( hashbase).hexdigest()
			if not os.path.exists(ramphash):
				print '...Making new SineMod3 ramp:  %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				for xi in range(N):
					t = (xi+1)*self.ss
					phys = p0 + (0.5*p0*depth/100.)* math.sin(  t * 2 * math.pi * freq/1000. )
					volt = OdtpowConvert(phys,servo)
					ramp = numpy.append(ramp, [ volt])
				ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated SineMod3 ramp %.2f +/- %.2f' % (p0, 0.5*p0*depth/100.)
				print '... [[ hashbase = %s ]]' % hashbase
				ramp = numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y,ramp)
		return
		
	#### FROM HERE ON RAMPS ARE NOT USED OR OBSOLETE ###
		
	def lineardither(self,vf,dt,ramps):
		"""Adds linear ramp to waveform, starts at current last 
			value and goes to 'vf' in 'dt' """
		v0=self.last()
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			s = math.floor(dt / ramps / self.ss)
			for i in range(N):
				if (i%s == 0):
					vi = v0 + (vf-v0)*(i+1)/N
				self.y=numpy.append(self.y,[vi+(0.0-vi)*(i%s)/s])
		return 
		
	def dither(self,dt,ramps):
		"""Appends the current last value enough times so that the 
			duration is increased by dt.  Little ramps with period
			of 2*littledt are appended to the ramp."""
		v=self.last()
		N=int(math.floor(dt/self.ss))
		a=numpy.array([])
		s=math.floor(dt / ramps / self.ss)
		print s
		for xi in range(N-1):
			a=numpy.append(a,[v+(0.0-v)*(xi%s)/s])
		a=numpy.append(a,[v])
		self.y = numpy.append(self.y,a)
		return
		

		

	def Exponential(self,y0,yf,dt,tau):
		"""Exponential turn to value max during dt with time constant tau on channel"""
		if dt <= 0.0:
			return
		else:
			N=int(round(dt/self.ss))
			print 'nsteps = ' + str(N)
			for xi in range(N-1):
				t = (xi+1)*self.ss
				phys = y0 + (yf-y0)*(1-math.exp(-t/tau))/(1-math.exp(-dt/tau))
				volt = cnv(self.name,phys)
				self.y=numpy.append( self.y, [ volt])
		return
	
	def AdiabaticRampDown(self,dt,tau,channel):
		"""Adiabatic RampDown during dt with time constant tau on channel"""
		if dt <= 0.0:
			return
		else:
			v0 = self.last()
			N=int(math.floor(dt/self.ss))
			for xi in range(N):
				t = (xi+1)*self.ss
				phys = v0 * math.pow( 1 + t/tau ,-2)
				volt = cnv(channel,phys)
				self.y=numpy.append( self.y, [ volt])
		return

		

		
	def sinRise(self,vf,dt,tau):
		"""Inserts a hyperbolic-sine-like ramp to the waveform.  
			tau is the ramp scale, it is understood in units of dt
			
			if tau is equal or greater to dt the ramp approaches a
			linear ramp
		
			as tau gets smaller than dt the ramp starts to deviate from 
			linear
			
			a real difference starts to be seen wheh tau = dt/3
			
			from tau=dt/20 it doesn't make a difference to keep making
			tau smaller
			
			good values to vary it are tau=dt/20, dt/5, dt/3, dt/2, dt"""
		v0=self.last()
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			for i in range(N):
				x=dt*(i+1)/N
				f=v0 + (vf-v0)*(x/tau-(x/tau)**3.0/6.0)/(dt/tau-(dt/tau)**3.0/6.0)
				self.y=numpy.append(self.y, [f])
		return
		
		
	def insertlin(self,vf,dt,start):
		"""Inserts a linear ramp (vf,dt) at a time 'start' referenced from 
			the end of the current sate of the wfm.  
			
			start > 0 : appends a hold before doing the ramp
			"""
		if start>0:
			self.apppendhold(start-ss)
			self.y = numpy.append(self.y,[vf])
			return
		elif -start > self.dt():
			print("Cannot insert ramp before the beggiging of the waveform")
			exit(1)
		elif dt > -start:
			print("Ramp is too long for inserting")
			exit(1)
		Nstart=int(math.floor(-start/self.ss))
		if dt==0. :
			N=0
			self.y[self.y.size -1 - Nstart]=vf
		else:
			N=int(math.floor(dt/self.ss))
			v0 = self.y[self.y.size -1 - Nstart]
			for i in range(N):
				self.y[self.y.size - Nstart + i] = v0 + (vf-v0)*(i+1)/N
		for i in range( Nstart -N):
			self.y[self.y.size - Nstart + N + i] = vf
		return
		
		
	def insertHeaviside(self,vf,dt,start):
		if start>0:
			print("Insertion in the future is not implemented")
			exit(1)
		elif -start > self.dt():
			print("Cannot insert ramp before the beggiging of the waveform")
			exit(1)
		elif dt > -start:
			print("Ramp is too long for inserting")
			exit(1)
		Nstart=int(math.floor(-start/self.ss))
		if dt==0. :
			N=0
			self.y[self.y.size -1 - Nstart]=vf
		else:
			N=int(math.floor(dt/self.ss))
			v0 = self.y[self.y.size -1 - Nstart]
			for i in range(N):
				self.y[self.y.size - Nstart + i] = vf
		for i in range( Nstart -N):
			self.y[self.y.size - Nstart + N + i] = vf
		return
		
		
	def insertExp(self,vf,dt,start):
		
		if start>0:
			print("Insertion in the future is not implemented")
			exit(1)
		elif -start > self.dt():
			print("Cannot insert ramp before the beggiging of the waveform")
			exit(1)
		elif dt > -start:
			print("Ramp is too long for inserting")
			exit(1)
		Nstart=int(math.floor(-start/self.ss))
		if dt==0. :
			N=0
			self.y[self.y.size -1 - Nstart]=vf
		else:
			N=int(math.floor(dt/self.ss))
			v0 = self.y[self.y.size -1 - Nstart]
			tau=dt/(-1*math.log(vf/v0))
			for i in range(N):
				self.y[self.y.size - Nstart + i] =v0*exp(- dt*(i+1)/N/tau)
		for i in range( Nstart -N):
			self.y[self.y.size - Nstart + N + i] = vf
		return
	
	
	
	

	

	
