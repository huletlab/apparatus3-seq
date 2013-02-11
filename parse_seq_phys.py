import matplotlib.pyplot as pyplot
import numpy as np

import os

if os.name == 'posix':
    lab = '/lab/'
else:
    lab = 'L:/'
import sys
sys.path.append(lab + 'software/apparatus3/seq')
sys.path.append(lab + 'software/apparatus3/seq/utilspy')

import seqconf
import argparse
import errormsg


endofline="\n"


class parse_seq:
    """This class parses the sequence txt files to python list of channels and waveforms"""
    
    def __init__(self,file_path = '' '''seqconf.seqtxtout()'''):
        """Initialize the class  """

        #Open sequence txt file        
        self.file_path = file_path
        self.folder, self.filename = os.path.split(self.file_path)
        self.seq = open(self.file_path,'rU').readlines()

        #Find the line numbers that mark start of analog waveform outputs
        self.analog_waveforms_position = []
        for position, line in enumerate(self.seq[1:]):	
            if (line == '#'+endofline): 
                self.analog_waveforms_position.append(position+1) # Plus one since we start from seq[1]

        """Parse Digital Waveforms"""
        self.digi_step = float(self.seq[1].split(" ")[1])

        self.digi_channels = self.seq[2].replace(' ','').split('!')
        self.digi_channels.pop(-1) # get rid of the final '\n'

        self.digi_data = [ [] for i in self.digi_channels]

        #Iterate through lines in the digital section and get the data
        digitalSection = self.seq[3:(self.analog_waveforms_position[0])]
        for i in digitalSection:
            self.digi_temp = i.replace(' ','').split('!')
            self.digi_temp.pop(-1) # get rid of the final '\n'
            
            for index, j in enumerate(self.digi_temp):
                self.digi_data[index].append(float(j))

        #The first column corresponds to the time values
        self.digi_time = self.digi_data.pop(0)
        self.digi_channels.pop(0) # get rid of the time(ms)
       
 
        """Parse Analog Waveforms"""
        self.analog_time0 = []
        self.analog_step = []
        self.analog_channels = []
        self.analog_data = []
        self.analog_time = []

        #Iterate over the waveforms, populating the above arrays        
        for i in range(len(self.analog_waveforms_position)-1):

            #Get TIME and STEP
            self.analog_temp = self.seq[(self.analog_waveforms_position[i]+2):(self.analog_waveforms_position[i+1])]
            self.analog_time0.append(float(self.analog_temp.pop(0).split("\t")[1].replace(endofline,'')))
            self.analog_step.append(float(self.analog_temp.pop(0).split("\t")[1].replace(endofline,'')))

            #Get CHANNELS, TIMEDATA, and VOLTAGEDATA
            self.analog_channels.append([])
            self.analog_data.append([])
            self.analog_time.append([])

            #Iterate over CHANNELS in WAVEFORM
            for index, analog in enumerate(self.analog_temp):
                analog.replace(endofline,'')
                if ( index % 2 ) == 0:
                    self.analog_channels[i].append(analog.replace(endofline,''))
                else:
                    self.analog_data[i].append( [ float(j) for j in analog.replace(' ','').split(',') ] )

            #All CHANNELS in WAVEFORM have the same TIMEDATA
            #Here it is calculated using the initial TIME and the STEP        
            self.analog_time[i] = list(np.arange(0, len(self.analog_data[i][0]), 1)*self.analog_step[i]  + self.analog_time0[i])
            if len(self.analog_time[i]) % 2 != 0 :
                err =  "\n WARNING:\n\n%s\n\nwaveform has an odd number of samples : %d" % (self.analog_channels[i], len(self.analog_time[i]))
                err = err +  "\n\nA DAQmx error will occur if you try to run this on labview"
                print err
                errormsg.box("INVALID WAVEFORM ERROR", err ) 


        #Collect information for each channel into two dictionaries
        self.flatwfms = {} 	#  just has the waveform data
        self.wfms = {} 	#  has the waveform data, along with an index that
			#  indicates which wfmout did this data belong to

        #the keys of the dictionary are the channel names
        #the values of the dictionary are an array with all the waveform outs for that channel

        for w, wfmouts in enumerate(self.analog_channels):

           for c, ch in enumerate(wfmouts):

             #The 2d-array called data represents the waveform:
             data = np.transpose(np.array(  [ self.analog_time[w], self.analog_data[w][c] ]  ))

             #chdat has two elements : [ data, index of wfm to which data corresponds ] 
             chdat =  [data,  w]

             #Populate the flatwfms and wfms dictionaries
             if ch not in self.wfms.keys():
               self.wfms[ch] = [chdat]
               self.flatwfms[ch] = data
             else:
               self.wfms[ch].append(chdat)
               self.flatwfms[ch] = np.concatenate( [self.flatwfms[ch],data], axis=0 )


        #The flatwfms dictionary is used to populate flat arrays
        #which contain all output information for each channel
        #This flat arrays are the ones used for plotting
        self.flat_analog_chs = []
        self.flat_analog_times = []
        self.flat_analog_data = []
        for i in self.flatwfms.keys(): 
           self.flat_analog_chs.append(i)
           self.flat_analog_times.append( self.flatwfms[i][:,0] )
           self.flat_analog_data.append( self.flatwfms[i][:,1] )
   
 
    def plot_analog(self):
        '''Plot the analog channels and save the plot '''
    
        for i , data in enumerate(self.analog_data):
            for index, wfm in enumerate(self.analog_data[i]):
                pyplot.plot( self.analog_time[i], wfm ,label= self.analog_channels[i][index])
            pyplot.ylim(-1,11)
            pyplot.legend()
            pyplot.savefig( self.folder + '/' + self.filename.split('.')[0] + '_analog_%d.png' %i)
            pyplot.close()

    def plot_digital(self):
        '''Plot the digital channels and save the plot '''
        fig = pyplot.figure()
        ax = pyplot.subplot(111)
        
        for index, wfm in enumerate(self.digi_data):
            ax.step( self.digi_time, np.array(wfm)+index*1.5, where = 'post' ,label = self.digi_channels[index])
            
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(bbox_to_anchor=(1., 1.,0.3,1),loc=2)
        pyplot.savefig( self.folder + '/' + self.filename.split('.')[0] + '_digital.png')
        pyplot.close()
        
        
    def diff( self, other):
        '''Return the difference of two sequency file and also a message string and a diff indicator '''
        if other.__class__.__name__ =='parse_seq':
            diff_counter_digi = 0
            diff_counter_anal = 0

            '''Diff Digital Channels'''
            diff_message = '\tDiscrepancies in Digial channels:\n\n'
            digi_channel_temp = [] 
            digi_time_self_temp = self.digi_time
            digi_time_other_temp = other.digi_time
            digi_data_self_temp = [] 
            digi_data_other_temp = []
            
            if self.digi_channels == other.digi_channels :
                
                for i , digi in enumerate(self.digi_channels):
                    if not self.digi_data[i] == other.digi_data[i]:
                        diff_counter_digi = diff_counter_digi + 1
                        digi_channel_temp.append(digi)
                        digi_data_self_temp.append(self.digi_data[i])
                        digi_data_other_temp.append(other.digi_data[i])
                        diff_message= diff_message + '\t\t' + digi + '\n'
                         
            else: 
                diff_message = diff_message + "\t Digital channels doesn't math!\n\n"
            
            if diff_counter_digi == 0: diff_message = diff_message +'\t\tNONE\n\n'


            '''Diff Analog Channels'''
            analog_channel_temp = [] 
            analog_time_self_temp = self.analog_time
            analog_time_other_temp = other.analog_time
            analog_data_self_temp = [] 
            analog_data_other_temp = []
            
            if self.analog_channels == other.analog_channels :

                for i , analog_ch in enumerate(self.analog_channels): 
                    diff_counter_temp = 0
                    diff_message = diff_message + '\n\tDiscrepancies in Analog channels waveform #%d:\n\n' %i
                    analog_data_self_temp.append([])
                    analog_data_other_temp.append([])
                    analog_channel_temp.append([])

                    for j , analog in enumerate(analog_ch):
                        if not self.analog_data[i][j] == other.analog_data[i][j] :
                            diff_counter_temp = diff_counter_temp + 1
                            analog_channel_temp[i].append(analog)
                            analog_data_self_temp[i].append(self.analog_data[i][j])
                            analog_data_other_temp[i].append(other.analog_data[i][j])
                            diff_message = diff_message + '\t\t' + analog + '\n'
                            
                    if diff_counter_temp == 0: diff_message = diff_message +'\t\tNONE\n\n'
                    diff_counter_anal = diff_counter_anal + diff_counter_temp 
                             
            else: 
                
                diff_message = diff_message + "\t Analog channels doesn't math!\n\n"
            
        else: print "Invalid input! The input should be a parse_seq instance."    

        diff_counter = diff_counter_digi + diff_counter_anal

        if diff_counter != 0 : 
            diff_data = [[digi_channel_temp , self.digi_time , digi_data_self_temp], \
                         [digi_channel_temp , other.digi_time ,digi_data_other_temp], \
                         [self.analog_channels,analog_time_self_temp,analog_data_self_temp], \
                         [other.analog_channels,analog_time_other_temp,analog_data_other_temp] \
                        ]
        else:
            diff_data = [] 
            diff_message = '\tPass\n'
            
        return diff_counter, diff_message, diff_data

if __name__ == '__main__':
    
    a=parse_seq('/lab/data/app3/2012/1209/120910/expseq3591.txt')
    b=parse_seq('/lab/data/app3/2012/1209/120910/expseq3590.txt')
    dc,dm,dd = a.diff(b)
    print dm
