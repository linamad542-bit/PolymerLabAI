"""
PolymerLab AI - Core Configuration & Scientific Constants
"""

from typing import Dict, Any

APP_NAME = "PolymerLab AI"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Intelligent Polymer Science & Mechanical Testing Suite"

# Referenced Engineering Standards (Calculation Methodologies Modeled)
# Note: Algorithmic screening implementation. Physical compliance requires accredited laboratory metrology.
SUPPORTED_STANDARDS = [
    "ASTM D638 (Tensile Properties of Plastics - Tensile Test Methodology)",
    "ISO 527-1 / ISO 527-2 (Determination of Tensile Properties of Plastics)",
    "ASTM D790 (Flexural Properties of Unreinforced and Reinforced Plastics - Reference)",
    "ISO 178 (Determination of Flexural Properties - Reference)",
]

# Physical Units Reference
UNITS: Dict[str, str] = {
    "stress": "MPa",
    "strain": "% (or mm/mm)",
    "modulus": "MPa (or GPa)",
    "force": "N",
    "displacement": "mm",
    "energy_toughness": "MJ/m³",
    "density": "g/cm³",
    "temperature": "°C",
}
