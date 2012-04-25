import numpy


y1= numpy.fromfile('L:/software/apparatus3/seq/seqstxt/before_before.txt',dtype=float, sep=',')
y2= numpy.fromfile('L:/software/apparatus3/seq/seqstxt/before.txt',dtype=float, sep=',')

print y1.size, y2.size


f1 = open('L:/software/apparatus3/seq/seqstxt/before_before.txt','r')
f2 = open('L:/software/apparatus3/seq/seqstxt/before.txt','r')

fout = open('L:/software/apparatus3/seq/seqstxt/diffout.txt','w')

nchar=0

while 1:
        char1 = f1.read(1)
        char2 = f2.read(1)
        fout.write(char1)
        nchar = nchar + 1
        if not char1: break
        if char1 != char2: 
            print str(nchar), char1,char2
            print f1.read(1)+f1.read(1)+f1.read(1)+f1.read(1)+f1.read(1)+f1.read(1)+f1.read(1)+f1.read(1)
            break

f1.close()
f2.close()
fout.close()

