import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

import argparse

channel_list = [ 
                 'odtfcpow', \
                 'odtdepth(1uK)', \
                 'odtdepth(100uK)', \
                 'odtfreqAx(100Hz)', \
                 'odtfreqRd(100Hz)', \
                 'odtfreqRdZ(100Hz)', \
                 'bfield(Amp)', \
                 'bfield(G)', \
                 'bfield(100G)', \
                 'ainns(100a0)', \
                 'arice(100a0)', \
               ]   

#
#General operations for physical data calculations 
# 
def interpdat( datfile, x, y, dat):
   table = np.loadtxt( datfile, usecols  = (x,y))
   try:
      f = interp1d( table[:,0], table[:,1], kind='cubic')
   except ValueError as e:
      print e
      print "Could not define interpolation function"
      f = lambda x: x 
   try:
      out = f(dat[:,1])
   except ValueError as e:
      out = dat[:,1] 
      print "Error when trying to interpolate from:"
      print "\t",datfile 
      print "\tTable range is  (%f,%f)" % (np.amin(table[:,0]), np.amax(table[:,0]) )
      print "\tData xrange is  (%f,%f)" % (np.amin(dat[:,1]), np.amax(dat[:,1]))
      print dat
     
   return (dat[:,0], out)

def scaleFactor( dat, scale ):
   """Takes some calculate data and scales the Y array"""
   return (dat[0], dat[1]*scale) 

#Run standalone to test interpolation of a table file
if __name__ == '__main__':
  parser = argparse.ArgumentParser('physics.py')
  parser.add_argument('datfile',action="store",type=str, help='datfile to plot')
  parser.add_argument('xcol',action="store",type=int, help='x column index')
  parser.add_argument('ycol',action="store",type=int, help='y column index')
  args=parser.parse_args() 
  
  dat = np.loadtxt( args.datfile, usecols  = (args.xcol,args.ycol))
  xdat = dat[:,0]
  ydat = dat[:,1]
  
  stackdat = np.transpose(np.vstack( (xdat,xdat) ))
  itpd =  interpdat( args.datfile, args.xcol, args.ycol, stackdat) 
  
  plt.plot( xdat, ydat, 'o', itpd[0], itpd[1], '-')
  plt.legend(['data','cubic'], loc='best')
  plt.show()


#
#Class for calculating quantities
#
class calc:
   def __init__(self, wfms ):
      self.wfms = wfms
      self.calcwfms = {}
      self.ch_list = channel_list

   def basicConversion( self, datfile, colX, colY, ch):
      """A basic channel can be converted via a single dat file"""
      dat = self.wfms[ch]
      dat = [out[0] for out in dat]
      dat = np.concatenate( dat, axis=0)
      return interpdat( datfile, colX, colY, dat) 
      
   def interpch( self, datfile, x, y, ch):
      return interpdat(datfile, x, y, np.transpose(np.vstack(self.calcwfms[ch])) )

   def prereq( self, ch ):
      if ch not in self.calcwfms.keys():
         print "      calculating prerequisite: %s" % ch
         self.calculate(ch)
      else:
         print "      reusing prerequisite: %s" % ch
 
   def calculate(self, ch):
      if ch in self.calcwfms.keys():
         return self.calcwfms[ch]

      ### Calculate trap depth and frequencies
      elif ch == 'odtfcpow': 
         """The table for the conversion from voltage to cpow is calculated
         using the odt.py module, inside the seq directory.  Type python odt.py 
         The table is saved in physics/odtfcpow.dat""" 
         self.calcwfms[ch] = self.basicConversion('physics/odtfcpow.dat', 0, 1, 'odtpow') 
         return self.calcwfms[ch] 

      elif ch == 'odtdepth(1uK)':
         self.prereq('odtfcpow')
         self.calcwfms[ch] = self.interpch('physics/odt.dat', 0, 1, 'odtfcpow')
         return self.calcwfms[ch] 

      elif ch == 'odtdepth(100uK)':
         self.prereq('odtfcpow')
         self.calcwfms[ch] = scaleFactor(self.interpch('physics/odt.dat', 0, 1, 'odtfcpow'), 1/100.)
         return self.calcwfms[ch] 

      elif ch == 'odtdepth(Er)':
         self.prereq('odtfcpow')
         self.calcwfms[ch] = scaleFactor(self.interpch('physics/odt.dat', 0, 1, 'odtfcpow'), 1/1.4)
         return self.calcwfms[ch] 

      elif ch == 'odtfreqAx(100Hz)':
         self.prereq('odtfcpow')
         self.calcwfms[ch] = scaleFactor(self.interpch('physics/odt.dat', 0, 2, 'odtfcpow'), 1/100.)
         return self.calcwfms[ch] 

      elif ch == 'odtfreqRd(100Hz)':
         self.prereq('odtfcpow')
         self.calcwfms[ch] = scaleFactor(self.interpch('physics/odt.dat', 0, 3, 'odtfcpow'), 1/100.)
         return self.calcwfms[ch] 

      elif ch == 'odtfreqRdZ(100Hz)':
         self.prereq('odtfcpow')
         self.calcwfms[ch] = scaleFactor(self.interpch('physics/odt.dat', 0, 4, 'odtfcpow'), 1/100.)
         return self.calcwfms[ch] 


      ### Calculate Bfield
      elif ch == 'bfield(Amp)':
         self.calcwfms[ch] = self.basicConversion('physics/bfield.dat', 0, 1, 'bfield')
         return self.calcwfms[ch] 
 
      elif ch == 'bfield(G)':
         self.prereq('bfield(Amp)')
         self.calcwfms[ch] = scaleFactor( self.calcwfms['bfield(Amp)'], 6.8 )
         return self.calcwfms[ch] 

      elif ch == 'bfield(100G)':
         self.prereq('bfield(G)')
         self.calcwfms[ch] = scaleFactor( self.calcwfms['bfield(G)'], 1/100.) 
         return self.calcwfms[ch]
      
      ### Calculate scattering length
      elif ch == 'ainns(100a0)':
         self.prereq('bfield(G)')
         self.calcwfms[ch] = scaleFactor(self.interpch( 'physics/ainns.dat', 0, 1, 'bfield(G)' ), 1/100.)
         return self.calcwfms[ch]

      elif ch == 'arice(100a0)':
         self.prereq('bfield(G)')
         self.calcwfms[ch] = scaleFactor(self.interpch( 'physics/arice.dat', 0, 1, 'bfield(G)' ), 1/100.)
         return self.calcwfms[ch]

      ### Calculate lattice,dimple depth and frequencies
      ### These start getting more complicated because they have two or more prerequisites
      #elif ch == 'latticeV0(Er)':
 

      ### Calculate on-site interactions  
    
      else:
         print "Physical channel not found: %s" %  ch


   
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
      
       
