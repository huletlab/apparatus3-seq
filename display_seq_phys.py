from traits.api \
    import   HasTraits, File, Button, Bool, List, Str, Int, Float
    
from traitsui.api \
    import   Handler, HSplit, View,Group, HGroup, VGroup, Item, \
             EnumEditor, ListEditor, CheckListEditor,  SetEditor, \
             spring
    
from traitsui.file_dialog  \
    import open_file
    
from parse_seq import parse_seq
import physics

import os
from mpl_figure_editor import MPLFigureEditor
from matplotlib.figure import Figure
import wx
import numpy
import seqconf
from time import sleep
import pickle

#Setup the path for the pck file that contains the session info
mainpck = os.path.realpath(__file__).split('.')[0]+'_'+os.name+'.pck'

print ""
print ""

#Get the path for the default sequence
if os.name == "posix":
    default_file = seqconf.seqtxtout().replace("L:","/lab")
else:
    default_file = seqconf.seqtxtout()
print "DEFAULT_FILE = ",default_file


#The sequence class contains the digital and analog wavforms
#for a given sequence 
class sequence(HasTraits):

    # Data elements
    name = Str
    txtfile = File()
    waveforms=List()
    digi_num = Int()
    analog_num = Int()

    # Buttons
    loaded = False
    load = Button ('Load')

    # Define the view
    view = View(    
                    Item('txtfile'),
                    Item('load'),
                    VGroup(            
                        Item( 'waveforms',
                                style  = 'custom',
                                editor = ListEditor( use_notebook = True,
                                           deletable    = True,
                                           dock_style   = 'tab',
                                           page_name    = '.name' )
                                ),
                        show_labels = False,
                        show_border = True,
                        label       = 'Waveforms')

                )

    # Define the action when the LOAD button is pressed
    # There used to be a RELOAD button, but not anymore
    def _load_fired(self):
        
        #Load the sequence sequence
        self.seq = parse_seq(self.txtfile)
        
        #Store all waveforms in an array
        self.waveforms= []
        self.waveforms.append( waveform( name= 'Digital', \
                               channels = self.seq.digi_channels, \
                               time = self.seq.digi_time, \
                               data = self.seq.digi_data))
        self.waveforms.append( waveform( name= 'Analog', \
                               channels = self.seq.flat_analog_chs, \
                               time = self.seq.flat_analog_times, \
                               data = self.seq.flat_analog_data))
        self.waveforms.append( waveform( name= 'Physical', \
                               channels = physics.channel_list, \
                               time = [], \
                               data = []))
        self.loaded = True


#The waveform class contains the information for a set of channels
#and their data
class waveform(HasTraits):
    name = Str
    channels = List(['empty','empty'])
    time = List()
    data = List()

    #This object is used as the channel selector 
    select_channels = List( 
                        editor = SetEditor(
                            name  = 'channels',
                            ordered            = False,
                            left_column_title  = 'Available Channels',
                            right_column_title = 'Plot Channels' ),
                            )
    #
    view = View( Item('select_channels',show_label = False), )
            
                  

class MainWindowHandler(Handler):
    ## This handler is just graciously taking care of closing 
    ## the application when it is in the middle of somehting
    def init(self, info): 
            info.object._pck_(action='load')
    
    def close(self, info, is_OK):
        try:
            info.object._pck_(action='save')
        except:
            pass
        return True


class MainWindow(HasTraits):
    
    #This functio takes care of loading or saving the pck
    def _pck_(self,action,f=mainpck):
        if action == 'load':
            try:
                fpck=open(f,"rb")
                print 'Loading panel from %s ... ' % mainpck
                self.seqs = pickle.load(fpck)
            except:
                print "Loading Fail"
                return
        if action == 'save':
            print 'Saving panel to %s ...' % mainpck
            fpck=open(f,"w+b")
            pickle.dump(self.seqs,fpck)
        fpck.close()
    
    #Here are the elements of the main window
    figure = Figure()
    seqs = List([sequence(name='S0',txtfile=default_file)])
    add = Button("Add Sequence")
    plot = Button("Plot")

    
    data_digi = List()
    data_digi_time = List()
    data_digi_names = List()

    data_analog = List()
    data_analog_time = List()
    data_analog_names = List()

    
    autorangeY = Bool(True, label="Autorange in Y?")
    plot_rangeY_max = Float(10)
    plot_rangeY_min = Float(0)
    
    autorange = Bool(True, label="Autorange?")
    plot_range_max = Float(10000)
    plot_range_min = Float()
    
    
    def _figure_default(self):
        self.figure = Figure()
        self.figure.add_axes([0.05, 0.04, 0.9, 0.92])
        
    #This group contains the View of the control buttons
    #and the waveforms  
    control_group = Group(
                        Item('plot', show_label = False),
                        VGroup(
                            Item( 'seqs',
                                style  = 'custom',
                                editor = ListEditor( use_notebook = True,
                                           deletable    = True,
                                           dock_style   = 'tab',
                                           page_name    = '.name')
                            ),
                            Item('add', show_label = False),       
                               show_labels = False,
                               show_border = True,
                               label       = 'seqs',
                        ))
     
    #This is the view of the Main Window, including the
    #control group
    view= View( 
                HSplit(
                    control_group,
                    VGroup( 
                        Item('figure', editor=MPLFigureEditor(),
                            dock='vertical', show_label = False,width=700),
                        HGroup( 'autorange',   'plot_range_min', spring, 'plot_range_max'),
                        HGroup( 'autorangeY', 'plot_rangeY_min', spring, 'plot_rangeY_max')
                          )
                      ),
                width     = 1,
                height    = 0.95,
                resizable = True,
                handler=MainWindowHandler(),
            )
    

    #Define action when a new sequence is added
    def _add_fired(self):
        self.seqs.append( sequence( name= 'S%d' % len(self.seqs) , txtfile=default_file) )
        
    #Define action when the plot button is pressed
    def _plot_fired(self):
         
        self.get_data()
        self.image_show()
    
    #~ def _plot_range_max_changed(self):
        #~ sleep()
        #~ self.image_show()
         
    #~ def _plot_range_min_changed(self):
         #~ self.image_show()
  
 
    #Here the data 
    def get_data(self):
        
        self.data_digi = []
        self.data_digi_time = []
        self.data_digi_names = []

        self.data_analog = []
        self.data_analog_time = []
        self.data_analog_names = []

        #Find out how many digital channels will be plotted 
        digi_counter = 1
        for seq in self.seqs:
            for waveform in seq.waveforms:
                for i, channel in enumerate( waveform.channels):
                    if channel in waveform.select_channels:

                        if waveform.name == 'Digital':
                            digi_counter = digi_counter + 1
      


        #Setup all the digital & analog channels from the various
        #seqs for plotting 
        digi_counter_2 = 1
        for seq in self.seqs:
            #Prepare the physical quantities calculator class   
            physical = physics.calc(seq.seq.wfms)
            for waveform in seq.waveforms:
                for i, channel in enumerate( waveform.channels):
                    if channel in waveform.select_channels:
                        
                        if waveform.name == 'Digital':
                            self.data_digi_time.append(waveform.time)
                            self.data_digi_names.append(seq.name + '_' + waveform.name + '_' + channel)
                            
                            length = len(waveform.select_channels)
                            height = 10./(digi_counter-1)
                            
                            self.data_digi.append(  [ i*height*0.8 - digi_counter_2*height + height*0.1  \
                                                      for i in waveform.data[i] ]  )

                            digi_counter_2 = digi_counter_2 + 1
                            
                        elif waveform.name == 'Analog':
                            self.data_analog_time.append(waveform.time[i])
                            self.data_analog_names.append(seq.name + '_' + waveform.name + '_' + channel)
                            self.data_analog.append(waveform.data[i])
                            
                        elif waveform.name == 'Physical':
                            self.data_analog_names.append(seq.name + '_' + waveform.name + '_' + channel)
                            dat = eval("physical.calculate('"+channel+"')")
                            self.data_analog_time.append( dat[0] )
                            self.data_analog.append( dat[1] )
                                                        
        
    def image_clear(self):
        """ Clears canvas 
        """
        self.figure.clf()
        wx.CallAfter(self.figure.canvas.draw)
    
    
    def image_show(self):
        """ Plots an image on the canvas
        """
        self.image_clear()
        self.figure.add_axes([0.08,0.5,0.7,0.4])
        analog_axis = self.figure.axes[0]

        self.figure.add_axes([0.08,0.05,0.7,0.4])
        self.figure.axes[1].set_yticks([])
        digi_axis = self.figure.axes[1].twinx()
        digi_ticks = []

        #Makes the digital plot
        for i, name in enumerate(self.data_digi_names):
            digi_axis.step(self.data_digi_time[i],self.data_digi[i],where = 'post', label = name)
            digi_ticks.append( - (i+0.5)*10./len(self.data_digi_names))
            digi_axis.axhline(- (i+1)*10./len(self.data_digi_names),color='grey', lw=1.5)

        #digi_axis.legend(bbox_to_anchor=(1.01, 0.5),loc=2,prop={'size':10})
        self.figure.axes[1].set_ylabel('TTL')
        digi_axis.grid(True)
        
    
        #Makes the analog plot
        for i, name in enumerate(self.data_analog_names):
            analog_axis.step(self.data_analog_time[i],self.data_analog[i],where = 'post', label = name)  
        
        analog_axis.axhline(0, color='black', lw=2)
        analog_axis.legend(bbox_to_anchor=(1.01, 1.01),loc=2,prop={'size':10})
        analog_axis.set_xlabel('Time(ms)')
        analog_axis.set_ylabel('Voltage(V)')
        analog_axis.grid(True)
       
        #Take care of the Yaxis range of the analog plot 
        if not self.autorangeY: 
            analog_axis.set_ylim(self.plot_rangeY_min,self.plot_rangeY_max)
        else:
            axismin =  min(analog_axis.get_ylim())
            axismax =  max(analog_axis.get_ylim())
            analog_axis.set_ylim(axismin,axismax)
            self.plot_rangeY_max = axismax
            self.plot_rangeY_min = axismin
        
        #Take care of the Xaxis(time) range for both plots
        if not self.autorange: 
            analog_axis.set_xlim(self.plot_range_min,self.plot_range_max)
            digi_axis.set_xlim(self.plot_range_min,self.plot_range_max)
        else:
            axismin =  min(analog_axis.get_xlim()+digi_axis.get_xlim())
            axismax =  max(analog_axis.get_xlim()+digi_axis.get_xlim())
            analog_axis.set_xlim(axismin,axismax)
            digi_axis.set_xlim(axismin,axismax)
            #~ analog_axis.set_ylim(bottom=0,top=11)
            self.plot_range_max = axismax
            self.plot_range_min = axismin
        
        #Label the digital waveforms using the ticklabels on the plot    
        digi_axis.set_ylim(bottom=-11,top=0)
        digi_axis.set_yticks(digi_ticks)
        digi_axis.set_yticklabels(self.data_digi_names)
        
        wx.CallAfter(self.figure.canvas.draw)


if __name__ == '__main__':
    MainWindow().configure_traits()
