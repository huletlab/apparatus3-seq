import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

def getInterpolationData ():
   dat = np.loadtxt('physics/scatt_length.dat')
   f = interp1d( dat[:,0], dat[:,1] , kind ='cubic') 
   
   x = np.linspace( np.amin(dat[:,0]), np.amax(dat[:,0]), 100)
   plt.plot( dat[:,0], dat[:,1], 'o', x, f(x), '-')
   plt.legend(['data','cubic'], loc='best')
   plt.show()


if __name__ == '__main__':
  getInterpolationData()
   

def interpdat( datfile, x, y, array):
   dat = np.loadtxt( datfile, usecols  = (x,y))
   f = interp1d( dat[:,0], dat[:,1], kind='cubic')
   return f(array) 

channel_list = [ 
                 'odtdepth(100uK)', \
                 'odtfreqAx(100Hz)', \
                 'odtfreqRd(100Hz)', \
                 'odtfreqRdZ(100Hz)', \
                 'bfield(G)', \
                 'bfield(100G)', \
                 'ainns(100a0)', \
                 'arice(100a0)', \
               ]   

class calc:
   def __init__(self, wfms ):
      self.wfms = wfms
      self.calcwfms = {}
      self.ch_list = channel_list
      
   def calculate(self, ch):
      if ch in self.calcwfms.keys():
         return self.calcwfms[ch]

      ### Calculate trap depth and frequencies
      if ch == 'odtdepth(100uK)':
         return ([],[])

      if ch == 'odtfreqAx(100Hz)':
         return ([],[])

      if ch == 'odtfreqRd(100Hz)':
         return ([],[])

      if ch == 'odtfreqRdZ(100Hz)':
         return ([],[])

      ### Calculate Bfield
 
      if ch == 'bfield(G)':
         self.calcwfms[ch] = bfield_G(self.wfms)
         return self.calcwfms[ch] 

      if ch == 'bfield(100G)':
         if 'bfield(G)' not in self.calcwfms.keys():
            self.calculate('bfield(G)')
         base = self.calcwfms['bfield(G)']
         self.calcwfms[ch] = (base[0], base[1]/100.) 
         return self.calcwfms[ch]
      
      ### Calculate scattering length
      if ch == 'ainns(100a0)':
         if 'bfield(G)' not in self.calcwfms.keys():
            self.calculate('bfield(G)')
         base = self.calcwfms['bfield(G)']
         a_s = interpdat( 'physics/ainns.dat', 0, 1, base[1]) / 100. 
         self.calcwfms[ch] = (base[0], a_s)
         return self.calcwfms[ch]

      if ch == 'arice(100a0)':
         if 'bfield(G)' not in self.calcwfms.keys():
            self.calculate('bfield(G)')
         base = self.calcwfms['bfield(G)']
         a_s = interpdat( 'physics/arice.dat', 0, 1, base[1]) / 100. 
         self.calcwfms[ch] = (base[0], a_s)
         return self.calcwfms[ch]

      ### Calculate lattice,dimple depth and frequencies 

      ### Calculate on-site interactions  
    
  
      else:
         print "Physical channel not found: %s", ch


### Calculate trap depth and frequencies




### Calculate Bfield

def bfield_G( wfms):
   """This function calculates the bfield in Gauss """
   print "\nCalculating:  bfield_G ... "
   #extract the bfield waveform data
   bfield = wfms['bfield']
   bfield = [out[0] for out in bfield]
   bfield = np.concatenate( bfield, axis=0)

   times = bfield[:,0]
   bfield = bfield[:,1]

   return times, interpdat( 'physics/bfield.dat', 0, 1, bfield) * 6.8 
  
### Calculate scattering length
 
def scatt_length():
   """This function calculates the scattering length"""
   pass
       

### Calculate lattice,dimple depth and frequencies 



### Calculate on-site interactions  

def onsite_int( wfms):
   """This function calculates the onsite interaction U"""
   print "\nCalculating: onsite_int ... "

   bfield = wfms['bfield']
   latticeV0 = wfms['ir1pow'] 
   #first find the set of wfmouts where both bfield and latticeV0 are involved
   intsct =  set([i[1] for i in bfield]) & set( [j[1] for j in latticeV0])

   #then extract the data for each waveform
   bfield = [out[0]  for out in bfield if out[1] in intsct  ]
   bfield = np.concatenate( bfield, axis=0)

   latticeV0 = [out[0]  for out in latticeV0 if out[1] in intsct  ]
   latticeV0 = np.concatenate( latticeV0, axis=0) 

   #and finally check if the resulting data has the same time axis
   if not (bfield[:,0] == latticeV0[:,0]).all() or bfield.shape != latticeV0.shape: 
     print "   Mismatching time axes after intersecting bfield and latticeV0" 
     return None
   else: 
     print "   Succesfully intersected bfield and latticeV0"

   times = bfield[:,0]
   bfield = bfield[:,1]
   latticeV0 = latticeV0[:,1]

   bfield_Gauss = interpdat( 'physics/bfield.dat', 0, 1, bfield) * 6.8 
   scatt_length = interpdat( 'physics/ainns.dat', 0, 1, bfield_Gauss ) / 100. 
  
   onsite =  scatt_length
 
   return times, onsite
      
       
