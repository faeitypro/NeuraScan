import os
import platform
import subprocess
import psutil
from psutil import cpu_percent, virtual_memory
import cpuinfo
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import json
from datetime import datetime
import socket
import GPUtil
import re
import zlib
from tkinter import filedialog
import wmi

# Génération des clés RSA (à faire une seule fois)
# from Crypto.PublicKey import RSA
# key = RSA.generate(1024)
# private_key = key.export_key()
# with open("config.key", "wb") as key_file:
#     key_file.write(private_key)
# public_key = key.publickey().export_key()

VERSION = "1.0.0"

# Chargement de la clé RSA
def load_rsa_key():
    try:
        with open("config.key", "rb") as key_file:
            return RSA.import_key(key_file.read())
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur de chargement de la clé RSA:\n{str(e)}")
        return None

def get_all_info():
    return {
        'Système': get_system_info(),
        'CPU': get_cpu_info(),
        'RAM': get_ram_info(),
        'Disques': get_disk_info(),
        'GPU': get_gpu_info(),
        'Numéros de série': get_serial_numbers(),
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
    info = cpuinfo.get_cpu_info()
    return {
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
        c = wmi.WMI()
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
        c = wmi.WMI()
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
        c = wmi.WMI()
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

# Fonction d'envoi d'email
def send_email(info, recipient_email=None):
    try:
        private_key = load_rsa_key()
        if not private_key:
            return False
        
        # Décryptage des informations SMTP
        cipher = PKCS1_OAEP.new(private_key)
        smtp_config = {
            'sender': cipher.decrypt(base64.b64decode(SMTP_SENDER)).decode(),
            'password': cipher.decrypt(base64.b64decode(SMTP_PASSWORD)).decode(),
            'server': cipher.decrypt(base64.b64decode(SMTP_SERVER)).decode(),
            'port': int(cipher.decrypt(base64.b64decode(SMTP_PORT)).decode())
        }
        
        # Préparation du message
        msg = MIMEMultipart()
        msg['From'] = smtp_config['sender']
        msg['To'] = recipient_email if recipient_email else smtp_config['sender']
        msg['Subject'] = f"NeurAScan Rapport - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Corps du message
        body = f"Rapport NeurAScan v{VERSION}\n\n"
        body += f"Date: {info['Date']}\n"
        body += f"Système: {info['Système']['Système']} {info['Système']['Version']}\n"
        body += f"Processeur: {info['CPU']['Marque']}\n"
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Pièce jointe JSON
        attachment = MIMEText(json.dumps(info, indent=4), 'plain')
        attachment.add_header('Content-Disposition', 'attachment', 
                           filename=f"neurascan_report_{info['Date'].replace(':', '-')}.json")
        msg.attach(attachment)
        
        # Envoi
        with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port']) as server:
            server.login(smtp_config['sender'], smtp_config['password'])
            server.send_message(msg)
            return True
            
    except Exception as e:
        messagebox.showerror("Erreur", f"Échec de l'envoi:\n{str(e)}")
        return False

# Interface graphique
class NeurAScanApp:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title(f"NeurAScan v{VERSION}")
        self.root.geometry("1000x700")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Scanner", command=self.scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Envoyer par email", command=self.send_email).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Sauvegarder", command=self.save_report).pack(side=tk.LEFT, padx=5)
        
        # Notebook (onglets)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Création des onglets
        self.create_tabs()
        
    def create_tabs(self):
        """Crée les onglets pour chaque catégorie d'information"""
        self.tabs = {
            'Système': ttk.Frame(self.notebook),
            'CPU': ttk.Frame(self.notebook),
            'RAM': ttk.Frame(self.notebook),
            'Disques': ttk.Frame(self.notebook),
            'GPU': ttk.Frame(self.notebook),
            'Numéros de série': ttk.Frame(self.notebook)
        }
        
        for name, tab in self.tabs.items():
            self.notebook.add(tab, text=name)
            
            # Treeview pour afficher les données
            tree = ttk.Treeview(tab)
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Scrollbars
            yscroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=tree.yview)
            yscroll.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=yscroll.set)
            
            # Configuration des colonnes
            if name == 'Disques':
                tree['columns'] = ('Device', 'Point de montage', 'Type', 'Total', 'Utilisé', 'Libre')
                for col in tree['columns']:
                    tree.heading(col, text=col)
                    tree.column(col, width=100)
            elif name == 'Numéros de série':
                tree['columns'] = ('Composant', 'Numéro')
                for col in tree['columns']:
                    tree.heading(col, text=col)
                    tree.column(col, width=200)
            else:
                tree['columns'] = ('Propriété', 'Valeur')
                for col in tree['columns']:
                    tree.heading(col, text=col)
                    tree.column(col, width=150)
    
    def scan(self):
        """Lance le scan du système"""
        info = get_all_info()
        self.display_info(info)
        messagebox.showinfo("Scan terminé", "L'analyse système est complète")
    
    def display_info(self, info):
        """Affiche les informations dans les onglets"""
        for tab_name in self.tabs:
            tree = self.notebook.nametowidget(self.tabs[tab_name].winfo_children()[0])
            tree.delete(*tree.get_children())
            
            if tab_name == 'Système':
                for k, v in info['Système'].items():
                    tree.insert('', tk.END, values=(k, v))
            elif tab_name == 'CPU':
                for k, v in info['CPU'].items():
                    tree.insert('', tk.END, values=(k, v))
            elif tab_name == 'RAM':
                for k, v in info['RAM'].items():
                    tree.insert('', tk.END, values=(k, v))
            elif tab_name == 'Disques':
                for disk in info['Disques']:
                    tree.insert('', tk.END, values=(
                        disk['Device'],
                        disk['Point de montage'],
                        disk['Type'],
                        disk['Total'],
                        disk['Utilisé'],
                        disk['Libre']
                    ))
            elif tab_name == 'GPU' and info['GPU']:
                for gpu in info['GPU']:
                    for k, v in gpu.items():
                        tree.insert('', tk.END, values=(k, v))
            elif tab_name == 'Numéros de série' and info['Numéros de série']:
                for k, v in info['Numéros de série'].items():
                    tree.insert('', tk.END, values=(k, v))
    
    def send_email(self):
        """Envoie le rapport par email"""
        if not hasattr(self, 'last_scan_info'):
            messagebox.showwarning("Aucun scan", "Veuillez d'abord scanner le système")
            return
            
        # Fenêtre pour entrer l'email
        email_dialog = tk.Toplevel(self.root)
        email_dialog.title("Envoyer le rapport")
        email_dialog.geometry("400x200")
        
        ttk.Label(email_dialog, text="Adresse email du destinataire:").pack(pady=10)
        
        email_var = tk.StringVar()
        email_entry = ttk.Entry(email_dialog, textvariable=email_var, width=40)
        email_entry.pack(pady=5)
        
        def send():
            if send_email(self.last_scan_info, email_var.get()):
                messagebox.showinfo("Succès", "Rapport envoyé avec succès")
            email_dialog.destroy()
        
        ttk.Button(email_dialog, text="Envoyer", command=send).pack(pady=10)
    
    def save_report(self):
        """Sauvegarde le rapport dans un fichier"""
        if not hasattr(self, 'last_scan_info'):
            messagebox.showwarning("Aucun scan", "Veuillez d'abord scanner le système")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json")],
            initialfile=f"neurascan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.last_scan_info, f, indent=4)
                messagebox.showinfo("Succès", f"Rapport sauvegardé sous:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de la sauvegarde:\n{str(e)}")

# Configuration SMTP cryptée (générée avec generate_smtp_config.py)
SMTP_SERVER = b'gxu1X8fXABZB6QKzvbXMS8EvKSfL+sTFBMn+hlPBGY2gglbGEIbxl3Je/VU6z9RLvT2wkwuYGWqwCt+xRI5YYxsaBnJLDTnC3xmeuMFEPN6FgwrC7S2/KMKq5JaA2scCDIQAziu8ntd54oIAyl96ZePtu7670JbGo389ZeGIrWw='
SMTP_PORT = b'd2lvK8lX322L2vwQTcU6sgdQXhE6N5Rzz9fDDiQMhEJ+U8HyCgmiIQqlFgBujorp1wnK3pJ8RoBpe3yhGPAFdiQGCvAkOQ+6Uy8gV9t2RfHB8PYu6LclHFaJC2kwrQUWRIK/O7rFk9OH6SaWOU1pI2xmcW8NYLFgZK1iuRJiWtg='
SMTP_SENDER = b'Xx208Pn4eal3GVCxsKxVJhySDhfWmSyY09aL6JhW16iHZ6QOrVj8LRGLg7TLK1w14yG3X0RIK3fjfA/cnxdiXnPjugQ3TcEyK25u3flmH/Px651EB/+Rw+pZZu7/v7wUcU3W/WpDHKxOD+gfTbFWK+6WPho6928RCwlG+z5gqbQ='
SMTP_PASSWORD = b'CrgudYwblu7Wk9jIApQmw26mmWbiaEkcsuVSAbaBX4oroDhzuezah6LHv4Jxthvl0ZlyY+W/shJiqa5u/VoJ9+o+sz5T3DId4eR79nQjzLl3alXVjYbpcPOY27PMvvGzXl1OxQO1hzM4w2utYuUgsNIzpFKgE9rPmfcxZXbPlfs='

if __name__ == "__main__":
    root = tk.Tk()
    app = NeurAScanApp(root)
    root.mainloop()