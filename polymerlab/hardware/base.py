"""
Abstract Base Hardware Architecture for Polymer Testing Machines
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class HardwareStatus(str, Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    STREAMING = "Streaming"
    ERROR = "Error"


@dataclass
class DataSample:
    timestamp_ms: float
    force_n: float
    displacement_mm: float
    temperature_c: Optional[float] = None


@dataclass
class SerialPortInfo:
    port: str
    description: str
    hardware_id: str
    is_arduino: bool


class BaseAcquisitionDevice(ABC):
    """
    Standard interface for laboratory sensor acquisition systems
    (Universal Testing Machines, load cells, LVDT extensometers, microcontroller bridges).
    """

    @abstractmethod
    def list_available_ports(self) -> List[SerialPortInfo]:
        """Scans host system for real COM / TTY ports without faking devices."""
        pass

    @abstractmethod
    def connect(self, port: str, baudrate: int = 115200, timeout_s: float = 2.0) -> bool:
        """Establishes connection to the instrument."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Closes serial stream and releases hardware port."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Returns True only when an active, confirmed serial link is open."""
        pass

    @abstractmethod
    def get_status(self) -> HardwareStatus:
        """Returns current device lifecycle status."""
        pass

    @abstractmethod
    def read_sample(self) -> Optional[DataSample]:
        """Reads a single calibrated telemetry frame."""
        pass

    @abstractmethod
    def tare_sensors(self) -> bool:
        """Zeroes load cell and extensometer baseline."""
        pass

    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """Returns device metadata (firmware version, ADC resolution, calibration factor)."""
        pass
