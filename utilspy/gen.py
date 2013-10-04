from configobj import ConfigObj
import seqconf
#This function is used to read boolean data in the report file
def b(num,report):
	return bool(int(report['BOOL']['b'+str(num)][0]))
	

#This function looks for a string 'str' in the report file and returns it's boolean value
def bstr(str,report):
	#~ print seqconf.runnumber()
	for item in report['BOOL'].values():
		bool=item.split(';')[0]
		if bool =='1':
			boolVal=True;
		else:
			boolVal=False;
		string=item.split(';')[1]
		if string==str:
			return boolVal
	print "Boolean description not found in report: " + str
	return 

report = seqconf.savedir()+'report'+seqconf.runnumber()+'.INI'
report = ConfigObj(report)

def getreport():
	global report
	#The parameters are loaded from the report file
	#~ f=open('L:/data/app3/comms/SaveDir')
	#~ savedir=f.readline()
	#~ f.close
	#~ f=open('L:/data/app3/comms/RunNumber')
	#~ shotnum=f.readline()
	#~ f.close
	#~ report=savedir+'report'+shotnum+'.INI'
	#print(report)
	
	##report=seqconf.savedir()+'report'+seqconf.runnumber()+'.INI'
	#print "report path = %s" % report
	##report=ConfigObj(report)
	return report
	
def save_to_report( sec, key, value):
	report = getreport()
	report[sec][key] = str(value)
	report.write()

#This function get lattice webcam data from: /lab/software/apparatus3/utilities/Lattice_Webcam/log.dat and save the data to the report
def get_lattice_webcam_data(input=""):
    logfile = seqconf.base_seqspypath().split("seq/")[0] +"utilities/Lattice_Webcam/log.dat"
    logfile = ConfigObj(logfile)
    sections = ["IR1","IR2","IR3","GR1","GR2","GR3"]
    report = getreport()
    
    
    if input in sections:
        data = str(logfile[input]["latest"]).split(",")
        report["LATTICEWEBCAM"][input+"_Cx"] = data[0]
        report["LATTICEWEBCAM"][input+"_Cy"] = data[1]
        report["LATTICEWEBCAM"][input+"_Wx"] = data[2]
        report["LATTICEWEBCAM"][input+"_Wy"] = data[3]
        report.write()
    else:
        for i in sections:
            data = str(logfile[i]["latest"]).split(",")
            report["LATTICEWEBCAM"][i+"_Cx"] = data[0]
            report["LATTICEWEBCAM"][i+"_Cy"] = data[1]
            report["LATTICEWEBCAM"][i+"_Wx"] = data[2]
            report["LATTICEWEBCAM"][i+"_Wy"] = data[3]
            report.write()           
class Section(object):
	def __init__(self, adict):
		self.__dict__.update(adict)
	def set( self, key , val):
		self.__dict__[key] = val
	
def getsection(SEC):
	ndict = {}
	secdict = getreport()[SEC]
	for key in secdict.keys():
		if '.' in secdict[key]:
			ndict[key] = float( secdict[key] )
		else:
			try:
				ndict[key] = int( secdict[key] )
			except:
				ndict[key] = secdict[key]
	return Section(ndict)
	
	
	
	

def initial(s):
	# set initial values for TTL lines in sequence
	s.digichg('motswitch',1)
	s.digichg('field',1)
	s.digichg('cameratrig',0)
	s.digichg('camerashut',0)
	s.digichg('zsshutter',1)
	s.digichg('motshutter',0)
	s.digichg('beamflag',0)
	s.digichg('uvaom1',0)
	s.digichg('prshutter',1)
	s.digichg('hfimg',0)
	# Keep UVAOM's warm
	s.digichg('uvshutter',0)
	s.digichg('uvaom1',1)
	s.digichg('uvaom2',1)
	s.digichg('irttl1',0)
	s.digichg('irttl2',0)
	s.digichg('irttl3',0)
	s.digichg('greenttl1',0)
	s.digichg('greenttl2',0)
	s.digichg('greenttl3',0)
	s.digichg('ipgttl',1)
	s.digichg('brshutter',1)
	s.digichg('bservo',1)
	s.digichg('quick2',0)
	s.digichg('select2',0)
	return s
	
def releaseMOT(s):
	#release MOT
	s.digichg('motswitch',0) 
	s.digichg('motshutter',1)
	s.digichg('field',0)
	s.digichg('uvaom1',0)
	return s
	
	
def shutdown(s):
	#set the scopetrig
	scopetrig =  float(report['SEQ']['scopetrig'])
	current_time = s.tcur
	if scopetrig < current_time:
		s.wait( -current_time + scopetrig )
		s.digichg('scopetrig',1)
		s.wait(  current_time - scopetrig )
		
	#shut down everything when finished
	s.digichg('motswitch',0)
	s.digichg('zsshutter',1)
	s.digichg('beamflag',0)
	s.digichg('field',0)
	s.digichg('uvaom1',1)
	s.digichg('uvaom2',1)
	s.digichg('cameratrig',0)
	s.digichg('camerashut',0)
	s.digichg('prshutter',1)
	s.digichg('probe',0)
	s.digichg('irttl1',0)
	s.digichg('irttl2',0)
	s.digichg('irttl3',0)
	s.digichg('motshutter',1)
	s.wait(10.0)
	s.digichg('feshbach',0)
	#s.digichg('hfimg',0)
	s.digichg('quick',0)
	s.digichg('hfquick',0)
	s.digichg('uvshutter',0)
	s.digichg('odtttl',0)
	s.digichg('irttl1',0)
	s.digichg('irttl2',0)
	s.digichg('irttl3',0)
	s.digichg('greenttl1',0)
	s.digichg('greenttl2',0)
	s.digichg('greenttl3',0)
	s.digichg('ipgttl',1)
	s.digichg('brshutter',1)
	s.digichg('bservo',1)
	s.digichg('quick2',0)
	s.digichg('select2',0)
	s.digichg('analogimgttl',0)
	s.digichg('latticeinterlockbypass', 0)
	s.digichg('gradientfieldttl',0)
	s.digichg('scopetrig',0)
	return s
	
def setphase(s):
    phase = float(report['SEQ']['phase'])
    cycle=(1.0/60.0);
    mscycle=cycle*1000;
    phasewait=(phase/360.0)*mscycle;
    s.wait(phasewait)
    return s