import matplotlib.pyplot as plt
import matplotlib
import sys
sys.path.append('/lab/software/apparatus3/seq/utilities')
import evap

fig = plt.figure()

ax = fig.add_subplot(111)
t1 = [500.,780.,1000.,3000.]
tau = 1400.
tau2=1000.
offset = -0.157
beta = 1.55
p1 = 6.5 
t2 = 3000.
p0=10.
image=9000.
steps =500
time = [ t*1.0/steps*image for t in range(steps)]
leg = []

for i in t1:
	datax=[]
	datay=[]
	for j in time:
		datax.append(j)
		datay.append(evap.v2(j,p0,p1,i,tau,beta,offset,t2,tau))
	ax.plot(datax,datay)
	leg.append("t1 = %.1f" %i )

ax.legend(leg)
ax.grid(True)
ax.set_xlabel('Image(ms)')
ax.set_ylabel('ODTpow')
plt.show()



