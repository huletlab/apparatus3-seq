import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
sys.path.append('/lab/software/apparatus3/py')
import qrange, statdat,fitlibrary
from scipy.interpolate import UnivariateSpline
from uncertainties import ufloat

# Fetch all data

dat = np.loadtxt('ajochim_original.dat') 
dat2 = np.loadtxt('ajochim_nonarrow.dat') 

# Get figure started, specifiy grid

from matplotlib import rc
rc('font',**{'family':'serif'})
figure = plt.figure(figsize=(5.,4.))
gs = matplotlib.gridspec.GridSpec( 1,1) 
figure.suptitle('Scattering length $a_{12}$ (Jochim 2013)')

ax = plt.subplot( gs[0,0] ) 
ax.plot( dat2[:,0], dat2[:,1], label='$a_{12}$, smooth narrow')
ax.plot( dat[:,0], dat[:,1], label='$a_{12}$') 

ax.plot( dat[:,0], dat[:,2], label='$a_{13}$')
ax.plot( dat[:,0], dat[:,3], label='$a_{23}$')
 

ax.set_ylabel('$a_{0}$')
ax.set_xlabel('Magnetic field (Gauss)')
ax.grid()
ax.legend(loc='best',numpoints=1,prop={'size':8})

ax.set_ylim(-1000.,1000.)


gs.tight_layout(figure, rect=[0,0.03,1.,0.95])
plt.savefig('ajochim_plot.png', dpi=150)
plt.show()


