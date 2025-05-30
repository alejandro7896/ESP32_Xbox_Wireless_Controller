import binascii
import ubluetooth
from micropython import const
from ubluetooth import UUID
from machine import Pin, PWM
import time
import machine
import _thread
import esp32

"""
╔══════════════════════════════════════════════════════════╗
║         Módulo de Conexión BLE para Control Xbox         ║
╠══════════════════════════════════════════════════════════╣
║ Autor: Alejandro Amavizca López (El Taller de Alex)      ║
║ Año: 2025                                                ║
║ Lenguaje: MicroPython                                    ║
║ Descripción:                                             ║
║ Código para manejar la conexión Bluetooth BLE entre un   ║
║ ESP32 y un control de Xbox.                              ║
║ Recibe y procesa datos de mando para control de proyectos║
║ Parte fundamental del proyecto del carrito de policía.   ║
╚══════════════════════════════════════════════════════════╝

Licencia MIT — úsalo libremente, solo no olvides dar crédito.

eltallerdealex.com.mx

https://github.com/alejandro7896/ESP32_Xbox_Wireless_Controller

"""


# UUIDs comunes para HID
HID_SERVICE_UUID = UUID(0x1812)  # UUID del servicio HID (general)
HID_REPORT_MAP_UUID = UUID(0x2A04)  # UUID de la característica "Report Map"
HID_REPORT_UUID = UUID(0x2A22)  # UUID de la característica "HID Report" (este es el que te interesa para datos de botones y movimientos)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)




ESCANEANDO = False
TARGET_NAME = "Xbox Wireless Controller"  # Así se llaman los controles de Xbox que traen BT
found_device = False #flag
secrets_store = {}
CONTROL_CONECTADO = False



#Obtener el nombre BT del dispositivo
def extract_name(adv_data):
    adv_bytes = bytes(adv_data)
    i = 0
    while i < len(adv_bytes):
        length = adv_bytes[i]
        if length == 0:
            break
        adv_type = adv_bytes[i + 1]
        if adv_type == 0x09:  # Nombre completo
            return adv_bytes[i + 2:i + 1 + length].decode("utf-8")
        elif adv_type == 0x08:  # Nombre abreviado
            return adv_bytes[i + 2:i + 1 + length].decode("utf-8")
        i += 1 + length
    return None


class BLESimpleCentral:

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',   # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[37;1m',  # White Bright
        'RESET': '\033[0m'   # Reset Color
    }

    def log(level, message, end=""):

        # Formatear el mensaje con el color correspondiente
        log_message = f"{self.COLORS.get(level, COLORS['RESET'])}{level}{self.COLORS['RESET']} - {message}"

        # Imprimir el mensaje
        print(log_message)

    def __init__(self, ble):
        self.gamepad_name = None
        self.gamepad_addr_type = None
        self.gamepad_addr = None
        self.conn_handle = None  # Inicializamos conn_handle como None
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self.bt_irq)

    def bt_irq(self, event, data):
        global found_device
        global secrets_store
        global CONTROL_CONECTADO
        global ESCANEANDO
        if event == _IRQ_CENTRAL_CONNECT:
            print("_IRQ_CENTRAL_CONNECT")
            conn_handle, addr_type, addr = data

        elif event == _IRQ_CENTRAL_DISCONNECT:
            # A central has disconnected from this peripheral.
            log("_IRQ_CENTRAL_DISCONNECT")
            conn_handle, addr_type, addr = data

        elif event == _IRQ_GATTS_WRITE:
            # A client has written to this characteristic or descriptor.
            print("_IRQ_GATTS_WRITE")
            conn_handle, attr_handle = data

        elif event == _IRQ_GATTS_READ_REQUEST:
            print("_IRQ_GATTS_READ_REQUEST")
            # A client has issued a read. Note: this is only supported on STM32.
            # Return a non-zero integer to deny the read (see below), or zero (or None)
            # to accept the read.
            conn_handle, attr_handle = data

        elif event == _IRQ_SCAN_RESULT:
            print("_IRQ_SCAN_RESULT")
            addr_type, addr, adv_type, rssi, adv_data = data

            # Convertir dirección a string
            address = ":".join("{:02X}".format(b) for b in bytes(addr))

            # Extraer el nombre del dispositivo
            name = extract_name(adv_data) or "Desconocido"

            # Mostrar resultados
            print(f"Dirección: {address}, Nombre: {name}, RSSI: {rssi}")
            if name == TARGET_NAME and not found_device:
                print(f"Encontrado control Xbox con la dirección: {address}")

                found_device = True

                #Detener escaneo:
                self._ble.gap_scan(None)
                ESCANEANDO = False

                #Intentar conexión:
                try:
                    self._ble.gap_connect(addr_type, addr)
                except Exception as e:
                    print(e)



        elif event == _IRQ_SCAN_DONE:
            print("_IRQ_SCAN_DONE")
            # Scan duration finished or manually stopped.
            ESCANEANDO = False

        elif event == _IRQ_PERIPHERAL_CONNECT:
            print("_IRQ_PERIPHERAL_CONNECT", end=": ")
            # A successful gap_connect().

            conn_handle, addr_type, addr = data

            address = ":".join("{:02X}".format(b) for b in bytes(addr))
            print(f"Conectado al dispositivo: {address}")

            # Emparejar el dispositivo
            self._ble.gap_pair(conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            CONTROL_CONECTADO = False
            found_device = False
            print("_IRQ_PERIPHERAL_DISCONNECT", end=": ")
            # Connected peripheral has disconnected.
            conn_handle, addr_type, addr = data
            address = ":".join("{:02X}".format(b) for b in bytes(addr))
            print(f"Desconectado del dispositivo: {address}")

            self._ble.gap_scan(None)
            if not ESCANEANDO:
                self.scan()


        elif event == _IRQ_GATTC_SERVICE_RESULT:
            print("_IRQ_GATTC_SERVICE_RESULT")
            # Called for each service found by gattc_discover_services().
            conn_handle, start_handle, end_handle, uuid = data

        elif event == _IRQ_GATTC_SERVICE_DONE:
            print("_IRQ_GATTC_SERVICE_DONE")
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            print("_IRQ_GATTC_CHARACTERISTIC_RESULT")
            # Called for each characteristic found by gattc_discover_services().
            conn_handle, end_handle, value_handle, properties, uuid = data

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            print("_IRQ_GATTC_CHARACTERISTIC_DONE")
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data

        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
            print("_IRQ_GATTC_DESCRIPTOR_RESULT")
            # Called for each descriptor found by gattc_discover_descriptors().
            conn_handle, dsc_handle, uuid = data

        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            print("_IRQ_GATTC_DESCRIPTOR_DONE")
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data

        elif event == _IRQ_GATTC_READ_RESULT:
            print("_IRQ_GATTC_READ_RESULT")
            # A gattc_read() has completed.
            conn_handle, value_handle, char_data = data

        elif event == _IRQ_GATTC_READ_DONE:
            print("_IRQ_GATTC_READ_DONE")
            # A gattc_read() has completed.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data

        elif event == _IRQ_GATTC_WRITE_DONE:
            print("_IRQ_GATTC_WRITE_DONE")
            # A gattc_write() has completed.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data

        elif event == _IRQ_GATTC_NOTIFY:

            CONTROL_CONECTADO = True
            conn_handle, value_handle, notify_data = data

            # Convertir los datos a una lista de bytes
            notify_bytes = bytes(notify_data)

            # Depuración: mostrar los datos crudos
            print(f"Notificación recibida de handle {value_handle}: {notify_bytes}")

        elif event == _IRQ_GATTC_INDICATE:
            print("_IRQ_GATTC_INDICATE")
            # A server has sent an indicate request.
            conn_handle, value_handle, notify_data = data

        elif event == _IRQ_GATTS_INDICATE_DONE:
            print("_IRQ_GATTS_INDICATE_DONE")
            # A client has acknowledged the indication.
            # Note: Status will be zero on successful acknowledgment, implementation-specific value otherwise.
            conn_handle, value_handle, status = data

        elif event == _IRQ_MTU_EXCHANGED:
            print("_IRQ_MTU_EXCHANGED")
            # ATT MTU exchange complete (either initiated by us or the remote device).
            conn_handle, mtu = data

        elif event == _IRQ_L2CAP_ACCEPT:
            print("_IRQ_L2CAP_ACCEPT")
            # A new channel has been accepted.
            # Return a non-zero integer to reject the connection, or zero (or None) to accept.
            conn_handle, cid, psm, our_mtu, peer_mtu = data

        elif event == _IRQ_L2CAP_CONNECT:
            print("_IRQ_L2CAP_CONNECT")
            # A new channel is now connected (either as a result of connecting or accepting).
            conn_handle, cid, psm, our_mtu, peer_mtu = data

        elif event == _IRQ_L2CAP_DISCONNECT:
            print("_IRQ_L2CAP_DISCONNECT")
            # Existing channel has disconnected (status is zero), or a connection attempt failed (non-zero status).
            conn_handle, cid, psm, status = data

        elif event == _IRQ_L2CAP_RECV:
            print("_IRQ_L2CAP_RECV")
            # New data is available on the channel. Use l2cap_recvinto to read.
            conn_handle, cid = data

        elif event == _IRQ_L2CAP_SEND_READY:
            print("_IRQ_L2CAP_SEND_READY")
            # A previous l2cap_send that returned False has now completed and the channel is ready to send again.
            # If status is non-zero, then the transmit buffer overflowed and the application should re-send the data.
            conn_handle, cid, status = data

        elif event == _IRQ_CONNECTION_UPDATE:
            print("_IRQ_CONNECTION_UPDATE")
            # The remote device has updated connection parameters.
            conn_handle, conn_interval, conn_latency, supervision_timeout, status = data

        elif event == _IRQ_ENCRYPTION_UPDATE:
            print("_IRQ_ENCRYPTION_UPDATE")
            # The encryption state has changed (likely as a result of pairing or bonding).
            conn_handle, encrypted, authenticated, bonded, key_size = data

            print(f"Conexión cifrada: {encrypted}, autenticada: {authenticated}, vinculada: {bonded}, tamaño clave: {key_size}")


        elif event == _IRQ_GET_SECRET:
            print("_IRQ_GET_SECRET")
            # Manejo de solicitud de secreto
            sec_type, index, key = data

            # Verificar si el secreto existe
            if key is None:  # Devuelve el secreto por índice
                value = secrets_store.get((sec_type, index), None)

            else:  # Devuelve el secreto asociado al tipo y clave
                try:
                    value = secrets_store.get((sec_type, key), None)
                except Exception as e:
                    print(e)
                    value = None

            print(f"Solicitando secreto: sec_type={sec_type}, index={index}, key={key}, valor encontrado={value}")
            return value


        elif event == _IRQ_SET_SECRET:
            print("_IRQ_SET_SECRET")
            # Guardar un secreto
            sec_type, key, value = data


            # Convertir key a bytes para que sea hashable
            if key is not None:
                key = bytes(key)


            secrets_store[(sec_type, key)] = value

            print(f"Secreto guardado: sec_type={sec_type}, key={key}, value={value}")
            return True

        elif event == _IRQ_PASSKEY_ACTION:
            print("_IRQ_PASSKEY_ACTION")
            # Respond to a passkey request during pairing.
            # See gap_passkey() for details.
            # action will be an action that is compatible with the configured "io" config.
            # passkey will be non-zero if action is "numeric comparison".
            conn_handle, action, passkey = data

    def scan(self):
        print("Starting scan...")
        self._ble.gap_scan(15000, 100000, 25000, True)


def main():

    global ESCANEANDO
    ble = ubluetooth.BLE()
    central = BLESimpleCentral(ble)
    central.scan()
    ESCANEANDO = True
    global CONTROL_CONECTADO

    while not CONTROL_CONECTADO and not ESCANEANDO:
        central.scan()

if __name__ == "__main__":
    main()
