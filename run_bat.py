import subprocess
import os
import time
import json

def open_edge():
    """Ejecuta el archivo batch para abrir Microsoft Edge."""
    batch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'open_edge.bat')
    print(f"Ejecutando {batch_file}...")
    try:
        subprocess.run([batch_file], shell=True, check=True)
        print("El archivo batch se ejecutó correctamente.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el archivo batch: {e}")
        return False

def load_searches_from_json(filename='searches.json', max_results=None): # None = buscar todas 
    """Lee el archivo JSON que contiene los términos de búsqueda y opcionalmente limita la cantidad."""
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    print(f"Leyendo búsquedas desde {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            searches = data.get("searches", [])
            if max_results is not None:
                searches = searches[:max_results]
            return searches
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")
        return []

def send_keys_to_edge(text, press_enter=True, slow=False):
    """
    Activa la ventana de Microsoft Edge y envía las teclas especificadas.
    Si slow=True, simula una escritura humana enviando letra por letra con pausas aleatorias.
    Garantiza que las teclas solo se envíen a Edge (re-enfocando si es necesario).
    """
    # Escapar las comillas dobles para evitar errores en PowerShell
    escaped_text = text.replace('"', '`"')
    
    if slow:
        # Enviar letra por letra con retraso aleatorio usando PowerShell re-enfocando Edge
        enter_cmd = '"~" | SendKeysSafe' if press_enter else ''
        ps_script = (
            '$wshell = New-Object -ComObject Wscript.Shell; '
            'filter SendKeysSafe { '
            '    if ($wshell.AppActivate("Edge")) { '
            '        Start-Sleep -Milliseconds 20; '
            '        $wshell.SendKeys($_); '
            '    } '
            '} '
            'if ($wshell.AppActivate("Edge")) { '
            '    Start-Sleep -Milliseconds 500; '
            f'   $text = "{escaped_text}"; '
            '    $specialChars = "+^%~(){}[]"; '
            '    foreach ($char in $text.ToCharArray()) { '
            '        $strChar = [string]$char; '
            '        if ($specialChars.Contains($strChar)) { '
            '            ("{" + $strChar + "}") | SendKeysSafe; '
            '        } else { '
            '            $strChar | SendKeysSafe; '
            '        } '
            '        $delay = Get-Random -Minimum 100 -Maximum 300; ' # Pausa aleatoria entre 100ms y 300ms
            '        Start-Sleep -Milliseconds $delay; '
            '    } '
            f'   {enter_cmd}; '
            '} else {'
            '    Write-Warning "No se pudo activar la ventana de Edge. No se enviaran las teclas.";'
            '}'
        )
    else:
        # Enviar todo de golpe (ideal para atajos como Ctrl+L)
        keys_to_send = escaped_text
        if press_enter:
            keys_to_send += "~"
            
        ps_script = (
            '$wshell = New-Object -ComObject Wscript.Shell; '
            'if ($wshell.AppActivate("Edge")) { '
            '    Start-Sleep -Milliseconds 500; '
            f'   $wshell.SendKeys("{keys_to_send}"); '
            '} else {'
            '    Write-Warning "No se pudo activar la ventana de Edge. No se enviaran las teclas.";'
            '}'
        )
    
    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al enviar las teclas: {e}")
        return False

def load_config(filename='config.txt'):
    """Lee el archivo de configuración txt y retorna un diccionario con los valores."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    config = {
        'limite_busquedas': None,
        'hacer_scroll': True,
        'entrar_en_web': True
    }
    
    if not os.path.exists(config_path):
        print("Archivo de configuración no encontrado. Usando valores por defecto.")
        return config
        
    print(f"Leyendo configuración desde {config_path}...")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip().lower()
                    val = val.strip().lower()
                    
                    if key == 'limite_busquedas':
                        config['limite_busquedas'] = int(val) if val != 'none' and val != '' else None
                    elif key == 'hacer_scroll':
                        config['hacer_scroll'] = (val == 'true' or val == '1' or val == 'yes')
                    elif key == 'entrar_en_web':
                        config['entrar_en_web'] = (val == 'true' or val == '1' or val == 'yes')
        return config
    except Exception as e:
        print(f"Error al leer el archivo de configuración: {e}. Usando valores por defecto.")
        return config

def simulate_interaction_in_edge(hacer_scroll=True, entrar_en_web=True):
    """
    Simula la interacción del usuario en la página de resultados y dentro de una web:
    1. Hace scroll en los resultados de búsqueda (si hacer_scroll es True).
    2. Entra a una web de forma aleatoria (si entrar_en_web es True).
    3. Hace scroll dentro de la web (si entrar_en_web y hacer_scroll son True).
    4. Vuelve atrás (si entrar_en_web es True).
    Garantiza que todas las teclas se envíen únicamente si Edge está activo,
    evitando escribir por error en otras aplicaciones.
    """
    if not hacer_scroll and not entrar_en_web:
        print("Interacción omitida según la configuración.")
        return True

    print(f"Simulando interacción (scroll={hacer_scroll}, navegar en web={entrar_en_web})...")
    
    scroll_search_block = """
    # 1. Hacer scroll en los resultados de búsqueda
    $scrolls = Get-Random -Minimum 2 -Maximum 5; 
    for ($i = 0; $i -lt $scrolls; $i++) { 
        "{PGDN}" | SendKeysSafe; 
        $delay = Get-Random -Minimum 1000 -Maximum 2000; 
        Start-Sleep -Milliseconds $delay; 
    } 
    """ if hacer_scroll else ""

    enter_web_block = """
    # 2. Navegar a un enlace usando TAB y presionar Enter
    $tabs = Get-Random -Minimum 12 -Maximum 20; 
    for ($i = 0; $i -lt $tabs; $i++) { 
        "{TAB}" | SendKeysSafe; 
        $delay = Get-Random -Minimum 100 -Maximum 250; 
        Start-Sleep -Milliseconds $delay; 
    } 
    "~" | SendKeysSafe; 
    Start-Sleep -Seconds 5; 
    """ if entrar_en_web else ""

    scroll_web_block = """
    # 3. Hacer scroll dentro de la web
    $webScrolls = Get-Random -Minimum 3 -Maximum 6; 
    for ($i = 0; $i -lt $webScrolls; $i++) { 
        if ((Get-Random -Minimum 0 -Maximum 10) -gt 8) { 
            "{PGUP}" | SendKeysSafe; 
        } else { 
            "{PGDN}" | SendKeysSafe; 
        } 
        $delay = Get-Random -Minimum 1500 -Maximum 3000; 
        Start-Sleep -Milliseconds $delay; 
    } 
    """ if (entrar_en_web and hacer_scroll) else ""

    go_back_block = """
    # 4. Volver atrás (Alt + Flecha Izquierda)
    "%{LEFT}" | SendKeysSafe; 
    Start-Sleep -Seconds 2; 
    """ if entrar_en_web else ""

    ps_script = (
        '$wshell = New-Object -ComObject Wscript.Shell; '
        'filter SendKeysSafe { '
        '    if ($wshell.AppActivate("Edge")) { '
        '        Start-Sleep -Milliseconds 50; '
        '        $wshell.SendKeys($_); '
        '    } '
        '} '
        'if ($wshell.AppActivate("Edge")) { '
        '    Start-Sleep -Seconds 4; ' # Esperar a que cargue la búsqueda
        f'{scroll_search_block}'
        f'{enter_web_block}'
        f'{scroll_web_block}'
        f'{go_back_block}'
        '} else {'
        '    Write-Warning "No se pudo activar la ventana de Edge para la interacción.";'
        '}'
    )
    
    try:
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        print("Interacción completada.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al simular interacción: {e}")
        return False

def main():
    # Cargar la configuración desde el archivo TXT
    config = load_config()
    limite_busquedas = config['limite_busquedas']
    hacer_scroll = config['hacer_scroll']
    entrar_en_web = config['entrar_en_web']
    
    print(f"Configuración cargada: Límite={limite_busquedas}, Scroll={hacer_scroll}, Entrar en Web={entrar_en_web}")
    
    # 1. Cargar las búsquedas desde el archivo JSON aplicando el límite
    busquedas = load_searches_from_json(max_results=limite_busquedas)
    if not busquedas:
        print("No se encontraron búsquedas en el archivo JSON. Saliendo...")
        return
        
    print(f"Se cargaron {len(busquedas)} búsquedas (Límite: {limite_busquedas}): {busquedas}")
    
    # 2. Abrir Edge
    if open_edge():
        # Esperar a que el navegador se cargue por primera vez
        wait_time = 4
        print(f"Esperando {wait_time} segundos para que Edge se cargue...")
        time.sleep(wait_time)
        
        # 3. Iterar y buscar cada término
        for idx, palabra in enumerate(busquedas):
            print(f"\n--- Búsqueda {idx + 1}/{len(busquedas)}: '{palabra}' ---")
            
            if idx > 0:
                # Si no es la primera búsqueda, enfocamos la barra de direcciones con Ctrl+L (^l)
                print("Enfocando la barra de direcciones (Ctrl+L)...")
                send_keys_to_edge("^l", press_enter=False, slow=False)
                # Esperar un momento a que la barra de direcciones se seleccione
                time.sleep(1)
            
            # Enviar la palabra a buscar y presionar Enter de forma lenta
            print(f"Escribiendo '{palabra}' y buscando...")
            send_keys_to_edge(palabra, press_enter=True, slow=True)
            
            # Simular scroll e ingresar a una web respetando las configuraciones
            simulate_interaction_in_edge(hacer_scroll=hacer_scroll, entrar_en_web=entrar_en_web)
            
            # Esperar unos segundos antes de la siguiente búsqueda
            pause_time = 5
            print(f"Esperando {pause_time} segundos antes de la siguiente búsqueda...")
            time.sleep(pause_time)

if __name__ == "__main__":
    main()



