
from Tkinter import *
import tkMessageBox

def box(title,msg):
  msglen = max( [ len(x) for x in title.split('\n') + msg.split('\n') ] ) 

  print '\n\n' 
  print '#'*(msglen+12)
  print '\t',title
  print '\t',msg
  print '#'*(msglen+12)
  print '\n\n' 
  
  # This used to be a pop-up window, but it got annoying sometimes 
  #window = Tk()
  #window.wm_withdraw()
  #tkMessageBox.showerror(title=title,message=msg, parent=window)  


if __name__ == "__main__":

  box("error","Error Mesagge") 


  ##window = Tk()
  ##window.wm_withdraw()

  #print window.geometry()

  #message at x:0,y:0
  #window.geometry("500x500+100+100")#remember its .geometry("WidthxHeight(+or-)X(+or-)Y")
  ##tkMessageBox.showerror(title="error",message="Error Message",parent=window)

  #centre screen message
  #window.geometry("1x1+"+str(window.winfo_screenwidth()/2)+"+"+str(window.winfo_screenheight()/2))
  #print window.geometry() 
  #tkMessageBox.showinfo(title="Greetings", message="Hello World!")


