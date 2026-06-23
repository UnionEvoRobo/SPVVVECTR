import tkinter as tk

#Create main app window
root = tk.Tk()

#Window adjustment
root.title ("Tensegrity Example")
root.configure (background = "white")
root.minsize(200, 200)
root.maxsize(500, 500)
root.geometry("300x300+475+175")
#Windox size + x_cord + y_cord

#Create Labels
label1 = tk.Label(root, text="Hopefully the robot can vibrate")
label2 = tk.Label(root, text="Brrrrr", font=("Helvetica", 20))

#Update the label
label1.config (text="The robot has moved!")
label2.config (anchor="center")

#Show the label
label1.pack()
label2.pack()

#display image
image = tk.PhotoImage(file="spvvvectr.png").subsample(2)
label3 = tk.Label(root, image=image).pack(expand=True)
root.mainloop()