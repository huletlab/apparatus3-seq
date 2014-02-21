
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d


if __name__ == "__main__":
  parser = argparse.ArgumentParser('plotdat.py')
  parser.add_argument('datfile',action="store",type=str, help='datfile to plot')
  parser.add_argument('xcol',action="store",type=int, help='x column index')
  parser.add_argument('ycol',action="store",type=int, help='y column index')
  args=parser.parse_args() 
  
  dat = np.loadtxt(args.datfile,)
  xdat = dat[:,args.xcol]
  ydat = dat[:,args.ycol]

  #f = interp1d( xdat,ydat , kind='cubic')
  
  #x = np.linspace( np.amin(xdat), np.amax(xdat), 100)
  #plt.plot( xdat, ydat, 'o', x, f(x), '-')
  #plt.legend(['data','cubic'], loc='best')
  plt.plot( xdat, ydat, 'o')
  plt.legend(['data'], loc='best')
  plt.show()



