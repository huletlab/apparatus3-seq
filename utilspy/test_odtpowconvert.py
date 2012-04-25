import numpy
import sys, math
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/convert')

from wfm import OdtpowConvert

#~ import matplotlib.pyplot as plt

#~ volt_a=numpy.array([])
#~ phys_a=numpy.array([])

#~ for phys in numpy.arange(0,10.0,0.1):
    #~ volt_a=numpy.append(volt_a,OdtpowConvert(phys))
    #~ phys_a=numpy.append(phys_a,phys)
    
#~ data = numpy.loadtxt('H:/ernie/data/PD_AOM.dat')


#~ for point in data:
    #~ print point

print "phys=0.0  ==> volt = %.2f" % OdtpowConvert(0.0)
print "phys=10.0 ==> volt = %.2f" % OdtpowConvert(10.0)
print "phys=12.0 ==> volt = %.2f" % OdtpowConvert(12.0)

#~ plt.plot(data[:,1]/3.573, -1*data[:,0],'.')
#~ plt.plot(phys_a,volt_a)
#~ plt.xlabel('phys')
#~ plt.ylabel('volt')
#~ plt.show()

