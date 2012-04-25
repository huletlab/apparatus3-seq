"""Evaporation trajectories."""

import sys,math

def v1(t,p0,p1,t1,tau,beta):
	if t < t1:
		phys =  (p0-p1)*math.tanh( beta/tau * (t-t1)* p1/(p0-p1))/math.tanh( beta/tau * (-t1) * p1/(p0-p1)) + p1
	else:
		phys =   p1 * math.pow(1,beta) / math.pow( 1 + (t-t1)/tau ,beta)
	return phys
	
def v2(t,p0,p1,t1,tau,beta, offset,t2,tau2):
	if t < t2:
		phys = (1-offset)*v1(t,p0,p1,t1,tau,beta) + 10*offset
	else:
		phys =  ((1-offset) * p1 * math.pow(1,beta) / math.pow( 1 + (t2-t1)/tau ,beta) + 10*offset) * math.pow( 1 + (t-t2)/tau2, -1)
	return phys
	

if __name__== "__main__":
	l=sys.argv[1].split(' ')
	if l[0] == 'v1' and len(l)==7:
		print v1(float(l[1]),float(l[2]),float(l[3]),float(l[4]),float(l[5]),float(l[6]))
		
	if l[0] == 'v2' and len(l)==10:
		print v2(float(l[1]),float(l[2]),float(l[3]),float(l[4]),float(l[5]),float(l[6]),\
				float(l[7]),float(l[8]),float(l[9]))
	
