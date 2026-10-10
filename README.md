# PolymerLab AI ðŸ§ª

**PolymerLab AI** is an intelligent, professional polymer science and mechanical testing laboratory suite built in Python 3.11 with Streamlit.

---

## ðŸŒŸ Features

1. **Scientific Dashboard**
   - Material KPI metrics and comparative material benchmarking.
   - Interactive stiffness, tensile strength, and multi-attribute property radar charts.
   - Transparent hardware status indicator.

2. **Searchable Polymer Reference Library**
   - Curated reference data for **PE** (HDPE & LDPE), **PP**, **PET**, **PVC**, **PS**, and **PMMA**.
   - Verified scientific values from *CRC Materials Science and Engineering Handbook* and *Mark's Polymer Handbook*.
   - Filter by SPI Resin Identification Code (#1 to #7), morphology (Semicrystalline vs. Amorphous), and search across chemical formula, CAS number, or applications.
   - Interactive radar and bar chart comparisons across polymers.

3. **Mechanical Testing Lab (ASTM D638 / ISO 527 Principles)**
   - Upload tensile test CSVs or select bundled pre-calibrated sample datasets.
   - Robust input validation and unit detection:
     - Stress: `MPa`, `GPa`, `kPa`, `Pa`, `psi`, `ksi` $\to$ automatically normalized to $\text{MPa}$.
     - Strain: `%`, ratio (`mm/mm`), `microstrain` $\to$ normalized to dimensionless ratio. High-ductility polymers ($\epsilon > 1.5$) are handled safely without false percentage division.
     - Force & Stroke: `N`, `kN`, `lbf` and `mm`, `m`, `in` $\to$ converted with specimen gauge length and cross-section ($L_0, w, t$).
   - Automatic extraction of:
     - **Young's Modulus ($E$)** [MPa and GPa] with $R^2$ linear fit coefficient.
     - **Yield Strength ($\sigma_y$)** via exact analytical 0.2% offset intersection or upper yield peak with sustained drop validation (noise-immune).
     - **Ultimate Tensile Strength (UTS)**.
     - **Elongation at Break ($\epsilon_b$)** [%] with catastrophic fracture drop detection.
     - **Tensile Toughness (Modulus of Toughness, $U_t$)** [$MJ/m^3$] via trapezoidal integration.
     - **Modulus of Resilience ($U_r$)** [$MJ/m^3$].
     - **Scientifically Grounded Failure Classification** (Brittle Fracture, Ductile with Necking, Highly Ductile / Cold Drawing, Flexible / Elastomeric).
   - Interactive Plotly stressâ€“strain curve with toggleable tangent line, 0.2% offset line, and shaded toughness area.
   - Export standardized curve (CSV) and full experimental analysis report (JSON).

4. **Modular Hardware & Arduino Integration Architecture**
   - Real Windows serial COM port scanning using `pyserial`.
   - **Zero-fake policy**: Reports real connection status (`Disconnected` when no hardware is attached).
   - Documented serial communication wire protocol (`PING`/`PONG`, `TARE`, and `D,<t>,<f>,<d>\n` telemetry).
   - Optional dry-run virtual test bench simulator for offline laboratory demonstrations.

5. **Automated Testing Suite**
   - 38 automated unit tests verifying calculations, unit conversions, database integrity, CSV validation, edge cases, and hardware drivers with `pytest`.

---

## âš ï¸ Scientific Limitations & Metrology Notice

1. **Screening Tool vs. Commercial Metrology**: The algorithms implemented in this package are derived from the mathematical formulations outlined in ASTM D638 and ISO 527-1. However, results are intended for research, educational, and computational screening purposes. They do not constitute certified compliance without physical testing on accredited, calibrated instruments (ISO/IEC 17025).
2. **Crosshead vs. Extensometer Compliance**: When displacement is recorded from machine crosshead stroke rather than a clip-on or optical/video extensometer, the measured deformation includes grip seating and machine frame compliance. This systematically **underestimates** the true Young's modulus of rigid plastics.
3. **Toe Region Compensation**: Initial curve curvature (toe region) is corrected using linear regression extrapolation ($\epsilon_{toe} = -\sigma_0 / E$). This serves as an automated approximation of ASTM D638 Section 10.3 manual tangent construction.
4. **Viscoelastic Sensitivity**: Thermoplastics exhibit pronounced strain-rate and temperature dependency. Modulus and yield stresses obtained from static tensile tests cannot be directly extrapolated to high-speed impact or elevated-temperature behavior.

---

## ðŸ“Š Benchmark Dataset Provenance

The bundled datasets in `data/`:
- `data/sample_tensile_pp.csv` (Polypropylene ductile curve)
- `data/sample_tensile_pmma.csv` (PMMA brittle curve)
- `data/sample_raw_load_displacement.csv` (UTM machine load-displacement curve)

**PROVENANCE DISCLOSURE**: These datasets are **idealized synthetic curves** generated algorithmically to represent typical constitutive tensile phenomena (Hookean elasticity, upper yield drop, cold drawing plateau, and catastrophic brittle fracture). They are provided for software verification, unit tests, and UI testing, and are **not** experimental records from an external physical load cell.

---

## ðŸ“ Project Structure

```text
PolymerLabAI/
â”œâ”€â”€ .venv/                         # Python 3.11 Virtual Environment
â”œâ”€â”€ app.py                         # Main Streamlit application entry point
â”œâ”€â”€ requirements.txt               # Application dependencies
â”œâ”€â”€ README.md                      # Documentation and run instructions
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ sample_tensile_pp.csv      # Synthetic Ductile PP tensile dataset
â”‚   â”œâ”€â”€ sample_tensile_pmma.csv    # Synthetic Brittle PMMA tensile dataset
â”‚   â””â”€â”€ sample_raw_load_displacement.csv # Synthetic UTM force & stroke dataset
â”œâ”€â”€ polymerlab/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ config.py                  # Scientific units and referenced standards
â”‚   â”œâ”€â”€ database/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ models.py              # Polymer record dataclasses
â”‚   â”‚   â””â”€â”€ polymer_db.py          # Authentic polymer reference database
â”‚   â”œâ”€â”€ analysis/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ mechanical.py          # Tensile stress-strain computation engine
â”‚   â”‚   â””â”€â”€ validation.py          # CSV schema & unit conversion validator
â”‚   â”œâ”€â”€ hardware/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ base.py                # Abstract acquisition base classes
â”‚   â”‚   â””â”€â”€ serial_device.py       # Arduino serial driver & virtual simulator
â”‚   â”œâ”€â”€ ui/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ dashboard.py           # Dashboard view
â”‚   â”‚   â”œâ”€â”€ library.py             # Reference library view
â”‚   â”‚   â”œâ”€â”€ mechanical.py          # Mechanical testing lab view
â”‚   â”‚   â””â”€â”€ hardware.py            # Hardware acquisition manager view
â”‚   â””â”€â”€ visualization/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â””â”€â”€ plots.py               # Plotly interactive graphs and radar charts
â””â”€â”€ tests/
    â”œâ”€â”€ test_polymer_db.py         # Polymer database tests
    â”œâ”€â”€ test_mechanical.py         # Calculation, noise jitter, and edge-case tests
    â”œâ”€â”€ test_validation.py         # Unit conversion, header, and format tests
    â””â”€â”€ test_hardware.py           # Serial scanner & simulator tests
```

---

## ðŸš€ Windows Setup & Run Instructions

### 1. Prerequisites
- Windows 10/11
- Python 3.11 (installed and configured)

### 2. Activate Virtual Environment (PowerShell)
Open PowerShell in the project directory:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Run Automated Tests
Execute the 34-test suite using pytest:
```powershell
.\.venv\Scripts\pytest.exe -v
```

### 4. Launch the Application
Start the Streamlit interface:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Navigate to: **`http://localhost:8501`**


