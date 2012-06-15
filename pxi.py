import seqconf

def linenum(name):
    """ linenum looks in the system.txt file for the line number
        corresponding to the given channel name. """
    #space for actually doing this
    #04/29/2012 - pmd - I don't remember why I wanted this...
    return 1

class digitalout:
    """ This class can store all the information for the digital outs
        available in system.txt.
        It has dictionaries for the physical channel, and channel number
        with the channel names as keys. It also has a list of the names
        in order and a list of the default values in order.
        The order is determined by the order in which they are
        written in system.txt.
        """
    def __init__(self,physCh={},dflts=[],num={},names=[]):
        self.physCh=physCh
        self.dflts=dflts
        self.num=num
        self.names=names
        self.load()
    def __str__(self):
        return str(self.physCh)+'\n'+str(self.dflts)+'\n'+str(self.num)
    def load(self):
        sysfile = open(seqconf.systemtxt(),"r")
        while True:
            line = sysfile.readline()
            if line[0:len('DIGITAL_OUT')]=='DIGITAL_OUT':
                break
        digoutSection = True
        num=0
        while True:
            line = sysfile.readline()
            if line[0]=='#':
                break
            else:
               ch=line.split()
               self.names.append(ch[1])
               self.dflts.append(ch[2])
               self.physCh[ch[1]]=ch[0]
               self.num[ch[1]]=num
               num=num+1
        self.len=len(self.names)

class analogout:
    """ This class can store all the information for the ANALOG_OUT's
        available in system.txt.
        It has dictionaries for the physical channel, default states,
        and channel number with the channel names as keys.
        It also has a list of the names in order.
        The order is determined by the order in which they are
        written in system.txt.
        """
    def __init__(self,physCh={},dflts={},num={},names=[]):
        self.physCh=physCh
        self.dflts=dflts
        self.num=num
        self.names=names
        self.load()
    def __str__(self):
        return str(self.physCh)+'\n'+str(self.dflts)+'\n'+str(self.num)
    def load(self):
        sysfile = open(seqconf.systemtxt(),"r")
        while True:
            line = sysfile.readline()
            if line[0:len('ANALOG_OUT')]=='ANALOG_OUT':
                break
        digoutSection = True
        num=0
        while True:
            line = sysfile.readline()
            if line[0]=='#':
                break
            else:
               ch=line.split()
               self.names.append(ch[1])
               self.physCh[ch[1]]=ch[0]
               self.dflts[ch[1]]=ch[2]
               self.num[ch[1]]=num
               num=num+1
        self.len=len(self.names)

class device:
    """ This class can store the information for the ANALOG_DEVICE's
        availabe in system.txt.  It has dictionaries for the
        DIGITAL_OUT_Trig(Out), the Trig(In) and the device number
        indexed by name.
        """
    def __init__(self,trigout={},trig={},num={},names=[]):
        self.trigout=trigout
        self.trig=trig
        self.num=num
        self.names=names
        self.load()
    def __str__(self):
        return str(self.trigout)+'\n'+str(self.trig)+'\n'+str(self.num)
    def load(self):
        sysfile = open(seqconf.systemtxt(),"r")
        while True:
            line = sysfile.readline()
            if line[0:len('ANALOG_DEVICE')]=='ANALOG_DEVICE':
                break
        deviceSection = True
        num=0
        while True:
            line = sysfile.readline()
            if line[0]=='#':
                break
            else:
               dev=line.split()
               self.names.append(dev[0])
               self.trigout[dev[0]]=dev[1]
               self.trig[dev[0]]=dev[2]
               self.num[dev[0]]=num
               num=num+1
        self.len=len(self.names)
    

if __name__=="__main__":
    test=digitalout()
    test.load()
    print test
    test2=analogout()
    test2.load()
    print test2
    
