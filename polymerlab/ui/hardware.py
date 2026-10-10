"""
Hardware & Arduino Interface Page
Modular architecture prepared for laboratory load cell acquisition.
Zero-fake policy: reports honest serial communication status.
"""

import streamlit as st
import pandas as pd
from polymerlab.hardware.serial_device import (
    ArduinoTensileAcquisition,
    MockTensileDevice,
)
from polymerlab.hardware.base import HardwareStatus


def render_hardware_manager() -> None:
    st.title("🔌 Hardware & Arduino Acquisition Bench")
    st.caption("Universal Testing Machine (UTM) Instrument Interfacing & Sensor Telemetry")

    # Initialize acquisition instances in session_state
    if "hardware_driver" not in st.session_state:
        st.session_state.hardware_driver = ArduinoTensileAcquisition()

    if "sim_driver" not in st.session_state:
        st.session_state.sim_driver = MockTensileDevice()

    driver: ArduinoTensileAcquisition = st.session_state.hardware_driver

    # Mode Selector: Real Serial vs Virtual Simulation
    mode = st.radio(
        "Hardware Operation Mode:",
        ["Physical Serial Connection (Arduino / USB)", "Offline Dry-Run Simulator (Virtual Test Bench)"],
        horizontal=True,
    )

    st.markdown("---")

    if mode == "Physical Serial Connection (Arduino / USB)":
        st.subheader("1. Host Serial Port Detection")

        # Scan host ports
        ports = driver.list_available_ports()

        if not ports:
            st.warning(
                "⚠️ **No COM ports detected on host system.** "
                "Ensure your Arduino microcontroller USB cable is plugged in."
            )
        else:
            st.success(f"Found {len(ports)} serial port(s) on Windows host:")
            port_table = []
            for p in ports:
                port_table.append({
                    "Port": p.port,
                    "Description": p.description,
                    "Hardware ID": p.hardware_id,
                    "Arduino Signature": "✅ Recognized" if p.is_arduino else "Generic COM",
                })
            st.dataframe(pd.DataFrame(port_table), use_container_width=True)

        st.subheader("2. Connection Controls")

        c1, c2, c3 = st.columns(3)
        with c1:
            port_names = [p.port for p in ports] if ports else ["No Ports Found"]
            selected_port = st.selectbox("Select COM Port:", port_names, disabled=not ports)
        with c2:
            baudrate = st.selectbox("Baud Rate:", driver.DEFAULT_BAUDRATES, index=4)  # 115200 default
        with c3:
            st.write("")
            st.write("")
            if driver.is_connected():
                if st.button("🔴 Disconnect Hardware", type="secondary"):
                    driver.disconnect()
                    st.rerun()
            else:
                if st.button("⚡ Connect to Arduino", type="primary", disabled=not ports):
                    success = driver.connect(selected_port, baudrate=baudrate)
                    if success:
                        st.success(f"Connected to {selected_port}!")
                    else:
                        st.error(driver.get_last_error() or "Connection failed.")
                    st.rerun()

        # Connection Telemetry Status
        status = driver.get_status()
        status_color = "red" if status == HardwareStatus.DISCONNECTED else ("green" if status == HardwareStatus.CONNECTED else "orange")
        st.markdown(
            f"**Current Status:** :{status_color}[**{status.value.upper()}**] "
            f"(Honest State: No fake hardware simulated in this mode)"
        )

        if driver.is_connected():
            st.success(f"Serial link active on `{selected_port}` @ {baudrate} baud.")
            if st.button("⚖️ Tare Sensors (Zero Load Cell & Extensometer)"):
                if driver.tare_sensors():
                    st.success("Load cell tared successfully.")
                else:
                    st.error("Tare command failed.")
        else:
            st.info(
                "💡 **Physical Hardware Notice**: PolymerLab AI is configured to interface with an Arduino running "
                "the `PolymerLab_UTM_Firmware_v1` firmware. When connected, it receives calibrated tensile force (N) "
                "and displacement (mm) in real-time."
            )

    else:
        # Offline Simulator Mode
        st.subheader("1. Virtual Test Bench Simulation")
        st.info("ℹ️ Running in **Virtual Dry-Run Simulator Mode** for offline UI and laboratory demonstration.")

        sim: MockTensileDevice = st.session_state.sim_driver
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if sim.is_connected():
                if st.button("⏹ Stop Virtual Acquisition", type="secondary"):
                    sim.disconnect()
                    st.rerun()
            else:
                if st.button("▶ Start Virtual Acquisition Run", type="primary"):
                    sim.connect("SIM_PORT_1")
                    st.rerun()

        with col_s2:
            st.metric("Virtual Instrument Status", "CONNECTED (Virtual)" if sim.is_connected() else "IDLE")

        if sim.is_connected():
            sample = sim.read_sample()
            if sample:
                st.write(f"**Latest Telemetry Frame:** Force: `{sample.force_n:.2f} N` | Crosshead: `{sample.displacement_mm:.2f} mm` | Temp: `{sample.temperature_c} °C`")

    # Technical Specifications & Firmware Blueprint
    st.markdown("---")
    st.subheader("3. Arduino Architecture & Protocol Specification")
    with st.expander("🛠 View Arduino Schematic & Serial Communication Protocol"):
        st.markdown(
            """
            #### Recommended Hardware Architecture:
            - **Microcontroller**: Arduino Uno R3 / R4, Nano, or ESP32.
            - **Load Cell Transducer**: S-beam or canister strain-gauge load cell (500 N – 5 kN capacity).
            - **Instrumentation Amplifier / ADC**: Avia Semiconductor **HX711** 24-bit differential ADC.
            - **Extensometer / Crosshead Encoder**: Optical quadrature rotary encoder attached to lead screw or linear LVDT.
            
            #### Serial Communication Protocol (115200 Baud, 8-N-1):
            1. **Handshake**: Host sends `PING\\n`, firmware replies `PONG\\n`.
            2. **Tare Command**: Host sends `TARE\\n`, firmware zeroes ADC offsets and replies `TARE_OK\\n`.
            3. **Telemetry Streaming**: Firmware continuously streams formatted CSV frames at 50 Hz:
            ```text
            D,<timestamp_ms>,<force_N>,<displacement_mm>,<optional_temp_C>\\r\\n
            ```
            Example:
            ```text
            D,1050,42.50,1.25,23.4
            D,1070,43.10,1.27,23.4
            ```
            """
        )
