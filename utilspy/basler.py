import math

def BaslerPicture(s,preexp,texp,postexp,probe):
    s.wait(-preexp) 
    s.digichg('basler',1) 
    s.wait(preexp) 
    #expose ccd
    s.digichg(probe,1) 
    s.wait(texp)
    s.digichg(probe,0) 
    s.wait(postexp)
    s.digichg('basler',0)
    return s
    
def BaslerBackground(s,preexp,texp,postexp):
    s.wait(-preexp) 
    s.digichg('basler',1) 
    s.wait(preexp) 
    #expose ccd
    s.wait(texp)
    s.wait(postexp)
    s.digichg('basler',0)
    return s
    
def BaslerInSitu(s,texp):
    s.digichg('basler',1)
    s.wait(texp)
    s.digichg('basler',0)
    return s
    
def Basler_AndorKineticSeries4(s,preexp,postexp,exp,light,noatoms):
    #PICTURE OF ATOMS
    
    t0 = s.tcur
    
    s=basler.BaslerPicture(s,preexp,exp,postexp,light)
    
    #SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
    #minimum time for no atoms is given by max trigger period in Andor settings
    s.wait(noatoms) 
    s.digichg('odtttl',0)
    s.wait(noatoms)
    s.digichg('odtttl',1)
    s.wait(noatoms)
    #PICTURE OF BACKGROUND
    s=basler.BaslerPicture(s,preexp,exp,postexp,light)
    
    tf = s.tcur
    
    return s, tf-t0
    
def Basler_FKSeries2(s,preexp,postexp,exp,light,noatoms):
    
    t0 = s.tcur
    
    #PICTURE OF ATOMS
    s=basler.BaslerPicture(s,preexp,exp,postexp,light)
    
    #CHECK THAT BACKGROUND PICTURE IS NOT TAKEN TOO FAST
    if 3*noatoms < 200.:
        print "Error:  need to wait longer between shots when using Basler\n"
        exit(1) 
    if noatoms < dt:
        print "Error:  need to wait longer between shots, clear trigger of NoAtoms will overlap with\
        \n end of accumulation trigger of Atoms"
        exit(1)    
    #SHUT DOWN TRAP, THEN TURN BACK ON FOR SAME BACKGROUND
    s.wait(noatoms)
    s.digichg('odtttl',0)
    s.wait(noatoms)
    s.digichg('odtttl',1)
    s.wait(noatoms)
    #PICTURE OF BACKGROUND
    s=basler.BaslerPicture(s,preexp,exp,postexp,light)
    
    tf = s.tcur
    
    return s, tf-t0

