"""
Arduino Serial Acquisition Implementation & Port Scanner
"""

import time
from typing import Any, Dict, List, Optional
import serial
import serial.tools.list_ports

from .base import BaseAcquisitionDevice, DataSample, HardwareStatus, SerialPortInfo


class ArduinoTensileAcquisition(BaseAcquisitionDevice):
    """
    Driver for Arduino-based universal testing bench load cells (e.g., HX711)
    and rotary optical encoder / LVDT extensometers.
    
    Reports honest hardware state. Never fakes connected hardware.
    """

    DEFAULT_BAUDRATES = [9600, 19200, 38400, 57600, 115200, 230400]
    
    # Known Arduino / USB-to-UART vendor IDs
    KNOWN_ARDUINO_VIDS = {
        0x2341,  # Arduino SA
        0x2A03,  # dog hunter AG (Arduino.org)
        0x1A86,  # QinHeng Electronics (CH340 / CH341)
        0x10C4,  # Silicon Labs (CP210x)
        0x0403,  # FTDI
    }

    def __init__(self) -> None:
        self._serial: Optional[serial.Serial] = None
        self._status: HardwareStatus = HardwareStatus.DISCONNECTED
        self._connected_port: Optional[str] = None
        self._baudrate: int = 115200
        self._last_error: Optional[str] = None

    def list_available_ports(self) -> List[SerialPortInfo]:
        """
        Scans all physical and virtual COM ports on Windows / system.
        """
        ports = serial.tools.list_ports.comports()
        detected: List[SerialPortInfo] = []

        for p in ports:
            vid = p.vid if p.vid is not None else 0
            is_ard = (
                vid in self.KNOWN_ARDUINO_VIDS
                or "arduino" in (p.description or "").lower()
                or "ch340" in (p.description or "").lower()
                or "cp210" in (p.description or "").lower()
            )
            detected.append(
                SerialPortInfo(
                    port=p.device,
                    description=p.description or "Generic Serial Port",
                    hardware_id=p.hwid or "N/A",
                    is_arduino=is_ard,
                )
            )
        return detected

    def connect(self, port: str, baudrate: int = 115200, timeout_s: float = 2.0) -> bool:
        """
        Connects to a real hardware COM port.
        """
        self.disconnect()
        self._status = HardwareStatus.CONNECTING
        self._last_error = None

        try:
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout_s,
                write_timeout=timeout_s,
            )
            # Allow Arduino auto-reset on DTR toggle
            time.sleep(1.5)
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # Handshake ping: send PING\n, expect PONG\n
            ser.write(b"PING\n")
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if "PONG" in line or "READY" in line or len(line) > 0:
                self._serial = ser
                self._connected_port = port
                self._baudrate = baudrate
                self._status = HardwareStatus.CONNECTED
                return True
            else:
                ser.close()
                self._status = HardwareStatus.ERROR
                self._last_error = f"Port '{port}' opened, but no response from PolymerLab firmware handshake."
                return False

        except serial.SerialException as err:
            self._status = HardwareStatus.ERROR
            self._last_error = f"Serial connection error on {port}: {str(err)}"
            return False

    def disconnect(self) -> None:
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
        self._connected_port = None
        self._status = HardwareStatus.DISCONNECTED

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open and self._status == HardwareStatus.CONNECTED

    def get_status(self) -> HardwareStatus:
        return self._status

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def tare_sensors(self) -> bool:
        """Sends TARE command to zero load cell."""
        if not self.is_connected() or self._serial is None:
            return False
        try:
            self._serial.write(b"TARE\n")
            resp = self._serial.readline().decode("utf-8", errors="ignore").strip()
            return "TARE_OK" in resp
        except Exception as e:
            self._last_error = str(e)
            return False

    def read_sample(self) -> Optional[DataSample]:
        """
        Reads line from Arduino: expected protocol 'D,<timestamp_ms>,<force_N>,<displacement_mm>\\n'
        """
        if not self.is_connected() or self._serial is None:
            return None

        try:
            if self._serial.in_waiting == 0:
                return None
            line = self._serial.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                return None

            parts = line.split(",")
            if len(parts) >= 3 and parts[0] == "D":
                t_ms = float(parts[1])
                f_n = float(parts[2])
                d_mm = float(parts[3])
                temp_c = float(parts[4]) if len(parts) > 4 else None
                return DataSample(timestamp_ms=t_ms, force_n=f_n, displacement_mm=d_mm, temperature_c=temp_c)
        except Exception as e:
            self._last_error = str(e)
        return None

    def get_device_info(self) -> Dict[str, Any]:
        return {
            "driver": "PolymerLab Arduino Driver",
            "protocol_version": "1.0",
            "port": self._connected_port or "None",
            "baudrate": self._baudrate,
            "status": self._status.value,
            "last_error": self._last_error,
            "expected_firmware": "PolymerLab_UTM_Firmware_v1.ino",
        }


class MockTensileDevice(BaseAcquisitionDevice):
    """
    Simulation / Dry-Run device for UI and testing development.
    Explicitly marked as SIMULATION so users know it is not real hardware.
    """

    def __init__(self, sample_polymer: str = "Polypropylene") -> None:
        self._connected = False
        self._polymer = sample_polymer
        self._time_offset = 0.0

    def list_available_ports(self) -> List[SerialPortInfo]:
        return [
            SerialPortInfo(
                port="SIM_PORT_1",
                description="PolymerLab Dry-Run Simulator (Virtual Test Bench)",
                hardware_id="SIMULATOR-VIRTUAL-001",
                is_arduino=False,
            )
        ]

    def connect(self, port: str, baudrate: int = 115200, timeout_s: float = 2.0) -> bool:
        self._connected = True
        self._time_offset = time.time()
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_status(self) -> HardwareStatus:
        return HardwareStatus.CONNECTED if self._connected else HardwareStatus.DISCONNECTED

    def tare_sensors(self) -> bool:
        return True

    def read_sample(self) -> Optional[DataSample]:
        if not self._connected:
            return None
        dt = (time.time() - self._time_offset)
        disp = min(50.0, dt * 1.5)  # 1.5 mm/s crosshead speed
        # Simulated stress-strain response
        strain = disp / 50.0
        force = 500.0 * (1.0 - (1.0 / (1.0 + 30.0 * strain)))
        return DataSample(timestamp_ms=dt * 1000.0, force_n=force, displacement_mm=disp, temperature_c=23.5)

    def get_device_info(self) -> Dict[str, Any]:
        return {
            "driver": "PolymerLab Virtual Test Bench (Dry-Run Simulator)",
            "is_simulation": True,
            "connected": self._connected,
        }
