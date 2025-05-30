# 🎮 Conectar un control de Xbox por Bluetooth usando MicroPython

Este proyecto muestra cómo escanear, identificar y conectar un **control inalámbrico de Xbox** (Bluetooth) a un microcontrolador con **ESP32** usando **MicroPython**.  
Está pensado para proyectos donde quieras recibir los datos del mando y controlarlo todo como un dios del DIY: carritos, robots, drones o lo que se te ocurra.  

## 🚀 ¿Qué hace este código?

- Activa el Bluetooth del ESP32 en modo *central* (cliente).
- Escanea los dispositivos cercanos.
- Detecta si hay un control de Xbox con el nombre `"Xbox Wireless Controller"`.
- Intenta conectarse automáticamente si lo encuentra.
- Muestra los datos recibidos vía `NOTIFY`, útiles para entender qué botones se están presionando o qué ejes se están moviendo.
- Maneja reconexiones si se pierde la señal.

> ⚠️ Este código **no decodifica** aún los datos del control. Solo los muestra en crudo. Si quieres mapear botones o sticks, necesitarás hacer parsing del payload recibido por `NOTIFY`.

## 🧠 Requisitos

- Una tarjeta con **ESP32**.
- Firmware de **MicroPython** actualizado.
- Un control de **Xbox que use Bluetooth** (no los viejos de 360).
- Thonny o cualquier entorno para cargar scripts en MicroPython.

## 🗂️ Estructura

El código está en un solo archivo, e incluye:

- Definición de eventos Bluetooth (`_IRQ_*`)
- Función para extraer el nombre del dispositivo desde `adv_data`.
- Clase `BLESimpleCentral` que gestiona:
  - Escaneo.
  - Conexión.
  - Emparejamiento.
  - Lectura de datos vía `NOTIFY`.

## 🧪 ¿Qué puedes hacer con esto?

- Controlar un carrito, dron, brazo robótico, luces, etc.
- Integrarlo con PWM, GPIO, multitarea y más en ESP32.
- Capturar pulsaciones y movimientos del joystick para convertirlos en acciones físicas.

## 📦 Pendiente o futuro

- Parsear los datos `notify_data` para identificar botones.
- Guardar los perfiles emparejados para reconectar más rápido.
- Soporte para otros tipos de controles BT (PS4, genéricos, etc.).

## 🤖 Ejemplo de uso

En consola del ESP32 deberías ver algo como:

_IRQ_SCAN_RESULT
Dirección: XX:XX:XX:XX:XX:XX, Nombre: Xbox Wireless Controller, RSSI: -60
Encontrado control Xbox con la dirección: XX:XX:XX:XX:XX:XX
Conectado al dispositivo: XX:XX:XX:XX:XX:XX
_IRQ_GATTC_NOTIFY
Datos crudos: b'\x01\x00\x7f\x80...'

## ❤️ Créditos

Hecho por [El Taller de Alex](https://www.eltallerdealex.com.mx) como parte de un proyecto de control de carritos y robots con ESP32.  
Si te sirvió, compártelo o sígueme en redes para ver más proyectos como este.
