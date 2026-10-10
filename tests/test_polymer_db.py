"""
Automated tests for Polymer Reference Database
"""

import pytest
from polymerlab.database.polymer_db import get_polymer_database, PolymerDatabase


def test_database_initialization():
    db = get_polymer_database()
    assert isinstance(db, PolymerDatabase)
    polymers = db.get_all()
    # At least HDPE, LDPE, PP, PET, PVC, PS, PMMA
    assert len(polymers) >= 7


def test_required_polymers_present():
    db = get_polymer_database()
    expected_ids = {"pe-hdpe", "pe-ldpe", "pp", "pet", "pvc", "ps", "pmma"}
    actual_ids = {p.id for p in db.get_all()}
    assert expected_ids.issubset(actual_ids), f"Missing polymers: {expected_ids - actual_ids}"


def test_authentic_polymer_properties():
    db = get_polymer_database()
    for poly in db.get_all():
        # Density must be positive and typical for polymers (0.8 - 2.0 g/cm³)
        assert 0.8 <= poly.density.typical <= 2.0
        assert poly.density.min_val <= poly.density.typical <= poly.density.max_val

        # Modulus must be strictly positive (50 - 5000 MPa)
        assert 50.0 <= poly.youngs_modulus.typical <= 5000.0

        # Tensile strength must be positive (5 - 150 MPa)
        assert 5.0 <= poly.tensile_strength.typical <= 150.0

        # Elongation at break must be positive
        assert poly.elongation_at_break.typical > 0.0

        # SPI resin identification code must be between 1 and 7
        assert 1 <= poly.spi_code <= 7


def test_database_search():
    db = get_polymer_database()
    
    # Search by abbreviation
    pp_results = db.search(query="PP")
    assert any(p.id == "pp" for p in pp_results)

    # Search by application keyword
    hinge_results = db.search(query="living hinges")
    assert any(p.id == "pp" for p in hinge_results)

    # Filter by SPI code
    spi_1_results = db.search(spi_code=1)
    assert len(spi_1_results) == 1
    assert spi_1_results[0].id == "pet"

    # Filter by morphology
    amorphous_results = db.search(morphology="Amorphous")
    amorphous_ids = {p.id for p in amorphous_results}
    assert "ps" in amorphous_ids
    assert "pmma" in amorphous_ids
    assert "pe-hdpe" not in amorphous_ids
