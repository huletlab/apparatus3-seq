from traits.api \
    import   HasTraits, File, Button, Bool, List, Str, Int, Float
    
from traitsui.api \
    import   Handler, HSplit, View,Group, HGroup, VGroup, Item, EnumEditor, ListEditor, CheckListEditor,  SetEditor, spring
    
from traitsui.file_dialog  \
    import open_file
    
from parse_seq import parse_seq

import os

from mpl_figure_editor import MPLFigureEditor

from matplotlib.figure import Figure

import wx

import numpy

import seqconf

from time import sleep

import pickle

mainpck = os.path.realpath(__file__).split('.')[0]+'_'+os.name+'.pck'

if os.name == "posix":
    default_file = seqconf.seqtxtout().replace("L:","/lab")
else:
    default_file = seqconf.seqtxtout()

import plot_seq

#~ print "DEFAULT_FILE",default_file

class sequence(HasTraits):

    name = Str
    
    file = File()
    
    waveforms=List()
    
    digi_num = Int()
    
    analog_num = Int()
    
    load = Button ('Load')
    
    reload = Button ('Reload')
    
    view = View(    
    
                    Item('file'),
                    
                    Item('load'),
                    
                    Item('reload'),
                
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

    def _load_fired(self):
        
        seq = parse_seq(self.file)
        
        self.waveforms= []
        
        self.waveforms.append( waveform( name= 'Digital', channels = seq.digi_channels, time = seq.digi_time, data = seq.digi_data))
        
        for i, analog in enumerate(seq.analog_channels):
            
            self.waveforms.append( waveform( name= 'Analog%d' %i, channels = analog, time = seq.analog_time[i], data = seq.analog_data[i] ))
    
    def _reload_fired(self):
        
        seq = parse_seq(self.file)
        
        self.waveforms[0].data = seq.digi_data
        self.waveforms[0].time = seq.digi_time
        
        for i, analog in enumerate(seq.analog_channels):
            
            self.waveforms[i+1].data = seq.analog_data[i]
            self.waveforms[i+1].time = seq.analog_time[i]
        
        

class waveform(HasTraits):
    
    name = Str
    
    channels = List(['empty','empty'])
    
    time = List()
    
    data = List()
    
    
    
    select_channels = List( 
    
                               
                        editor = SetEditor(
                        
                            name  = 'channels',
                            
                            ordered            = False,
                            
                            left_column_title  = 'Available Channels',
                            
                            right_column_title = 'Plot Channels' ),
                            
                            )
    
    view = View(             
                    Item('select_channels',show_label = False),
            )
            
                  

class MainWindowHandler(Handler):
    ## This handler is just graciously taking care of closing 
    ## the application when it is in the middle of doing a plot or a fit
    def init(self, info): 
            info.object._pck_(action='load')
    
    def close(self, info, is_OK):
        try:
            info.object._pck_(action='save')
        except:
            pass
        return True


class MainWindow(HasTraits):
    
    def _pck_(self,action,f=mainpck):
        if action == 'load':
            try:
                fpck=open(f,"rb")
                print 'Loading panel from %s' % mainpck
                self.seqs = pickle.load(fpck)
            except:
                print "Loading Fail"
                return
        if action == 'save':
            print 'Saving panel to %s' % mainpck
            fpck=open(f,"w+b")
            pickle.dump(self.seqs,fpck)
        fpck.close()
    
    figure = Figure()
    
    seqs = List([sequence(name='S0',file=default_file)])
    
    add = Button("Add Sequence")
    
    plot = Button("Plot")
    
    data_digi = List()
    
    data_analog = List()
    
    data_digi_time = List()
    
    data_digi_names = List()
    
    data_analog_time = List()
    
    data_analog_names = List()
    
    autorange = Bool(True, label="Autorange?")
    
    plot_range_max = Float(10000)
    
    plot_range_min = Float()
    
    
    def _figure_default(self):
        
        self.figure = Figure()
        
        self.figure.add_axes([0.05, 0.04, 0.9, 0.92])
        
    
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
                        )
                    )
    
    view= View( 
    
                HSplit(
                    control_group,
                    VGroup(
                    Item('figure', editor=MPLFigureEditor(),
                            dock='vertical', show_label = False,width=700),
                    HGroup(
                    'autorange',
                    'plot_range_min',
                     spring,
                    'plot_range_max'
                    )
                    )
                ),
                width     = 1,
                height    = 0.95,
                resizable = True,
                handler=MainWindowHandler(),
            )
    
 
    def _add_fired(self):
         
        self.seqs.append( sequence( name= 'S%d' %len(self.seqs),file=default_file) )
        
    def _plot_fired(self):
         
        self.get_data()
        
        self.image_show()
    
    #~ def _plot_range_max_changed(self):
        #~ sleep()
        #~ self.image_show()
         
    #~ def _plot_range_min_changed(self):
         #~ self.image_show()
    
    def get_data(self):
        
        self.data_digi = []
    
        self.data_analog = []
    
        self.data_digi_time = []
    
        self.data_digi_names = []
    
        self.data_analog_time = []
    
        self.data_analog_names = []
        
        digi_counter = 1
        
        for seq in self.seqs:
            
            for waveform in seq.waveforms:
                
                for i, channel in enumerate( waveform.channels):
                    
                    if channel in waveform.select_channels:
                        
                        if waveform.name == 'Digital':
                            digi_counter = digi_counter + 1
        
        digi_counter_2 = 1
        
        for seq in self.seqs:
            
            for waveform in seq.waveforms:
                
                for i, channel in enumerate( waveform.channels):
                    
                    if channel in waveform.select_channels:
                        
                        if waveform.name == 'Digital':
                            
                            self.data_digi_time.append(waveform.time)
                        
                            self.data_digi_names.append(seq.name + '_' + waveform.name + '_' + channel)
                            
                            length = len(waveform.select_channels)
                            
                            height = 10./(digi_counter-1)
                            
                            self.data_digi.append([ i*height*0.8 - digi_counter_2*height + height*0.1  for i in waveform.data[i]])
                                
                            digi_counter_2 = digi_counter_2 + 1
                            
                        else:
                            
                            self.data_analog_time.append(waveform.time)
                        
                            self.data_analog_names.append(seq.name + '_' + waveform.name + '_' + channel)
                            
                            self.data_analog.append(waveform.data[i])
                        
        

    def image_clear(self):
        """ Clears canvas 
        """
        self.figure.clf()
        
        wx.CallAfter(self.figure.canvas.draw)
        
    def image_show(self):
        """ Plots an image on the canvas
        """
        
        self.image_clear()
        plot_seq.plot_seq(self.figure,self.data_digi_names,self.data_digi_time,self.data_digi,self.data_analog_names,self.data_analog_time,self.data_analog,self.autorange,self.plot_range_min,self.plot_range_max)
        
        
        wx.CallAfter(self.figure.canvas.draw)


if __name__ == '__main__':
    MainWindow().configure_traits()