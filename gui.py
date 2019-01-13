from tkinter import *
from tkinter import font
from tkinter import ttk
from petadmin import *
from confirm import *
from winioctlcon import F3_120M_512

class CrowbankApp():
    font = font.Font(family='Helvetica', size=24)

    def __init__(self, root):
        for l in self.labels:
            label = Label(root, padx=6, pady=6, text=l['title'], font=self.font)
            label.grid(row=l['row'], column=l['column'], sticky=l['sticky'])
        
        for b in self.buttons:
            pass


class PaymentApp(CrowbankApp):
    labels = {
        'bk_no' : {
            'title' : 'Booking #',
            'row' : 0,
            'column' : 0,
            'sticky' : 'e'},
        'customer' : {
            'title' : 'Customer',
            'row' : 1,
            'column' : 0,
            'sticky' : 'e'},
        'pets' : {
            'title' : 'Pets',
            'row' : 2,
            'column' : 0,
            'sticky' : 'e'},
        'start' : {
            'title' : 'Start',
            'row' : 3,
            'column' : 0,
            'sticky' : 'e'},
        'end' : {
            'title' : 'End',
            'row' : 3,
            'column' : 2,
            'sticky' : 'e'},
        'gross' : {
            'title' : 'Gross',
            'row' : 4,
            'column' : 0,
            'sticky' : 'e'},
        'deposit' : {
            'title' : 'Deposit',
            'row' : 5,
            'column' : 0,
            'sticky' : 'e'},
        'pay_type' : {
            'title' : 'Payment Type',
            'row' : 5,
            'column' : 2,
            'sticky' : 'e'},
        'pay_date' : {
            'title' : 'Payment Date',
            'row' : 6,
            'column' : 0,
            'sticky' : 'e'}
        }
    buttons = {
        'review' : {
            'title' : 'Review Confirmation',
            'row' : 7,
            'column' : 0,
            'sticky' : 'ew'}
        }
    
    entries = {
        'bk_no' : {
            'row' : 0,
            'column' : 1}
        }
    pass

root = Tk()
pa = PetAdmin(env)

# root.title("Crowbank Manager")
# frame = Frame(root, )

import tkinter as tk
from tkinter import ttk

style = ttk.Style(root)
style.configure('lefttab.TNotebook', tabposition='wn')

notebook = ttk.Notebook(root, style='lefttab.TNotebook')

f_payment = tk.Frame(notebook, padx=10, pady=10)
f_deposit = tk.Frame(notebook, padx=10, pady=10)
f_clockdata = tk.Frame(notebook, padx=10, pady=10)

font = font.Font(family='Helvetica', size=24)

notebook.add(f_payment, text='Deposit')
notebook.add(f_deposit, text='Confirmation')
notebook.add(f_clockdata, text='Clock Data')

notebook.grid(row=0, column=0, sticky="nw")

payment_label_texts = ['Booking #', 'Customer', 'Pets', 'Start', 'End', 'Gross', 'Deposit', 'Payment Type', 'Payment Date']
payment_labels = []
for t in payment_label_texts:
    payment_labels.append(Label(f_payment, padx=6, pady=6, text=t, font=font))
    
status_label = Label(f_payment, padx=6, pady=10, text="Ready", bg="yellow", font=font)

bk_no = IntVar()
booking_number_field = Entry(f_payment, width=10, font=font, bg='yellow')

booking_value_labels = {'customer' : Label(f_payment, bk='yellow', font=font),
                        'pets' : Label(f_payment, bk='yellow', font=font),
                        }

def clicked():
    status_label.configure(text="Payment Processed")

def load_booking(event):
    bk_no = booking_number_field.get()
    booking = pa.bookings.get(bk_no)

booking_number_field.bind('<Enter>', load_booking)
btn = Button(f_payment, text="Enter Payment", command=clicked, font=font)

payment_labels[0].grid(row=0, column=0, sticky='e')
payment_labels[1].grid(row=1, column=0, sticky='e')
payment_labels[2].grid(row=2, column=0, sticky='e')
payment_labels[3].grid(row=3, column=0, sticky='e')
payment_labels[4].grid(row=3, column=2, sticky='e')
payment_labels[5].grid(row=4, column=0, sticky='e')
payment_labels[6].grid(row=5, column=0, sticky='e')
payment_labels[7].grid(row=5, column=2, sticky='e')
payment_labels[8].grid(row=6, column=0, sticky='e')
                            
booking_number_field.grid(row=0, column=1, sticky='w')

btn.grid(row=7, column=0)
status_label.grid(row=8, columnspan=8, sticky="ew")



root.mainloop()