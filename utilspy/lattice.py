###########################################
#### LATTICE ANALOG WAVEFORM ###
###########################################

import sys
sys.path.append('L:/software/apparatus3/seq/seq')
sys.path.append('L:/software/apparatus3/seq/utilspy')
sys.path.append('L:/software/apparatus3/seq/seqspy')
sys.path.append('L:/software/apparatus3/convert')
import seqconf, wfm, gen, math, cnc, time, os, numpy, hashlib, evap, physics, errormsg

import matplotlib.pyplot as plt

from scipy import interpolate

#GET SECTION CONTENTS
DIMPLE = gen.getsection('DIMPLE')
DL = gen.getsection('DIMPLELATTICE')


class lattice_wave(wfm.wave):
	"""The lattice_wave class helps construct the waveforms that 
		will be used to ramp the lattice.
		
		Several methods are added that allow doing special ramps
		"""


def dimple_to_lattice(s):
    
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
    
    fig = plt.figure( figsize=(6.,7.))
    ax0 = fig.add_axes( [0.12,0.63,0.76,0.32]) 
    ax1 = fig.add_axes( [0.12,0.43,0.76,0.16])
    ax2 = fig.add_axes( [0.12,0.23,0.76,0.16])
    

    ax0.plot( x_v0, v0, 'b', lw=2.5, label='Lattice depth')
    
    ###########################################
    #### USER DEFINED RAMPS: IR, GR, and U ###
    ###########################################
    
    # Define how we want to ramp up the IR power
    ir = numpy.array( [float(i) for i in DL.irpow ] )
    ir = ir.reshape( (ir.size/2, 2 ))
    ir[:,1] = ir[:,1] + DIMPLE.ir1pow
    ir_spline = interpolate.InterpolatedUnivariateSpline( ir[:,0], ir[:,1], k=2) 
    ir_interp = interpolate.interp1d( ir[:,0], ir[:,1] ) 
    
    dt_ir = numpy.amax( ir[:,0]) - numpy.amin( ir[:,0])
    N_ir = int(math.floor( dt_ir / DL.ss ))
    x_ir = numpy.arange( dt_ir/N_ir, dt_ir, dt_ir/N_ir)
    
    y_ir = ir_spline(x_ir) 
    
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
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
    
    ax0.plot(ir[:,0],ir[:,1],'.', color='darkorange', label='irpow dat')
    ax0.plot(x_ir, ir_spline(x_ir),':',color='darkorange',label='spline')
    ax0.plot(x_v0, y_ir, color='darkorange',label='irpow')
    #ax0.plot(x_ir, ir_interp(x_ir),'--', color='darkorange',label='interp')
    
    
    # Define how we want to ramp up the GR power
    gr = numpy.array( [float(i) for i in DL.grpow ] )
    gr = gr.reshape( (gr.size/2, 2 ))
    gr[:,1] = gr[:,1] + DIMPLE.gr1pow
    gr_spline = interpolate.InterpolatedUnivariateSpline( gr[:,0], gr[:,1], k=2) 
    gr_interp = interpolate.interp1d( gr[:,0], gr[:,1] ) 
    
    dt_gr = numpy.amax( gr[:,0]) - numpy.amin( gr[:,0])
    N_gr = int(math.floor( dt_gr / DL.ss ))
    x_gr = numpy.arange( dt_gr/N_gr, dt_gr, dt_gr/N_gr)
    
    y_gr = gr_spline(x_gr) 
    
    if v0.size > y_gr.size:
        y_gr = numpy.append(y_gr, (v0.size-y_gr.size)*[y_gr[-1]])
    elif v0.size < y_gr.size:
        y_gr = y_gr[0:v0.size]
        
    if v0.size != y_gr.size:
        msg = "GRPOW ERROR: number of samples in GR ramp and V0 ramp does not match!"
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
        
    
    ax0.plot(gr[:,0],gr[:,1],'.g', label='grpow dat')
    ax0.plot(x_gr, gr_spline(x_gr),':g',label='spline')
    ax0.plot(x_v0, y_gr, color='green', label='grpow')
    #ax0.plot(x_gr, gr_interp(x_gr),'g--',label='interp')
    
    
    # Define how we want to ramp up the onsite interactions
    U = numpy.array( [float(i) for i in DL.onsite ] )
    U = U.reshape( (U.size/2, 2 ))
    U_spline = interpolate.InterpolatedUnivariateSpline( U[:,0], U[:,1], k=2) 
    U_interp = interpolate.interp1d( U[:,0], U[:,1] ) 
    
    dt_U = numpy.amax( U[:,0]) - numpy.amin( U[:,0])
    N_U = int(math.floor( dt_U / DL.ss ))
    x_U = numpy.arange( dt_U/N_U, dt_U, dt_U/N_U)
    
    y_U = U_spline(x_U) 
    
    if v0.size > y_U.size:
        y_U = numpy.append(y_U, (v0.size-y_U.size)*[y_U[-1]])
    elif v0.size < y_U.size:
        y_U = y_U[0:v0.size]
        
    if v0.size != y_U.size:
        msg = "U ERROR: number of samples in U ramp and V0 ramp does not match!"
        errormsg.box('LATTICE LOADING ERROR',msg)
        exit(1)
    
    
    ax1.plot(U[:,0],U[:,1],'.k', label='U/t dat')
    ax1.plot(x_U, U_spline(x_U),':k',label='spline')
    ax1.plot(x_v0, y_U, color='black', label='U/t')
    #ax0.plot(x_U, U_interp(x_U),'k--',label='interp')
    
    ax0.set_xlim(right= ax0.get_xlim()[1]*1.1)    
    ylim = ax0.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax0.set_ylim( ylim[0]-extra, ylim[1]+extra )

    ax0.set_ylabel('$E_{r}$',size=16, labelpad=0)
    ax1.set_ylabel('$U/t$',size=16, labelpad=0)
    ax0.set_title('Lattice Loading')
    ax0.legend(loc='best',numpoints=1,prop={'size':6})
    
    ax1.set_xlim( ax0.get_xlim()) 
    ylim = ax1.get_ylim()
    extra = (ylim[1]-ylim[0])*0.1
    ax1.set_ylim( ylim[0]-extra, ylim[1]+extra )
    ax1.legend(loc='best',numpoints=1,prop={'size':6})
    

    #######################################################################
    #### CALCULATED RAMPS:  ALPHA, TUNNELING, SCATTERING LENGTH, BFIELD ###
    #######################################################################
    
    alpha = (v0/y_ir)**2.
    
    ax2.plot( x_v0, alpha, color='saddlebrown', label='alpha')
    
    ax2.set_xlim( ax0.get_xlim()) 
    ax2.set_ylim(-0.05,1.01)
    
    ax2.set_xlabel('time (ms)')
    ax2.legend(loc='best',numpoints=1,prop={'size':6})
    

    

    
    plt.savefig( seqconf.seqtxtout().split('.')[0]+'_latticeRamp.png', dpi=140 )
    
    #plst.show()


    
    
    
    return s 
                        

    