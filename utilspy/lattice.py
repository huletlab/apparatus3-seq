###########################################
#### LATTICE ANALOG WAVEFORM ###
###########################################

import sys
sys.path.append('L:/software/apparatus3/seq/seq')
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seqconf, wfm, gen, math, cnc, time, os, numpy, hashlib, evap, physics, errormsg, odt

import shutil
import matplotlib as mpl
mpl.use('Agg') # This is for making the pyplot not complaining when there is no x server

import matplotlib.pyplot as plt

from scipy import interpolate

#GET SECTION CONTENTS
DIMPLE = gen.getsection('DIMPLE')
DL = gen.getsection('DIMPLELATTICE')
ANDOR  = gen.getsection('ANDOR')


class lattice_wave(wfm.wave):
	"""The lattice_wave class helps construct the waveforms that 
		will be used to ramp the lattice.
		
		Several methods are added that allow doing special ramps
		"""

def interpolate_ramp(rampstr, yoffset=0.):
    pts=[]
       
    for spl in  ','.join(rampstr).split('--'):
        for pt in spl.split('~~'):
            pt = pt.strip('()').split(',')
            pts.append((float(pt[0]), float(pt[1])))
        pts.append('--')

    
    newpts=[]
    defpts=[]
    linear = False
    for i,pt in enumerate(pts):
        ### Force zero slope at beginning
        if not isinstance( pt, str):
            defpts = defpts + [pt]
        if i==0:
            prept = [ (pt[0]-10*j,pt[1]) for j in reversed(range(3)) ]
            newpts = prept 
            continue
        if pt == '--':
            linear = True
            continue
        if linear == True:
            n=5.
            q = newpts[-1]
            dx = pt[0]-q[0]
            dy = pt[1]-q[1]
            m = dy/dx
            linepts = [ ( q[0] + dx*j/5., q[1] + m*dx*j/5.)  for j in range(1,int(n)) ]
            newpts = newpts + linepts + [pt]
            linear = False
        else:
            newpts = newpts + [pt]
    
    
    xy = numpy.array( [ [pt[0], pt[1] + yoffset] for pt in newpts] )
    defxy = numpy.array( [ [pt[0], pt[1] + yoffset] for pt in defpts] )
        
    
    
    return interpolate.InterpolatedUnivariateSpline( xy[:,0], xy[:,1],k=2), xy, defxy
        



def dimple_to_lattice(s,cpowend):
    
    print "----- LATTICE LOADING RAMPS -----"
    
    dt = DL.dt
    tau = DL.tau
    shift = DL.shift
    
    N0 = int(math.floor( DL.t0/ DL.ss))
    
    N = int(math.floor( dt/ DL.ss))
    x = numpy.arange(dt/N, dt, dt/N)
    tau = tau*dt
    shift = dt/2. + shift*dt/2.
    
    # Define how we want to ramp up the lattice depth
    v0 = 0. + DL.latticeV0 * ( (1+numpy.tanh((x-shift)/tau)) - (1+numpy.tanh((-shift)/tau)) )\
                        / ( (1+numpy.tanh((dt-shift)/tau)) - (1+numpy.tanh((-shift)/tau)) )
                        
    NH = int(math.floor( DL.dthold/ DL.ss))
    
    v0 = numpy.concatenate(( numpy.zeros(N0), v0, numpy.array(NH*[v0[-1]])  ))
    
    x_v0 = numpy.arange( v0.size )
    x_v0 = x_v0*DL.ss
    
    # Number of samples to keep
    NS = int(math.floor( DL.image / DL.ss))
    if NS > v0.size:
        x_v0 = numpy.append(x_v0, (NS-v0.size)*[x_v0[-1]])
        v0 = numpy.append(v0, (NS-v0.size)*[v0[-1]])
        
    else:
        x_v0 = x_v0[:NS]
        v0 = v0[:NS]
    
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
    
    lw=1.5
    labelx=-0.12
    legsz =10.
    
    xymew=0.5
    xyms=9

    ax0.plot( x_v0, v0, 'b', lw=2.5, label='Lattice depth')
    
    ###########################################
    #### USER DEFINED RAMPS: IR, GR, and U ###
    ###########################################      
    
    # Define how we want to ramp up the IR power
    ir_ramp, xy_ir, ir =  interpolate_ramp( DL.irpow, yoffset=DIMPLE.ir1pow)
    
    dt_ir = numpy.amax( ir[:,0]) - numpy.amin( ir[:,0])
    N_ir = int(math.floor( dt_ir / DL.ss ))
    x_ir = numpy.arange( dt_ir/N_ir, dt_ir, dt_ir/N_ir)
    
    #y_ir = ir_spline(x_ir) 
    y_ir = ir_ramp(x_ir)
    
    if v0.size > y_ir.size:
        y_ir = numpy.append(y_ir, (v0.size-y_ir.size)*[y_ir[-1]])
    elif v0.size < y_ir.size:
        y_ir = y_ir[0:v0.size]
        
    if v0.size != y_ir.size:
        msg = "IRPOW ERROR: number of samples in IR ramp and V0 ramp does not match!"
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
        
    
    if (v0 > y_ir).any():
        msg = "IRPOW ERROR:  not enough power to get desired lattice depth"
        print msg
        bad = numpy.where( v0 > y_ir)
        msg = msg + "\nFirst bad sample = %d out of %d" % (bad[0][0], v0.size)
        msg = msg + "\n v0 = %f " %   v0[ bad[0][0] ]
        msg = msg + "\n ir = %f " % y_ir[ bad[0][0] ]
        print v0[bad[0][0]]
        print y_ir[bad[0][0]]
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
    
    ax0.plot(xy_ir[:,0],xy_ir[:,1], 'x', color='darkorange', ms=5.)
    ax0.plot(ir[:,0],ir[:,1], '.', mew=xymew, ms=xyms, color='darkorange')
    ax0.plot(x_v0, y_ir, lw=lw, color='darkorange',label='irpow')
    
    
    # Define how we want to ramp up the GR power
    gr_ramp, xy_gr, gr =  interpolate_ramp( DL.grpow, yoffset=DIMPLE.gr1pow)
    
    dt_gr = numpy.amax( gr[:,0]) - numpy.amin( gr[:,0])
    N_gr = int(math.floor( dt_gr / DL.ss ))
    x_gr = numpy.arange( dt_gr/N_gr, dt_gr, dt_gr/N_gr)
    
    y_gr = gr_ramp(x_gr) 
    
    if v0.size > y_gr.size:
        y_gr = numpy.append(y_gr, (v0.size-y_gr.size)*[y_gr[-1]])
    elif v0.size < y_gr.size:
        y_gr = y_gr[0:v0.size]
        
    if v0.size != y_gr.size:
        msg = "GRPOW ERROR: number of samples in GR ramp and V0 ramp does not match!"
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)


    ax0.plot(xy_gr[:,0],xy_gr[:,1], 'x', color='green', ms=5.)
    ax0.plot(gr[:,0],gr[:,1],'.', mew=xymew, ms=xyms, color='green')#, label='grpow dat')
    ax0.plot(x_v0, y_gr, lw=lw, color='green', label='grpow')
    
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
    y_a_s = a_s_ramp(x_a_s)
    
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
    ax1.plot(x_v0, y_a_s/100., lw=lw, color='#C10087', label=r'$a_s\mathrm{(100 a_{0})}$')
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
    
    alpha_desired = numpy.copy(alpha)
    
    if N_adv < v0.size:
        alpha = alpha[N_adv:]
        alpha = numpy.append(alpha, (v0.size-alpha.size)*[alpha[-1]])
    else:
        alpha = numpy.array( v0.size*[alpha[-1]] )
    
    
    
    ax2.plot( x_v0, alpha, lw=lw, color='saddlebrown', label='alpha adv')
    ax2.plot( x_v0, alpha_desired,':', lw=lw, color='saddlebrown', label='alpha')
    
    ax2.set_xlim( ax0.get_xlim()) 
    ax2.set_ylim(-0.05,1.05)
    plt.setp( ax2.get_xticklabels(), visible=False)
    ax2.grid()
    ax2.set_ylabel('$\\alpha$',size=16, labelpad=0)
    ax2.yaxis.set_label_coords(labelx, 0.5)
    
    ax2.legend(loc='best',numpoints=1,prop={'size':legsz})
    
    
    tunneling_Er  = physics.inv('t_to_V0', v0)
    tunneling_kHz = tunneling_Er * 29.2
    
    ax3.plot( x_v0, tunneling_kHz, lw=lw, color='red', label='$t$ (kHz)')
    
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
    
    U_over_t = y_a_s * bohrRadius / lattice_spacing * wannierF / tunneling_Er
    
    
    
    
    ax4.plot( x_v0, U_over_t, lw=lw, color='k', label=r'$U/t$')
    
    ax4.set_xlim( ax0.get_xlim()) 
    ylim = ax4.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax4.set_ylim( ylim[0]-extra, ylim[1]+extra )
    plt.setp( ax4.get_xticklabels(), visible=False)
    ax4.grid(True)
    ax4.set_ylabel(r'$U/t$',size=16, labelpad=0)
    ax4.yaxis.set_label_coords(labelx, 0.5)
    
    ax4.legend(loc='best',numpoints=1,prop={'size':legsz})
    
    
    ax5.plot( x_v0, bfieldG, lw=lw, color='purple', label='$B$ (G)')
    
    ax5.set_xlim( ax0.get_xlim()) 
    ylim = ax5.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax5.set_ylim( ylim[0]-extra, ylim[1]+extra )
    ax5.grid(True)
    plt.setp( ax5.get_xticklabels(), visible=False)
    ax5.set_ylabel(r'$B\,\mathrm{(G)}$',size=16, labelpad=0)
    ax5.yaxis.set_label_coords(labelx, 0.5)
    
    
    ax5.legend(loc='best',numpoints=1,prop={'size':legsz})
    
    
    ax6.plot( x_v0, (tunneling_Er / U_over_t), lw=lw, color='#25D500', label=r'$t^{2}/U\,(E_{r)}$')
    ax6.set_yscale('log')
    
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
    
    shutil.copyfile( figfile,  seqconf.savedir() + 'expseq' + seqconf.runnumber() + '_latticeRamp.png')
    #plt.savefig( seqconf.savedir() + 'expseq' + seqconf.runnumber() + '_latticeRamp.png', dpi=120)
    
    
    #################################
    #### APPEND RAMPS TO SEQUENCE ###
    #################################
    
    wfms=[]
    
    for ch in ['ir1pow','ir2pow','ir3pow']:
        n = filter( str.isdigit, ch)[0] 
        w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
        w.y = physics.cnv( ch, y_ir )
        wfms.append(w)
        
    for ch in ['greenpow1','greenpow2','greenpow3']:
        n = filter( str.isdigit, ch)[0] 
        w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
        w.y = physics.cnv( ch, y_gr )
        wfms.append(w)
        
    for ch in ['lcr1','lcr2','lcr3']:
        n = filter( str.isdigit, ch)[0] 
        w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
        w.y = physics.cnv( ch, alpha )
        wfms.append(w)
    

    
    bfieldA = bfieldG/6.8
    

    bfield = wfm.wave('bfield', 0.0, DL.ss)
    bfield.y = physics.cnv( 'bfield', bfieldA)
    wfms.append(bfield)
    
    buffer = 20.
    s.wait(buffer)

    
    odtpow = odt.odt_wave('odtpow', cpowend, DL.ss)
    if DIMPLE.odt_t0 > buffer :
        odtpow.appendhold( DIMPLE.odt_t0 - buffer)
    if DIMPLE.odt_pow < 0.:
        odtpow.appendhold( DIMPLE.odt_dt)
    else:
        odtpow.tanhRise( DIMPLE.odt_pow, DIMPLE.odt_dt, DIMPLE.odt_tau, DIMPLE.odt_shift)    
        
    if numpy.absolute(DIMPLE.odt_pow) < 0.0001:
        s.wait( odtpow.dt() )
        s.digichg('odtttl',0)
        s.wait(-odtpow.dt() )
    
    wfms.append(odtpow)
        
    
    # RF sweep
    if DL.rf == 1:   
        rfmod  = wfm.wave('rfmod', 0., DL.ss)
        rfmod.appendhold( bfield.dt() + DL.rftime )
        rfmod.linear( DL.rfvoltf, DL.rfpulsedt)
        wfms.append(rfmod)
        
        
    # Kill hfimg
    if DL.probekill ==1 or DL.braggkill ==1:
        hfimgdelay = 40. #ms
        analogimg = wfm.wave('analogimg', ANDOR.hfimg, DL.ss)
        
        if DL.probekill == 1:
            analogimg.appendhold( bfield.dt() + DL.probekilltime - hfimgdelay)
            analogimg.linear( DL.probekill_hfimg , 0.0)
            analogimg.appendhold( hfimgdelay + DL.probekilldt + 3*DL.ss)
        
        elif DL.braggkill == 1:
            analogimg.appendhold( bfield.dt() + DL.braggkilltime - hfimgdelay)
            analogimg.linear( DL.braggkill_hfimg , 0.0)
            analogimg.appendhold( hfimgdelay + DL.braggkilldt + 3*DL.ss)
            
        analogimg.linear( ANDOR.hfimg, 0.)
        
        wfms.append(analogimg)
            
    
    duration = s.analogwfm_add(DL.ss,wfms)
    
        
    s.wait( duration )
    
    if duration > DL.t0 + DL.dt:
        s.wait(-DL.lattice_interlock_time)
        if DL.use_lattice_interlock == 1:
            s.digichg('latticeinterlockbypass',0)
        else:
            s.digichg('latticeinterlockbypass',1)
        s.wait( DL.lattice_interlock_time)
    
    
    return s 
                        

    