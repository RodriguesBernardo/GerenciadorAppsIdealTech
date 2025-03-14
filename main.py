import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from ttkthemes import ThemedTk
import requests
import subprocess
import os
import ctypes
import sys
from threading import Thread, Event
import time
import platform
import winreg
import psutil
import GPUtil
import logging
import wmi
import webbrowser
import time
import webbrowser
import wmi
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup

# Variáveis globais
root = None
progress_var = None
progress_label = None
time_label = None
cancel_event = None
current_program = None
is_notebook = None
installation_in_progress = False

logging.basicConfig(filename='log do instalador.txt', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PROGRAM_URLS = {


# URLs dos programas (dependendo da versão do Windows)
    "Windows 10": {
        "Chrome": "https://dl.google.com/chrome/install/latest/chrome_installer.exe",
        "Firefox": "https://download.mozilla.org/?product=firefox-latest&os=win&lang=pt-BR",
        "WinRAR": "https://www.win-rar.com/fileadmin/winrar-versions/winrar/winrar-x64-624br.exe",  # WinRAR 6.24 (64-bit)
        "AnyDesk": "https://download.anydesk.com/AnyDesk.exe",  # AnyDesk
        "K-Lite Codecs": "https://files3.codecguide.com/K-Lite_Codec_Pack_1790_Basic.exe",  # K-Lite Codecs Basic
        "Adobe Reader": "https://admdownload.adobe.com/rdcm/installers/live/readerdc64_ha_crd_install.exe",
        "Avast": "https://files.avast.com/iavs9x/avast_free_antivirus_setup_offline.exe",  # Avast Free Antivirus (Offline Installer)
        ".NET Framework": "https://go.microsoft.com/fwlink/?linkid=2088631",  # .NET Framework 4.8
        # Programas opcionais
        "Steam": "https://cdn.cloudflare.steamstatic.com/client/installer/SteamSetup.exe",
        "Spotify": "https://download.scdn.co/SpotifySetup.exe",
        # "VLC Media Player": "https://get.videolan.org/vlc/last/win64/vlc-3.0.18-win64.exe",
    },
    "Windows 11": {
        "Chrome": "https://dl.google.com/chrome/install/latest/chrome_installer.exe",
        "Firefox": "https://download.mozilla.org/?product=firefox-latest&os=win&lang=pt-BR",
        "WinRAR": "https://www.win-rar.com/fileadmin/winrar-versions/winrar/winrar-x64-624br.exe",  # WinRAR 6.24 (64-bit)
        "AnyDesk": "https://download.anydesk.com/AnyDesk.exe",  # AnyDesk
        "K-Lite Codecs": "https://files3.codecguide.com/K-Lite_Codec_Pack_1790_Basic.exe",  # K-Lite Codecs Basic
        "Adobe Reader": "https://admdownload.adobe.com/rdcm/installers/live/readerdc64_ha_crd_install.exe",
        "Avast": "https://files.avast.com/iavs9x/avast_free_antivirus_setup_offline.exe",  # Avast Free Antivirus (Offline Installer)
        ".NET Framework": "https://go.microsoft.com/fwlink/?linkid=2088631",  # .NET Framework 4.8
        # Programas opcionais
        "Steam": "https://cdn.cloudflare.steamstatic.com/client/installer/SteamSetup.exe",
        "Spotify": "https://download.scdn.co/SpotifySetup.exe",
        # "VLC Media Player": "https://get.videolan.org/vlc/last/win64/vlc-3.0.18-win64.exe",
    },
}

def detectar_placa_video():
    """Detecta a placa de vídeo instalada no sistema."""
    c = wmi.WMI()
    placas_video = []

    for dispositivo in c.Win32_VideoController():
        placas_video.append(dispositivo.Name)

    return placas_video

def obter_driver_nvidia(modelo):
    """Obtém o link do driver mais recente para uma placa NVIDIA."""
    url = "https://www.nvidia.com/Download/processFind.aspx"
    params = {
        "psid": "123",  # Substitua pelo PSID correto, se disponível
        "pfid": "456",  # Substitua pelo PFID correto, se disponível
        "osid": "57",   # Windows 10 64-bit (ajuste conforme necessário)
        "lid": "1",     # Idioma: Inglês
        "whql": "1",    # WHQL Certified
        "lang": "en-us",
        "ctk": "0"
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        link_driver = soup.find("a", {"id": "lnkDownload"})
        if link_driver:
            return link_driver["href"]
    return None

def obter_driver_amd(modelo):
    """Obtém o link do driver mais recente para uma placa AMD."""
    url = f"https://www.amd.com/en/support/search?query={modelo}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        link_driver = soup.find("a", {"class": "download-link"})
        if link_driver:
            return link_driver["href"]
    return None

def abrir_site_drivers():
    """Abre o site de drivers da NVIDIA ou AMD com base na placa de vídeo detectada."""
    placas_video = detectar_placa_video()

    if not placas_video:
        messagebox.showinfo("Info", "Nenhuma placa de vídeo detectada.")
        return

    for placa in placas_video:
        if "NVIDIA" in placa:
            modelo = placa.split("NVIDIA")[-1].strip()
            driver_url = obter_driver_nvidia(modelo)
            if driver_url:
                webbrowser.open(driver_url)
            else:
                webbrowser.open("https://www.nvidia.com/Download/index.aspx")
            break
        elif "AMD" in placa or "Radeon" in placa:
            modelo = placa.split("AMD")[-1].strip()
            driver_url = obter_driver_amd(modelo)
            if driver_url:
                webbrowser.open(driver_url)
            else:
                webbrowser.open("https://www.amd.com/en/support")
            break
    else:
        messagebox.showinfo("Info", "Nenhum link de driver disponível para a placa de vídeo detectada.")

def obter_info_processador():
    try:
        import wmi
        c = wmi.WMI()
        for processador in c.Win32_Processor():
            return processador.Name.strip()
    except Exception as e:
        logging.error(f"Erro ao obter informações do processador: {e}")
        return platform.processor()  

def obter_info_memoria():
    """Retorna informações sobre a memória RAM."""
    memoria = psutil.virtual_memory()
    return f"Total: {memoria.total / 1024 / 1024 / 1024:.2f} GB, Disponível: {memoria.available / 1024 / 1024 / 1024:.2f} GB"

def obter_velocidade_memoria():
    """Retorna a velocidade da memória RAM (se disponível)."""
    try:
        c = wmi.WMI()
        for mem in c.Win32_PhysicalMemory():
            return f"{mem.Speed} MHz"
    except Exception:
        return "Velocidade da memória não detectada"

def obter_info_placa_video():
    """Retorna informações sobre a placa de vídeo."""
    gpus = GPUtil.getGPUs()
    if len(gpus) > 0:
        return gpus[0].name
    else:
        return "Nenhuma placa de vídeo detectada"

def exibir_configuracoes():
    """Exibe as configurações do PC em uma nova janela."""
    config_window = tk.Toplevel(root)
    config_window.title("Configurações do PC")
    config_window.geometry("400x300")

    # Exibir informações do sistema operacional
    windows_version = get_windows_version()
    ttk.Label(config_window, text=f"Sistema Operacional: {windows_version}").pack(pady=5)

    # Exibir informações do processador
    processador = obter_info_processador()
    ttk.Label(config_window, text=f"Processador: {processador}").pack(pady=5)

    # Exibir informações da memória RAM
    memoria = obter_info_memoria()
    ttk.Label(config_window, text=f"Memória RAM: {memoria}").pack(pady=5)

    # Exibir velocidade da memória RAM
    velocidade_memoria = obter_velocidade_memoria()
    ttk.Label(config_window, text=f"Velocidade da Memória: {velocidade_memoria}").pack(pady=5)

    # Exibir informações da placa de vídeo
    placa_video = obter_info_placa_video()
    ttk.Label(config_window, text=f"Placa de Vídeo: {placa_video}").pack(pady=5)

def get_windows_version():
    """Retorna a versão do Windows (10 ou 11)."""
    version = platform.version()
    if "10" in version:
        return "Windows 10"
    elif "11" in version:
        return "Windows 11"
    else:
        return "Windows Desconhecido"

def is_dotnet_installed():
    """Verifica se o .NET Framework 4.8 ou superior está instalado."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full")
        release = winreg.QueryValueEx(key, "Release")[0]
        winreg.CloseKey(key)
        return release >= 528040
    except Exception:
        return False

def is_program_installed(program_name):
    """Verifica se um programa já está instalado."""
    try:
        if program_name == "Chrome":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
            winreg.CloseKey(key)
            return True
        elif program_name == "Firefox":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Mozilla\Mozilla Firefox")
            winreg.CloseKey(key)
            return True
        elif program_name == "Adobe Reader":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Adobe\Acrobat Reader")
            winreg.CloseKey(key)
            return True
        elif program_name == "WinRAR":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WinRAR")
            winreg.CloseKey(key)
            return True
        elif program_name == "AnyDesk":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AnyDesk")
            winreg.CloseKey(key)
            return True
        elif program_name == "Avast":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Avast Software")
            winreg.CloseKey(key)
            return True
        elif program_name == "K-Lite Codecs":
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\KLCodecPack")
            winreg.CloseKey(key)
            return True
    except FileNotFoundError:
        return False
    return False

def install_dotnet_framework():
    """Instala o .NET Framework se não estiver instalado."""
    if is_dotnet_installed():
        messagebox.showinfo(".NET Framework", "O .NET Framework já está instalado.")
        return

    dotnet_url = PROGRAM_URLS[get_windows_version()][".NET Framework"]
    destination = os.path.join(os.getcwd(), "dotnet48.exe")

    if download_file(dotnet_url, destination, update_progress):
        try:
            subprocess.run([destination, "/q", "/norestart"], check=True)
            messagebox.showinfo("Sucesso", ".NET Framework instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Erro ao instalar o .NET Framework: {e}")
        finally:
            if os.path.exists(destination):
                os.remove(destination)

def download_file(url, destination, progress_callback=None):
    """Baixa um arquivo da internet com barra de progresso."""
    global cancel_event
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0
        start_time = time.time()

        with open(destination, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if cancel_event.is_set():
                    return False
                file.write(chunk)
                downloaded_size += len(chunk)
                if progress_callback:
                    elapsed_time = time.time() - start_time
                    progress_callback(downloaded_size, total_size, elapsed_time)
        return True
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao baixar o arquivo: {e}")
        return False

def install_program(installer_path, program):
    """Instala um programa a partir do caminho do instalador."""
    try:
        if not os.path.exists(installer_path):
            raise FileNotFoundError(f"Arquivo {installer_path} não encontrado.")
        if os.path.getsize(installer_path) == 0:
            raise ValueError(f"Arquivo {installer_path} está vazio ou corrompido.")

        # Verificar se a instalacao silenciosa foi selecionada
        if programas_silenciosos[program].get():
            if installer_path.endswith(".exe"):
                subprocess.run([installer_path, "/S", "/quiet"], check=True)
            elif installer_path.endswith(".msi"):
                subprocess.run(["msiexec", "/i", installer_path, "/quiet"], check=True)
            else:
                subprocess.run([installer_path], check=True)
        else:
            subprocess.run([installer_path], check=True)

        messagebox.showinfo("Sucesso", f"{program} instalado com sucesso!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erro", f"Erro ao instalar {program}: {e}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar o arquivo: {e}")
        
def ativar_net_framework_3_5():
    try:
        logging.info("Verificando o status do .NET Framework 3.5...")
        resultado = subprocess.run(
            ["dism", "/online", "/get-features", "/format:table"],
            capture_output=True, text=True, check=True
        )

        if "NetFx3 | Enabled" in resultado.stdout:
            logging.info(".NET Framework 3.5 já está ativado. Nenhuma ação necessária.")
            return

        logging.info("Ativando o .NET Framework 3.5...")
        subprocess.run(
            ["dism", "/online", "/enable-feature", "/featurename:NetFx3", "/all"],
            check=True
        )
        logging.info(".NET Framework 3.5 ativado com sucesso.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao ativar o .NET Framework 3.5: {e}")
        raise

def configure_windows(progress_bar, progress_label, configure_status_label):
    try:
        configure_status_label.config(text="Iniciando configuração do Windows...", foreground="blue")
        progress_bar["value"] = 0
        root.update()

        configure_status_label.config(text="Desativando suspensão e desligamento da tela...")
        progress_label.config(text="Desativando suspensão e desligamento da tela...")
        os.system("powercfg /change standby-timeout-ac 0")
        os.system("powercfg /change monitor-timeout-ac 0")
        progress_bar["value"] = 10
        root.update()
        time.sleep(1)

        configure_status_label.config(text="Desativando notificações do UAC...")
        progress_label.config(text="Desativando notificações do UAC...")
        subprocess.run(["reg", "add", "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", 
                        "/v", "EnableLUA", "/t", "REG_DWORD", "/d", "0", "/f"], check=True)
        logging.info('Desativado notificações do UAC!')
        progress_bar["value"] = 20
        root.update()
        time.sleep(1)

        configure_status_label.config(text="Desativando todas as notificações de Segurança e Manutenção...")
        progress_label.config(text="Desativando todas as notificações de Segurança e Manutenção...")
        subprocess.run(["reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings", 
                        "/v", "NOC_GLOBAL_SETTING_TOASTS_ENABLED", "/t", "REG_DWORD", "/d", "0", "/f"], check=True)
        logging.info('Todas as notificações foram desativadas.')
        progress_bar["value"] = 50
        root.update()
        configure_status_label.config(text="Ativando .NET Framework 3.5...")
        time.sleep(1)
        progress_label.config(text="Ativando .NET Framework 3.5...")
        ativar_net_framework_3_5()
        progress_bar["value"] = 100
        root.update()
        time.sleep(1)

        configure_status_label.config(text="Configurações do Windows aplicadas com sucesso!", foreground="green")
        progress_label.config(text="Configurações do Windows aplicadas com sucesso!")
        messagebox.showinfo("Sucesso", "Configurações do Windows aplicadas com sucesso!")

        resposta = messagebox.askyesno("Reiniciar", "As alterações foram aplicadas. Deseja reiniciar agora?")
        if resposta:
            configure_status_label.config(text="Reiniciando o computador em 10 segundos...", foreground="blue")
            progress_label.config(text="Reiniciando o computador em 10 segundos...")
            root.update()
            time.sleep(10)
            os.system("shutdown /r /t 0")
        else:
            configure_status_label.config(text="Reinicie o computador manualmente para aplicar as alterações.", foreground="blue")
            progress_label.config(text="Reinicie o computador manualmente para aplicar as alterações.")
            messagebox.showinfo("Sucesso", "Reinicie o computador manualmente para que as alterações tenham efeito.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao executar comando: {e}")
        configure_status_label.config(text=f"Erro ao configurar o Windows: {e}", foreground="red")
        messagebox.showerror("Erro", f"Erro ao configurar o Windows: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}", exc_info=True)
        configure_status_label.config(text=f"Erro inesperado ao configurar o Windows: {e}", foreground="red")
        messagebox.showerror("Erro", f"Erro inesperado ao configurar o Windows: {e}")

def update_progress(downloaded_size, total_size, elapsed_time):
    """Atualiza a barra de progresso e o tempo restante."""
    if total_size > 0:
        progress = int((downloaded_size / total_size) * 100)
        progress_var.set(progress)
        if elapsed_time > 0:
            download_speed = downloaded_size / elapsed_time
            remaining_size = total_size - downloaded_size
            if download_speed > 0:
                remaining_time = remaining_size / download_speed
                # Converte o tempo restante para minutos e segundos
                if remaining_time > 60:
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    if minutes > 60:
                        hours = int(minutes // 60)
                        minutes = int(minutes % 60)
                        time_label.config(text=f"Tempo restante: {hours} horas, {minutes} minutos e {seconds} segundos")
                    else:
                        time_label.config(text=f"Tempo restante: {minutes} minutos e {seconds} segundos")
                else:
                    time_label.config(text=f"Tempo restante: {int(remaining_time)} segundos")
        progress_label.config(
            text=f"Baixando: {current_program} ({downloaded_size / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB)"
        )
        root.update_idletasks()

def start_installation():
    global cancel_event, installation_in_progress

    # Verificar se já há uma instalação em andamento
    if installation_in_progress:
        messagebox.showwarning("Aviso", "Uma instalação já está em andamento!")
        logging.warning("Tentativa de iniciar uma nova instalação enquanto outra está em andamento.")
        return

    # Obter programas selecionados
    selected_programs = [program for program, var in programs.items() if var.get()]

    # Verificar se há programas selecionados
    if not selected_programs:
        messagebox.showwarning("Aviso", "Nenhum programa selecionado!")
        logging.warning("Nenhum programa selecionado para instalação.")
        return

    # Inicializar variáveis de controle
    progress_var.set(0)
    cancel_event = Event()
    installation_in_progress = True
    logging.info("Iniciando instalação dos programas selecionados.")

    def install_program(program):
        """Função para instalar um programa."""
        global current_program
        current_program = program  # Atualizar o programa atual

        # Verificar se o programa já está instalado
        if is_program_installed(program):
            logging.info(f"Programa {program} já está instalado. Pulando instalação.")
            return

        # Baixar o instalador
        url = program_urls.get(program)
        if not url:
            logging.error(f"URL não encontrada para {program}.")
            return

        destination = os.path.join(os.getcwd(), f"{program.replace(' ', '_')}.exe")
        if not download_file(url, destination, update_progress):
            logging.error(f"Falha ao baixar o instalador de {program}.")
            return

        # Instalar o programa
        try:
            if program == ".NET Framework":
                install_dotnet_framework()
            else:
                # Parâmetros de instalação silenciosa (ajuste conforme necessário)
                silent_params = {
                    "Chrome": "/silent /install",
                    "Firefox": "/S",
                    "Adobe Reader": "/sAll /rs /rps /msi /norestart /quiet",
                    "WinRAR": "/S",
                    "AnyDesk": "--silent",
                    "Avast": "/silent",
                    "K-Lite Codecs": "/verysilent"
                }
                params = silent_params.get(program, "/S")  # Usar /S como padrão
                subprocess.run([destination, params], check=True)
                logging.info(f"Programa {program} instalado com sucesso.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Erro ao instalar {program}: {e}")
        finally:
            # Remover o instalador após a instalação
            if os.path.exists(destination):
                os.remove(destination)

    def run_installation():
        """Função principal para executar a instalação em paralelo."""
        threads = []
        for program in selected_programs:
            if cancel_event.is_set():
                break
            thread = Thread(target=install_program, args=(program,))
            thread.start()
            threads.append(thread)

        # Aguardar todas as threads terminarem
        for thread in threads:
            thread.join()

        # Finalizar a instalação
        if not cancel_event.is_set():
            messagebox.showinfo("Concluído", "Todos os programas foram instalados!")
            logging.info("Todos os programas foram instalados com sucesso.")
        progress_label.config(text="Pronto!")
        time_label.config(text="")
        installation_in_progress = False
        logging.info("Instalação concluída.")

    # Iniciar a instalação em uma thread separada
    Thread(target=run_installation).start()
    
def cancel_download():
    """Cancela o download e exclui o instalador, se existir."""
    global installation_in_progress
    if cancel_event:
        cancel_event.set()
        progress_label.config(text="Download cancelado!")
        logging.info(f'Download do programa {current_program} cancelada!')
        time_label.config(text="")
        if current_program:
            destination = os.path.join(os.getcwd(), f"{current_program.replace(' ', '_')}.exe")
            if os.path.exists(destination):
                time.sleep(3)
                os.remove(destination)
                logging.info(f'Removido instalador do programa no caminho {destination}')
        installation_in_progress = False  # Redefine a variável para permitir uma nova instalacao

def detect_notebook():
    """Detecta se o sistema é um notebook ou PC."""
    try:
        battery = psutil.sensors_battery()
        if battery is not None:
            logging.info("Notebook detectado.")
            return True
        else:
            logging.info("PC detectado (sem bateria).")
            return False
    except Exception as e:
        logging.error(f"Erro ao detectar notebook ou PC: {e}")
        return False

def list_startup_programs():
    """Lista os programas que iniciam automaticamente com o Windows."""
    startup_programs = {}
    try:
        # Acessa a chave do Registro que contém os programas de inicialização
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        i = 0
        while True:
            try:
                # Obtém o nome e o valor de cada entrada
                name, value, _ = winreg.EnumValue(reg_key, i)
                startup_programs[name] = value
                i += 1
            except OSError:
                break
        winreg.CloseKey(reg_key)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao acessar o Registro do Windows: {e}")
    return startup_programs

def remove_startup_program(program_name):
    """Remove um programa da lista de inicialização automática."""
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        winreg.DeleteValue(reg_key, program_name)
        winreg.CloseKey(reg_key)
        messagebox.showinfo("Sucesso", f"O programa '{program_name}' foi removido da inicialização automática.")
        logging.info(f'Removendo programa da inicialização automatica: {program_name}')
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao remover o programa '{program_name}': {e}")

def manage_startup_programs():
    """Exibe uma interface para gerenciar os programas que iniciam automaticamente."""
    startup_programs = list_startup_programs()
    if not startup_programs:
        messagebox.showinfo("Info", "Nenhum programa configurado para iniciar automaticamente.")
        return

    # Cria uma nova janela para gerenciar os programas
    manage_window = tk.Toplevel(root)
    manage_window.title("Gerenciar Programas de Inicialização")
    manage_window.geometry("400x300")

    # Frame para conter os checkboxes
    frame = ttk.Frame(manage_window)
    frame.pack(pady=10, padx=10, fill="both", expand=True)

    # Variáveis para armazenar o estado dos checkboxes
    program_vars = {name: tk.BooleanVar(value=True) for name in startup_programs.keys()}

    # Adiciona um checkbox para cada programa
    for name, value in startup_programs.items():
        cb = ttk.Checkbutton(frame, text=f"{name} ({value})", variable=program_vars[name])
        cb.pack(anchor="w", padx=5, pady=2)

    # Função para aplicar as alterações
    def apply_changes():
        """Aplica as alterações após a confirmação do usuário."""
        confirm = messagebox.askyesno("Confirmar", "Tem certeza que deseja remover os programas selecionados da inicialização automática?")
        
        if confirm:  # Se o usuário confirmar
            for name, var in program_vars.items():
                if not var.get():  # Se o checkbox estiver desmarcado, remove o programa
                    remove_startup_program(name)
            manage_window.destroy()  # Fecha a janela de gerenciamento
        else:
            messagebox.showinfo("Info", "Nenhuma alteração foi aplicada.")

    # Botão para aplicar as alterações
    ttk.Button(manage_window, text="Aplicar Alterações", command=apply_changes).pack(pady=10)

""" def detectar_placa_video():
    c = wmi.WMI()
    placas_video = []

    for dispositivo in c.Win32_VideoController():
        placas_video.append(dispositivo.Name)

    return placas_video

def obter_driver_nvidia(modelo):

    url = "https://www.nvidia.com/Download/processFind.aspx"
    params = {
        "psid": "123",  # Substitua pelo PSID correto, se disponível
        "pfid": "456",  # Substitua pelo PFID correto, se disponível
        "osid": "57",   # Windows 10 64-bit (ajuste conforme necessário)
        "lid": "1",     # Idioma: Inglês
        "whql": "1",    # WHQL Certified
        "lang": "en-us",
        "ctk": "0"
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        link_driver = soup.find("a", {"id": "lnkDownload"})
        if link_driver:
            return link_driver["href"]
    return None

def obter_driver_amd(modelo):
    url = f"https://www.amd.com/en/support/search?query={modelo}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        link_driver = soup.find("a", {"class": "download-link"})
        if link_driver:
            return link_driver["href"]
    return None

def abrir_site_drivers():
    placas_video = detectar_placa_video()

    if not placas_video:
        messagebox.showinfo("Info", "Nenhuma placa de vídeo detectada.")
        return

    for placa in placas_video:
        if "NVIDIA" in placa:
            modelo = placa.split("NVIDIA")[-1].strip()
            driver_url = obter_driver_nvidia(modelo)
            if driver_url:
                webbrowser.open(driver_url)
            else:
                webbrowser.open("https://www.nvidia.com/Download/index.aspx")
            break
        elif "AMD" in placa or "Radeon" in placa:
            modelo = placa.split("AMD")[-1].strip()
            driver_url = obter_driver_amd(modelo)
            if driver_url:
                webbrowser.open(driver_url)
            else:
                webbrowser.open("https://www.amd.com/en/support")
            break
    else:
        messagebox.showinfo("Info", "Nenhum link de driver disponível para a placa de vídeo detectada.")
 """

def create_gui():
    global root, progress_var, progress_label, time_label, programs, program_urls, is_notebook, programas_silenciosos

    # Configuração da janela principal
    root = ThemedTk(theme="arc")  # Tema moderno
    root.title("Instalador de Programas - IdealTech Soluções em Informática")
    root.geometry("420x710")  # Aumentei o tamanho para acomodar as colunas

    # Detectar se é notebook ou PC
    is_notebook = detect_notebook()

    # Exibir o tipo de sistema na interface
    system_type = "Notebook" if is_notebook else "PC"
    system_label = ttk.Label(root, text=f"Tipo de Sistema: {system_type}")
    system_label.pack(pady=5)

    # Exibir informações do sistema operacional
    windows_version = get_windows_version()
    if windows_version not in PROGRAM_URLS:
        messagebox.showerror("Erro", "Sistema operacional não suportado!")
        sys.exit(1)

    ttk.Label(root, text=f"Sistema Operacional: {windows_version}").pack(pady=5)

    # Inicializar a variável programs com os programas padrão
    program_urls = PROGRAM_URLS[windows_version]  # Definir program_urls antes de usar
    programs = {program: tk.BooleanVar() for program in program_urls}

    # Variável para instalação silenciosa
    programas_silenciosos = {program: tk.BooleanVar() for program in program_urls}

    # Programas marcados por padrão
    programas_marcados = [
        "Chrome", "Firefox", "Adobe Reader", "WinRAR", "AnyDesk", "Avast", "K-Lite Codecs"
    ]

    # Programas com instalação silenciosa ativada por padrão
    programas_silenciosos_padrao = ["Chrome", "Firefox", "Adobe Reader", "WinRAR", "K-Lite Codecs"]

    # Botão para selecionar/desselecionar todos os programas
    def toggle_all_programs():
        state = all(var.get() for var in programs.values())
        for var in programs.values():
            var.set(not state)

    ttk.Button(root, text="Selecionar/Desselecionar Todos", command=toggle_all_programs).pack(pady=5)

    # Frame para os checkboxes
    checkbox_frame = ttk.Frame(root)
    checkbox_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Configurar as colunas para centralizar os checkboxes
    for i in range(5):  # 5 colunas
        checkbox_frame.columnconfigure(i, weight=1)  # Centralizar as colunas

    # Criar checkboxes para seleção de programas em uma grade 5x5 (5 por coluna)
    row, col = 0, 0
    for program, var in programs.items():
        # Definir se o programa deve vir marcado por padrão
        if program in programas_marcados:
            var.set(True)  # Marcado por padrão

        # Marcar como silencioso por padrão, se o programa estiver na lista
        if program in programas_silenciosos_padrao:
            programas_silenciosos[program].set(True)

        # Criar o checkbox para seleção do programa
        cb = ttk.Checkbutton(checkbox_frame, text=program, variable=var)
        cb.grid(row=row, column=col, padx=5, pady=5, sticky="w")

        # Atualizar a posição na grade
        row += 1
        if row >= 5:  # 5 linhas por coluna
            row = 0
            col += 1  # Avançar para a próxima coluna

    # Configurar estilo para programas opcionais
    style = ttk.Style()
    style.configure("Opcional.TCheckbutton", foreground="blue", font=("Arial", 10, "italic"))

    # Barra de progresso
    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var)
    progress_bar.pack(pady=10)

    # Labels de status
    progress_label = ttk.Label(root, text="Pronto!")
    progress_label.pack()

    time_label = ttk.Label(root, text="")
    time_label.pack()

    # Exibir atualizações da configuração do Windows
    configure_status_label = ttk.Label(root, text="", foreground="red")
    configure_status_label.pack(pady=5)

    # Botões principais
    ttk.Button(root, text="Instalar Programas Selecionados", command=start_installation).pack(pady=10)
    ttk.Button(root, text="Cancelar Download", command=cancel_download).pack(pady=5)
    ttk.Button(root, text="Configurar Windows", command=lambda: configure_windows(progress_bar, progress_label, configure_status_label)).pack(pady=10)

    # Botão para gerenciar programas de inicialização
    ttk.Button(root, text="Gerenciar Inicialização Automática", command=manage_startup_programs).pack(pady=10)

    # Botão para verificar configurações do PC
    ttk.Button(root, text="Verificar Configurações do PC", command=exibir_configuracoes).pack(pady=10)

    # Botão para verificar e baixar drivers
    ttk.Button(root, text="Verificar GPU e Baixar Drivers", command=abrir_site_drivers).pack(pady=10)

    root.mainloop()
    
if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        messagebox.showerror("Erro", "Execute o programa como administrador!")
        sys.exit(1)
    create_gui()