###########################################
#### ROUNDTRIPS ANALOG WAVEFORM ###
###########################################

import sys
import seqconf, wfm, gen, math, cnc, time, os, numpy, hashlib, evap, physics, errormsg, odt, bfieldwfm, lattice
import shutil
import pprint
import matplotlib as mpl
#mpl.use('Agg') # This is for making the pyplot not complaining when there is no x server

numpy.seterr(all='raise')
np = numpy

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
RT = gen.getsection('ROUNDTRIP')

def makeplot( ylist, ss=None, name=None ):
    """useful for debugging stuff""" 
    figure = plt.figure( figsize = (5.,4.) )
    ax0 = figure.add_subplot(111) 
    for y in ylist:
        if isinstance( y, wfm.wave ):
            ax0.plot( y.ss*np.arange(len(y.y)), y.y)
        else:
            if ss is not None:
                ax0.plot( ss*np.arange(len(y)), y )
    if name is None:
        name = 'makeplot.png'

    figure.savefig( name, dpi=200)

 


def do_roundtrip( s, wfms ):
    """ creates roundtrips to characterize cooling in lattice.
        wfms are the lattice wfms, they can be mirrored here if a mirror 
        ramp is desired. """

    s.wait( RT.wait_at_top)

    # This case is for mirrored ramps
    if RT.mirror == 1 :
        alpha_desired = wfms[1]
        wfms = wfms[0] 
        mirrorwfms = []
        for wavefm in wfms:
            cp = copy.deepcopy( wavefm ) 
            cp.idnum = time.time()*100
            mirrorwfms.append( cp ) 

        for w in mirrorwfms:
            if 'lcr' in w.name:
                yvals = w.y
                
                # Get the reverse of the alpha desired array
                alpha_mirror = numpy.copy(alpha_desired[::-1])
                makeplot( [w, alpha_mirror], name=w.name ) 
  
                # It needs to have the same length as yvals, so append 
                # constant samples at the beginning if needed
                if alpha_mirror.size > yvals.size:
                    print "Error making mirror ramp for LCR."
                    print "Program will exit."
                    exit(1)
                alpha_mirror = numpy.append( (yvals.size - alpha_mirror.size)*[ alpha_mirror[0] ], alpha_mirror )
                
                # This is how much the mirror ramp will be advanced
                N_adv = int(math.floor( RT.lcr_mirror_advance / DL.ss))
                
                if N_adv < alpha_mirror.size:
                    alpha_mirror = alpha_mirror[N_adv:]
                    alpha_mirror = numpy.append(alpha_mirror, (yvals.size-alpha_mirror.size)*[alpha_mirror[-1]])
                else:
                    alpha_mirror = numpy.array( yvals.size*[alpha_mirror[-1]] )
                
                if RT.lcr_snap == 1:
                    alpha_mirror[ alpha_mirror > 0.01 ] = 1.  
                w.y = physics.cnv( w.name, alpha_mirror)  
            else:
                w.y = w.y[::-1]
            w.appendhold( RT.wait_at_end)
        wfms = mirrorwfms

    # This case is for custom ramps
    else:
        # There need to be 10 waveforms
        # 3IR, 3LCR, 3GR, BFIELD 
        # This follows the procedure done for the lattice ramps

        Xendtime = float( RT.image ) 
        Nnew = int(math.floor( Xendtime / DL.ss) ) 
        Xnew = numpy.arange( Xendtime/Nnew, RT.image, Xendtime/Nnew ) 
        ir_ramp, xy_ir, ir =  lattice.interpolate_ramp( RT.irpow, yoffset=0.)
        y_ir = ir_ramp(Xnew)

        grwfms = {}
        for i,grramp in enumerate([RT.grpow1, RT.grpow2, RT.grpow3]):
            gr_ramp, xy_gr, gr =  lattice.interpolate_ramp( grramp, yoffset=0.)
            y_gr = gr_ramp(Xnew)
            grwfms[ 'greenpow' + '%1d' % (i+1) ] = y_gr

        alpha_ramp, xy_alpha, alpha = lattice.interpolate_ramp( RT.alpha, yoffset=0. ) 
        y_alpha =  alpha_ramp(Xnew)

        wfms = []
        for ch in ['ir1pow', 'ir2pow', 'ir3pow']:
            n = filter( str.isdigit, ch)[0] 
            w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
            w.y = physics.cnv( ch, y_ir )
            wfms.append(w)
        for ch in ['greenpow1','greenpow2','greenpow3']:
            n = filter( str.isdigit, ch)[0] 
            w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
            
            correction = DIMPLE.__dict__['gr'+n+'correct']
            w.y = physics.cnv( ch, correction * grwfms[ch] )
            wfms.append(w)

        for ch in ['lcr1','lcr2','lcr3']:
            n = filter( str.isdigit, ch)[0] 
            w = wfm.wave(ch, 0.0, DL.ss)  #Start value will be overrriden
            print "Obtaining LCR waveform for ROUNDTRIP..."
            print y_alpha
            w.y = physics.cnv( ch, y_alpha )
            wfms.append(w)
 
        ##ADD field
        bfieldG = physics.cnv('as_to_B', DL.knob05)
        bfieldA = bfieldG/6.8
        bfield = wfm.wave('bfield', bfieldA, DL.ss)
        bfield.extend( wfms[-1].dt() ) 
        wfms.append(bfield)

    # Include ramp to zerocrossing, valid for mirror and custom cases
    # Final field can be given in amps (default) or in a0
    if RT.enable_zc == 1 :
        if isinstance(RT.zc_bias, str):
            if 'a0' in RT.zc_bias: 
                print "Using scattering length units for final field"
                scattlen = float(re.sub('a0','', RT.zc_bias))
                bfieldG = physics.cnv('as_to_B', scattlen)
                bfieldA = bfieldG/6.8
            elif 'knob05' in RT.zc_bias:
                print "Using knob05 as the final scattering length, amounts to no change"
                bfieldG = physics.cnv('as_to_B', DL.knob05)
                bfieldA = bfieldG/6.8
        else:
            bfieldA = RT.zc_bias 
            bfieldG = bfieldA*6.8
    else:
        print "Using knob05 as the final scattering length, amounts to no change"
        bfieldG = physics.cnv('as_to_B', DL.knob05)
        bfieldA = bfieldG/6.8

    # Set hfimg value for the given final field
    hfimg0 = -1.*(100.0 + 163.7 - 1.414*bfieldG)
    print "\n...ANDOR:hfimg and hfimg0 will be modified  in report\n"
    print "\tNEW  ANDOR:hfimg  = %.2f MHz" % ( hfimg0 - RT.imgdet)
    print "\tNEW  ANDOR:hfimg0 = %.2f MHz\n" %  hfimg0
    gen.save_to_report('ANDOR','hfimg', hfimg0 - RT.imgdet)
    gen.save_to_report('ANDOR','hfimg0', hfimg0)
    newANDORhfimg = hfimg0 - RT.imgdet
        
            
    for w in wfms:
        if 'bfield' in w.name:
            bfieldw = w
            if RT.enable_zc == 1 :
                if RT.zc_mirror_t0 < 0.:
                    dt = w.dt()
                    w.chop( w.dt() + RT.zc_mirror_t0 ) 
                if RT.zc_mirror_t0 > 0.:
                    w.appendhold( RT.zc_mirror_t0 )
                w.linear( bfieldA, RT.zc_mirror_rampdt)
                w.appendhold( RT.zc_mirror_holddt ) 

    for i,w in enumerate(wfms):
        if 'gradientfield' in w.name:
            gradientfield_i = i
    print "REMOVING GRADIENT FIELD"
    print len(wfms)  
    wfms = [ w for w in wfms if  w.name != 'gradientfield' ]
    print len(wfms)
    #Add gradientfield ramp to have levitation all the time
    from bfieldwfm import gradient_wave
    gradient = gradient_wave('gradientfield', 0.0, bfieldw.ss,volt = 0.0)
    gradient.follow( bfieldw)
    wfms.append(gradient)
      




    duration = s.analogwfm_add(DL.ss,wfms)
    s.wait(duration)
            
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

 
    #INDICATE WHICH CHANNELS ARE TO BE CONSIDERED FOR THE BACKGROUND
    bg = ['odtttl','irttl1','irttl2','irttl3','greenttl1','greenttl2','greenttl3']
    bgdictPRETOF={}
    for ch in bg:
        bgdictPRETOF[ch] = s.digistatus(ch)
    bgdictPRETOF['tof'] = RT.tof
    print "\nChannel status for pictures: PRE-TOF"
    print bgdictPRETOF
    print
        
    #RELEASE FROM LATTICE
    if RT.tof <= 0.:
        s.wait(1.0+ANDOR.exp)
    s.digichg('greenttl1',0)
    s.digichg('greenttl2',0)
    s.digichg('greenttl3',0)
    s.digichg('irttl1',0)
    s.digichg('irttl2',0)
    s.digichg('irttl3',0)
    #RELEASE FROM IR TRAP
    s.digichg('odtttl',0)
    if RT.tof <= 0.:
        s.wait(-1.0+ANDOR.exp)

    print "TIME WHEN RELEASED FROM LATTICE = ",s.tcur
    s.wait(RT.tof)
    
    return s, noatomswfms, bgdictPRETOF
   



