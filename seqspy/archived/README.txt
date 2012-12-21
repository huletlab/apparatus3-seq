##################################
This is the Sequence graveyard
##################################

If you no longer use a sequence and also want to clear out all related obsolete sections in params.INI, then use this folder. 

Each archived or retired sequence corresponds to a directory in this folder.  Each archived sequence directory has to have the following contents:

1.  app3control-entry.txt 

	This file contains the entry that used to correspond to the sequence in the app3control.INI file.  
	
2.  report.INI

	This file contains a report with all relevant parameters that are necessary to compile the sequence. 
	
3.	***.py 

	This is the sequence python file.   When retiring a sequence make sure that when you run this file it will compile with the report that is included in the archived sequence directory ( the report in entry 2. ).  Also make sure that the sequence output will be written to a file called expseq.txt,  inside the archived sequence directory,  see next entry.  
	
4.  expseq.txt

	This is the result of compiling the retired sequence.  You can display its contents using the python display sequence gui. 
	
