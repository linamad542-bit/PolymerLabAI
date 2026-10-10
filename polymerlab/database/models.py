"""
Polymer Data Models and Typed Structures
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class PropertyRange:
    min_val: float
    max_val: float
    typical: float
    unit: str

    def to_display(self) -> str:
        if self.min_val == self.max_val:
            return f"{self.typical} {self.unit}"
        return f"{self.min_val} – {self.max_val} {self.unit} (typ. {self.typical})"


@dataclass
class PolymerRecord:
    id: str
    name: str
    abbreviation: str
    common_names: List[str]
    chemical_formula: str
    cas_number: str
    spi_code: int  # Resin Identification Code (1 to 7)
    morphology: str  # Semicrystalline or Amorphous
    density: PropertyRange  # g/cm³
    glass_transition_temp: PropertyRange  # °C
    melting_temp: Optional[PropertyRange]  # °C, None for amorphous polymers
    youngs_modulus: PropertyRange  # MPa
    tensile_strength: PropertyRange  # MPa
    elongation_at_break: PropertyRange  # %
    flexural_modulus: PropertyRange  # MPa
    max_service_temp: PropertyRange  # °C
    chemical_resistance: str
    typical_applications: List[str]
    recyclability_notes: str
    advantages: List[str]
    limitations: List[str]
    astm_standards: List[str] = field(default_factory=list)
