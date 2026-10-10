"""
Automated tests for Hardware Interfaces and Serial Scanner
"""

import pytest
from polymerlab.hardware.base import HardwareStatus
from polymerlab.hardware.serial_device import ArduinoTensileAcquisition, MockTensileDevice


def test_arduino_scanner_runs_without_exceptions():
    device = ArduinoTensileAcquisition()
    ports = device.list_available_ports()
    assert isinstance(ports, list)
    # Does not throw errors, returns standard port list structure


def test_disconnected_hardware_state():
    device = ArduinoTensileAcquisition()
    assert not device.is_connected()
    assert device.get_status() == HardwareStatus.DISCONNECTED
    assert device.read_sample() is None
    assert device.tare_sensors() is False


def test_failed_connection_to_invalid_port():
    device = ArduinoTensileAcquisition()
    # Connecting to non-existent COM999 should fail safely and not crash
    success = device.connect("COM999_NON_EXISTENT", timeout_s=0.2)
    assert not success
    assert not device.is_connected()
    assert device.get_status() == HardwareStatus.ERROR
    assert device.get_last_error() is not None


def test_mock_device_lifecycle():
    mock = MockTensileDevice()
    assert not mock.is_connected()
    assert mock.get_status() == HardwareStatus.DISCONNECTED

    success = mock.connect("SIM_PORT_1")
    assert success
    assert mock.is_connected()
    assert mock.get_status() == HardwareStatus.CONNECTED

    # Check sample reading
    sample = mock.read_sample()
    assert sample is not None
    assert sample.force_n >= 0.0
    assert sample.displacement_mm >= 0.0

    mock.disconnect()
    assert not mock.is_connected()
    assert mock.get_status() == HardwareStatus.DISCONNECTED
