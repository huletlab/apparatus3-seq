import numpy as np
from scipy.interpolate import interp1d, UnivariateSpline
import matplotlib.pyplot as plt

import argparse
import glob
import os

import pwlinterpolate, errormsg

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
#IR and GR photodiode calibrations
#

#beam waist
w0d = {}   
w0d['ir1pow'] = 40.6
w0d['ir2pow'] = 40.7
w0d['ir3pow'] = 41.5
w0d['greenpow1'] = 37.3
w0d['greenpow2'] = 36.0
w0d['greenpow3'] = 34.5

#PD slopes
m1d = {}
m1d['ir1pow'] = 8.00e-03
m1d['ir2pow'] = 8.21e-03
m1d['ir3pow'] = 6.86e-03
m1d['greenpow1'] = 8.33e-03
m1d['greenpow2'] = 9.17e-03
m1d['greenpow3'] = 7.05e-03

#PD offset
V0d = {}
V0d['ir1pow'] = 2.55e-02
V0d['ir2pow'] = 1.19e-02
V0d['ir3pow'] = 1.85e-02
V0d['greenpow1'] = 8.21e-2 - 4.4e-2
V0d['greenpow2'] = 3.23e-3
V0d['greenpow3'] = 8.84e-3

#Er max
ErMaxd = {}
ErMaxd['ir1pow'] = 83.6
ErMaxd['ir2pow'] = 81.3
ErMaxd['ir3pow'] = 93.4
ErMaxd['greenpow1'] = 9.97
ErMaxd['greenpow2'] = 12.6
ErMaxd['greenpow3'] = 33.6

#V max
VMaxd = {}
VMaxd['greenpow1'] = 4.18
VMaxd['greenpow2'] = 5.32
VMaxd['greenpow3'] = 10.0



#
#Class for making physical to voltage conversions
#
class convert:
    def __init__(self):
        dats = glob.glob('L:/software/apparatus3/convert/data/*.dat')
        self.fs={}
        for d in dats:
            table = np.loadtxt(d, usecols  = (1,0))
            ch =  os.path.splitext( os.path.split(d)[1] )[0]
            try:
                #f = interp1d( table[:,0], table[:,1], kind='linear')
                #print "interpolating ch = %s" % d
                f = pwlinterpolate.interp1d( table[:,0], table[:,1] , name = ch)
            except ValueError as e:
                print e
                print "Could not define cubic interpolation function for : \n\t%s" % d
                try:
                    #f = interp1d( table[:,0], table[:,1], kind='linear')
                    #f = interp1d( table[:,0], table[:,1], kind='linear')
                    #f = UnivariateSpline( table[:,0], table[:,1], k=1, s=0)
                    f = pwlinterpolate.interp1d( table[:,0], table[:,1] )
                except ValueError as e:
                    print e
                    print "Could not define cubic interpolation function for : \n\t%s" % d
                    exit(1)
            
            self.fs[ch] = f

    def plot(self):
        dats = glob.glob('L:/software/apparatus3/convert/data/*.dat')
        for d in dats:
            ch =  os.path.splitext( os.path.split(d)[1] )[0]

            table = np.loadtxt(d, usecols  = (1,0))
            xdat = table[:,0]
            ydat = table[:,1]
            plt.plot( xdat, ydat, 'o')

            xvals = np.union1d ( np.linspace( np.amin(xdat), np.amax(xdat) , 20 ), xdat )
            try:
                plt.plot( xvals, self.fs[ch](xvals), '-')
            except ValueError as e:
                print "Error in producing interpolation data plot for ch = %s" % ch
                #for val in xvals:
                #  print val
                #  print " f(%f) = %f "%  (val, self.fs[ch](val))
                print xvals
                print xdat
                print e
            plt.legend([ch,'interpolation'], loc='best')
            plt.show()



    def check( self, ch , ins, outs ):
        
        insa  = np.asarray(ins[0])
        outsa = np.asarray(outs[0])
         
        outof_bounds_in = (insa < ins[1]).any() or (insa> ins[2]).any()
        outof_bounds_out = (outsa < outs[1]).any() or (outsa > outs[2]).any()
        
        if outof_bounds_in.any():
            msg = "Desired value is out of specified range."
            msg = msg +  "\t%s  = %f   :  MIN=%f , MAX=%f" % (ch, ins[0], ins[1], ins[2] )
            print msg
            errormsg.box( "CONVERSION", msg)
            exit(1)
        if outof_bounds_out.any():
            msg = "Output is out of specified range."
            msg = msg + "\t%s  = %f   :  MIN=%f , MAX=%f" % (ch, outs[0], outs[1], outs[2] )
            print msg
            errormsg.box( "CONVERSION", msg)
            exit(1)
        return outs[0]

    def cnv(self, ch, val):
        if ch == 'trapdet':
            ### IN    :  MHz detuning at atoms
            ### CALIB :  Double-pass AOM frequency
            ### OUT   :  Volts
            out =  self.fs[ch]( (val + 120. + 120.) / 2. )
            return self.check( ch, (val, -200.0, 200.), (out, 2.0, 8.0))

        if ch == 'repdet':
            ### IN    :  MHz detuning at atoms
            ### CALIB :  Double-pass AOM frequency
            ### OUT   :  Volts
            out =  self.fs[ch]( (val + 228.2 -80.0 + 120.) / 2. )
            return self.check( ch, (val, -200.0, 200.), (out, 2.0, 8.0))

        if ch == 'motpow':
            ### IN    :  Isat/beam at atoms
            ### CALIB :  Power measured by MOT TA monitor
            ### OUT   :  Volts
            w0 = 0.86  # beam waist
            ta = 1.682 # power lost to TA sidebands
            op = 1.37  # power loss in MOT optics
            calib = op*ta*6*val*5.1*(3.14*w0*w0)/2.
            out = self.fs[ch]( calib )
            return self.check( ch, (val, 0.0, 1.14), (out, 0.1, 10))

        if ch == 'trappow':
            ### IN    :  power injected to TA
            ### CALIB :  same as IN
            ### OUT   :  volts
            out = self.fs[ch]( val )
            return self.check( ch, (val, 0.0, 15.9), (out, 0., 10))
            
        if ch == 'reppow':
            ### IN    :  power injected to TA
            ### CALIB :  same as IN
            ### OUT   :  volts
            out = self.fs[ch]( val )
            return self.check( ch, (val, 0.0,13.5), (out, 0., 10))
            
        if ch == 'bfield':
            ### IN    :  current measured on power supply
            ### CALIB :  same as IN
            ### OUT   :  volts
            out = self.fs[ch]( val )
            return self.check( ch, (val, 0.0,120.), (out, 0., 8.2))
        
        if ch == 'uvdet':
            ### IN    :  UV detuning in MHz
            ### CALIB :  Double-pass AOM frequency
            ### OUT   :  Volts
            out = self.fs[ch]( (val + 130.17 )/2.0  )
            return self.check( ch, (val, -8.,4.0), (out, 2.744, 4.744))
            
        if ch == 'uvpow':
            ### IN    :  power measured after 75 um pinhole
            ### CALIB :  same as IN
            ### OUT   :  volts
            out = self.fs[ch]( val )
            return self.check( ch, (val, 0.0,20.0), (out, 0., 7.0))
            
        if ch == 'uvpow2':
            ### IN    :  volts
            ### CALIB :  None
            ### OUT   :  volts
            out = val
            return self.check( ch, (val, 0.0,8.0), (out, 0., 8.0))
            
        if ch == 'uv1freq':
            ### IN    :  Frequency of uvaom1 in MHz
            ### CALIB :  same as IN
            ### OUT   :  volts
            out = self.fs[ch]( val )
            return self.check( ch, (val, 70.0,153.0), (out, 0., 10.0))
            
        if ch == 'shunt':
            ### IN    :  volts
            ### CALIB :  None
            ### OUT   :  volts
            out = val
            return self.check( ch, (val, 0.0,10.0), (out, 0., 10.0))
            
        if ch == 'ipganalog':
            ### IN    :  volts
            ### CALIB :  None
            ### OUT   :  volts
            out = val
            return self.check( ch, (val, 0.0,10.0), (out, 0., 10.0))
            
        if ch == 'rfmod':
            ### IN    :  volts
            ### CALIB :  None
            ### OUT   :  volts
            out = val
            return self.check( ch, (val, 0.0,10.0), (out, -1., 1.0))
            
            
        if ch == 'analogimg':
            ### IN    :  Frequency of offset lock beat signal MHz
            ### CALIB :  same as IN
            ### OUT   :  volts
            out = self.fs[ch]( val )
            return self.check( ch, (val, 300.,1500.0), (out, 0., 10.0))
            
            
            
        if ch == 'lcr1' or ch == 'lcr2' or ch == 'lcr3':
            ### IN    :  Lattice ratio:  1=lattice  0=dimple
            ### CALIB :  same as IN
            ### OUT   :  volts
            out = self.fs[ch]( val )
            return self.check( ch, (val, 0.0,1.0), (out, 0., 10.0))
            
        if ch == 'ir1pow' or ch == 'ir2pow' or ch == 'ir3pow':
            ### IN    :  Lattice depth in Er
            ### CALIB :  None (using PD slope)
            ### OUT   :  volts         
            #power in mW
            p = 1000. * val / 4. / 38709. * 1.4 * w0d[ch] * w0d[ch] 
            out = m1d[ch] * p + V0d[ch] 
            return self.check( ch, (val, 0.0, ErMaxd[ch]), (out, 0., 10.0))
            
            
        if ch == 'greenpow1' or ch == 'greenpow2' or ch == 'greenpow3':
            ### IN    :  Lattice depth in Er
            ### CALIB :  None (using PD slope)
            ### OUT   :  volts
            #power in mW
            p = 1000. * val / 1. / 39461. * 1.4 * w0d[ch] * w0d[ch] 
            out = m1d[ch] * p + V0d[ch] 
            return self.check( ch, (val, 0.0, ErMaxd[ch]), (out, 0., VMaxd[ch]))
            
        errormsg.box('CONVERSION : ' + ch, 'No conversion defined for this channel')
        raise ValueError("No conversion has been defined for channel = %s" % ch )
        return None





dll = convert()


#datfile =  'L:/software/apparatus3/convert/data/' + ch + '.dat'

def cnv( ch, val ):
    global dll
    return dll.cnv(ch, val)
#   datfile =  'L:/software/apparatus3/convert/data/' + ch + '.dat'
#   table = np.loadtxt(datfile, usecols  = (1,0))
#   try:
#      f = interp1d( table[:,0], table[:,1], kind='cubic')
#   except ValueError as e:
#      print e
#      print "Could not define interpolation function"
#      f = lambda x: x
#   try:
#      out = f(val)
#   except ValueError as e:
#      out = val
#      print e
#      print "Error when trying to interpolate from:"
#      print "\t",datfile
#      print "\tTable range is  (%f,%f)" % (np.amin(table[:,0]), np.amax(table[:,0]) )
#      #print "\tData xrange is  (%f,%f)" % (np.amin(val[:,1]), np.amax(val[:,1]))
#      print val
#   return out



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
    dll.plot()
    exit(0)


    parser = argparse.ArgumentParser('physics.py')
    parser.add_argument('datfile',action="store",type=str, help='datfile to plot')
    parser.add_argument('xcol',action="store",type=int, help='x column index')
    parser.add_argument('ycol',action="store",type=int, help='y column index')
    parser.add_argument('--cnv',action="store",type=bool, help='plot cnv interpolations')
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
