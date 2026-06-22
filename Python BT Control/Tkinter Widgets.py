def button_widget():
    import tkinter as tk

    root = tk.Tk()
    root.title("Tkinter Button")
    root.geometry("200x100")

    def on_click():
        label.config(text="Button clicked!")

    button = tk.Button(
        root,
        text="Click Me",
        command=on_click,
    )
    button.pack(padx=5, pady=5)

    # A helper label to show the result of the click
    label = tk.Label(root, text="Waiting for click...")
    label.pack(padx=5, pady=5)

    root.mainloop()

def entry_widget():
    import tkinter as tk

    root = tk.Tk()
    root.title("Tkinter Entry")

    def return_pressed(event):
        label.config(text=event.widget.get())

    entry = tk.Entry(root)
    entry.insert(0, "Enter your text")
    entry.bind("<Return>", return_pressed)
    entry.pack(padx=5, pady=5, fill="x")

    # A helper label to show the selected value
    label = tk.Label(root, text="Entry demo!")
    label.pack(padx=5, pady=5, fill="x")

    root.mainloop()

def scale_widget():
    import tkinter as tk

    root = tk.Tk()
    root.title("Tkinter Scale")
    root.geometry("200x80")

    def value_changed(event):
        label.config(text=event.widget.get())

    scale = tk.Scale(root, from_=0, to=500, orient="horizontal")
    scale.bind("<Motion>", value_changed)
    scale.pack(padx=5, pady=5, fill="x")

    # A helper label to show the selected value
    label = tk.Label(root, text="0")
    label.pack(padx=5, pady=5, fill="x")

    root.mainloop()

entry_widget()