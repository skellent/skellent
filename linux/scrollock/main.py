import glob
import sys
import os

try:
    import evdev
except ImportError:
    print("[!] Falta la librería 'evdev'.")
    print("    Instálala según tu distribución (ej. sudo apt install python3-evdev)")
    sys.exit(1)

def get_scroll_lock_path():
    """Busca la ruta del archivo que controla el LED del Scroll Lock."""
    paths = glob.glob('/sys/class/leds/*scrolllock/brightness')
    return paths[0] if paths else None

def set_scroll_lock(path, state):
    """Escribe 1 (encendido) o 0 (apagado) en el archivo del LED."""
    value = '1' if state else '0'
    try:
        with open(path, 'w') as f:
            f.write(value)
        estado_str = "encendido" if state else "apagado"
        print(f"[*] Scroll Lock {estado_str}.")
    except Exception as e:
        print(f"\n[!] Error al escribir en el dispositivo: {e}")
        sys.exit(1)

def find_keyboard_with_scroll_lock():
    """Busca el primer dispositivo de entrada que tenga la tecla física Scroll Lock."""
    dispositivos = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for dispositivo in dispositivos:
        capacidades = dispositivo.capabilities()
        # Verifica si el dispositivo envía eventos de teclas y si tiene la tecla Scroll Lock
        if evdev.ecodes.EV_KEY in capacidades:
            if evdev.ecodes.KEY_SCROLLLOCK in capacidades[evdev.ecodes.EV_KEY]:
                return dispositivo
    return None

def main():
    # Validación estricta de permisos de administrador
    if os.geteuid() != 0:
        print("[!] Debes ejecutar este script como administrador.")
        print("    Uso correcto: sudo python3 scroll_lock_sys.py")
        sys.exit(1)

    led_path = get_scroll_lock_path()
    if not led_path:
        print("[!] No se encontró el LED del Scroll Lock en /sys/class/leds/")
        sys.exit(1)

    teclado = find_keyboard_with_scroll_lock()
    if not teclado:
        print("[!] No se encontró ningún teclado con la tecla Scroll Lock física.")
        sys.exit(1)

    print(f"[*] Teclado detectado para escuchar: {teclado.name}")

    # Definimos el estado inicial
    estado_led = True
    set_scroll_lock(led_path, estado_led)

    print("\n" + "="*50)
    print(" 🟢 Script en ejecución.")
    print(" ⌨️  Presiona la tecla 'Scroll Lock' para alternar la luz.")
    print(" 🛑 Presiona Ctrl+C en esta terminal para salir y apagar el LED.")
    print("="*50 + "\n")

    try:
        # El loop de lectura se queda "escuchando" el teclado en tiempo real
        for evento in teclado.read_loop():
            if evento.type == evdev.ecodes.EV_KEY:
                # evento.value puede ser: 1 (se presionó), 0 (se soltó), 2 (se mantiene presionada)
                # Solo queremos alternar cuando se PRESIONA (1)
                if evento.code == evdev.ecodes.KEY_SCROLLLOCK and evento.value == 1:
                    estado_led = not estado_led
                    set_scroll_lock(led_path, estado_led)
                    
    except KeyboardInterrupt:
        print("\n[!] Has presionado Ctrl+C. Deteniendo el script...")
        
    finally:
        # Apagamos el LED al final, pase lo que pase
        set_scroll_lock(led_path, False)
        print("[*] Script finalizado de forma segura.")

if __name__ == "__main__":
    main()
