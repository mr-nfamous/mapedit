from widgets import *


def paste(*args):
    c.create_image(640, 640, image=p)
root = Tk()
but = Button(root, text='press', command=paste)
but.grid(row=1,column=0)
f = Frame(root, height=400, width=400)
c = Canvas(f, width=384,height=384,highlightthickness=0,border=0,bg='pink',
           scrollregion=(0,0,640,640))
vbar=Scrollbar(f, orient='vertical', command=c.yview)
hbar=Scrollbar(f, orient='horizontal',command=c.xview)
c.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
i=Image.open('9.png')
p=PhotoImage(i)
c.create_image(0,0,image=p)
f.grid(row=0)
c.grid(row=0, column=0)
vbar.grid(row=0,column=1,sticky='ns')
hbar.grid(row=1,column=0,sticky='ew')
root.mainloop()
