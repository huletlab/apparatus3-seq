import numpy as np
import numpy.ma as ma
from scipy.interpolate import interp1d, UnivariateSpline


import argparse
import glob
import os
import pprint



if os.name == 'posix':
    lab = '/lab/'
else:
    lab = 'L:/'
    
import sys
sys.path.append(lab + 'software/apparatus3/seq')
sys.path.append(lab + 'software/apparatus3/seq/utilspy')

physpath = lab + 'software/apparatus3/seq/physics/'

import pwlinterpolate, errormsg


import seqconf, gen


channel_list = [
                 'odtfcpow', \
                 'odtdepth(1uK)', \
                 'odtdepth(Er)', \
                 'odtdepth(100uK)', \
                 'odtfreqAx(100Hz)', \
                 'odtfreqRd(100Hz)', \
                 'odtfreqRdZ(100Hz)', \
                 'bfield(Amp)', \
                 'bfield(G)', \
                 'hfimg0(100MHz)', \
                 'analoghfimg(100MHz)', \
                 'bfield(100G)', \
                 'ainns(100a0)', \
                 'arice(100a0)', \
                 'greenpow1(Er)',\
                 'greenpow2(Er)',\
                 'greepow3(Er)',\
                 'ir1pow(Er)',\
                 'ir2pow(Er)',\
                 'ir3pow(Er)',\
                 'greenpow1(100mW)',\
                 'greenpow2(100mW)',\
                 'greenpow3(100mW)',\
                 'ir1pow(100mW)',\
                 'ir2pow(100mW)',\
                 'ir3pow(100mW)',\
                 'lcr1(alpha)',\
                 'lcr2(alpha)',\
                 'lcr3(alpha)',\
                 'lattice1V0(Er)',\
                 'lattice2V0(Er)',\
                 'lattice3V0(Er)',\
                 'lattice1freq(100kHz)',\
                 'lattice2freq(100kHz)',\
                 'lattice3freq(100kHz)',\
                 'lattice1V0(Er)',\
                 'lattice2V0(Er)',\
                 'lattice3V0(Er)',\
                 'lattice1freq(100kHz)',\
                 'lattice2freq(100kHz)',\
                 'lattice3freq(100kHz)',\
                 't1(Er)',\
                 't2(Er)',\
                 't3(Er)',\
                 't1(kHz)',\
                 't2(kHz)',\
                 't3(kHz)',\
                 'wannierF1(Er/a)',\
                 'wannierF2(Er/a)',\
                 'wannierF3(Er/a)',\
                 'U1(Er)',\
                 'U2(Er)',\
                 'U3(Er)',\
                 'U1(kHz)',\
                 'U2(kHz)',\
                 'U3(kHz)',\
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
m1d['ir1pow'] = 7.55e-03
m1d['ir2pow'] = 8.21e-03
m1d['ir3pow'] = 6.86e-03
m1d['greenpow1'] = 8.33e-03
m1d['greenpow2'] = 9.17e-03
m1d['greenpow3'] = 7.05e-03

#PD offset
V0d = {}
V0d['ir1pow'] = 3.88e-3
V0d['ir2pow'] = 1.19e-02
V0d['ir3pow'] = 1.85e-02
V0d['greenpow1'] = 8.21e-2 - 4.4e-2
V0d['greenpow2'] = 3.23e-3
V0d['greenpow3'] = 8.84e-3

#Er max
ErMaxd = {}
ErMaxd['ir1pow'] = 83.6
ErMaxd['ir2pow'] = 81.2
ErMaxd['ir3pow'] = 93.4
ErMaxd['greenpow1'] = 9.97
ErMaxd['greenpow2'] = 12.6
ErMaxd['greenpow3'] = 33.5

#V max
VMaxd = {}
VMaxd['ir1pow'] = 10.0
VMaxd['ir2pow'] = 10.0
VMaxd['ir3pow'] = 10.0
VMaxd['greenpow1'] = 4.17
VMaxd['greenpow2'] = 5.32
VMaxd['greenpow3'] = 10.0




try:
    ODT = gen.getsection('ODT')
    ODTCALIB = gen.getsection('ODTCALIB')
    if ODT.use_servo == 0:
        b  = ODTCALIB.b_nonservo
        m1 = ODTCALIB.m1_nonservo
        m2 = ODTCALIB.m2_nonservo
        m3 = ODTCALIB.m3_nonservo
        kink1 = ODTCALIB.kink1_nonservo
        kink2 = ODTCALIB.kink2_nonservo
    elif ODT.use_servo == 1:
        b  = ODTCALIB.b
        m1 = ODTCALIB.m1
        m2 = ODTCALIB.m2
        m3 = 0.
        kink1 = ODTCALIB.kink
        kink2 = 11.

except:
    print
    print "Could not setup odtpow calibration parameters."
    print "Possibly because the report is not loaded."
    print "If you are running this module as standalone"
    print "the odtpow calibration params will be loaded"
    print "from params.INI"
    print 

    from configobj import ConfigObj
    report=ConfigObj( lab + 'software/apparatus3/log/params/params.INI' )
    #print report
    b=float(report['ODTCALIB']['b'])
    m1=float(report['ODTCALIB']['m1'])
    m2=float(report['ODTCALIB']['m2'])
    m3=0.001
    kink1=float(report['ODTCALIB']['kink'])
    kink2=11
        






class odtpow_ch:
    def __init__(self):
        self.GT10warning = True
        self.LT0warning = True
        
    def cnvcalib(self, phys):
        # odt phys to volt conversion
        # max odt power = 10.0
        
        volt = b+m1*kink1 + m2*(kink2-kink1) + m3*(phys-kink2) if phys > kink2 else \
                b+m1*kink1 + m2*(phys-kink1) if phys > kink1 else b+m1*phys

        if volt >10:
            volt=10.	
            if self.GT10warning==False:
                errormsg.box('OdtpowConvert','Odtpow conversion has resulted in a value greater than 10 Volts!'\
                                        +' \n\nResult will be coerced and this warning will not be shown again')
                self.GT10warning=True
        if volt <0.:
            volt=0.
            if self.LT0warning==False:
                errormsg.box('OdtpowConvert','Odtpow conversion has resulted in a value less than 0 Volts!' \
                                        + '\n\nResult will be coerced and this warning will not be shown again')
                self.LT0warning=True                    
                    
        return volt
    
    def invcalib(self, volt):
        
        phys=(volt-b-m1*kink1-m2*(kink2-kink1))/m3+kink2 if volt> b+m1*kink1+m2*(kink2-kink1) \
            else (volt-b-m1*kink1)/m2+kink1 if volt > b+m1*kink1 \
                else (volt-b)/m1
                    
        if phys > 11.:
            phys = 11.
        if phys < 0.:
            phys = 0.
                    
        return phys
    
    def f( self, p ): return p
    def g( self, p ): return p
        
    def physlims(self):
        return np.array([0., 11.0] )
    def voltlims(self):
        return np.array([0., 10.0] ) 


class lattice_ch:
    def __init__(self, name, w0, m, V0, ErMax, Vmax): 
        self.name = name
        self.w0 = w0
        self.m = m
        self.V0 = V0
        self.ErMax = ErMax
        self.Vmax = Vmax
    ### CALIB : power in mW 
    ### FS : PD voltag
    def cnvcalib( self, val ):
        if 'ir' in self.name:
            return 1000. * val / 4. / 38709. * 1.4 * self.w0 * self.w0 
        if 'gr' in self.name:
            return 1000. * val / 1. / 39461. * 1.4 * self.w0 * self.w0
    def invcalib( self, val ):
        if 'ir' in self.name:
            return val / 1000. * 4. * 38709. / 1.4 / self.w0 / self.w0
        if 'gr' in self.name:
            return val / 1000. * 1. * 39461. / 1.4 / self.w0 / self.w0
            
    def f(self, p):
        return self.m * p + self.V0
        
    def g(self, p):
        return (p-self.V0)/self.m
    
    def physlims(self):
        return np.array([0., self.ErMax] )
    def voltlims(self):
        return np.array([0., self.Vmax] ) 



#
#Class for making physical to voltage conversions
#
class convert:
    
    def cnv(self, ch, val,errorshow = 1):
        if ch not in self.fs.keys():
            
            print "Channels with defined conversions: "
            pprint.pprint(self.fs.keys())
            if errorshow:
                errormsg.box('CONVERSION : ' + ch, 'No conversion defined for this channel')
            raise ValueError("No conversion has been defined for channel = %s" % ch )
            return None
            
        out = self.fs[ch](  self.cnvcalib[ch]( val) )
        return self.check( ch, val, out)[0]
        
    def inv(self, ch, val,errorshow = 1):
        if ch not in self.fs.keys():
            
            print "Channels with defined conversions: "
            pprint.pprint(self.fs.keys())
            
            if errorshow:
                  errormsg.box('CONVERSION : ' + ch, 'No conversion defined for this channel')
            raise ValueError("No conversion has been defined for channel = %s" % ch )
            return None
        
        out = self.invcalib[ch]( self.gs[ch]( val) )
        return self.check( ch, out, val)[1]
    
    def __init__(self):
        
        ### This dictionaries define the functions used for conversion 
        self.fs={}
        self.gs={}
        self.cnvcalib={}
        self.invcalib={}
        self.physlims={}
        self.voltlims={}
        
        
        
        ### The for loop below takes care of all the channels that 
        ### are associated with a calibration file 
        dats = glob.glob(lab + 'software/apparatus3/convert/data/*.dat')

        for d in dats:
            table = np.loadtxt(d, usecols  = (1,0))
            
            ydat = table[:,1]  # voltages
            xdat = table[:,0] # calibrated quantity
            
            ch =  os.path.splitext( os.path.split(d)[1] )[0]
            
            try:
                f = pwlinterpolate.interp1d( xdat, ydat , name = ch)
                g = pwlinterpolate.interp1d( ydat, xdat , name = ch)
                
            except ValueError as e:
                print e
                print "Could not define piecewiwse linear nterpolation function for : \n\t%s" % d
                exit(1)
            
            self.fs[ch] = f
            self.gs[ch] = g
            
            
            if ch == 'trapdet':
                ### IN    :  MHz detuning at atoms
                ### CALIB :  Double-pass AOM frequency
                self.cnvcalib[ch] = lambda val: (val+120.+120.)/2. 
                self.invcalib[ch] = lambda val: 2*val - 120 - 120. 
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([2.0, 8.0])
                
            elif ch == 'repdet':
                ### IN    :  MHz detuning at atoms
                ### CALIB :  Double-pass AOM frequency
                self.cnvcalib[ch] = lambda val: (val+228.2 -80.0 + 120.)/2. 
                self.invcalib[ch] = lambda val: 2*val -228.2 + 80.0 - 120.
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([2.0, 8.0])
                
            elif ch == 'motpow':
                ### IN    :  Isat/beam at atoms
                ### CALIB :  Power measured by MOT TA monitor
                w0 = 0.86  # beam waist
                ta = 1.682 # power lost to TA sidebands
                op = 1.37  # power loss in MOT optics
                self.cnvcalib[ch] = lambda val: op*ta*6*val*5.1*(3.14*w0*w0)/2.
                self.invcalib[ch] = lambda val: 2*val/op/ta/6/5.1/(3.14*w0*w0) 
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([0.1, 10.])

            elif ch == 'trappow' or ch == 'reppow':
                ### IN    :  power injected to TA
                ### CALIB :  same as IN
                self.cnvcalib[ch] = lambda val: val
                self.invcalib[ch] = lambda val: val
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([0., 10.])
                

            elif ch == 'bfield':
                ### IN    :  current measured on power supply
                ### CALIB :  same as IN
                self.cnvcalib[ch] = lambda val: val
                self.invcalib[ch] = lambda val: val
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([0., 9.0])
                
            elif ch == 'uvdet':
                ### IN    :  UV detuning in MHz
                ### CALIB :  Double-pass AOM frequency
                self.cnvcalib[ch] = lambda val: (val + 130.17)/2.0
                self.invcalib[ch] = lambda val: val*2.0 - 130.17
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([2.744, 4.744])
                
            elif ch == 'uvpow':
                ### IN    :  power measured after 75 um pinhole
                ### CALIB :  same as IN
                self.cnvcalib[ch] = lambda val: val
                self.invcalib[ch] = lambda val: val
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([0., 7.0])
        
            elif ch == 'uv1freq':
                ### IN    :  Frequency of uvaom1 in MHz
                ### CALIB :  same as IN
                self.cnvcalib[ch] = lambda val: val
                self.invcalib[ch] = lambda val: val
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([0., 10.0])

            elif ch == 'analogimg':
                ### IN    :  Frequency of offset lock beat signal MHz
                ### CALIB :  same as IN
                self.cnvcalib[ch] = lambda val: val
                self.invcalib[ch] = lambda val: val
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([0., 10.0])
                
            elif ch == 'lcr1' or ch == 'lcr2' or ch == 'lcr3':
                ### IN    :  Lattice ratio:  1=lattice  0=dimple
                ### CALIB :  same as IN
                self.cnvcalib[ch] = lambda val: val
                self.invcalib[ch] = lambda val: val
                self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
                self.voltlims[ch] = np.array([0., 10.0])
                
            else:
                self.cnvcalib[ch] = lambda val:val
                self.invcalib[ch] = lambda val:val
                self.physlims[ch] = None
                self.voltlims[ch] = None
             
             
        
        ### Channels that are NOT associated with calibration files are 
        ### defined below 

        chs = ['uvpow2', 'gradientfield', 'ipganalog', 'rfmod'] 
        for ch in chs:
            self.cnvcalib[ch] = lambda val: val
            self.invcalib[ch] = lambda val: val
            self.fs[ch] = lambda x: x 
            self.gs[ch] = lambda x: x
            self.physlims[ch] = np.array([0., 10.])
            self.voltlims[ch] = np.array([0., 10.])
        
        
        latticechs = ['ir1pow', 'ir2pow', 'ir3pow','greenpow1', 'greenpow2', 'greenpow3' ]
        for ch in latticechs:
            ### CALIB : power in mW 
            ### FS : PD voltag
            l = lattice_ch( ch, w0d[ch], m1d[ch], V0d[ch], ErMaxd[ch], VMaxd[ch])
            self.cnvcalib[ch] = l.cnvcalib
            self.fs[ch] = l.f
            self.invcalib[ch] = l.invcalib
            self.gs[ch] = l.g
            self.physlims[ch] = l.physlims()
            self.voltlims[ch] = l.voltlims()
            
        ### ODTPOW
        o = odtpow_ch() 
        ch = 'odtpow'
        self.cnvcalib[ch] = np.vectorize(o.cnvcalib)
        self.fs[ch] = o.f
        self.invcalib[ch] = np.vectorize(o.invcalib)
        self.gs[ch] = o.g
        self.physlims[ch] = o.physlims()
        self.voltlims[ch] = o.voltlims()    

        ### TUNNELING / WANNIERFACTOR to LATTICE DEPTH
        tANDu = ['t_to_V0','wF_to_V0']
        for ch in tANDu:
            ### CALIB : unity
            ### FS : interpolation
            if 't_' in ch:
                table = np.loadtxt(physpath+'tANDU.dat', usecols  = (1,0))
            elif 'wF_' in ch:
                table = np.loadtxt(physpath+'tANDU.dat', usecols  = (2,0))
            else:
                msg = 'ERROR initializing physics.py conversion ch = %s' % ch
                errormsg.box('PHYSICS.PY', msg)
                exit(1)
            
            ydat = table[:,1] # lattice depths
            xdat = table[:,0] # tunneling / wFactor
            
            try:
                f = pwlinterpolate.interp1d( xdat, ydat , name = ch)
                g = pwlinterpolate.interp1d( ydat, xdat , name = ch)
                
            except ValueError as e:
                print e
                print "Could not define piecewiwse linear nterpolation function for : \n\t%s" % d
                exit(1)
 
            self.fs[ch] = f
            self.gs[ch] = g
           
            self.cnvcalib[ch] = lambda val: val
            self.invcalib[ch] = lambda val: val
            self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
            self.voltlims[ch] = np.array([0., 46.])

        ### SCATTERING LENGTH to BFIELD 
        ch = 'as_to_B' 
        ### CALIB : unity
        ### FS : interpolation
        table = np.loadtxt(physpath+'ainns.dat', usecols  = (1,0))

        ydat = table[:,1] # bfield (Gauss)
        xdat = table[:,0] # scattering length (a0)
        
        try:
            f = pwlinterpolate.interp1d( xdat, ydat , name = ch)
            g = pwlinterpolate.interp1d( ydat, xdat , name = ch)
            
        except ValueError as e:
            print e
            print "Could not define piecewiwse linear nterpolation function for : \n\t%s" % d
            exit(1)

        self.fs[ch] = f
        self.gs[ch] = g

        self.cnvcalib[ch] = lambda val: val
        self.invcalib[ch] = lambda val: val
        self.physlims[ch] = self.invcalib[ch]( np.array( [ np.amin(xdat), np.amax(xdat) ] ) ) 
        self.voltlims[ch] = np.array( [ np.amin(xdat), np.amax(xdat) ] ) 
         
         

    def plot(self):
        import matplotlib.pyplot as plt
        dats = glob.glob(lab + 'software/apparatus3/convert/data/*.dat')
        
        plotdat = raw_input("Do you wish to plot calibrations in .dat files? (y/n)")
        
        
        datchs = []
        for d in dats:
            ch =  os.path.splitext( os.path.split(d)[1] )[0]
            datchs.append(ch)

            table = np.loadtxt(d, usecols  = (1,0))
            xdat = table[:,0]
            ydat = table[:,1]
           
            
            print "-------- %s --------" % ch 
            print "physical limits = ", self.physlims[ch]
            print "voltage  limits = ", self.voltlims[ch]
            
            if plotdat == 'y':
                
                plt.plot( xdat, ydat, 'o')

                xvals = np.union1d ( np.linspace( np.amin(xdat), np.amax(xdat) , 20 ), xdat )
                try:
                    plt.plot( xvals, self.fs[ch](xvals), '-')
                except ValueError as e:
                    print "Error in producing interpolation data plot for ch = %s" % ch
                    print xvals
                    print xdat
                    print e
                plt.legend([ch,'interpolation'], loc='best')
                plt.show()
                
        plotdat = raw_input("Do you wish to plot conversions for channels NOT in .dat files? (y/n)")
        
    
        
        for ch in self.fs.keys():
            if ch not in datchs and ( 'ir' in ch or 'gr' in ch or 'odt' in ch or 'V0' in ch):
                print "-------- %s --------" % ch 
                print "physical limits = ", self.physlims[ch]
                print "voltage  limits = ", self.voltlims[ch]
                
                voltvals = np.linspace( self.voltlims[ch][0] , self.voltlims[ch][1] , 40 )
                physvals = np.linspace( self.physlims[ch][0] , self.physlims[ch][1] , 40 )
                
                if plotdat == 'y':

                    #~ try:

                        
                    plt.plot( self.cnv(ch,physvals), physvals,  '--', lw=2)
                    plt.plot( voltvals, self.inv(ch,voltvals), '-')
                        
                    #~ except ValueError as e:
                        #~ print "Error in producing conversion plot for ch = %s" % ch
                        #~ print "voltvals = ", voltvals
                        #~ print "physvals = ", physvals
                        #~ print xdat
                        #~ print e
                        
                    plt.legend([ch+'_cnv', ch+'_inv'], loc='best')
                    plt.show()
                
                


    def check( self, ch , phys, volt ):
        
        physa = np.asarray(phys)
        volta = np.asarray(volt)
        
        #Give a little room for rounding errors 
        #and some wiggle room for the physical limits
        physMin = self.physlims[ch][0] - 0.000001
        physMax = self.physlims[ch][1] + 0.000001
        
        
        physMin = physMin - (physMax-physMin)*0.01
        physMax = physMax + (physMax-physMin)*0.01
        

        voltMin = self.voltlims[ch][0] - 0.000001
        voltMax = self.voltlims[ch][1] + 0.000001
        
        #print type(val)
        #print type(out)
        
        below_bound_phys = physa < physMin
        above_bound_phys = physa > physMax
        
        below_bound_volt = volta < voltMin
        above_bound_volt = volta > voltMax
        
        if below_bound_phys.any() or above_bound_phys.any():
            print "phys =", physa
            out_of_bounds_phys = None
            
            print "Error in conversion of %s with length = %d" % ( type(physa), len(physa) )
              
            msg = "The following values are outside the physical limits [%f,%f]: " % (physMin, physMax)
            
            if physa.ndim < 1:
                out_of_bounds_phys = physa
                msg = msg + '\n\t' + str(out_of_bounds_phys) 
            else:
                out_of_bounds_phys  =  np.concatenate( (physa[ np.where( physa < physMin ) ],physa[np.where( physa > physMax)] ))
                msg = msg + '\n\t' + str(out_of_bounds_phys) 
            
            print msg 
              
            errormsg.box('CONVERSION CHECK:: ' + ch, msg)

            raise ValueError("A value is outside the physics range.  ch = %s" % ch)

        if below_bound_volt.any() or above_bound_volt.any():

            
            out_of_bounds_volt = None
              
            msg = "The following values are outside the voltage limits [%f,%f]: " % (voltMin, voltMax)

            if volta.ndim < 1:
                out_of_bounds_volt = volta
                msg = msg + '\n\t' + str(out_of_bounds_volt) 
            else:
                out_of_bounds_volt  =  np.concatenate( (volta[ np.where( volta < voltMin ) ], volta[np.where( volta > voltMax)]))
                msg = msg + '\n\t' + str(out_of_bounds_volt) 
            
            print msg 
              
            errormsg.box('CONVERSION CHECK :: ' + ch, msg)

            raise ValueError("A value is outside the voltage range. ch = %s" % ch)
                
                
        return (volt, phys)







dll = convert();

def cnv( ch, val ):
    global dll
    return dll.cnv(ch, val)
    
def inv( ch, val ):
    global dll
    return dll.inv(ch, val)




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
    #~ dll.plot()
    #~ exit(0)


    parser = argparse.ArgumentParser('physics.py')
    parser.add_argument('channel',action="store",type=str, help='Channel to convert')
    parser.add_argument('value',action="store",type=float, help='value to convert')
    #~ parser.add_argument('datfile',action="store",type=str, help='datfile to plot')
    #~ parser.add_argument('xcol',action="store",type=int, help='x column index')
    #~ parser.add_argument('ycol',action="store",type=int, help='y column index')
    #~ parser.add_argument('--cnv',action="store",type=bool, help='plot cnv interpolations')
    args=parser.parse_args()
    
    if 'Phys' in args.channel:
        ch = args.channel.split('Phys')[0]
        print "converted value =",dll.inv(ch,args.value)
    
    else:
        print "converted value =",dll.cnv(args.channel,args.value)
    #~ dat = np.loadtxt( args.datfile, usecols  = (args.xcol,args.ycol))
    #~ xdat = dat[:,0]
    #~ ydat = dat[:,1]

    #~ stackdat = np.transpose(np.vstack( (xdat,xdat) ))
    #~ itpd =  interpdat( args.datfile, args.xcol, args.ycol, stackdat)

    #~ plt.plot( xdat, ydat, 'o', itpd[0], itpd[1], '-')
    #~ plt.legend(['data','cubic'], loc='best')
    #~ plt.show()


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
    
    def cnvInversion( self, ch):
        """A basic channel can be converted by using its inverse conversion function"""
        dat = self.wfms[ch]
        dat = [out[0] for out in dat]
        dat = np.concatenate( dat, axis=0)
        return (dat[:,0], dll.inv( ch, dat[:,1]))
        

    def interpch( self, datfile, x, y, ch):
        return interpdat(datfile, x, y, np.transpose(np.vstack(self.calcwfms[ch])) )

    def prereq( self, ch ):
        if ch not in self.calcwfms.keys():
            print "\tcalculating prerequisite: %s" % ch
            self.calculate(ch)
        else:
            print "\treusing prerequisite: %s" % ch

    def calculate(self, ch):
        if ch in self.calcwfms.keys():
            print"\talready in dictionary"
            return self.calcwfms[ch]

        ### Calculate trap depth and frequencies
        elif ch == 'odtfcpow':
            """The table for the conversion from voltage to cpow is calculated
            using the odt.py module, inside the seq directory.  Type python odt.py
            The table is saved in physics/odtfcpow.dat"""
            #self.calcwfms[ch] = self.basicConversion(physpath+'odtfcpow.dat', 0, 1, 'odtpow')
            self.calcwfms[ch] = self.cnvInversion( 'odtpow')
            return self.calcwfms[ch]

        elif ch == 'odtdepth(1uK)':
            self.prereq('odtfcpow')
            self.calcwfms[ch] = self.interpch(physpath+'odt.dat', 0, 1, 'odtfcpow')
            return self.calcwfms[ch]

        elif ch == 'odtdepth(Er)':
            self.prereq('odtdepth(1uK)')
            self.calcwfms[ch] = scaleFactor( self.calcwfms['odtdepth(1uK)'], 1/1.4)
            return self.calcwfms[ch]

        elif ch == 'odtdepth(100uK)':
            self.prereq('odtfcpow')
            self.calcwfms[ch] = scaleFactor(self.interpch(physpath+'odt.dat', 0, 1, 'odtfcpow'), 1/100.)
            return self.calcwfms[ch]

        elif ch == 'odtdepth(Er)':
            self.prereq('odtfcpow')
            self.calcwfms[ch] = scaleFactor(self.interpch(physpath+'odt.dat', 0, 1, 'odtfcpow'), 1/1.4)
            return self.calcwfms[ch]

        elif ch == 'odtfreqAx(100Hz)':
            self.prereq('odtfcpow')
            self.calcwfms[ch] = scaleFactor(self.interpch(physpath+'odt.dat', 0, 2, 'odtfcpow'), 1/100.)
            return self.calcwfms[ch]

        elif ch == 'odtfreqRd(100Hz)':
            self.prereq('odtfcpow')
            self.calcwfms[ch] = scaleFactor(self.interpch(physpath+'odt.dat', 0, 3, 'odtfcpow'), 1/100.)
            return self.calcwfms[ch]

        elif ch == 'odtfreqRdZ(100Hz)':
            self.prereq('odtfcpow')
            self.calcwfms[ch] = scaleFactor(self.interpch(physpath+'odt.dat', 0, 4, 'odtfcpow'), 1/100.)
            return self.calcwfms[ch]


        ### Calculate Bfield
        elif ch == 'bfield(Amp)':
            #self.calcwfms[ch] = self.basicConversion(physpath+'bfield.dat', 0, 1, 'bfield')
            self.calcwfms[ch] = self.cnvInversion('bfield')
            return self.calcwfms[ch]

        elif ch == 'bfield(G)':
            self.prereq('bfield(Amp)')
            self.calcwfms[ch] = scaleFactor( self.calcwfms['bfield(Amp)'], 6.8 )
            return self.calcwfms[ch]

        elif ch == 'bfield(100G)':
            self.prereq('bfield(G)')
            self.calcwfms[ch] = scaleFactor( self.calcwfms['bfield(G)'], 1/100.)
            return self.calcwfms[ch]

        ### Calculate imaging frequencies
        elif ch == 'hfimg0(100MHz)':
            self.prereq('bfield(G)')
            x,y = self.calcwfms['bfield(G)'] 
            self.calcwfms[ch] = (x, -1.*(100.0 + 163.7 - 1.414*y)/100. )
            return self.calcwfms[ch]

        elif ch == 'analoghfimg(100MHz)':
            x,y = self.cnvInversion('analogimg')
            self.calcwfms[ch] = (x, y/100.)
            return self.calcwfms[ch]

        ### Calculate scattering length
        elif ch == 'ainns(100a0)':
            self.prereq('bfield(G)')
            self.calcwfms[ch] = scaleFactor(self.interpch( physpath+'ainns.dat', 0, 1, 'bfield(G)' ), 1/100.)
            return self.calcwfms[ch]

        elif ch == 'arice(100a0)':
            self.prereq('bfield(G)')
            self.calcwfms[ch] = scaleFactor(self.interpch( physpath+'arice.dat', 0, 1, 'bfield(G)' ), 1/100.)
            return self.calcwfms[ch]
            
        
        ### Calculate depth of IR and green beams
        elif ch in ['ir1pow(Er)', 'ir2pow(Er)', 'ir3pow(Er)', 'greenpow1(Er)', 'greenpow1(Er)', 'greenpow3(Er)']: 
            self.calcwfms[ch] = self.cnvInversion( ch.split('(')[0] ) 
            return self.calcwfms[ch]

        elif ch in ['ir1pow(100mW)', 'ir2pow(100mW)', 'ir3pow(100mW)', 'greenpow1(100mW)', 'greenpow1(100mW)', 'greenpow3(100mW)']:
            lch  = ch.split('(')[0] 
            Erch = lch + '(Er)' 
            self.prereq( Erch )
            l = lattice_ch( lch, w0d[lch], m1d[lch], V0d[lch], ErMaxd[lch], VMaxd[lch])
            dat = self.calcwfms[Erch] 
            self.calcwfms[ch] = (dat[0], l.cnvcalib( dat[1] )/100. )
            return self.calcwfms[ch] 

        ### Calculate lattice ratio
        elif ch in ['lcr1(alpha)', 'lcr2(alpha)', 'lcr3(alpha)']:
            self.calcwfms[ch] = self.cnvInversion( ch.split('(')[0] )
            return self.calcwfms[ch] 



        ### These start getting more complicated because they have two or more prerequisites
        
        ### Calculate lattice depth, frequencies, tunneling rate, wannierFactor

        elif ch in ['lattice1V0(Er)', 'lattice2V0(Er)', 'lattice3V0(Er)', \
                    'lattice1freq(100kHz)', 'lattice2freq(100kHz)', 'lattice3freq(100kHz)', \
                    't1(Er)', 't2(Er)', 't3(Er)', \
                    't1(kHz)', 't2(kHz)', 't3(kHz)', \
                    'wannierF1(Er/a)', 'wannierF2(Er/a)', 'wannierF3(Er/a)' \
                   ]:

            n=filter( str.isdigit, ch)[0]

            v0 = self.wfms[ 'ir' + n + 'pow' ]
            alpha = self.wfms[ 'lcr' + n ]

            #Find the set of wfmouts where Er and alpha are defined
            intsct = set( [i[1] for i in v0] )  &  set( [j[1] for j in alpha] )
            
            print "\tv0 and alpha are defined for %d wfmouts" % len(intsct) 

            #Extract the waveforms and the data for the wfmouts where v0 and alpha are defined 
            v0intwfm = [ out for out in v0 if out[1] in intsct ]
            alintwfm = [ out for out in alpha if out[1] in intsct ]

            v0intdat = np.concatenate( [ out[0] for out in v0intwfm ], axis=0)
            alintdat = np.concatenate( [ out[0] for out in alintwfm ], axis=0) 

            #Check that all have the same time axis 
            if not ( v0intdat[:,0] == alintdat[:,0]).all() or v0intdat.shape != alintdat.shape or len(v0intwfm) != len(alintwfm):
                print "\tMismatching time axes after intersecting v0 and alpha"
                return None
            else:
                print "\tSuccesfully intersected v0 and alpha"
            
            #Convert the extracted data
            times = v0intdat[:,0]

            print "\tA total of %d samples will be calculated" % len(times)
             
            v0intdat  =   dll.inv( 'ir' + n + 'pow', v0intdat[:,1]  )
            alintdat = dll.inv('lcr' + n, alintdat[:,1] )
  
            #Lattice depth         
            self.calcwfms['lattice'+n+'V0(Er)'] = (times, v0intdat * np.sqrt(alintdat) )

            #Lattice frequencies \vu = (2 Er / h)*sqrt(V0) = (58.33 kHz)*sqrt(V0)
            self.calcwfms['lattice'+n+'freq(100kHz)'] = (times, (58.33/100.)*np.sqrt( v0intdat * np.sqrt(alintdat) ) )


            #Anything that uses tANDU.dat needs to discard lattice depths outside (1.0, 40.0) !!!
            #For this purpose we implement masked arrays
        
            #Calculate tunneling rate and wannierFactor,
            #save the results in self.wfms format
            t  = [] 
            wf = []
            for i in range(len(v0intwfm)):

                v0 = v0intwfm[i]
                al = alintwfm[i] 

                index = v0[1]

                if v0[1] != al[1]:  
                   print "Index error in intersected wfm of v0 and alpha"
                   return None
                
                
                #From the wfms obtain the data  
                v0dat = v0[0][:,1]
                aldat = al[0][:,1]

                #Convert this data to physical units using cnvInversion 
                v0dat =  dll.inv( 'ir'+n+'pow' , v0dat)         
                aldat =  dll.inv('lcr'+n, aldat) 
                
                latticeDepth = v0dat * np.sqrt(aldat) 

                #Valid lattice depths
                v0valid = ma.masked_array( latticeDepth, \
                                   mask = np.logical_not( np.logical_and( latticeDepth > 0., latticeDepth < 46.0 )) )

                #Fill bad lattice depths with a 1.0 
                v0valid = v0valid.filled(1.0) 

                
                latticeDepth = np.transpose( np.vstack( ( np.zeros( v0valid.shape), v0valid )) )

                tunneling = interpdat( physpath + 'tANDU.dat', 0, 1, latticeDepth )[1]
                t.append( [ np.transpose( np.vstack( (v0[0][:,0], tunneling) ) ) , index ] )

                wannierF  = interpdat( physpath + 'tANDU.dat', 0, 2, latticeDepth )[1]
                wf.append([ np.transpose( np.vstack( (v0[0][:,0], wannierF) ) ) , index ] ) 

            #Units of tunneling are Er
            self.wfms['t'+n] = t 
 
            #Units of wannier factor are   Er / ( lattice spacing )
            self.wfms['wannierF'+n] = wf

            #Wannier factor 
            wfdat = np.concatenate( [ out[0] for out in wf], axis=0)
            self.calcwfms['wannierF'+n+'(Er/a)'] = ( wfdat[:,0], wfdat[:,1] ) 
            
            #Save tunneling in various units to calcwfms
            tdat = np.concatenate( [ out[0] for out in t ], axis=0)

            #Tunneling rate in Er and in kHz ==> 1 Er = 29.2 kHz
            self.calcwfms['t'+n+'(Er)'] = ( tdat[:,0], tdat[:,1] ) 
            self.calcwfms['t'+n+'(kHz)'] =( tdat[:,0], tdat[:,1]*29.2 )  
            
            return self.calcwfms[ch] 

        ### Calculate on-site interactions
        elif ch in ['U1(Er)', 'U2(Er)', 'U3(Er)', \
                    'U1(kHz)', 'U2(kHz)', 'U3(kHz)' ]:
            
            n=filter( str.isdigit, ch)[0]

            wannierF = self.wfms[ 'wannierF' + n ]
            bfield = self.wfms[ 'bfield']

            #Find the set of wfmouts where the wannier factor and the bfield are defined
            intsct = set( [i[1] for i in wannierF] )  &  set( [j[1] for j in bfield] )
            
            print "\twannierFactor and bfield are defined for %d wfmouts" % len(intsct) 

            #Extract the waveforms and the data for the wfmouts where v0 and alpha are defined 
            wFintwfm = [ out for out in wannierF if out[1] in intsct ]
            BFintwfm = [ out for out in bfield if out[1] in intsct ]
           
            wFintdat = np.concatenate( [ out[0] for out in wFintwfm ], axis=0)
            BFintdat = np.concatenate( [ out[0] for out in BFintwfm ], axis=0)


            #Check that all have the same time axis 
            if not ( wFintdat[:,0] == BFintdat[:,0]).all() or wFintdat.shape != BFintdat.shape or len(wFintwfm) != len(BFintwfm):
                print "\tMismatching time axes after intersecting wannierFactor and bfield"
                return None
            else:
                print "\tSuccesfully intersected wannierFactor and bfield"

            times = wFintdat[:,0]
            print "\tA total of %d samples will be calculated" % len(times)

            wannierFactor = wFintdat[:,1]

            B_Amps = dll.inv('bfield', BFintdat[:,1] )
           
            B_Gauss= np.transpose( np.vstack( (np.zeros(B_Amps.shape), B_Amps*6.8))) 

            #Scattering length is calculated below using units of a0 
            a_s = interpdat( physpath+'ainns.dat', 0, 1, B_Gauss)[1]

            #Then converted into units of lattice spacing
            a0 = 5.29e-11 # meters
            a  = 1.064e-6/2. #meters
            a_s = ( a_s * a0 ) / a

            #Onsite interactions are obtained
            U = a_s * wannierFactor

            self.calcwfms['U'+n+'(Er)'] = (times, U)
            self.calcwfms['U'+n+'(kHz)'] = (times, U*29.2)
            
            return self.calcwfms[ch] 

        
        ### Calculate 'confinement' 
        


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

    bfield_Gauss = interpdat( physpath+'bfield.dat', 0, 1, bfield) * 6.8
    scatt_length = interpdat( physpath+'ainns.dat', 0, 1, bfield_Gauss ) / 100.

    onsite =  scatt_length

    return times, onsite
