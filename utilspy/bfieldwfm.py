import sys
sys.path.append('L:/software/apparatus3/seq/seq')
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seqconf, wfm, gen, math, cnc, time, os, numpy, hashlib, evap, physics, errormsg, odt, bfieldwfm
import numpy as np



###########################################
#### GRADIENT FIELD ANALOG WAVEFORM ###
###########################################


class gradient_wave(wfm.wave):
	"""The gradient_wave class helps construct the waveform that 
		will be used to shunt current from the top coil, so that we
		cancel gravity at any value of the magnetic field
		
		The main method is 'follow', which allows the shunt current
		to be set according to our levitation calibration.
		"""
	def follow(self, bfield):
		### Levitation voltage:
		###
		### Vlev = slope * I + offset
		###
		### wherer I is the current on the bias coils
		### slope and offset have been calibrated and are set below:
		
		## These numbers are now store in physics.py
		## slope = 0.0971
		## offset = -2.7232
		
		if self.ss != bfield.ss:
			msg = "ERROR in GRADIENT wave:  step size does not match the bfield ramp!"
			print msg
			errormsg.box('gradient_wave.follow', msg)
			exit(1)
		
		print "...Setting GRADIENT to follow bfield ramp"
		
		bfieldV = numpy.copy(bfield.y)
		bfieldA = physics.inv( 'bfield', bfieldV)
		#~ self.y = slope * bfieldA + offset
		self.y= np.array([physics.cnv( 'gradientfield', bA) for bA in bfieldA])
		#~ print bfieldA
		#~ print [ a*1.0/b for a,b in zip(self.y,self.y2)]
		
		
###########################################
#### HFIMG ANALOG WAVEFORM ###
###########################################


class hfimg_wave(wfm.wave):
	"""The hfimg_wave class helps construct the waveform that 
		will be used to set hfimg.  This follows the bfield
		so that we image at the given detuning.
		"""
	def follow(self, bfield, detuning):
		### Levitation voltage:
		###
		### Vlev = slope * I + offset
		###
		### wherer I is the current on the bias coils
		### slope and offset have been calibrated and are set below:
		
		slope = 0.0971
		offset = -2.7232
		
		if self.ss != bfield.ss:
			msg = "ERROR in HFIMG wave:  step size does not match the bfield ramp!"
			print msg
			errormsg.box('hfimg_wave.follow', msg)
			exit(1)
		
		print "...Setting ANALOGHFIMG to follow bfield ramp"
		
		bfieldV = numpy.copy(bfield.y)
		bfieldG = physics.inv( 'bfield', bfieldV)* 6.8
		
		hfimg0 = -1.*(100.0 + 163.7 - 1.414*bfieldG)
		
		self.y = physics.cnv( 'analogimg', hfimg0 - detuning)
		
		return hfimg0[-1]