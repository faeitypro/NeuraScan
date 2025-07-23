import sys
import os

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))


sys.path.append(os.path.join(base_path, "libraries"))
sys.path.append(os.path.join(base_path,"libraries/py-cpuinfo-9.0.0"))
sys.path.append(os.path.join(base_path,"libraries/pycryptodome-3.23.0/lib"))
sys.path.append(os.path.join(base_path,"libraries/pycryptodome-3.23.0-cp313-cp313t-win_amd64"))
sys.path.append(os.path.join(base_path,"libraries"))
sys.path.append(os.path.join(base_path,"libraries/GPUtil-1.4.0/"))
sys.path.append(os.path.join(base_path,"libraries/WMI-1.5.1"))
sys.path.append(os.path.join(base_path,"libraries/pywin32-311-cp313-cp313-win_amd64"))

import platform
import subprocess
import psutil # type: ignore
from psutil import cpu_percent, virtual_memory # type: ignore
import cpuinfo # type: ignore
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#from Crypto.PublicKey import RSA
#from Crypto.Cipher import PKCS1_OAEP
import base64
import json
from datetime import datetime
import socket
import GPUtil
import re
import zlib
from tkinter import filedialog
import _wmi
import random
import math


VERSION = "1.0.0"


print("hello world")

def get_all_info():
    return {
        'Système': get_system_info(),
        'CPU': get_cpu_info(),
        'RAM': get_ram_info(),
        'Disques': get_disk_info(),
        'GPU': get_gpu_info(),
        'Numéros de série': get_serial_numbers(),
        'Températures & Ventilateurs': get_temperatures_and_fans(),
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Version': VERSION
    }

def get_system_info():
    """Récupère les infos basiques du système"""
    return {
        'Système': platform.system(),
        'Nom utilisateur': platform.node(),
        'Version': platform.version(),
        'Machine': platform.machine(),
        'Processeur': platform.processor(),
        'Version Python': platform.python_version(),
    }

def get_cpu_info():
    """récupère les info du pross"""
    return{
        'Marque': info.get('brand_raw', 'Inconnu'),
        'Architecture': info.get('arch_string_raw', 'Inconnu'),
        'Fréquence': f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else 'Inconnu',
        'Cœurs physiques': psutil.cpu_count(logical=False),
        'Cœurs logiques': psutil.cpu_count(logical=True),
        'Utilisation': f"{psutil.cpu_percent()}%"
    }

def get_ram_info():
    virt = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        'Total': f"{virt.total / (1024**3):.2f} Go",
        'Disponible': f"{virt.available / (1024**3):.2f} Go",
        'Utilisée': f"{virt.used / (1024**3):.2f} Go",
        'Pourcentage utilisé': f"{virt.percent}%"
    }

def get_disk_info():
    """Récupère les infos des disques"""
    disks = []
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        disks.append({
            'Device': part.device,
            'Point de montage': part.mountpoint,
            'Type': part.fstype,
            'Total': f"{usage.total / (1024**3):.2f} Go",
            'Utilisé': f"{usage.used / (1024**3):.2f} Go",
            'Libre': f"{usage.free / (1024**3):.2f} Go"
        })
    return disks

def get_gpu_info():
    try:
        gpus = GPUtil.getGPUs()
        return [{
            'ID': gpu.id,
            'Nom': gpu.name,
            'Charge': f"{gpu.load*100}%",
            'Mémoire libre': f"{gpu.memoryFree} MB",
            'Mémoire utilisée': f"{gpu.memoryUsed} MB",
            'Mémoire totale': f"{gpu.memoryTotal} MB",
            'Température': f"{gpu.temperature} °C"
        } for gpu in gpus]
    except:
        return None



def get_serial_numbers():
    """Récupère les numéros de série des composants"""
    serials = {}
    
    # CPU
    if platform.system() == 'Windows':
        c = _wmi.WMI()
        for processor in c.Win32_Processor():
            serials['CPU'] = processor.ProcessorId.strip()
    elif platform.system() == 'Linux':
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'serial' in line.lower():
                        serials['CPU'] = line.split(':')[1].strip()
        except:
            pass
    
    # Carte mère
    if platform.system() == 'Windows':
        c = _wmi.WMI()
        for board in c.Win32_BaseBoard():
            serials['Carte mère'] = board.SerialNumber.strip()
    elif platform.system() == 'Linux':
        try:
            result = subprocess.run(['dmidecode', '-t', 'baseboard'], 
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Serial Number' in line:
                    serials['Carte mère'] = line.split(':')[1].strip()
        except:
            pass
    
    # Disques
    if platform.system() == 'Windows':
        c = _wmi.WMI()
        for disk in c.Win32_DiskDrive():
            serials[f'Disque {disk.Index}'] = disk.SerialNumber.strip()
    elif platform.system() == 'Linux':
        try:
            for disk in os.listdir('/sys/block'):
                if disk.startswith(('sd', 'nvme')):
                    try:
                        with open(f'/sys/block/{disk}/device/serial', 'r') as f:
                            serials[f'Disque {disk}'] = f.read().strip()
                    except:
                        pass
        except:
            pass
    
    return serials if serials else None

def get_temperatures_and_fans():
    """Récupère les températures et les informations des ventilateurs"""
    temp_info = {}
    fan_info = {}
    try:
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            temp_info[name] = [
                {
                    'label': entry.label or '',
                    'current': entry.current,
                    'high': entry.high,
                    'critical': entry.critical
                } for entry in entries
            ]
    except Exception as e:
        temp_info['Erreur'] = str(e)
    try:
        fans = psutil.sensors_fans()
        for name, entries in fans.items():
            fan_info[name] = [
                {
                    'label': entry.label or '',
                    'current': entry.current
                } for entry in entries
            ]
    except Exception as e:
        fan_info['Erreur'] = str(e)
    return {'Températures': temp_info, 'Ventilateurs': fan_info}



#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



class NeuraScanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NeuraScan")
        #self.iconbitmap("icone.ico")  # remplace si nécessaire
        try:
            self.state('zoomed')  # Windows
        except:
            self.attributes('-fullscreen', True)
        self.configure(bg="#cfeaf2")  # fond clair comme l'image

        self.canvas = tk.Canvas(self, width=800, height=600, bg="#cfeaf2", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.create_text(400, 40, text="NeuraScan", fill="#3a3a3a", font=("Segoe UI", 30, "bold"))
        self.draw_brain(center_x= 300, center_y= 400)
        self.demi_cercle(500, 300, 200, 150, "top", "purple", "purple", 2)

    def draw_brain(self, center_x, center_y):
        # Forme du cerveau relative au centre (0,0)
        brain_outline_relative = [
            (0, 100), (-110, -50), (-100, -80), (-90, -100),
            (-60, -120), (-30, -130), (10, -120), (50, -130),
            (90, -120), (110, -90), (120, -60), (110, -30),
            (130, 10), (130, 50), (110, 80), (90, 110),
            (70, 130), (50, 150), (30, 160), (10, 150),
            (-10, 130), (-30, 110), (-50, 80), (-60, 50),
            (-70, 20)
        ]
        
        # Translate les coordonnées pour centrer sur le point donné
        brain_outline = [(x + center_x, y + center_y) for x, y in brain_outline_relative]
        
        self.canvas.create_polygon(brain_outline, fill="#5e6ad2", outline="#3f4bb8", 
                                 width=3, smooth=True)
        
    
        # Génère des nœuds à l’intérieur de la forme
        nodes = []
        for _ in range(30):
            while True:
                x = random.randint(310, 470)
                y = random.randint(110, 360)
                if self.point_in_brain(x, y):
                    nodes.append((x, y))
                    break

        # Dessine les connexions
        for i, (x1, y1) in enumerate(nodes):
            for j in range(i + 1, len(nodes)):
                x2, y2 = nodes[j]
                if self.distance(x1, y1, x2, y2) < 70:
                    self.canvas.create_line(x1, y1, x2, y2, fill="#4e4e9c", width=1)

        # Dessine les nœuds
        for x, y in nodes:
            self.canvas.create_oval(x-4, y-4, x+4, y+4, fill="#88c0d0", outline="#2e3440")
    def demi_cercle(self, x, y, width=200, height=150, orientation="top", fill_color="purple", outline_color="purple", line_width=2):
    # Crée une demi-ellipse (Arc + ligne de base)
    # Calcul des coordonnées du rectangle englobant
        x1, y1 = x - width//2, y - height//2
        x2, y2 = x + width//2, y + height//2
    
    # Définition des angles et lignes selon l'orientation
        if orientation == "top":
            start, extent = 0, 180
            line_coords = (x1, y, x2, y)
        elif orientation == "bottom":
            start, extent = 180, 180
            line_coords = (x1, y, x2, y)
        elif orientation == "right":
            start, extent = 270, 180
            line_coords = (x, y1, x, y2)
        elif orientation == "left":
            start, extent = 90, 180
            line_coords = (x, y1, x, y2)
        else:
            start, extent = 0, 180
            line_coords = (x1, y, x2, y)
        
    # Dessine l'arc avec remplissage
        arc = self.canvas.create_arc(x1, y1, x2, y2, 
                                    start=start, extent=extent, 
                                    fill=fill_color, outline=outline_color, 
                                    width=line_width, style="pieslice")
        
        # Dessine la ligne de base
        line = self.canvas.create_line(line_coords[0], line_coords[1], 
                                    line_coords[2], line_coords[3], 
                                    fill=outline_color, width=line_width)
        
        return arc, line


    def point_in_brain(self, x, y):
        # Délimitation simplifiée du cerveau pour filtrer les points
        return 310 <= x <= 470 and 110 <= y <= 370

    def distance(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

if __name__ == "__main__":
    app = NeuraScanApp()
    app.mainloop()
