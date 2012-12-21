#!/usr/bin/python
import sys
import os
import argparse
sys.path.append( os.path.split(os.path.dirname(os.path.realpath(__file__)))[0] ) # include parent folder

import seqconf
import parse_seq


def diff( file1path, file2path ):
    
    ''' find the diff of the benchmark for two dates and create a report'''

    seqlist1 =  os.listdir(file1path)
    
    seqlist2 =  os.listdir(file2path)
    
    diff_log = 'Diff between path:\n\t%s\n\t%s\n\n' % (file1path,file2path) 
    
    # Find out the difference in seqence files
    
    seq_common = set(seqlist1) & set(seqlist2)
    
    diff_in_seqs_file = ''
    
    for i in set(seqlist1)-seq_common:
    
        diff_in_seqs_file = diff_in_seqs_file + '\t+' + i + '\n'
        
        
    for i in set(seqlist2)-seq_common:
    
        diff_in_seqs_file = diff_in_seqs_file + '\t-' + i + '\n'   
        
    
    if diff_in_seqs_file == '': diff_in_seqs_file = '\tnone\n '



    diff_log = diff_log + 'Difference in seqs files:\n' + diff_in_seqs_file + '\n'
    
    
    # Find the diff in the common seqfiles
    
    for seq in seq_common:
        
        if seq.endswith('.txt'):
        
            print "Diffing file: %s\n" %seq 
            
            file1 = parse_seq.parse_seq( file1path + seq)
            
            file2 = parse_seq.parse_seq( file2path + seq)
            
            diff_counter, diff_message, diff_data = file1.diff(file2)
            
            if diff_counter:
                
                diff_log = diff_log + 'Mismatch in file: ' + seq +'\n\n' + diff_message +'\n\n'
                
                
            print diff_message
    
    f = open(file1path + 'diff.log', 'w')
    
    f.write(diff_log)
    
    f.close
    
def diff_file(filepath1,filepath2):
    
    print "Diffing file:\n\n\t%s\n\t%s \n" %(filepath1,filepath2)
    
    file1 = parse_seq.parse_seq( filepath1 )
            
    file2 = parse_seq.parse_seq( filepath2 )
            
    diff_counter, diff_message, diff_data = file1.diff(file2)
    
    print "Result:"
    print diff_message
    
    return diff_message
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser('diff.py')
    parser.add_argument('path', nargs=2,action="store", type=str, help='The two paths to compare')
    parser.add_argument('--folder',dest="diff_function",action="store_const", const =diff,default=diff_file, help='Compare all the file with same filename in the two directories instead compare only two files')
    path1 = parser.parse_args().path[0]
    path2 = parser.parse_args().path[1]
    #print parser.parse_args().diff_function
    parser.parse_args().diff_function(path1,path2)
 
