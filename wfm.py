import os, sys, seqconf, gen, math, numpy, hashlib, time, physics, errormsg


report=gen.getreport()

def rawcalibdat(ch):
    with open( os.path.join([path for path in sys.path if 'convert' in path][0], os.path.join('data',ch+'.dat')) ) as f:
        return f.read()
        


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

		self.idnum = time.time()*100 + 1e3*numpy.random.randint(0,1e8)
		self.name = name
		
		self.lastPhys = None
		
		if volt != -11:
			val=volt
		else:
			
			#print "INITIALIZING WFM:  %s, val=%f,  volt=%f" % (name,val,physics.cnv(self.name,val))
			
			self.lastPhys = val
			val=physics.cnv(self.name,val)
			
				
		self.y= numpy.array(N*[val])
		self.ss=stepsize
		
		
		
		#print ("...Initialized waveform %s, idnum=%s" % ( self.name, self.wfm_id()))
		
	def wfm_id(self):
		#~ return str(self.idnum).split('.')[0]
		return "%d" % self.idnum
		
	def fileoutput(self,filename):
		#print "fileoutput length = %d"  % (self.y.size)
		#print "fileoutput last value %s = %.8f" % (self.name, self.y[-1])
		
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
	
	def mirror(self):
		"""Mirror a waveform, it has a total duration twice of its original duration"""
		yvals= self.y
		self.y = numpy.concatenate((yvals,yvals[::-1]))
		
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
		if self.dt() < dt:
			print "----> Chop error, cannot remove samples to make wfm longer!!"
			return
		self.lastPhys = None
		dt0 = self.dt()
		self.y = self.y[: math.floor(dt/self.ss)+1+extra]
		dtf = self.dt()
		if round(self.dt(),4) != round(dt,4):
			print "-----> Chop error, ended up with the wrong number of samples in waveform"
			print "-----> %s : dt = %f,  selfdt = %f" % (self.name, dt, self.dt())
			print "-----> dt0 = %f,  dtf = %f" % (dt0, dtf)
		return
		
	def retain_last( self, dt):
		"""Discards everything except the last dt ms from the end of the waveform."""
		if self.dt() <= dt:
			return
		tokeep = math.floor(dt/self.ss)  
		self.y = self.y[ self.y.size - tokeep : ] 
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
			raise 
			
		return
		
	### THIS RAMP BELOW IS VESTIGIAL OF OUR RED MOT COOL AND COMPRESS, IT CAN BE USED
	### AS AN EXAMPLE OF WHAT CAN BE DONE WITH A WAVEFORM.  FOR SOMETHING SO SPECIFIC
	### IT IS RECOMMENDED TO DEFINE A NEW CLASS THAT INHERITS FROM THE wave CLASS  
		
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
		self.lastPhys = vf
		vf=physics.cnv(self.name,vf)
		
		v0=self.last()
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			
			hashbase = ''
			hashbase = hashbase + self.name
			hashbase = hashbase + '%.8f' % vf
			hashbase = hashbase + '%.8f' % v0
			hashbase = hashbase + '%.8f' % N
			hashbase = hashbase + '%.8f' % dt
			hashbase = hashbase + '%.8f' % tau
			ramphash = seqconf.ramps_dir() + 'sinhRise_' + hashlib.md5(hashbase).hexdigest()
			
			if not os.path.exists(ramphash) or True:
				print '...Making new sinhRise ramp'
				
				x = numpy.linspace( dt/N, dt, N)
				ramp = v0 + (vf-v0)*(x/tau+(x/tau)**3.0/6.0)/(dt/tau+(dt/tau)**3.0/6.0)
				
				#ramp.tofile(ramphash,sep=',',format="%.4f")
				
				
			else:
				print '...Recycling previously calculated sinhRise ramp'
				ramp =  numpy.fromfile(ramphash,sep=',')
			
			self.y=numpy.append(self.y, ramp)
		return


	def linear(self,vf,dt,volt=-11):
		"""Adds linear ramp to waveform, starts at current last 
			value and goes to 'vf' in 'dt' 
			CAREFUL: This is linear in voltage, not in phys"""
		#~ if 'ir' in self.name  and 'pow' in self.name:
			#~ print "%s LINEAR: Conversion flag = %d, vf_in=%f" % (self.name, volt,vf)
			
		if volt >= -10.0 and volt <= 10.0:
			self.lastPhys = None
			vf=volt
		elif volt == -11:
			self.lastPhys = vf
			vf=physics.cnv(self.name,vf)
			
		#~ if 'ir' in self.name  and 'pow' in self.name:
			#~ print "%s  LINEAR: Conversion flag = %d, vf_out=%f" % (self.name, volt,vf)
			
		v0 = round(self.last(),4)
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			x = numpy.linspace( 1, N, N)
			ramp =   numpy.around(v0 + (vf-v0)*x/N, decimals=4)
			self.y = numpy.append( self.y, ramp )
		return



	def insertlin_cnv(self,vf,dt,start):
		"""Inserts a linear ramp (vf,dt) at a time 'start' referenced from 
			the end of the current sate of the wfm.  
			
			start > 0 : appends a hold before doing the ramp
			"""
		self.lastPhys = vf
		vf=physics.cnv(self.name,vf)
		
		if start>0:
			self.apppendhold(start-self.ss)
			self.y = numpy.append(self.y,[vf])
			return
		elif -start > self.dt():
			exc = "wfm.py: Cannot insert ramp before the beggiging of the waveform"
                        print exc
                        raise Exception(exc)
			#exit(1)
		elif dt > -start:
			exc = "wfm.py: Ramp is too long for inserting"
                        print exc
                        raise Exception(exc)
			#exit(1)
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


	def linear_phys(self,vf,dt):
		"""Adds linear ramp to waveform, starts at current last 
			value and goes to 'vf' in 'dt'"""
		
		if self.lastPhys == None:
			msg = "The last physics value is not available\n for this waveform."
			msg = msg + "\n\nProgram will be stopped."
			errormsg.box('wfm.linear_phys :: ' + self.name, msg)
			exit(1)
		
		print "...linear_phys last physical value is = %f" % self.lastPhys
		
		v0 = self.lastPhys
		
		#One could also obtain v0 via conversion, but it is not recommended		
		#v0=physics.cnv(self.name+"Phys",self.last())
		
		if dt == 0.0:
			self.y[ self.y.size -1] = physics.cnv(self.name,vf)
			return

			
		N = int(math.floor(dt/self.ss))

		hashbase = ''
		hashbase = hashbase + self.name
		hashbase = hashbase + '%.8f' % vf
		hashbase = hashbase + '%.8f' % v0
		hashbase = hashbase + '%.8f' % N
		hashbase = hashbase + '%.8f' % dt
		hashbase = hashbase + rawcalibdat( self.name ) 
		
		ramphash = seqconf.ramps_dir() + 'linearPhys_' \
			           + hashlib.md5( hashbase ).hexdigest()
	
		if not os.path.exists(ramphash) or True:
				print '...Making new linearPhys ramp for ' + self.name
				
				x = numpy.linspace( v0 + (vf-v0)/N , vf , N )
				ramp = physics.cnv( self.name, x )
				
				#yramp= numpy.array([cnv(self.name,v0 + 1.0*(vf-v0)*(i+1)/N) for i in range(N)])
				
				#if ( numpy.absolute( yramp - ramp ) > 0.0001 ).any():
				#	print "NOT EQUAL!"
				#else:
				#	print "EQUAL!"
					
					
				#ramp.tofile(ramphash,sep=',',format="%.4f")
				
				
		else:
				print '...Recycling previously calculated linearPhys ramp for '  + self.name
				ramp =  numpy.fromfile(ramphash,sep=',')	

		self.y=numpy.append(self.y, ramp)
		self.lastPhys = vf
		
		return



	def tanhRise(self,vf,dt,tau,shift):
		#print "---> Initializing lattice wave : %s" % self.name
		#print "convert.cnv(%.6f) = %.6f" % ( vf, cnv(self.name,vf))
		#print "physics.cnv(%.6f) = %.6f" % ( vf, physics.cnv(self.name,vf))
		#vf=cnv(self.name,vf)
		physf = vf
		vf=physics.cnv(self.name,vf)
		v0=self.last()
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			print '...Making new tanhRise ramp for ' + self.name + \
			       ' physf=%.3f, vf = %.3f, dt = %.3f, tau = %.2f, shift = %.2f' % (physf,vf, dt, tau, shift)
			x=numpy.arange(dt/N,dt+dt/N,dt/N) # arange is half open: [start,stop)
                        #print '\t x[ 0] =',x[ 0]
                        #print '\t x[-1] =',x[-1]
                        #print '\t    ss =',self.ss
                        #print '\tlen(x) =',x.size
                        #print '\t     N =',N
			tau = tau*dt
			shift = dt/2. + shift*dt/2.
			ramp= v0 + (vf-v0)* ( (1+numpy.tanh((x-shift)/tau)) - (1+numpy.tanh((-shift)/tau)) )\
							/ ( (1+numpy.tanh((dt-shift)/tau)) - (1+numpy.tanh((-shift)/tau)) )
			self.y=numpy.append(self.y, ramp)	
			return



	####
	####
	####
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
			print "Using cnv in Exponential (for loop)"
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
			print "Using cnv in Adiabatic Ramp Down (for loop)"
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
			self.appendhold(start-self.ss)
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
	
	
	
	

	

	
