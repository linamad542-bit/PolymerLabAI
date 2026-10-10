"""
Authentic Polymer Reference Database
Data verified against CRC Materials Science Handbook and Mark's Polymer Handbook.
"""

from typing import Dict, List, Optional
from .models import PolymerRecord, PropertyRange


class PolymerDatabase:
    """In-memory searchable scientific reference library for engineering polymers."""

    def __init__(self) -> None:
        self._polymers: Dict[str, PolymerRecord] = self._load_verified_records()

    def _load_verified_records(self) -> Dict[str, PolymerRecord]:
        records = [
            PolymerRecord(
                id="pe-hdpe",
                name="High-Density Polyethylene",
                abbreviation="HDPE (PE)",
                common_names=["HDPE", "Polyethylene High Density", "Polyethene"],
                chemical_formula="(C2H4)n",
                cas_number="9002-88-4",
                spi_code=2,
                morphology="Semicrystalline (60–80% crystallinity)",
                density=PropertyRange(0.941, 0.965, 0.952, "g/cm³"),
                glass_transition_temp=PropertyRange(-125.0, -110.0, -120.0, "°C"),
                melting_temp=PropertyRange(126.0, 137.0, 132.0, "°C"),
                youngs_modulus=PropertyRange(700.0, 1400.0, 1050.0, "MPa"),
                tensile_strength=PropertyRange(20.0, 38.0, 28.0, "MPa"),
                elongation_at_break=PropertyRange(100.0, 900.0, 500.0, "%"),
                flexural_modulus=PropertyRange(1000.0, 1500.0, 1250.0, "MPa"),
                max_service_temp=PropertyRange(70.0, 80.0, 75.0, "°C"),
                chemical_resistance="High resistance to strong acids, bases, and alcohols. Poor resistance to aromatic and chlorinated hydrocarbons.",
                typical_applications=[
                    "Potable water & gas distribution pipes",
                    "Chemical storage drums & containers",
                    "Blow-molded milk jugs & detergent bottles",
                    "Geomembranes & landfill liners",
                    "Bottle caps & injection-molded closures",
                ],
                recyclability_notes="Widely recycled worldwide (SPI Code #2). Readily reprocessed into pipes, plastic lumber, and crates.",
                advantages=[
                    "High strength-to-density ratio",
                    "Exceptional moisture barrier",
                    "High impact resistance even at low temperatures",
                    "Cost-effective and easy to process",
                ],
                limitations=[
                    "Susceptible to environmental stress cracking (ESCR)",
                    "High thermal expansion coefficient",
                    "Difficult to bond without surface treatment (corona/plasma)",
                ],
                astm_standards=["ASTM D1248", "ASTM D3350", "ASTM D638"],
            ),
            PolymerRecord(
                id="pe-ldpe",
                name="Low-Density Polyethylene",
                abbreviation="LDPE (PE)",
                common_names=["LDPE", "Polyethylene Low Density", "Branched Polyethylene"],
                chemical_formula="(C2H4)n",
                cas_number="9002-88-4",
                spi_code=4,
                morphology="Semicrystalline (40–55% crystallinity, highly branched)",
                density=PropertyRange(0.910, 0.930, 0.922, "g/cm³"),
                glass_transition_temp=PropertyRange(-125.0, -100.0, -115.0, "°C"),
                melting_temp=PropertyRange(105.0, 115.0, 110.0, "°C"),
                youngs_modulus=PropertyRange(150.0, 300.0, 220.0, "MPa"),
                tensile_strength=PropertyRange(8.0, 20.0, 13.0, "MPa"),
                elongation_at_break=PropertyRange(300.0, 700.0, 500.0, "%"),
                flexural_modulus=PropertyRange(200.0, 350.0, 280.0, "MPa"),
                max_service_temp=PropertyRange(60.0, 70.0, 65.0, "°C"),
                chemical_resistance="Resistant to acids, alkalis, and vegetable oils. Attacked by strong oxidizing agents and aromatic solvents.",
                typical_applications=[
                    "Blown film packaging (shopping bags, bread bags)",
                    "Squeeze bottles and laboratory wash bottles",
                    "Agricultural greenhouse covers",
                    "Wire & cable jacket insulation",
                ],
                recyclability_notes="Recyclable (SPI Code #4). Typically recycled into trash can liners, shipping envelopes, and floor tiles.",
                advantages=[
                    "High flexibility and elongation",
                    "Good clarity in thin films",
                    "Tough at cryogenic temperatures",
                    "Excellent electrical insulating properties",
                ],
                limitations=[
                    "Low tensile strength and stiffness",
                    "High gas permeability compared to barrier polymers",
                    "Lower temperature ceiling compared to HDPE and PP",
                ],
                astm_standards=["ASTM D1248", "ASTM D882"],
            ),
            PolymerRecord(
                id="pp",
                name="Polypropylene",
                abbreviation="PP",
                common_names=["PP", "Polypropene", "Isotactic Polypropylene"],
                chemical_formula="(C3H6)n",
                cas_number="9003-07-0",
                spi_code=5,
                morphology="Semicrystalline (50–60% crystallinity)",
                density=PropertyRange(0.895, 0.920, 0.905, "g/cm³"),
                glass_transition_temp=PropertyRange(-20.0, 0.0, -10.0, "°C"),
                melting_temp=PropertyRange(160.0, 168.0, 165.0, "°C"),
                youngs_modulus=PropertyRange(1100.0, 1600.0, 1350.0, "MPa"),
                tensile_strength=PropertyRange(30.0, 40.0, 35.0, "MPa"),
                elongation_at_break=PropertyRange(100.0, 600.0, 250.0, "%"),
                flexural_modulus=PropertyRange(1200.0, 1800.0, 1500.0, "MPa"),
                max_service_temp=PropertyRange(100.0, 115.0, 105.0, "°C"),
                chemical_resistance="Exceptional resistance to diluted and concentrated acids, alcohols, and bases. Swells in halogenated hydrocarbons.",
                typical_applications=[
                    "Integral living hinges (shampoo caps, container lids)",
                    "Microwaveable food packaging and reusable containers",
                    "Automotive battery cases and bumper fascias",
                    "Sterilizable medical equipment & disposable syringes",
                    "Synthetic carpet fibers and thermal textiles",
                ],
                recyclability_notes="Recyclable (SPI Code #5). Recycled into battery cables, broom bristles, and storage bins.",
                advantages=[
                    "Lowest density among high-volume commodity plastics",
                    "Superb flex fatigue resistance (living hinges)",
                    "Autoclavable and microwave-safe",
                    "Excellent chemical resistance",
                ],
                limitations=[
                    "Brittle below 0 °C (improved in copolymer grades)",
                    "Susceptible to UV degradation without UV stabilizers",
                    "High mold shrinkage",
                ],
                astm_standards=["ASTM D4101", "ASTM D638", "ASTM D790"],
            ),
            PolymerRecord(
                id="pet",
                name="Polyethylene Terephthalate",
                abbreviation="PET",
                common_names=["PET", "PETE", "Polyester", "Dacron", "Mylar"],
                chemical_formula="(C10H8O4)n",
                cas_number="25038-59-9",
                spi_code=1,
                morphology="Semicrystalline (strain-induced crystallization)",
                density=PropertyRange(1.33, 1.40, 1.38, "g/cm³"),
                glass_transition_temp=PropertyRange(67.0, 81.0, 74.0, "°C"),
                melting_temp=PropertyRange(250.0, 265.0, 255.0, "°C"),
                youngs_modulus=PropertyRange(2800.0, 3500.0, 3100.0, "MPa"),
                tensile_strength=PropertyRange(55.0, 80.0, 70.0, "MPa"),
                elongation_at_break=PropertyRange(30.0, 120.0, 60.0, "%"),
                flexural_modulus=PropertyRange(2700.0, 3400.0, 3000.0, "MPa"),
                max_service_temp=PropertyRange(115.0, 130.0, 120.0, "°C"),
                chemical_resistance="Good resistance to mineral oils, aliphatic hydrocarbons, and weak acids. Hydrolyzes in strong alkalis and boiling water.",
                typical_applications=[
                    "Carbonated soft drink and mineral water bottles",
                    "Synthetic textile fibers (clothing, fleece)",
                    "Thermoformed blister packs & food clamshells",
                    "Biaxially-oriented dielectric films (BOPET / Mylar)",
                ],
                recyclability_notes="Most widely recycled consumer plastic (SPI Code #1). Re-extruded into rPET flakes for clothing fibers and food-grade packaging.",
                advantages=[
                    "Superior gas barrier (CO2 and O2)",
                    "High optical clarity and glass-like appearance",
                    "High dimensional stability and tensile strength",
                    "Approved for direct food contact",
                ],
                limitations=[
                    "Hygroscopic - requires deep drying prior to melt processing",
                    "Susceptible to hydrolytic degradation at elevated melt temperatures",
                    "Not resistant to strong bases and ketones",
                ],
                astm_standards=["ASTM D4603", "ASTM D638"],
            ),
            PolymerRecord(
                id="pvc",
                name="Polyvinyl Chloride (Rigid / uPVC)",
                abbreviation="PVC",
                common_names=["PVC", "uPVC", "Rigid PVC", "Vinyl"],
                chemical_formula="(C2H3Cl)n",
                cas_number="9002-86-2",
                spi_code=3,
                morphology="Amorphous (predominantly atactic, ~5–10% syndiotactic microcrystallites)",
                density=PropertyRange(1.35, 1.45, 1.38, "g/cm³"),
                glass_transition_temp=PropertyRange(75.0, 85.0, 81.0, "°C"),
                melting_temp=None,  # Amorphous; decomposes prior to a true thermodynamic melting point
                youngs_modulus=PropertyRange(2400.0, 3400.0, 2900.0, "MPa"),
                tensile_strength=PropertyRange(40.0, 60.0, 52.0, "MPa"),
                elongation_at_break=PropertyRange(20.0, 80.0, 40.0, "%"),
                flexural_modulus=PropertyRange(2600.0, 3600.0, 3000.0, "MPa"),
                max_service_temp=PropertyRange(60.0, 70.0, 65.0, "°C"),
                chemical_resistance="Exceptional resistance to acids, salts, bases, and alcohols. Attacked by ketones, esters, and aromatic solvents.",
                typical_applications=[
                    "Plumbing, drainage, and sewer pipes",
                    "Window and door structural profiles",
                    "Exterior siding and gutters",
                    "Credit cards and ID cards",
                    "Rigid medical blister packaging",
                ],
                recyclability_notes="Recyclable (SPI Code #3). Reprocessed into speed bumps, mats, and guttering, though sorting is critical to avoid chlorine contamination.",
                advantages=[
                    "Inherent flame retardancy due to 57 wt% chlorine content",
                    "High stiffness, hardness, and durability",
                    "Outstanding outdoor weatherability",
                    "Cost-effective for building & infrastructure",
                ],
                limitations=[
                    "Low thermal degradation threshold (releases corrosive HCl gas without heat stabilizers)",
                    "Lower heat deflection temperature (60–70 °C)",
                    "Brittle at low temperatures without impact modifiers",
                ],
                astm_standards=["ASTM D1784", "ASTM D638"],
            ),
            PolymerRecord(
                id="ps",
                name="Polystyrene (General Purpose / GPPS)",
                abbreviation="PS",
                common_names=["PS", "GPPS", "Crystal Polystyrene"],
                chemical_formula="(C8H8)n",
                cas_number="9003-53-6",
                spi_code=6,
                morphology="Amorphous (atactic, no crystalline lattice)",
                density=PropertyRange(1.04, 1.07, 1.05, "g/cm³"),
                glass_transition_temp=PropertyRange(95.0, 105.0, 100.0, "°C"),
                melting_temp=None,  # Amorphous: softens at Tg, no true Tm
                youngs_modulus=PropertyRange(3000.0, 3500.0, 3200.0, "MPa"),
                tensile_strength=PropertyRange(35.0, 55.0, 45.0, "MPa"),
                elongation_at_break=PropertyRange(1.2, 3.0, 2.0, "%"),
                flexural_modulus=PropertyRange(3000.0, 3600.0, 3300.0, "MPa"),
                max_service_temp=PropertyRange(65.0, 75.0, 70.0, "°C"),
                chemical_resistance="Resistant to water, diluted acids, and bases. Dissolves rapidly in aromatic hydrocarbons (toluene, benzene), ketones, and chlorinated solvents.",
                typical_applications=[
                    "Petri dishes, cell culture plates, and laboratory test tubes",
                    "CD/DVD jewel cases and clear cosmetic display containers",
                    "Disposable clear drink cups and cutlery",
                    "Scale model hobby kits and refrigerator crisper drawers",
                ],
                recyclability_notes="Recyclable (SPI Code #6). Recycled into insulation boards, thermal rulers, and foam packaging.",
                advantages=[
                    "Sparkling optical clarity (refractive index ~1.59)",
                    "High dimensional stability and very low mold shrinkage",
                    "High surface hardness and stiffness",
                    "Economical for precision injection molding",
                ],
                limitations=[
                    "Extremely brittle at room temperature (elongation < 3%)",
                    "Poor solvent resistance (crazes and stress-cracks readily)",
                    "Flammable with dense soot emission",
                ],
                astm_standards=["ASTM D4549", "ASTM D638"],
            ),
            PolymerRecord(
                id="pmma",
                name="Poly(methyl methacrylate)",
                abbreviation="PMMA",
                common_names=["PMMA", "Acrylic", "Plexiglas", "Lucite", "Perspex"],
                chemical_formula="(C5O2H8)n",
                cas_number="9011-14-7",
                spi_code=7,
                morphology="Amorphous (atactic)",
                density=PropertyRange(1.17, 1.20, 1.18, "g/cm³"),
                glass_transition_temp=PropertyRange(100.0, 108.0, 105.0, "°C"),
                melting_temp=None,  # Amorphous: softens above 120-130 °C
                youngs_modulus=PropertyRange(2800.0, 3400.0, 3100.0, "MPa"),
                tensile_strength=PropertyRange(65.0, 80.0, 72.0, "MPa"),
                elongation_at_break=PropertyRange(2.0, 5.5, 3.5, "%"),
                flexural_modulus=PropertyRange(2900.0, 3500.0, 3200.0, "MPa"),
                max_service_temp=PropertyRange(75.0, 85.0, 80.0, "°C"),
                chemical_resistance="Resistant to non-oxidizing acids, aqueous salt solutions, and aliphatic hydrocarbons. Soluble in esters, ketones, and aromatics.",
                typical_applications=[
                    "Aircraft windshields, canopy glazing, and submarine viewports",
                    "Optical lenses, fiber-optic light guides, and prism displays",
                    "Automotive taillight lenses and instrumentation covers",
                    "Biomedical bone cement and intraocular lenses",
                    "Commercial aquariums and architectural glazed barriers",
                ],
                recyclability_notes="Recyclable (SPI Code #7 'Other'). Can be depolymerized by thermal cracking back to pure methyl methacrylate (MMA) monomer with high yield.",
                advantages=[
                    "Peerless optical transparency (~92% visible light transmission, superior to glass)",
                    "Outstanding UV radiation and weather resistance (decades outdoors without yellowing)",
                    "High scratch resistance compared to other transparent plastics",
                    "Excellent biocompatibility",
                ],
                limitations=[
                    "Brittle failure under high strain impact",
                    "Susceptible to solvent crazing (e.g. rubbing alcohol)",
                    "Moderate max service temperature (80 °C)",
                ],
                astm_standards=["ASTM D788", "ASTM D638"],
            ),
        ]
        return {r.id: r for r in records}

    def get_all(self) -> List[PolymerRecord]:
        return list(self._polymers.values())

    def get_by_id(self, polymer_id: str) -> Optional[PolymerRecord]:
        return self._polymers.get(polymer_id.lower())

    def search(
        self,
        query: str = "",
        spi_code: Optional[int] = None,
        morphology: Optional[str] = None,
        min_temp: Optional[float] = None,
    ) -> List[PolymerRecord]:
        results = []
        q = query.lower().strip()

        for poly in self._polymers.values():
            if spi_code is not None and poly.spi_code != spi_code:
                continue

            if morphology and morphology.lower() not in poly.morphology.lower():
                continue

            if min_temp is not None and poly.max_service_temp.typical < min_temp:
                continue

            if q:
                match = (
                    q in poly.name.lower()
                    or q in poly.abbreviation.lower()
                    or any(q in cn.lower() for cn in poly.common_names)
                    or q in poly.chemical_formula.lower()
                    or any(q in app.lower() for app in poly.typical_applications)
                    or q in poly.cas_number.lower()
                )
                if not match:
                    continue

            results.append(poly)

        return results


_DB_INSTANCE: Optional[PolymerDatabase] = None


def get_polymer_database() -> PolymerDatabase:
    global _DB_INSTANCE
    if _DB_INSTANCE is None:
        _DB_INSTANCE = PolymerDatabase()
    return _DB_INSTANCE
