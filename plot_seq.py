from parse_seq import parse_seq
import matplotlib.pyplot as plt
import argparse
import os
def plot_seq(figure,data_digi_names,data_digi_time,data_digi,data_analog_names,data_analog_time,data_analog,autorange=1,plot_range_min=0,plot_range_max=10000):
        
        figure.add_axes([0.08,0.5,0.7,0.4])
        
        analog_axis = figure.axes[0]
        
        figure.add_axes([0.08,0.05,0.7,0.4])
        
        figure.axes[1].set_yticks([])
        
        digi_axis = figure.axes[1].twinx()
        
        digi_ticks = []
        
        for i, name in enumerate(data_digi_names):
            
            digi_axis.step(data_digi_time[i],data_digi[i],where = 'post', label = name)
            
            digi_ticks.append( - (i+0.5)*10./len(data_digi_names))
            
            digi_axis.axhline(- (i+1)*10./len(data_digi_names),color='grey', lw=1.5)
            
        for i, name in enumerate(data_analog_names):
            
            #~ print name,len(data_analog_time[i]),len(data_analog[i])
            analog_axis.step(data_analog_time[i],data_analog[i],where = 'post', label = name)  
        
        analog_axis.axhline(0, color='black', lw=2)
                   
        analog_axis.legend(bbox_to_anchor=(1.01, 1.01),loc=2,prop={'size':10})
        
        #digi_axis.legend(bbox_to_anchor=(1.01, 0.5),loc=2,prop={'size':10})
        
        analog_axis.set_xlabel('Time(ms)')
        
        figure.axes[1].set_ylabel('TTL')
        
        analog_axis.set_ylabel('Voltage(V)')
        
        analog_axis.grid(True)
        
        
        if not autorange: 
            
            analog_axis.set_xlim(plot_range_min,plot_range_max)
            
            digi_axis.set_xlim(plot_range_min,plot_range_max)
            
        else:
            
            axismin =  min(analog_axis.get_xlim()+digi_axis.get_xlim())
            
            axismax =  max(analog_axis.get_xlim()+digi_axis.get_xlim())
            
            analog_axis.set_xlim(axismin,axismax)
            
            digi_axis.set_xlim(axismin,axismax)
            
            analog_axis.set_ylim(bottom=0,top=11)
            
            plot_range_max = axismax
            
            plot_range_min = axismin
            
        digi_axis.set_ylim(bottom=-11,top=0)
        
        digi_axis.set_yticks(digi_ticks)
        
        digi_axis.set_yticklabels(data_digi_names)
        
def plot_file(seq_file, digital=['odtttl','probe'], analog=['odtpow','bfield'],autorange=1,plot_range_min=0,plot_range_max=10000):

    seq = parse_seq(seq_file)
    data_digi_names = []
    data_digi_time = []
    data_digi = []

    for chan,data in zip(seq.digi_channels,seq.digi_data):

        if chan in digital:

            data_digi_names.append(chan)
            data_digi_time.append(seq.digi_time)
            data_digi.append(data)

    data_analog_names = []
    data_analog_time = []
    data_analog = []       

    for channels,data,time in zip(seq.analog_channels,seq.analog_data,seq.analog_time):

        for chan,da in zip(channels,data):

            if chan in analog:

                data_analog_names.append(chan)
                data_analog_time.append(time)
                data_analog.append(da)
                
    fig = plt.figure()
    plot_seq(fig,data_digi_names,data_digi_time,data_digi,data_analog_names,data_analog_time,data_analog,autorange,plot_range_min,plot_range_max)
    fig.set_size_inches(16.0,10.0)
    fig.savefig(seq_file.split('.')[0]+'.png')
    #plt.show()

def plot_folder(seq_folder,digital,analog,autorange=1,plot_range_min=0,plot_range_max=10000):

	if not os.path.isdir(seq_folder): return "This is not a folder!"

	filelist = os.listdir(seq_folder)

	for file in filelist:
		
		if file.endswith(".txt"):
			
			print "Plotting file " + file +":\n\n"	
			plot_file(os.path.abspath(os.path.join(seq_folder,file)),digital,analog,autorange,plot_range_min,plot_range_max) 





if __name__ == '__main__':

 	parser = argparse.ArgumentParser()
 	parser.add_argument('path',action="store", type=str, help='Path of the seq file to plot.')
 	parser.add_argument('--analog',action="store", default='odtpow,bfield',type=str, help='Selec the analog channels to plot. Default is odtpow,bfield w/o this flag')
 	parser.add_argument('--digital',action="store", default='odtttl,probe',type=str, help='Selec the digital channels to plot. Default is odtttl,probe w/o this flag')
 	parser.add_argument('--range',action="store", default='auto',type=str, help='Set the range of the plot. For example: 0,1000')
 	parser.add_argument('--folder',action="store_const", default=0,const=1,help='Plot all the "txt" files the entire folder. Would try to find plotchannels.INI for parameters.')
	args = parser.parse_args()
    
	plot_func = plot_file if args.folder == 0 else plot_folder

	if args.range == 'auto': 
       		plot_func(args.path,args.digital.split(','),args.analog.split(','))
 	else:
 		range = args.range.split(',')
 		plot_func(args.path,args.digital.split(','),args.analog.split(','),autorange=0,plot_range_min=float(range[0]),plot_range_max=float(range[1]))
        
