###########################################
#### LATTICE ANALOG WAVEFORM ###
###########################################

import sys
#~ sys.path.append('L:/software/apparatus3/seq/seq')
#~ sys.path.append('L:/software/apparatus3/seq/utilspy')
#~ sys.path.append('L:/software/apparatus3/seq/seqspy')
#~ sys.path.append('L:/software/apparatus3/convert')
import seqconf, wfm, gen, math, cnc, time, os, numpy, hashlib, evap, physics, errormsg, odt, bfieldwfm
import shutil
import pprint
import matplotlib as mpl
mpl.use('Agg') # This is for making the pyplot not complaining when there is no x server

import copy
import re

import matplotlib.pyplot as plt
import manta
from scipy import interpolate
from bfieldwfm import gradient_wave

#GET SECTION CONTENTS
DIMPLE = gen.getsection('DIMPLE')
DL = gen.getsection('DIMPLELATTICE')
ANDOR  = gen.getsection('ANDOR')
MANTA  = gen.getsection('MANTA')




class lattice_wave(wfm.wave):
	"""The lattice_wave class helps construct the waveforms that 
		will be used to ramp the lattice.
		
		Several methods are added that allow doing special ramps
		"""

def interpolate_subramp( pts , yoffset): 
    newpts=[]
    defpts=[]
    linear = False
    for i,pt in enumerate(pts):
        ### Force zero slope at beginning
        if not isinstance( pt, str):
            defpts = defpts + [pt]
        if i==0 and pts[i+1]=='~~':
            prept = [ (pt[0]-10*j,pt[1]) for j in reversed(range(3)) ]
            newpts = prept 
            continue
        if pt == '--':
            linear = True
            continue
        if linear == True:
            n=8.  #guide points
            seg = 8. #segments
            q = newpts[-1]
            dx = pt[0]-q[0]
            dy = pt[1]-q[1]
            m = dy/dx
            linepts = [ ( q[0] + dx*j/seg, q[1] + m*dx*j/seg)  for j in range(1,int(n)) ]
            newpts = newpts + linepts + [pt]
            linear = False
        else:
            newpts = newpts + [pt]
    
    
    xy = numpy.array( [ [pt[0], pt[1] + yoffset] for pt in newpts] )
    defxy = numpy.array( [ [pt[0], pt[1] + yoffset] for pt in defpts] )

    return interpolate.InterpolatedUnivariateSpline( xy[:,0], xy[:,1],k=2), xy, defxy


def rampseg_dt(  seg , dt):
    ''' This function is used to increase the time values for a given 
        ramp segment. '''
    dt = float(dt)
    seg =  ','.join( seg )
    pattern = re.compile(r'\([0-9.]+,[0-9.]+\)')
    m = pattern.search( seg )
   
    newseg = ''
    while m is not None:
        left = seg[ : seg.find( m.group() ) ] 
        right = seg[ seg.find( m.group() ) + len(m.group()) : ] 
        newseg += left
        tup = [ float(num) for num in m.group()[1:-1].split(',') ]
        newseg += '(%.2f,%.2f)' % (tup[0] + dt, tup[1]) 
        seg = right
        m = pattern.search( seg )

    return newseg

def replace_knob(rampstr):
    for i in range(1,9):
      if 'knob'+'%1d'%i in DL.__dict__.keys():
        rampstr = rampstr.replace('?'+'%1d'%i,str(DL.__dict__['knob'+'%1d'%i]))	
    return rampstr
def parse_rampstr( rampstr ):
    rampstr = ','.join(rampstr)
  
    while '@' in rampstr:
        start = rampstr.find('@') 
        tok0  = rampstr.find('<')
        tokf  = rampstr.find('>')
        if start < tok0 and tok0 < tokf:
            pass
        else:
            print "Error parsing @ section in ramp string, token characters appear out of order."
            exit(1)
        # Obtain the specified ramp segment from the report
        try: 
            seg_t0   =  rampstr[ start+1: tok0]
            seg_key  =  rampstr[ tok0+1: tokf ]
	    #print DL.__dict__[seg_key]
            seg =  [replace_knob(key) for key in DL.__dict__[seg_key]] 
	    #seg =  DL.__dict__[seg_key] 
            newseg =  rampseg_dt( seg, seg_t0 ) 
            rampstr = rampstr[:start] + newseg + rampstr[tokf+1:] 
        except Exception,e:
            print "Error obtaining @ ramp segment."
            print e
            exit(1)
    rampstr = replace_knob(rampstr)           

    #First parse all the points and separators into a list
    ptlist = rampstr.split('xx')
    for i,elem in enumerate(ptlist):
        if elem.startswith('--') and i!=0:
          lastpt = '('+ptlist[i-1].split('(')[-1]
          #print lastpt
          ptlist[i] = lastpt + ptlist[i]
    #print ptlist

    subramps = []
    for subramp in ptlist:
        pts = [] 
        for spl in  subramp.split('--'):
            for pt in spl.split('~~'):
                pt = pt.strip('()').split(',')
                pts.append((float(pt[0]), float(pt[1])))
            pts.append('--')
        subramps.append(pts) 

    return rampstr, ptlist, subramps

def xdomain( rampstr ) :
    rampstr, ptlist, subramps = parse_rampstr(rampstr) 
    defpts=[]
    for sr in subramps:
        for pt in sr:
            if not isinstance( pt, str ):
                defpts = defpts + [pt]
    defpts =  numpy.array(defpts)
    return (numpy.amin(defpts[:,0]), numpy.amax(defpts[:,0]))


def interpolate_ramp(rampstr, yoffset=0.):
    """This function is used to create ramps by patching splines. 
       The splines are created using points defined by the user. 
       A point is specified as (xval, yval),  points can be joined
       with one of three delimiters
       
       --  A straight line will join the two points

       ~~  A spline will be used to interpolate through the points

       xx  Two splines will be used, one for xval less than this 
           point and another for xval greater than this point 
    """

    print
    print "-- MAKING POINT DEFINED RAMP:" 
    print "Raw rampstr:\n", rampstr

    rampstr, ptlist, subramps = parse_rampstr(rampstr)  
    
    print 
    print "Parsed rampstr:\n", rampstr
    print


    splinepts=None
    samplepts=None
    endpt = None
    fs = [] 
    for i, sr in enumerate(subramps):
        fun, splpts, smplpts = interpolate_subramp(sr, yoffset)
        funrange = (smplpts[0][0], smplpts[-1][0])
        if splinepts == None:
            splinepts = splpts
        else:
            splinepts = numpy.concatenate( (splinepts, splpts), axis=0)        
         
        if samplepts == None:
            samplepts = smplpts
        else:
            samplepts = numpy.concatenate( (samplepts, smplpts), axis=0)    
        
        # We adopt the convetion that a function is constant before
        # its first value, so an initial [fun, funrange] is appended here.
        if  i == 0:
            fun0 = lambda x : samplepts[0,0] 
            funrange0 = ( samplepts[0,0] - 5000. , samplepts[0,0] )  
            fs.append( [fun0, funrange0] ) 
            
        fs.append( [fun, funrange] )
        endpt = ( fun( samplepts[-1,0] ) , samplepts[-1,0] ) 

    # We adopt the convention that a function is constant after its last value
    # so a final [fun, funrange] is appended here. 
    funrange = ( endpt[1], endpt[1] + 5000. )
    fun = lambda x : endpt[0] 
    fs.append( [fun, funrange] )  
 
    return piecewisefun(fs) ,splinepts, samplepts
   
class piecewisefun:
    def __init__(self, fs):
        self.xr =[]
        self.f = []
        for e in fs:
            self.f.append( e[0] ) 
            for xpt in e[1]:
                if xpt not in self.xr:
                    self.xr.append(xpt)
        if len(self.xr) - 1 != len(fs):
            print "Error creating piecewisefun for ramp. Program will exit"
            exit(1) 

    def __call__(self, x):
        conds =[]
        for i in range(len(self.xr)-1):
            conds.append( numpy.logical_and( x > self.xr[i] , x <= self.xr[i+1] ))
        funs  = self.f
        return numpy.piecewise( x, conds, funs ) 
        



def dimple_to_lattice(s,cpowend):
    
    print "----- LATTICE LOADING RAMPS -----"

    # Find out which is the longest of the ramps we are dealing with:
    maxX =max( [xdomain(DL.latticeV0)[1] ,\
         xdomain(DL.irpow)[1],\
         xdomain(DL.grpow1)[1],\
         xdomain(DL.grpow2)[1],\
         xdomain(DL.grpow3)[1],\
         xdomain(DL.a_s)[1]] )
    print "Largest x value = %.3f ms\n" %  maxX
   
    # We define the times for which all functions will be evaluated
    # MIN TIME TO DO DIGITAL EXTENSION
    DIGEXTENSION = 2050.
    if DL.image >= DIGEXTENSION:
        Xendtime = DIGEXTENSION
    else:
        Xendtime = float( DL.image )

    Nnew = int(math.floor( Xendtime / DL.ss) ) 
    print "Nnew = ", Nnew 
    print "Xendtime = ", Xendtime 
    print "Division = ", Xendtime/Nnew
    Xnew = numpy.arange( Xendtime/Nnew, DL.image, Xendtime/Nnew ) 
    print "X array defined from dt:"
    print "DL.ss =", DL.ss
    print "x0  = ",Xnew[0]
    print "xf  = ",Xnew[-1]
    print "xdt = ",Xnew[1]-Xnew[0]
    print "%d samples" % Nnew
    print 'x shape = ', Xnew.shape
    
    # Define how we want to ramp up the lattice depth
    v0_ramp, xy_v0, v0set =  interpolate_ramp( DL.latticeV0)
    v0  = v0_ramp(Xnew)
                        
    
    
    ###########################################
    #### AXIS DEFINITIONS FOR PLOTS ###
    ###########################################    
    
    fig = plt.figure( figsize=(4.5*1.05,8.*1.1))
    ax0 = fig.add_axes( [0.18,0.76,0.76,0.20]) 
    ax2 = fig.add_axes( [0.18,0.645,0.76,0.11])
    ax3 = fig.add_axes( [0.18,0.53,0.76,0.11])
    ax1 = fig.add_axes( [0.18,0.415,0.76,0.11])
    ax5 = fig.add_axes( [0.18,0.30,0.76,0.11])
    ax4 = fig.add_axes( [0.18,0.185,0.76,0.11])
    ax6 = fig.add_axes( [0.18,0.07,0.76,0.11])

    allax = [ax0, ax1, ax2, ax3, ax4, ax5, ax6]
    for ax in allax:
        ax.axvline( DL.image, linewidth = 1., color='black', alpha=0.6)
    
    lw=1.5
    labelx=-0.12
    legsz =8.
    
    xymew=0.5
    xyms=9
    
    
    ax0.plot( Xnew, v0, 'b', lw=2.5, label='Lattice depth')
    ax0.plot(xy_v0[:,0],xy_v0[:,1], 'x', color='blue', ms=5.)
    ax0.plot(v0set[:,0],v0set[:,1], '.', mew=xymew, ms=xyms, color='blue')
    
    
    ###########################################
    #### USER DEFINED RAMPS: IR, GR, and U ###
    ###########################################      
    
    # Define how we want to ramp up the IR power
    if DIMPLE.allirpow > 0.:
      ir_offset = DIMPLE.allirpow
    else:
      ir_offset = DIMPLE.ir1pow2
    ir_ramp, xy_ir, ir =  interpolate_ramp( DL.irpow, yoffset=ir_offset)
    
    dt_ir = numpy.amax( ir[:,0]) - numpy.amin( ir[:,0])
    N_ir = int(math.floor( dt_ir / DL.ss ))
    x_ir = numpy.arange( dt_ir/N_ir, dt_ir, dt_ir/N_ir)
    
    y_ir = ir_ramp(Xnew)
    
    if v0.size > y_ir.size:
        y_ir = numpy.append(y_ir, (v0.size-y_ir.size)*[y_ir[-1]])
    elif v0.size < y_ir.size:
        y_ir = y_ir[0:v0.size]
        
    if v0.size != y_ir.size:
        msg = "IRPOW ERROR: number of samples in IR ramp and V0 ramp does not match!"
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
        
   
    alpha_clip_range = 0.1 
    if (v0 > y_ir+ alpha_clip_range).any():
        msg = "IRPOW ERROR:  not enough power to get desired lattice depth"
        print msg
        bad = numpy.where( v0 > y_ir + alpha_clip_range)
        timefail =  int(bad[0][0])*float(DL.ss)
        msg = msg + "\nFirst bad sample = %d out of %d" % (bad[0][0], v0.size)
        msg = msg + "\n  t = %f " %  timefail
        msg = msg + "\n v0 = %f " %   v0[ bad[0][0] ]
        msg = msg + "\n ir = %f " % y_ir[ bad[0][0] ]
        print v0[bad[0][0]]
        print y_ir[bad[0][0]]
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
    
    ax0.plot(xy_ir[:,0],xy_ir[:,1], 'x', color='darkorange', ms=5.)
    ax0.plot(ir[:,0],ir[:,1], '.', mew=xymew, ms=xyms, color='darkorange')
    ax0.plot(Xnew, y_ir, lw=lw, color='darkorange',label='irpow')
    
    
    # Define how we want to ramp up the GR power
    grwfms = {}
    splmrkr = ['x','+','d']
    ptsmrkr = ['^','s','p']
    for i,grramp in enumerate([(DL.grpow1,DIMPLE.gr1pow2), (DL.grpow2,DIMPLE.gr2pow2), (DL.grpow3,DIMPLE.gr3pow2)]):
      ramppts = grramp[0]
      ramp0 = grramp[1] 

      print 'gr'+'%d'%i +' offset = %f' % ramp0

      gr_ramp, xy_gr, gr =  interpolate_ramp( ramppts, yoffset=ramp0)
    
      dt_gr = numpy.amax( gr[:,0]) - numpy.amin( gr[:,0])
      N_gr = int(math.floor( dt_gr / DL.ss ))
      x_gr = numpy.arange( dt_gr/N_gr, dt_gr, dt_gr/N_gr)
    
      y_gr = gr_ramp(Xnew)
      if DL.signal == 0:
          y_gr = y_gr / 2.0
    
      if v0.size > y_gr.size:
          y_gr = numpy.append(y_gr, (v0.size-y_gr.size)*[y_gr[-1]])
      elif v0.size < y_gr.size:
          y_gr = y_gr[0:v0.size]
        
      if v0.size != y_gr.size:
          msg = "GRPOW ERROR: number of samples in GR ramp and V0 ramp does not match!"
          errormsg.box('LATTICE LOADING ERROR',msg)
          exit(1)

      grwfms[ 'greenpow' + '%1d' % (i+1) ] = y_gr 

      ax0.plot(xy_gr[:,0],xy_gr[:,1], marker= splmrkr[i] ,mec='green', mfc='None', ms=3.)
      ax0.plot(gr[:,0],gr[:,1], marker=ptsmrkr[i], mew=xymew, ms=xyms/2., mfc='None', mec='green')#, label='grpow dat')
      ax0.plot(Xnew, y_gr, lw=lw, color='green', label='grpow')

    for grch in grwfms.keys():
      print grch, " = ", grwfms[grch].shape
    
    ax0.set_xlim(left=-10., right= ax0.get_xlim()[1]*1.1)   
    plt.setp( ax0.get_xticklabels(), visible=False)
    ylim = ax0.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax0.set_ylim( ylim[0]-extra, ylim[1]+extra )
    ax0.grid(True)
    ax0.set_ylabel('$E_{r}$',size=16, labelpad=0)
    ax0.yaxis.set_label_coords(labelx, 0.5)
    ax0.set_title('Lattice Loading')
    ax0.legend(loc='best',numpoints=1,prop={'size':legsz*0.8})
    
    
    # Define how we want to ramp up the scattering length (control our losses)
    a_s_ramp, xy_a_s, a_s =  interpolate_ramp( DL.a_s)
    
    
    dt_a_s = numpy.amax( a_s[:,0]) - numpy.amin( a_s[:,0])
    N_a_s = int(math.floor( dt_a_s / DL.ss ))
    x_a_s = numpy.arange( dt_a_s/N_a_s, dt_a_s, dt_a_s/N_a_s)
    y_a_s = a_s_ramp(Xnew)

   
    
    if v0.size > y_a_s.size:
        y_a_s = numpy.append(y_a_s, (v0.size-y_a_s.size)*[y_a_s[-1]])
    elif v0.size < y_a_s.size:
        y_a_s = y_a_s[0:v0.size]
        
    if v0.size != y_a_s.size:
        msg = "a_s ERROR: number of samples in a_s ramp and V0 ramp does not match!"
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
    
    
    
    ax1.plot(xy_a_s[:,0],xy_a_s[:,1]/100., 'x', color='#C10087', ms=5.)
    ax1.plot(a_s[:,0],a_s[:,1]/100., '.', mew=xymew, ms=xyms, color='#C10087')
    ax1.plot(Xnew, y_a_s/100., lw=lw, color='#C10087', label=r'$a_s\mathrm{(100 a_{0})}$')
    ax1.set_ylabel(r'$a_s\mathrm{(100 a_{0})}$',size=16, labelpad=0)
    ax1.yaxis.set_label_coords(labelx, 0.5)

    
    ax1.set_xlim( ax0.get_xlim()) 
    ylim = ax1.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax1.set_ylim( ylim[0]-extra, ylim[1]+extra )
    plt.setp( ax1.get_xticklabels(), visible=False)
    ax1.grid(True)
    ax1.legend(loc='best',numpoints=1,prop={'size':legsz})
    

    #######################################################################
    #### CALCULATED RAMPS:  ALPHA, TUNNELING, SCATTERING LENGTH, BFIELD ###
    #######################################################################
    
    alpha = (v0/y_ir)**2.
    
    alpha_advance = 100.
    N_adv = int(math.floor( alpha_advance / DL.ss))
    
    alpha  = alpha.clip(0.,1.)
    alpha_desired = numpy.copy(alpha)
    
    if N_adv < v0.size:
        alpha = alpha[N_adv:]
        alpha = numpy.append(alpha, (v0.size-alpha.size)*[alpha[-1]])
    else:
        alpha = numpy.array( v0.size*[alpha[-1]] )
    
    #alpha = alpha.clip(0., 1.)
    
    ax2.plot( Xnew, alpha, lw=lw, color='saddlebrown', label='alpha adv')
    ax2.plot( Xnew, alpha_desired,':', lw=lw, color='saddlebrown', label='alpha')
    
    ax2.set_xlim( ax0.get_xlim()) 
    ax2.set_ylim(-0.05,1.05)
    plt.setp( ax2.get_xticklabels(), visible=False)
    ax2.grid()
    ax2.set_ylabel('$\\alpha$',size=16, labelpad=0)
    ax2.yaxis.set_label_coords(labelx, 0.5)
    
    ax2.legend(loc='best',numpoints=1,prop={'size':legsz})
    
    
    tunneling_Er  = physics.inv('t_to_V0', v0)
    tunneling_kHz = tunneling_Er * 29.2
    
    ax3.plot( Xnew, tunneling_kHz, lw=lw, color='red', label='$t$ (kHz)')

    
    ax3.set_xlim( ax0.get_xlim()) 
    ylim = ax3.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax3.set_ylim( ylim[0]-extra, ylim[1]+extra )
    plt.setp( ax3.get_xticklabels(), visible=False)
    ax3.grid(True)
    ax3.set_ylabel(r'$t\,\mathrm{(kHz)}$',size=16, labelpad=0)
    ax3.yaxis.set_label_coords(labelx, 0.5)
    ax3.legend(loc='best',numpoints=1,prop={'size':legsz})

    
    wannierF = physics.inv('wF_to_V0', v0)
     
    bohrRadius = 5.29e-11 #meters
    lattice_spacing = 1.064e-6 / 2. #meters
    
    bfieldG = physics.cnv('as_to_B', y_a_s)
    print 
    print "The last value of the scattering length ramp is:"
    print 'a_s =', y_a_s[-1]
    print 'B   =', bfieldG[-1]
    print 
    
    U_over_t = y_a_s * bohrRadius / lattice_spacing * wannierF / tunneling_Er
    
    
    
    
    ax4.plot( Xnew, U_over_t, lw=lw, color='k', label=r'$U/t$')
    
    ax4.set_xlim( ax0.get_xlim()) 
    ylim = ax4.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax4.set_ylim( ylim[0]-extra, ylim[1]+extra )
    plt.setp( ax4.get_xticklabels(), visible=False)
    ax4.grid(True)
    ax4.set_ylabel(r'$U/t$',size=16, labelpad=0)
    ax4.yaxis.set_label_coords(labelx, 0.5)
    
    ax4.legend(loc='best',numpoints=1,prop={'size':legsz})
    
    
    ax5.plot( Xnew, bfieldG, lw=lw, color='purple', label='$B$ (G)')
    
    ax5.set_xlim( ax0.get_xlim()) 
    ylim = ax5.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax5.set_ylim( ylim[0]-extra, ylim[1]+extra )
    ax5.grid(True)
    plt.setp( ax5.get_xticklabels(), visible=False)
    ax5.set_ylabel(r'$B\,\mathrm{(G)}$',size=16, labelpad=0)
    ax5.yaxis.set_label_coords(labelx, 0.5)
    
    
    ax5.legend(loc='best',numpoints=1,prop={'size':legsz})
    
    
    ax6.plot( Xnew, (tunneling_Er / U_over_t), lw=lw, color='#25D500', label=r'$t^{2}/U\,(E_{r)}$')
    #ax6.set_yscale('log')
    
    ax6.set_xlim( ax0.get_xlim()) 
    ylim = ax6.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax6.set_ylim( ylim[0]*0.5, ylim[1] )
    ax6.grid(True)
    ax6.set_ylabel(r'$t^{2}/U\,(E_{r)}$',size=16, labelpad=0)
    ax6.yaxis.set_label_coords(labelx, 0.5)
    
    
    ax6.legend(loc='best',numpoints=1,prop={'size':legsz})
    
    ax6.set_xlabel('time (ms)')

    figfile = seqconf.seqtxtout().split('.')[0]+'_latticeRamp.png'    
    plt.savefig(figfile , dpi=120 )
    
    #Save all ramps to a txt file for later plotting. 
    datfile = seqconf.seqtxtout().split('.')[0]+'_latticeRamp.dat'
    allRamps = numpy.transpose(numpy.vstack((Xnew, v0, y_ir, grwfms['greenpow1'], y_a_s, alpha, alpha_desired, \
                                    tunneling_kHz, U_over_t, bfieldG)))
    header = '# Column index'
    header = header + '\n#\t0\t' + 'time(ms)'
    header = header + '\n#\t1\t' + 'Lattice Depth (Er)'
    header = header + '\n#\t2\t' + 'Ir power (Er)'
    header = header + '\n#\t3\t' + 'GR power (Er)'
    header = header + '\n#\t4\t' + 'a_s (a0)'
    header = header + '\n#\t5\t' + 'alpha - advance'
    header = header + '\n#\t6\t' + 'alpha - desired'
    header = header + '\n#\t7\t' + 'tunneling (kHz)'
    header = header + '\n#\t8\t' + 'U/t'
    header = header + '\n#\t9\t' + 'bfield (Gauss)'
    header = header + '\n'
    
    numpy.savetxt( datfile, allRamps)
    
    with open(datfile, 'w') as f:
        X = numpy.asarray( allRamps )
        f.write(bytes(header))
        
        format = '%.6e'
        ncol = X.shape[1]
        format = [format ,] *ncol
        format = ' '.join(format)
        
        newline = '\n'
        for row in X:
            f.write(numpy.compat.asbytes(format % tuple(row) + newline))

    
    shutil.copyfile( figfile,  seqconf.savedir() + 'expseq' + seqconf.runnumber() + '_latticeRamp.png')
    shutil.copyfile( datfile,  seqconf.savedir() + 'expseq' + seqconf.runnumber() + '_latticeRamp.dat')
    #plt.savefig( seqconf.savedir() + 'expseq' + seqconf.runnumber() + '_latticeRamp.png', dpi=120)
    
    
    #################################
    #### APPEND RAMPS TO SEQUENCE ###
    #################################
    
    wfms=[]

    if DL.signal == 0:
          print " LOCK VALUE FOR SIGNAL / NOSIGNAL "
          print " before = ", DL.lock_Er
          DL.lock_Er = DL.lock_Er / 1.8
          print " after  = \n", DL.lock_Er
    
    for ch in ['ir1pow','ir2pow','ir3pow']:
        n = filter( str.isdigit, ch)[0] 
        w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
        w.y = physics.cnv( ch, y_ir )
        if DL.lock:
            endval = w.y[-1]
            w.insertlin_cnv(DL.lock_Er, DL.lock_dtUP, DL.lock_t0 )
        elif DL.lightassist_lock:
            endval = w.y[-1]
            w.linear(DL.lightassist_lockpowIR, DL.lightassist_lockdtUP)
            w.appendhold( DL.lightassist_t0 + DL.lightassistdt )
            if DL.endvalIR >= 0.:
                w.linear(  DL.endvalIR, DL.lightassist_lockdtDOWN)
            else:
                w.linear(  None, DL.lightassist_lockdtDOWN, volt=endval)
        wfms.append(w)
        
    for ch in ['greenpow1','greenpow2','greenpow3']:
        n = filter( str.isdigit, ch)[0] 
        w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
        
        correction = DIMPLE.__dict__['gr'+n+'correct']
        
        w.y = physics.cnv( ch, correction * grwfms[ch] )
        if DL.lightassist_lock:
            endval = w.y[-1]
            w.linear(DL.lightassist_lockpowGR, DL.lightassist_lockdtUP)
            w.appendhold( DL.lightassist_t0 + DL.lightassistdt )
            if DL.endvalGR >= 0.:
                w.linear(  DL.endvalGR, DL.lightassist_lockdtDOWN)
            else:
                w.linear(  None, DL.lightassist_lockdtDOWN, volt=endval)
        wfms.append(w)
     

    for ch in ['lcr1','lcr2','lcr3']:
        n = filter( str.isdigit, ch)[0] 
        w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
        force = DL.__dict__['force_'+ch]
        if force >= 0 and force <=1:
            print "...Forcing LCR%s = %f during lattice ramp" % (n,force)
            w.y = physics.cnv( ch, numpy.array( alpha.size*[force] )  )
        elif DL.signal == 0:
            print "...Forcing LCR%s = 0. so that it does NOT rotate to LATTICE" % n 
            w.y = physics.cnv( ch, numpy.array( alpha.size*[0.0] )  )
        else:
            w.y = physics.cnv( ch, alpha )
        wfms.append(w)
    

    
    bfieldA = bfieldG/6.8
    
    ##ADD field
    bfield = wfm.wave('bfield', 0.0, DL.ss)
    bfield.y = physics.cnv( 'bfield', bfieldA)
    print "The last value of the bfield voltage is =", bfield.y[-1]
    print 
    wfms.append(bfield)
    
    
    ##ADD gradient field
    gradient = gradient_wave('gradientfield', 0.0, DL.ss,volt = 0.0)
    gradient.follow(bfield)
    wfms.append(gradient)
   
    
    buffer = 40.
    s.wait(buffer)
    
    
    #~ odtpow = odt.odt_wave('odtpow', cpowend, DL.ss)
    #~ if DIMPLE.odt_t0 > buffer :
        #~ odtpow.appendhold( DIMPLE.odt_t0 - buffer)
    #~ if DIMPLE.odt_pow < 0.:
        #~ odtpow.appendhold( DIMPLE.odt_dt)
    #~ else:
        #~ odtpow.tanhRise( DIMPLE.odt_pow, DIMPLE.odt_dt, DIMPLE.odt_tau, DIMPLE.odt_shift)    
        
    #~ if numpy.absolute(DIMPLE.odt_pow) < 0.0001:
        #~ s.wait( odtpow.dt() )
        #~ s.digichg('odtttl',0)
        #~ s.wait(-odtpow.dt() )
    
    #~ wfms.append(odtpow)
        
    
    # RF sweep
    if DL.rf == 1:   
        rfmod  = wfm.wave('rfmod', 0., DL.ss)
        rfmod.appendhold( bfield.dt() + DL.rftime )
        rfmod.linear( DL.rfvoltf, DL.rfpulsedt)
        wfms.append(rfmod)


    if DL.round_trip == 1:
        bindex = 0  # Calculate detunings using starting field
    else: 
        bindex = -1 # Calculate detunings using field at the end of ramps

    bfieldG = physics.inv( 'bfield', bfield.y[bindex]) * 6.8
    hfimg0 = -1.*(100.0 + 163.7 - 1.414*bfieldG)
   
    # Find bindex for braggkill time 
    bindex_BK =  math.floor(-DL.braggkilltime / bfield.ss)
    bfieldG_BK = physics.inv( 'bfield', bfield.y[-1-bindex_BK]) * 6.8
    hfimg0_BK =  -1.*(100.0 + 163.7 - 1.414*bfieldG_BK) 
    DL.braggkill_hfimg = hfimg0_BK - DL.braggkill_hfimg
    print "\n...Braggkill hfimg modification:\n"
    print "\tNEW braggkill_hfimg = %.2f MHz" % DL.braggkill_hfimg

    # Find bindex for bragg2kill time 
    bindex_B2K =  math.floor(-DL.bragg2killtime / bfield.ss)
    bfieldG_B2K = physics.inv( 'bfield', bfield.y[-1-bindex_B2K]) * 6.8
    hfimg0_B2K =  -1.*(100.0 + 163.7 - 1.414*bfieldG_B2K) 
    DL.bragg2kill_hfimg1 = hfimg0_B2K - DL.bragg2kill_hfimg1
    DL.bragg2kill_hfimg2 = hfimg0_B2K - DL.bragg2kill_hfimg2
    print "\n...Bragg2kill hfimg modification:\n"
    print "\tNEW brag2gkill_hfimg1 = %.2f MHz" % DL.bragg2kill_hfimg1
    print "\tNEW brag2gkill_hfimg2 = %.2f MHz" % DL.bragg2kill_hfimg2
    
    
    print "\n...ANDOR:hfimg and hfimg0 will be modified  in report\n"
    print "\tNEW  ANDOR:hfimg  = %.2f MHz" % ( hfimg0 - DL.imgdet)
    print "\tNEW  ANDOR:hfimg0 = %.2f MHz\n" %  hfimg0
    gen.save_to_report('ANDOR','hfimg', hfimg0 - DL.imgdet)
    gen.save_to_report('ANDOR','hfimg0', hfimg0)
    
    newANDORhfimg = hfimg0 - DL.imgdet

    # THIS DEFINES THE TIME IT TAKES THE OFFSET LOCK TO SWITCH TO
    # A NEW SETPOINT
    hfimgdelay = 50. #ms
        
    # Kill hfimg
    if DL.probekill ==1 or DL.braggkill ==1 or  DL.bragg2kill==1 or DL.lightassist or DL.lightassist_lock:
        analogimg = wfm.wave('analogimg', newANDORhfimg, DL.ss)
        
        if DL.probekill == 1:
            if (-DL.probekilltime+hfimgdelay) < DL.image:
                analogimg.appendhold( bfield.dt() + DL.probekilltime - hfimgdelay)
                analogimg.linear( DL.probekill_hfimg , 0.0)
                analogimg.appendhold( hfimgdelay + DL.probekilldt + 3*DL.ss)
        
        elif DL.braggkill == 1:
            print "Setting up analogimg for braggkill"
            if (-DL.braggkilltime+hfimgdelay) < DL.image:
                analogimg.appendhold( bfield.dt() + DL.braggkilltime - hfimgdelay)
                analogimg.linear( DL.braggkill_hfimg , 0.0)
                analogimg.appendhold( hfimgdelay + DL.braggkilldt + 3*DL.ss)
 
        elif DL.bragg2kill == 1:
            print "Setting up analogimg for bragg2kill"
            if (-DL.bragg2killtime+hfimgdelay) < DL.image:
                # This sets up the detuning for the first pulse
                analogimg.appendhold( bfield.dt() + DL.bragg2killtime - hfimgdelay)
                analogimg.linear( DL.bragg2kill_hfimg1 , 0.0)
                analogimg.appendhold( hfimgdelay + DL.bragg2killdt + 3*DL.ss)
 
                # Then set up the detuning for the second pulse
                analogimg.linear( DL.bragg2kill_hfimg2 , 0.0)
                analogimg.appendhold( hfimgdelay + DL.bragg2killdt + 3*DL.ss)
                
            
        
        elif DL.lightassist == 1 or DL.lightassist_lock:
            analogimg.appendhold( bfield.dt()  - hfimgdelay)
            analogimg.linear( DL.lightassist_hfimg , 0.0)
            duration = DL.lightassist_lockdtUP + DL.lightassist_t0 + DL.lightassistdt + DL.lightassist_lockdtDOWN
            analogimg.appendhold( hfimgdelay + duration + 3*DL.ss)
            
        analogimg.linear( newANDORhfimg, 0.)
        analogimg.extend(10)
        wfms.append(analogimg)
    
        

    
    #analogimg = bfieldwfm.hfimg_wave('analogimg', ANDOR.hfimg, DL.ss)
    #andorhfimg0 = analogimg.follow(bfield, DL.imgdet)
    #wfms.append(analogimg)
    

    # If we are doing round trip END, then mirror all the ramps 
    # before adding them to the sequence
    if DL.round_trip == 1:
        if DL.round_trip_type == 1:
            maxdt = 0.
            maxi = -1
            for i,w in enumerate(wfms):
                if w.dt() > maxdt:
                    maxdt = w.dt()
                    maxi = i
    
            maxdt = maxdt + DL.wait_at_top / 2. 
    
            for w in wfms:
                w.extend(maxdt)
                if 'lcr' in w.name:
                    yvals = w.y
                    
                    #Get the reverse of the alpha desired array
                    alpha_mirror = numpy.copy(alpha_desired[::-1])
                    
                    #Add the wait at top part so that it has same length as yvals
                    if alpha_mirror.size > yvals.size:
                        print "Error making mirror ramp for LCR."
                        print "Program will exit."
                        exit(1)
                    alpha_mirror = numpy.append( (yvals.size - alpha_mirror.size)*[ alpha_mirror[0] ], alpha_mirror )
                    
                                   
                    #This is how much the mirror ramp will be advanced
                    N_adv = int(math.floor( DL.lcr_mirror_advance / DL.ss))
                    
                    if N_adv < alpha_mirror.size:
                        alpha_mirror = alpha_mirror[N_adv:]
                        alpha_mirror = numpy.append(alpha_mirror, (yvals.size-alpha_mirror.size)*[alpha_mirror[-1]])
                    else:
                        alpha_mirror = numpy.array( yvals.size*[alpha_mirror[-1]] )
                    
                    
                    
                    w.y = numpy.concatenate((yvals,physics.cnv( w.name, alpha_mirror )))
                else:
                    w.mirror()
                w.appendhold( DL.wait_at_end)
            
        
    
    N_adv = int(math.floor( alpha_advance / DL.ss))
    
    alpha_desired = numpy.copy(alpha)
    
    
    for wavefm in wfms:
        print "%s dt = %f" % (wavefm.name, wavefm.dt())
   
     
    
    duration = s.analogwfm_add(DL.ss,wfms)
    
    if DL.image < DIGEXTENSION:
        s.wait(duration)
    else:
        print "...DL.image = %f  >= %.2f  Digital seq extension will be used." % (DL.image, DIGEXTENSION)
        s.wait( DL.image )
        
    
    ### Prepare the parts of the ramps that are going to be used to mock
    ### the conditions for the noatoms shot
    ### 1. get dt = [noatoms] ms from the end of the lattice ramps.
    if 'manta' in DL.camera:
        noatomsdt = MANTA.noatoms
    else:
        noatomsdt = ANDOR.noatoms
    noatomswfms = []
    for wavefm in wfms:
        cp = copy.deepcopy( wavefm ) 
        cp.idnum = time.time()*100
        cp.retain_last( DL.bgRetainDT )
        noatomswfms.append( cp ) 
    
        
        
    
    
    
    ### Figure out when to turn interlock back on, using alpha information
    #~ if duration > DL.t0 + DL.dt:
        #~ s.wait(-DL.lattice_interlock_time)
        #~ if DL.use_lattice_interlock == 1:
            #~ s.digichg('latticeinterlockbypass',0)
        #~ else:
            #~ s.digichg('latticeinterlockbypass',1)
        #~ s.wait( DL.lattice_interlock_time)
        
        
    #########################################
    ## OTHER TTL EVENTS: probekill, braggkill, rf, quick2
    #########################################
    # Braggkill
    if DL.braggkill == 1:
        print "Using Bragg Kill"
        s.wait( DL.braggkilltime)
        s = manta.OpenShutterBragg(s,DL.shutterdelay)
        s.digichg('bragg',1)
        s.wait( DL.braggkilldt)
        s.digichg('brshutter',1) # to close shutter
        s.digichg('bragg',0)
        
        s.wait( -DL.braggkilldt)
        s.wait( -DL.braggkilltime )

    if DL.bragg2kill == 1:
        print "Using Bragg 2 Kill"
        tcur = s.tcur 
        s.wait( DL.bragg2killtime )
        s = manta.OpenShutterBragg(s,DL.shutterdelay)
        s.digichg('bragg',1)
        s.wait( DL.bragg2killdt)
        s.digichg('brshutter',1) # to close shutter
        s.digichg('bragg',0)
  
        s.wait( hfimgdelay + 3*DL.ss )
        s = manta.OpenShutterBragg(s,DL.shutterdelay)
        s.digichg('bragg',1)
        s.wait( DL.bragg2killdt)
        s.digichg('brshutter',1) # to close shutter
        s.digichg('bragg',0)

        # Revert to current time after pulses have been added in the past
        s.tcur = tcur

        
       
        
         

    # Probe Kill
    if DL.probekill == 1:
        s.wait(DL.probekilltime)
        
        s.wait(-10)
        s.digichg('prshutter',0)
        s.wait(10)
        s.digichg('probe',1)
        s.wait(DL.probekilldt)
        s.digichg('probe',0)

        s.digichg('prshutter',1)
        s.wait(-DL.probekilltime)


    # Pulse RF
    if DL.rf == 1:
        s.wait(DL.rftime)
        s.digichg('rfttl',1)
        s.wait(DL.rfpulsedt)
        s.digichg('rfttl',0)
        s.wait(-DL.rfpulsedt)
        s.wait(-DL.rftime)
        



    # QUICK2
    if DL.quick2 == 1:
        s.wait( DL.quick2time)
        s.digichg('quick2',1)
        s.wait(-DL.quick2time)
        

    # Light-assisted collisions
    if DL.lightassist == 1 or DL.lightassist_lock:
        s.wait( -DL.lightassist_lockdtUP -DL.lightassist_t0 -DL.lightassistdt -DL.lightassist_lockdtDOWN - 3*DL.ss)
        
        s.wait(DL.lightassist_lockdtUP + DL.lightassist_t0)
        s.wait(-10)
        s.digichg('prshutter',0)
        s.wait(10)
        s.digichg('probe', DL.lightassist)
        s.wait(DL.lightassistdt)
        s.digichg('probe',0)

        s.digichg('prshutter',1)
        s.wait(DL.lightassist_lockdtDOWN)
        s.wait(3*DL.ss)
        # After the collisions happen we still need to wait some time 
        # for the probe frequency to come back to the desired value
        s.wait(hfimgdelay)


    #########################################
    ## GO BACK IN TIME IF DOING ROUND-TRIP START
    #########################################
    if DL.round_trip == 1:
        if DL.round_trip_type == 0:
            s.wait( -DL.image )
            s.stop_analog()


    #########################################
    ## TURN GREEN OFF BEFORE PICTURES
    #########################################
    if DL.greenoff == 1:
      s.wait( DL.greenoff_t0 ) 
      s.digichg('greenttl1', 0)
      s.digichg('greenttl2', 0)
      s.digichg('greenttl3', 0)
      s.wait(-DL.greenoff_t0 ) 


    
    #########################################
    ## LATTICE LOCK WITH POSSIBILITY OF RF
    #########################################
    bufferdt = 5.0
    lastIR = y_ir[-1]
   
    lockwfms=[]
    if DL.locksmooth == 1 and DL.lock == 0:
        s.wait(bufferdt)
        for ch in ['ir1pow','ir2pow','ir3pow']:
            n = filter( str.isdigit, ch)[0]
            w = wfm.wave(ch, lastIR, DL.lockss)  #Start value will be overrriden
            w.tanhRise( DL.lock_Er, DL.lock_dtUP, 0.4,0.2)
            lockwfms.append(w)
        print "...LOCKING LATTICE TO %f Er" % DL.lock_Er
        print "...lastIR = %.4f" % lastIR
        duration = s.analogwfm_add(DL.lockss,lockwfms)
        print "...duration = %.2f" % duration
        s.wait(duration)
        #~ if DL.lockrf:
            #~ s.digichg('rfttl',1)
            #~ s.wait(DL.rfpulsedt)
            #~ s.digichg('rfttl',0)
        #~ s.wait(0.036)
    #else:
    #    s.wait(bufferdt)
  
    lockwfmscopy = []
    for wavefm in lockwfms:
        cp = copy.deepcopy( wavefm ) 
        cp.idnum = time.time()*100 + 1e3*numpy.random.randint(0,1e8)
        lockwfmscopy.append( cp ) 
        
    
    #########################################
    ## IMAGING AT LOW FIELD
    #########################################
    if DL.lowfieldimg == 1:
        s.wait(DL.lowfieldimg_t0)
        s.digichg('field',0)
        s.wait(-DL.lowfieldimg_t0)
    
    
    #########################################
    ## TTL RELEASE FROM ODT and LATTICE
    #########################################
    #INDICATE WHICH CHANNELS ARE TO BE CONSIDERED FOR THE BACKGROUND
    bg = ['odtttl','irttl1','irttl2','irttl3','greenttl1','greenttl2','greenttl3']
    bgdictPRETOF={}
    for ch in bg:
        bgdictPRETOF[ch] = s.digistatus(ch)
    bgdictPRETOF['tof'] = DL.tof
    print "\nChannel status for pictures: PRE-TOF"
    print bgdictPRETOF
    print
        
    #RELEASE FROM LATTICE
    if DL.tof <= 0.:
        s.wait(1.0+ANDOR.exp)
    s.digichg('greenttl1',0)
    s.digichg('greenttl2',0)
    s.digichg('greenttl3',0)
    s.digichg('irttl1',0)
    s.digichg('irttl2',0)
    s.digichg('irttl3',0)
    #RELEASE FROM IR TRAP
    s.digichg('odtttl',0)
    if DL.tof <= 0.:
        s.wait(-1.0+ANDOR.exp)

    print "TIME WHEN RELEASED FROM LATTICE = ",s.tcur
    s.wait(DL.tof)
    
    return s, noatomswfms, lockwfmscopy, bgdictPRETOF

    
    
