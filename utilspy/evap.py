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

def v3(cut_time,m,y,t0,t):
	# Hard coded trajectory use v2 until 1 sec and use a path polynomial

        p0       = 10.2000
        p1       = 6.5000
        t1       = 780.0000
        tau      = 1400.0000
        beta     = 1.5500
        offset   = -0.1570
        t2       = 3000.0000
        tau2     = 1000.0000
        #cut_time = 1560.00
        V_2 = lambda t:v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)
    
        deltaT = 0.001
        m1 = (V_2(cut_time)-V_2(cut_time-deltaT))/deltaT
        y1 = V_2(cut_time)

        if t < cut_time:
            phys = V_2(t)
        else:
            phys = patch_function2(m1,m,y1,y,t0,t-cut_time)

        return phys

def v4(cut_time,m,y,t0,m_t0,t):
        # Hard coded trajectory use v2 until cuttime and use a patch polynomial and use a line after t0+cuttime

        p0       = 10.2000
        p1       = 6.5000
        t1       = 780.0000
        tau      = 1400.0000
        beta     = 1.5500
        offset   = -0.1570
        t2       = 3000.0000
        tau2     = 1000.0000
        #cut_time = 1560.00
        V_2 = lambda t:v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)

        deltaT = 0.001
        m1 = (V_2(cut_time)-V_2(cut_time-deltaT))/deltaT
        y1 = V_2(cut_time)

        if t < cut_time:
                phys = V_2(t)
        elif t<(cut_time+t0):
                phys = patch_function2(m1,m,y1,y,t0,t-cut_time)
        else:
                phys = m_t0*t+(y-m_t0*(cut_time+t0))
        
        return phys

def v5(cut_time,m,y,t0,kink1,kink2,m_t0_1,m_t0_2,t):
        # Hard coded trajectory use v2 until cuttime and use a patch polynomial and use a line after t0+cuttime

        p0       = 10.2000
        p1       = 6.5000
        t1       = 780.0000
        tau      = 1400.0000
        beta     = 1.5500
        offset   = -0.1570
        t2       = 3000.0000
        tau2     = 1000.0000
        #cut_time = 1560.00
        V_2 = lambda t:v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)

        deltaT = 0.001
        m1 = (V_2(cut_time)-V_2(cut_time-deltaT))/deltaT
        y1 = V_2(cut_time)

        if t < cut_time:
                phys = V_2(t)
        elif t<(cut_time+t0):
                phys = patch_function2(m1,m,y1,y,t0,t-cut_time)
        elif t<(kink1):
                phys = m*t+(y-m*(cut_time+t0))
        elif t<(kink2):
                phys = m_t0_1*t+(m*kink1+(y-m*(cut_time+t0))-m_t0_1*(kink1))
        else:
                phys = m_t0_2*t+(m_t0_1*kink2+(m*kink1+(y-m*(cut_time+t0))-m_t0_1*(kink1))-m_t0_2*(kink2))
        return phys

def func1(t,offset,p0,p1,t1,tau,beta):
	return (1-offset)*v1(t,p0,p1,t1,tau,beta) + 10*offset

def func2(t,offset,p1,t1,t2,tau,tau2,beta):
	return ((1-offset) * p1 * math.pow(1,beta) / math.pow( 1 + (t2-t1)/tau ,beta) + 10*offset) * math.pow( 1 + (t-t2)/tau2, -1)
	
def v6(t,p0,p1,t1,tau,beta, offset,t2,tau2,smoothdt):
	# same as version 2 only use a patch polynomial to smooth out the kink at t2
	sdt = smoothdt*0.5
	if t < (t2-sdt):
		phys = func1(t,offset,p0,p1,t1,tau,beta)
	elif t< (t2+sdt):
		deltaT=1e-3 # 1 us to get slope of function
		m1 = (func1(t2-sdt,offset,p0,p1,t1,tau,beta)-func1(t2-sdt-deltaT,offset,p0,p1,t1,tau,beta))/deltaT
		m2 = ( func2(t2+sdt+deltaT,offset,p1,t1,t2,tau,tau2,beta)- func2(t2+sdt,offset,p1,t1,t2,tau,tau2,beta))/deltaT
		y1 = func1(t2-sdt,offset,p0,p1,t1,tau,beta)
		y2 = func2(t2+sdt,offset,p1,t1,t2,tau,tau2,beta)
		phys = patch_function2(m1,m2,y1,y2,smoothdt,t-(t2-sdt))
	else:
		phys =  func2(t,offset,p1,t1,t2,tau,tau2,beta)
	return phys

def patch_function(f1,f2,t0,patcht,t):
	if t < t0: 
		return f1(t)
	elif t< (t0+patcht):
		return f1(t)*(math.sin(math.pi*(1./2+(t-t0)/patcht))+1)/2 + f2(t)*(-math.sin(math.pi*(1./2+(t-t0)/patcht))+1)/2 
	else:
		return f2(t) 

def patch_function2(m1,m2,y1,y2,t0,t):
	a = y1
	b = m1 
	d = ((y2-a-b*t0)/t0*2-(m2-b))/(-t0**2)
	c = (y2-a-b*t0-d*t0**3)/t0**2
	return a+b*t+c*t**2+d*t**3 #if (-c/3/d>t0 or -c/3/d<0 ) else 0

def patch_function3(m1,y1,y2,t0,t):
	tau = math.log(m1/m2)**(-1)*t0
	a = -m1*tau
	b = y1 -a
	return a*exp(-t/tau)+b
		

if __name__=="__main__":
	import matplotlib.pyplot as plt
	import matplotlib
	import numpy 

	p0       = 10.2000
	p1       = 6.5000
	t1       = 780.0000
	tau      = 1400.0000
	beta     = 1.5500
	offset   = -0.1570
	t2       = 3000.0000
	tau2     = 1000.0000
	duration = 60.0000

	V_2 = lambda t:v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)
	
	cut_time = 1560.0
	deltaT = 0.001
	m1 = (V_2(cut_time)-V_2(cut_time-deltaT))/deltaT
	y1 = V_2(cut_time)

	end_depth = 0.05
	end_time = 12000.
	max_slope = (end_depth- V_2(cut_time))/(end_time- cut_time)

	test_depth = 0.5

	test_samples = 10
	test_range = 0.2

	endpoints_start = (test_depth-(y1-m1*cut_time))/m1	

	endpoints_end = (test_depth-(end_depth-max_slope*end_time))/max_slope 

	test_endpoints = [ (-endpoints_start + endpoints_end)/ (test_samples-1) *(i)*test_range +endpoints_start for i in range(test_samples) ]
	
	test_slope_samples = 4
	test_slope_range = 1
	test_slopes = []

	for i in test_endpoints:
		m_min = (test_depth-y1)/(i-cut_time) 
		m_max = (end_depth- test_depth)/(end_time-i)
		test_slopes.append([ (m_max -  m_min)/(test_slope_samples-1)*(l)*test_slope_range +  m_min for l in range(test_slope_samples)])		
	
	colors = ['red','green', 'blue', 'black', 'magenta', 'cyan', 'yellow', 'orange', 'firebrick', 'steelblue','deeppink','darkgreen','goldenrod','chartreuse','red','green', 'blue', 'black', 'magenta']
	fig = plt.figure()
	ax1 = fig.add_axes([0.1,0.1,.8,.8])
	ax1.set_xlabel("Time(ms)")
	ax1.set_ylabel("ODTPOW")
	x = numpy.linspace(0.,end_time,1000)
	y = [max_slope*t+(end_depth-max_slope*end_time) for t in x] 
	ax1.plot(x,y,label="Max slope")
	y = [V_2(t) for t in x] 
	ax1.plot(x,y,label='Original,Test_endpow = %.4e' %test_depth)
	trajectory_count = 0

	for i,tp in enumerate(test_endpoints):
		for ts in test_slopes[i]:
			t0 = tp-cut_time
			y2 = test_depth
			m2 = ts
			a = y1
			b = m1
			d = ((y2-a-b*t0)/t0*2-(m2-b))/(-t0**2)
			c = (y2-a-b*t0-d*t0**3)/t0**2
			#Check whether if the sencond derivitive go to zero 
			if (-c/3/d>=(tp-cut_time) or -c/3/d<=0 ):
				x = numpy.linspace(cut_time,tp,100)
				y = [patch_function2(m1,ts,y1,test_depth,tp-cut_time,t-cut_time) for t in x]
				time_to_end = (end_depth-(y2-ts*tp))/ts
				leg = "Trac%d,m=%.3e,t0=%.3e,image_time=%.3e,time_to_odtpowf = %.3e" %(trajectory_count,ts,tp-cut_time,tp,time_to_end)
				ax1.plot(x,y,label=leg,color=colors[trajectory_count])
				trajectory_count = trajectory_count + 1
			ax1.legend()
	plt.show()
	#print v2(t,p0,p1,t1,tau,beta, offset,t2,tau2)

#if __name__== "__main__":
#	l=sys.argv[1].split(' ')
#	if l[0] == 'v1' and len(l)==7:
#		print v1(float(l[1]),float(l[2]),float(l[3]),float(l[4]),float(l[5]),float(l[6]))
#		

#	if l[0] == 'v2' and len(l)==10:
#		print v2(float(l[1]),float(l[2]),float(l[3]),float(l[4]),float(l[5]),float(l[6]),\
#				float(l[7]),float(l[8]),float(l[9]))
	
