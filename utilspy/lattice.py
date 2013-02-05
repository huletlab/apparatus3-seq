###########################################
#### LATTICE ANALOG WAVEFORM ###
###########################################

import sys
sys.path.append('L:/software/apparatus3/seq/seq')
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seqconf, wfm, gen, math, cnc, time, os, numpy, hashlib, evap, physics
from convert import cnv

class lattice_wave(wfm.wave):
	"""The lattice_wave class helps construct the waveforms that 
		will be used to ramp the lattice.
		
		Several methods are added that allow doing special ramps
		"""
	def tanhRise(self,vf,dt,tau,shift):
		#print "---> Initializing lattice wave : %s" % self.name
		#print "convert.cnv(%.6f) = %.6f" % ( vf, cnv(self.name,vf))
		#print "physics.cnv(%.6f) = %.6f" % ( vf, physics.cnv(self.name,vf))
		#vf=cnv(self.name,vf)
		vf=physics.cnv(self.name,vf)
		v0=self.last()
		if dt == 0.0:
			self.y[ self.y.size -1] = vf
			return
		else:
			N = int(math.floor(dt/self.ss))
			ramp=[]
			ramphash = seqconf.ramps_dir() + 'tanhRise_' \
			           + hashlib.md5(str(self.name)+str(vf)+str(v0)+str(N)+str(dt)+str(tau)+str(shift)).hexdigest()
			if not os.path.exists(ramphash) or True:
				print '...Making new tanhRise ramp for ' + self.name
				x=numpy.arange(dt/N,dt,dt/N)
				tau = tau*dt
				shift = dt/2. + shift*dt/2.
				ramp= v0 + (vf-v0)* ( (1+numpy.tanh((x-shift)/tau)) - (1+numpy.tanh((-shift)/tau)) )\
				                   / ( (1+numpy.tanh((dt-shift)/tau)) - (1+numpy.tanh((-shift)/tau)) )
				#ramp.tofile(ramphash,sep=',',format="%.4f")
			else:
				print '...Recycling previously calculated tanhRise ramp for ' + self.name
				ramp =  numpy.fromfile(ramphash,sep=',')		
			self.y=numpy.append(self.y, ramp)
		return		
		
	