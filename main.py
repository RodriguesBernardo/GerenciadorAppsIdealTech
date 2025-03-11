import tkinter as tk
from tkinter import ttk, messagebox
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

logging.basicConfig(filename='log do instalador.txt', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variáveis globais
root = None
progress_var = None
progress_label = None
time_label = None
cancel_event = None
current_program = None
is_notebook = None
installation_in_progress = False

# URLs dos programas (dependendo da versão do Windows)
PROGRAM_URLS = {
    "Windows 10": {
        "Chrome": "https://dl.google.com/chrome/install/latest/chrome_installer.exe",
        "Firefox": "https://download.mozilla.org/?product=firefox-latest&os=win&lang=pt-BR",
        "WinRAR": "https://www.win-rar.com/fileadmin/winrar-versions/winrar/winrar-x64-624br.exe",  # WinRAR 6.24 (64-bit)
        "AnyDesk": "https://download.anydesk.com/AnyDesk.exe",  # AnyDesk
        "K-Lite Codecs": "https://files3.codecguide.com/K-Lite_Codec_Pack_1790_Basic.exe",  # K-Lite Codecs Basic
        "Adobe Reader": "https://admdownload.adobe.com/rdcm/installers/live/readerdc64_ha_crd_install.exe",
        "Avast": "https://files.avast.com/iavs9x/avast_free_antivirus_setup_offline.exe",  # Avast Free Antivirus (Offline Installer)
        ".NET Framework": "https://go.microsoft.com/fwlink/?linkid=2088631",  # .NET Framework 4.8
    },
    "Windows 11": {
        "Chrome": "https://dl.google.com/chrome/install/latest/chrome_installer.exe",
        "Firefox": "https://download.mozilla.org/?product=firefox-latest&os=win&lang=pt-BR",
        "WinRAR": "https://www.win-rar.com/fileadmin/winrar-versions/winrar/winrar-x64-624br.exe",  # WinRAR 6.24 (64-bit)
        "AnyDesk": "https://download.anydesk.com/AnyDesk.exe",  # AnyDesk
        "K-Lite Codecs": "https://files3.codecguide.com/K-Lite_Codec_Pack_1790_Basic.exe",  # K-Lite Codecs Basic
        "Avast": "https://files.avast.com/iavs9x/avast_free_antivirus_setup_offline.exe",  # Avast Free Antivirus (Offline Installer)
        "Adobe Reader": "https://admdownload.adobe.com/rdcm/installers/live/readerdc64_ha_crd_install.exe",
        ".NET Framework": "https://go.microsoft.com/fwlink/?linkid=2088631",  # .NET Framework 4.8
    },
}

# DRIVER_LINKS = {
#    "RTX 4060": "https://www.nvidia.com/Download/driverResults.aspx/213877/en-us/",
#   "RTX 3060": "https://www.nvidia.com/Download/driverResults.aspx/213877/en-us/",
#    "RX 6700 XT": "https://www.amd.com/en/support/graphics/amd-radeon-6000-series/amd-radeon-6700-series/amd-radeon-rx-6700-xt",
#}



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

import os
import subprocess
import logging
import tkinter.messagebox as messagebox

def ativar_net_framework_3_5():
    """Ativa o .NET Framework 3.5 (inclui .NET 2.0 e 3.0) usando o DISM."""
    try:
        # Caminho da origem para ativação do .NET Framework
        source_path = os.path.join(os.environ["SystemRoot"], "WinSxS")

        # Comando para ativar o .NET Framework 3.5 via DISM
        comando = [
            "DISM", "/Online", "/Enable-Feature", "/FeatureName:NetFx3", "/All",
            "/LimitAccess", f'/Source:"{source_path}"'
        ]

        # Executa o comando
        resultado = subprocess.run(comando, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Verifica se o comando foi executado com sucesso
        if resultado.returncode == 0:
            messagebox.showinfo("Sucesso", ".NET Framework 3.5 ativado com sucesso!")
            logging.info(".NET Framework 3.5 ativado com sucesso.")
        else:
            messagebox.showerror("Erro", "Falha ao ativar o .NET Framework 3.5.")
            logging.error("Falha ao ativar o .NET Framework 3.5.")

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erro", f"Erro ao ativar o .NET Framework 3.5: {e.stderr}")
        logging.error(f"Erro ao ativar o .NET Framework 3.5: {e.stderr}")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro inesperado ao ativar o .NET Framework 3.5: {e}")
        logging.error(f"Erro inesperado ao ativar o .NET Framework 3.5: {e}")


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


def install_program(installer_path):
    """Instala um programa a partir do caminho do instalador."""
    try:
        if not os.path.exists(installer_path):
            raise FileNotFoundError(f"Arquivo {installer_path} não encontrado.")
        if os.path.getsize(installer_path) == 0:
            raise ValueError(f"Arquivo {installer_path} está vazio ou corrompido.")

        subprocess.run([installer_path, "/S", "/quiet"], check=True)
        # messagebox.showinfo("Sucesso", "Programa instalado com sucesso!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erro", f"Erro ao instalar o programa: {e}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar o arquivo: {e}")


def configure_windows():
    """Configura o Windows para não suspender ou desligar a tela e ativa o .NET Framework 3.5."""
    try:
        # Desativar suspensão (PC e Notebook)
        os.system("powercfg /change standby-timeout-ac 0")  # Nunca suspender (AC)
        os.system("powercfg /change monitor-timeout-ac 0")  # Nunca desligar a tela (AC)
        if is_notebook:
            os.system("powercfg /change standby-timeout-dc 0")  # Nunca suspender (Bateria)
            os.system("powercfg /change monitor-timeout-dc 0")  # Nunca desligar a tela (Bateria)

        # Desativar notificações do UAC (Controle de Conta de Usuário)
        subprocess.run(["reg", "add", "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "/v", "EnableLUA", "/t", "REG_DWORD", "/d", "0", "/f"])

        logging.info('Desativado notificações do controle de conta do usuário')

        # Desativar notificações de Segurança e Manutenção
        subprocess.run(["reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings", "/v", "NOC_GLOBAL_SETTING_TOASTS_ENABLED", "/t", "REG_DWORD", "/d", "0", "/f"])
        
        # Desativar checkboxes de Segurança e Manutenção
        subprocess.run(["reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings\\Windows.SystemToast.SecurityAndMaintenance", "/v", "Enabled", "/t", "REG_DWORD", "/d", "0", "/f"])
        subprocess.run(["reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings\\Windows.SystemToast.SecurityAndMaintenance", "/v", "ShowInActionCenter", "/t", "REG_DWORD", "/d", "0", "/f"])

        # Desativar o Centro de Ações (Action Center)
        subprocess.run(["reg", "add", "HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer", "/v", "DisableNotificationCenter", "/t", "REG_DWORD", "/d", "1", "/f"])
        subprocess.run(["reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications", "/v", "ToastEnabled", "/t", "REG_DWORD", "/d", "0", "/f"])

        # Desativar Verificação de Manutenção Automática
        subprocess.run(["reg", "add", "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\Maintenance", "/v", "MaintenanceDisabled", "/t", "REG_DWORD", "/d", "1", "/f"])
        logging.info('Desativado notificações do controle de segurança e manutenção')

        # Ativar o .NET Framework 3.5
        ativar_net_framework_3_5()

        # Perguntar ao usuário se deseja reiniciar o computador
        resposta = messagebox.askyesno("Reiniciar", "As alterações foram aplicadas. Deseja reiniciar o computador agora?")
        if resposta:
            os.system("shutdown /r /t 3")  # Reinicia o computador após 3 segundos
            messagebox.showinfo("Reiniciar", "O computador será reiniciado em 3 segundos.")
        else:
            messagebox.showinfo("Sucesso", "Configurações do Windows aplicadas com sucesso! Reinicie o computador manualmente para que as alterações entrem em vigor.")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao configurar o Windows: {e}")


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
                time_label.config(text=f"Tempo restante: {int(remaining_time)} segundos")
        progress_label.config(
            text=f"Baixando: {current_program} ({downloaded_size / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB)"
        )
        root.update_idletasks()

def start_installation():
    global cancel_event, current_program, installation_in_progress

    if installation_in_progress:
        messagebox.showwarning("Aviso", "Uma instalação já está em andamento!")
        logging.warning("Tentativa de iniciar uma nova instalação enquanto outra está em andamento.")
        return

    selected_programs = [program for program, var in programs.items() if var.get()]

    if not selected_programs:
        messagebox.showwarning("Aviso", "Nenhum programa selecionado!")
        logging.warning("Nenhum programa selecionado para instalação.")
        return

    progress_var.set(0)
    cancel_event = Event()
    installation_in_progress = True
    logging.info("Iniciando instalação dos programas selecionados.")

    def run_installation():
        # Verifica se a checkbox "Baixar Drivers da Placa de Vídeo" está marcada
        if "Baixar Drivers da Placa de Vídeo" in selected_programs:
            placa_video = obter_info_placa_video()
            if placa_video:
                link_driver = DRIVER_LINKS.get(placa_video)
                if link_driver:
                    messagebox.showinfo(
                        "Placa de Vídeo Detectada",
                        f"Placa de vídeo detectada: {placa_video}\n\nIniciando download dos drivers..."
                    )
                    destination = os.path.join(os.getcwd(), f"driver_{placa_video.replace(' ', '_')}.exe")
                    if download_file(link_driver, destination, update_progress):
                        messagebox.showinfo("Sucesso", f"Drivers da {placa_video} baixados com sucesso!")
                    else:
                        messagebox.showerror("Erro", "Falha ao baixar os drivers.")
                else:
                    messagebox.showinfo(
                        "Placa de Vídeo Detectada",
                        f"Placa de vídeo detectada: {placa_video}\n\nNenhum link de driver disponível."
                    )

        for program in selected_programs:
            if program == "Baixar Drivers da Placa de Vídeo":
                continue  # Pula a instalação de drivers, pois já foi tratada acima

            global current_program
            current_program = program

            # Verifica se o programa já está instalado
            if is_program_installed(program):
                messagebox.showinfo("Info", f"{program} já está instalado. Pulando instalação.")
                logging.info(f"Programa {program} já está instalado. Pulando instalação.")
                continue

            if program == ".NET Framework":
                install_dotnet_framework()
                continue

            url = program_urls.get(program)
            if not url:
                messagebox.showerror("Erro", f"URL não encontrada para {program}")
                logging.error(f"URL não encontrada para {program}.")
                continue

            destination = os.path.join(os.getcwd(), f"{program.replace(' ', '_')}.exe")
            if download_file(url, destination, update_progress):
                if cancel_event.is_set():
                    break
                install_program(destination)
                if os.path.exists(destination):
                    os.remove(destination)
        if not cancel_event.is_set():
            messagebox.showinfo("Concluído", "Todos os programas foram instalados!")
            logging.info("Todos os programas foram instalados com sucesso.")
        progress_label.config(text="Pronto!")
        time_label.config(text="")
        installation_in_progress = False
        logging.info("Instalação concluída.")

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
                os.remove(destination)
                logging.info(f'Removido instalador do programa no caminho {destination}')
        installation_in_progress = False  # Redefine a variável para permitir uma nova instalação


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

import webbrowser

def abrir_site_drivers(placa_video):
    """Abre o site de drivers da NVIDIA ou AMD com base na placa de vídeo."""
    if "NVIDIA" in placa_video:
        webbrowser.open("https://www.nvidia.com/Download/index.aspx")
    elif "AMD" in placa_video:
        webbrowser.open("https://www.amd.com/en/support")
    else:
        messagebox.showinfo("Info", "Nenhum link de driver disponível para a placa de vídeo detectada.")

def create_gui():
    global root, progress_var, progress_label, time_label, programs, program_urls, is_notebook

    root = tk.Tk()
    root.title("Instalador de Programas - IdealTech Soluções em Informática")
    # root.iconbitmap("icon.ico")

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

    # Exibir informações do processador
    processador = obter_info_processador()
    # ttk.Label(root, text=f"Processador: {processador}").pack(pady=5)

    # Exibir informações da memória RAM
    memoria = obter_info_memoria()
    # ttk.Label(root, text=f"Memória RAM: {memoria}").pack(pady=5)

    # Exibir velocidade da memória RAM
    velocidade_memoria = obter_velocidade_memoria()
    # ttk.Label(root, text=f"Velocidade da Memória: {velocidade_memoria}").pack(pady=5)

    # Exibir informações da placa de vídeo
    placa_video = obter_info_placa_video()
    # ttk.Label(root, text=f"Placa de Vídeo: {placa_video}").pack(pady=5)


    # Inicializar a variável programs com os programas padrão
    program_urls = PROGRAM_URLS[windows_version]
    programs = {program: tk.BooleanVar() for program in program_urls}

  
    # Botão para selecionar/desselecionar todos os programas
    def toggle_all_programs():
        state = all(var.get() for var in programs.values())
        for var in programs.values():
            var.set(not state)

    ttk.Button(root, text="Selecionar/Desselecionar Todos", command=toggle_all_programs).pack(pady=5)

    # Criar checkboxes para seleção de programas (todos marcados por padrão)
    for program, var in programs.items():
        var.set(True)  # Marca todos os checkboxes por padrão
        cb = ttk.Checkbutton(root, text=program, variable=var)
        cb.pack(anchor="w", padx=10, pady=5)

    progress_var = tk.IntVar()
    ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var).pack(pady=10)

    progress_label = ttk.Label(root, text="Pronto!")
    progress_label.pack()

    time_label = ttk.Label(root, text="")
    time_label.pack()

    ttk.Button(root, text="Instalar Programas Selecionados", command=start_installation).pack(pady=10)
    ttk.Button(root, text="Cancelar Download", command=cancel_download).pack(pady=5)
    ttk.Button(root, text="Configurar Windows", command=configure_windows).pack(pady=10)
    
    # Adicionar botão para baixar drivers, se NVIDIA ou AMD for detectada
    if "NVIDIA" in placa_video or "AMD" in placa_video:
        ttk.Button(root, text="Baixar Drivers da Placa de Vídeo", command=lambda: abrir_site_drivers(placa_video)).pack(pady=5)
      # Adicionar botão para baixar drivers, se NVIDIA ou AMD for detectada
    
    if "NVIDIA" in placa_video or "AMD" in placa_video:
        ttk.Button(root, text="Baixar Drivers da Placa de Vídeo", command=lambda: abrir_site_drivers(placa_video)).pack(pady=5)

    if "Nenhuma" not in placa_video:
        programs["Baixar Drivers da Placa de Vídeo"] = tk.BooleanVar()

    # Botão para gerenciar programas de inicialização
    ttk.Button(root, text="Gerenciar Inicialização Automática", command=manage_startup_programs).pack(pady=10)

    # Botão para verificar configurações do PC
    ttk.Button(root, text="Verificar Configurações do PC", command=exibir_configuracoes).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        messagebox.showerror("Erro", "Execute o programa como administrador!")
        sys.exit(1)
    create_gui()