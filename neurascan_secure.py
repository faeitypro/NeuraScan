import sys
import os

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))


#path libraries
sys.path.append(os.path.join(base_path, "libraries"))
sys.path.append(os.path.join(base_path, "libraries/py-cpuinfo-9.0.0"))
sys.path.append(os.path.join(base_path, "libraries/pycryptodome-3.23.0/lib"))
sys.path.append(os.path.join(base_path, "libraries/pycryptodome-3.23.0-cp313-cp313t-win_amd64"))
sys.path.append(os.path.join(base_path, "libraries/GPUtil-1.4.0/"))
#sys.path.append(os.path.join(base_path, "libraries/WMI-1.5.1"))
sys.path.append(os.path.join(base_path, "libraries/pywin32-311-cp313-cp313-win_amd64"))
sys.path.append(os.path.join(base_path, "libraries/requests-2.32.4/src"))
sys.path.append(os.path.join(base_path, "libraries/tkinter"))

#end path libraries


import platform
import subprocess
import psutil # type: ignore
from psutil import cpu_percent, virtual_memory # type: ignore
import cpuinfo # type: ignore
from cpuinfo import get_cpu_info# type: ignore
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#from Crypto.PublicKey import RSA  #a chech pour voir pourquoi ca ne marche pas
#from Crypto.Cipher import PKCS1_OAEP #a chech pour voir pourquoi ca ne marche pas
import base64
import json
from datetime import datetime
import time
import socket
import GPUtil # type: ignore
import re
import zlib
from tkinter import filedialog
import re
import random
import math

#------------------------------------------------------------------end-import--------------------------------------------------------------------
VERSION = "1.1"
#interface

#------------------------------------------------------------------interfaces-------------------------------------------------------------------


class NeuraScanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"NeuraScan V:{VERSION}") # nom de l'interface
        self.iconbitmap("icon.ico") #icon de l'app
        self.iconify() # a changer
        try:
            self.state('zoomed')  # pleine écran windows
        except:
            self.attributes('-fullscreen', True) #pleine écran linux ou mac
        
        
        
        #/////////////////////////////////////////////////zone global
        main_container = ttk.Frame(self, padding="5")
        main_container.pack(fill="both", expand=False)

        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill="x", pady=5)
        

        #///////////////////////////////////////////////////////////////////////////////////style boutton et conf notebook
        style = ttk.Style()
        style.configure("Button.TNotebook", foreground="red", background="greens")

        information_container = ttk.Frame(self, padding="5")
        information_container.pack(fill="both", expand=True)

        information_frame = ttk.Frame(information_container)
        information_frame.pack(fill="x", pady=5)
        information_frame.configure(style="BW.TNotebook")
        self.tab(information_frame=information_frame)
        
        #//////////////////////////////////////////////////////////////////////////////////////////conf notebook

        style = ttk.Style()
        style.configure("Button.TButton", background="purple", foreground="green", font=("Helvetica", 14, "bold"))

        # Boutons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        #ttk.Button(btn_frame, text="E-mail", command=self.mail, style="Button.TButton").pack(side=tk.LEFT, padx=5) #////// to setup mail sender
        ttk.Button(btn_frame, text="Save", command=self.save, style="Button.TButton").pack(side=tk.LEFT, padx=5)

        # Créer le label et stocker la référence
        self.clock_label = ttk.Label(btn_frame, font=("Arial", 12))
        self.clock_label.pack(side="right")

        # Démarrer la mise à jour de l'horloge
        self.update_clock()
        

    def update_clock(self):
        now = datetime.now().strftime('%H:%M:%S')
        self.clock_label.config(text=now)
        self.after(1000, self.update_clock)

    #def mail(self):
    #    messagebox.showinfo("Scan terminé", "L'analyse système est complète")
    def save(self):
        NAMEFILE = F"neurascan {datetime.now().strftime('%Y %m %d %HH %M')}.txt"
        file = open(f"report/{NAMEFILE}", "w")
        file.write(f"Neurascan V: {VERSION}\nOS : {platform.system()}\nComputer name : {platform.node()} \nAll user name :{psutil.users()}\n")#////////////////a finir //////////////////////////////////////////////////////////////////////////////////////////////////////////////
        file.close()
        messagebox.showinfo("save file","you have a new file in the report folder named neurascan.txt. we don't can add disk information")

    def tab(self, information_frame):
        TAB = ttk.Notebook(information_frame)
        #/////////////////////////////////////////////////////////
        AFrame = ttk.Frame(TAB) 
        tree = ttk.Treeview(AFrame,columns=("information","data"))
        tree.column("#0", width=0, stretch=False)
        tree.heading("information",text="Information")
        tree.heading("data",text="Data")
        tree.column("information")
        tree.column("data")
        tree.insert("", "end",values=("Os",platform.system()))
        tree.insert("", "end",values=("Computer name",platform.node()))
        tree.insert("", "end",values=("All user name",psutil.users()))
        tree.insert("", "end",values=("Os version", platform.version()))
        tree.insert("", "end",values=("Computer architecture", platform.machine()))
        tree.insert("", "end",values=("Processor", platform.processor()))
        tree.pack(fill=tk.BOTH,expand=True)
        
        #///////////////////////////////////////////////////////////////////////////
        
        BFrame = ttk.Frame(TAB)
        tree = ttk.Treeview(BFrame,columns=("information","data"))
        tree.column("#0", width=0, stretch=False)
        tree.heading("information",text="Information")
        tree.heading("data",text="Data")
        tree.column("information")
        tree.column("data")
        info = cpuinfo.get_cpu_info()
        if(info.get("vendor_id_raw", 'Inconnu') == "GenuineIntel"):
            tree.insert("", "end",values=("Label","intel"))
        elif(info.get("vendor_id_raw", 'Inconnu')== "AuthenticAMD" or info.get("vendor_id_raw", 'Inconnu')== "AMDisbetter!"):
            tree.insert("", "end",values=("Label","AMD"))
        else:
            tree.insert("", "end",values=("Label",info.get("vendor_id_raw", 'Inconnu')))    
        tree.insert("", "end",values=("CPU frequency (GHZ)",psutil.cpu_freq().current / (1000**1)))
        tree.insert("", "end",values=("CPU thread number",psutil.cpu_count()))
        tree.insert("", "end",values=("CPU bits",info.get("bits")))
        tree.pack(fill=tk.BOTH,expand=True)
        
        #///////////////////////////////////////////////////////////////////////////
        
        CFrame = ttk.Frame(TAB)
        tree = ttk.Treeview(CFrame,columns=("information","data"))
        tree.column("#0", width=0, stretch=False)
        tree.heading("information",text="Information")
        tree.heading("data",text="Data")
        tree.column("information")
        tree.column("data")
        virt = psutil.virtual_memory()
        swap = psutil.swap_memory()
        tree.insert("", "end",values=("Total",f"{virt.total / (1024**3):.2f} Go"))
        tree.insert("", "end",values=("Available",f"{virt.available / (1024**3):.2f} Go"))
        tree.insert("", "end",values=("Used", f"{virt.used / (1024**3):.2f} Go"))
        tree.pack(fill=tk.BOTH,expand=True)

        #///////////////////////////////////////////////////////////////////////////
        
        DFrame = ttk.Frame(TAB)
        tree = ttk.Treeview(DFrame,columns=("information","data"))
        tree.column("#0", width=0, stretch=False)
        tree.heading("information",text="Information")
        tree.heading("data",text="Data")
        tree.column("information")
        tree.column("data")
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            tree.insert("", "end",values=("GPU name", gpu.name))
            tree.insert("", "end",values=("GPU total memory", f"{gpu.memoryTotal} MB"))
            tree.insert("", "end",values=("GPU free space", f"{gpu.memoryFree} MB"))
            tree.insert("", "end",values=("GPU used space", f"{gpu.memoryUsed} MB"))
            tree.insert("", "end",values=("GPU temp", f"{gpu.temperature} °C"))
        tree.pack(fill=tk.BOTH,expand=True)
        
        #///////////////////////////////////////////////////////////////////////////
        
        EFrame = ttk.Frame(TAB)
        tree = ttk.Treeview(EFrame,columns=("disc letter","total space","used space","free space","label"))
        tree.column("#0", width=0, stretch=False)
        tree.heading("disc letter",text="Disc letter")
        tree.heading("total space",text="Total space")
        tree.heading("used space",text="Used space")
        tree.heading("free space",text="Free space")
        tree.heading("label",text="label")
        tree.column("disc letter")
        tree.column("total space")
        tree.column("used space")
        tree.column("free space")
        tree.column("label")
        tree.pack(fill=tk.BOTH,expand=True)
        part = psutil.disk_partitions()
        for partition in part:
            try:
                
                usage = psutil.disk_usage(partition.mountpoint)
                letter = partition.device
                total = f"{usage.total / (1024**3):.2f} Go"
                used = f"{usage.used / (1024**3):.2f} Go"
                free = f"{usage.free / (1024**3):.2f} Go"
                #label = wmi.WMI().Win32_DiskDrive().Index
                tree.insert("", "end", values=(letter, total, used, free))
            except PermissionError:
                tree.insert("","end",values=(f"{usage.total / (1024**3):.2f} Go", f"{usage.used / (1024**3):.2f} Go", f"{usage.free / (1024**3):.2f} Go"))
        
        #///////////////////////////////////////////////////////////////////////////
        
        PORFrame = ttk.Frame(TAB)
        tree = ttk.Treeview(PORFrame,columns=("information","data"))
        tree.column("#0", width=0, stretch=False)
        tree.heading("information",text="Information")
        tree.heading("data",text="Data")
        tree.column("information")
        tree.column("data")
        tree.insert("", "end",values=("Battery level",psutil.sensors_battery()))
        tree.pack(fill=tk.BOTH,expand=True)
        self.after(1000, self.tab)


        # Pack
        AFrame.pack(fill = tk.BOTH, expand = True)
        BFrame.pack(fill = tk.BOTH, expand = True)
        CFrame.pack(fill = tk.BOTH, expand = True)
        DFrame.pack(fill = tk.BOTH, expand = True)
        EFrame.pack(fill = tk.BOTH, expand = True)
        PORFrame.pack(fill = tk.BOTH, expand = True)
        TAB.pack(fill = tk.BOTH, expand = True)

        # Add Tabs
        TAB.add(AFrame, text = "system")
        TAB.add(BFrame, text = "CPU")
        TAB.add(CFrame, text = 'RAM')
        TAB.add(DFrame, text = 'GPU')
        TAB.add(EFrame, text = 'Storage')
        TAB.add(PORFrame, text= "portable computer")


if __name__ == "__main__":
    app = NeuraScanApp()
    app.mainloop()  


    #------------------------------------------------------------------end-interfaces--------------------------------------------------------------------
