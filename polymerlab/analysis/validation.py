"""
Input Validation, CSV Parser, and Unit Conversion for Mechanical Testing Data
"""

import io
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np


@dataclass
class ValidationResult:
    is_valid: bool
    data_format: str  # "STRESS_STRAIN" or "FORCE_DISPLACEMENT" or "UNKNOWN"
    df: Optional[pd.DataFrame] = None
    strain_col: Optional[str] = None
    stress_col: Optional[str] = None
    displacement_col: Optional[str] = None
    force_col: Optional[str] = None
    detected_strain_unit: str = "ratio"
    detected_stress_unit: str = "MPa"
    detected_displacement_unit: str = "mm"
    detected_force_unit: str = "N"
    strain_is_percentage: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# Unit conversion factors to standard SI / Metric engineering units:
# Target Stress: MPa (N/mm²)
# Target Strain: ratio (mm/mm)
# Target Force: N
# Target Displacement: mm

STRESS_CONVERSIONS: Dict[str, float] = {
    "mpa": 1.0,
    "n/mm2": 1.0,
    "n/mm^2": 1.0,
    "gpa": 1000.0,
    "kpa": 0.001,
    "pa": 1e-6,
    "psi": 0.006894757,
    "ksi": 6.894757,
    "bar": 0.1,
}

FORCE_CONVERSIONS: Dict[str, float] = {
    "n": 1.0,
    "kn": 1000.0,
    "lbf": 4.448222,
    "kgf": 9.80665,
}

DISPLACEMENT_CONVERSIONS: Dict[str, float] = {
    "mm": 1.0,
    "m": 1000.0,
    "cm": 10.0,
    "in": 25.4,
    "inch": 25.4,
    "inches": 25.4,
    "um": 0.001,
    "µm": 0.001,
}

STRAIN_CONVERSIONS: Dict[str, float] = {
    "ratio": 1.0,
    "-": 1.0,
    "mm/mm": 1.0,
    "in/in": 1.0,
    "%": 0.01,
    "percent": 0.01,
    "pct": 0.01,
    "microstrain": 1e-6,
    "με": 1e-6,
    "ue": 1e-6,
}

# Synonyms for column identification
STRAIN_SYNONYMS = ["strain", "strain [-]", "strain (%)", "engineering strain", "elongation", "strain_ratio"]
STRESS_SYNONYMS = ["stress", "stress (mpa)", "stress_mpa", "engineering stress (mpa)", "tensile stress"]
DISPLACEMENT_SYNONYMS = ["displacement", "displacement (mm)", "displacement_mm", "extension", "extension (mm)", "stroke"]
FORCE_SYNONYMS = ["force", "force (n)", "force_n", "load", "load (n)", "load_n"]

# Column tokens to reject when searching for primary strain/stress columns
FORBIDDEN_MODIFIERS = ["rate", "speed", "velocity", "time", "error", "std", "stdev", "uncertainty"]


def extract_unit_from_header(header: str, quantity_type: str) -> Optional[str]:
    """
    Extracts explicit measurement unit from column header.
    E.g.: 'Stress (MPa)' -> 'mpa', 'Strain [%]' -> '%', 'Force [kN]' -> 'kn'.
    """
    cleaned = header.strip().lower()
    # Find text inside brackets, parentheses, or trailing after underscore / slash
    matches = re.findall(r"[\(\[\{/\_]([^\)\]\}\s]+)[\)\]\}]?", cleaned)
    tokens = matches if matches else cleaned.split()

    if quantity_type == "stress":
        for tok in tokens:
            t = tok.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
            if t in STRESS_CONVERSIONS:
                return t
        # Direct check
        for unit in STRESS_CONVERSIONS:
            if re.search(rf"\b{re.escape(unit)}\b", cleaned):
                return unit

    elif quantity_type == "strain":
        if "%" in cleaned or "pct" in cleaned or "percent" in cleaned:
            return "%"
        if "microstrain" in cleaned or "με" in cleaned or "ue" in cleaned:
            return "microstrain"
        if "mm/mm" in cleaned or "in/in" in cleaned or "[-]" in cleaned or "ratio" in cleaned:
            return "ratio"

    elif quantity_type == "force":
        for tok in tokens:
            t = tok.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
            if t in FORCE_CONVERSIONS:
                return t
        for unit in FORCE_CONVERSIONS:
            if re.search(rf"\b{re.escape(unit)}\b", cleaned):
                return unit

    elif quantity_type == "displacement":
        for tok in tokens:
            t = tok.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
            if t in DISPLACEMENT_CONVERSIONS:
                return t
        for unit in DISPLACEMENT_CONVERSIONS:
            if re.search(rf"\b{re.escape(unit)}\b", cleaned):
                return unit

    return None


def convert_stress_to_mpa(values: np.ndarray, unit: str) -> np.ndarray:
    """Converts input stress array to standard MPa."""
    factor = STRESS_CONVERSIONS.get(unit.lower(), 1.0)
    return np.asarray(values, dtype=float) * factor


def convert_strain_to_ratio(values: np.ndarray, unit: str) -> np.ndarray:
    """Converts input strain array to dimensionless ratio (mm/mm)."""
    factor = STRAIN_CONVERSIONS.get(unit.lower(), 1.0)
    return np.asarray(values, dtype=float) * factor


def convert_force_to_n(values: np.ndarray, unit: str) -> np.ndarray:
    """Converts input force array to standard N."""
    factor = FORCE_CONVERSIONS.get(unit.lower(), 1.0)
    return np.asarray(values, dtype=float) * factor


def convert_displacement_to_mm(values: np.ndarray, unit: str) -> np.ndarray:
    """Converts input displacement array to standard mm."""
    factor = DISPLACEMENT_CONVERSIONS.get(unit.lower(), 1.0)
    return np.asarray(values, dtype=float) * factor


def _is_forbidden_column(col: str) -> bool:
    """Checks if column contains modifier like 'rate' that invalidates it as primary variable."""
    col_lower = col.strip().lower()
    return any(re.search(rf"\b{mod}\b", col_lower) for mod in FORBIDDEN_MODIFIERS)


def _match_column(df_columns: List[str], synonyms: List[str]) -> Optional[str]:
    """
    Finds matching column prioritizing exact matches and rejecting anti-synonyms (e.g. 'strain rate').
    """
    # Filter out forbidden columns first
    candidates = [c for c in df_columns if not _is_forbidden_column(c)]

    # 1. Exact match pass
    for col in candidates:
        clean_col = col.strip().lower().replace("_", " ").replace("-", " ")
        for syn in synonyms:
            clean_syn = syn.lower().replace("_", " ").replace("-", " ")
            if clean_col == clean_syn:
                return col

    # 2. Prefix / containment pass
    for col in candidates:
        clean_col = col.strip().lower().replace("_", " ").replace("-", " ")
        for syn in synonyms:
            clean_syn = syn.lower().replace("_", " ").replace("-", " ")
            if clean_col.startswith(clean_syn) or clean_syn in clean_col:
                return col

    return None


def validate_mechanical_csv(
    file_or_content: Union[str, bytes, io.StringIO, io.BytesIO],
    filename: str = "upload.csv",
) -> ValidationResult:
    """
    Validates uploaded CSV file against polymer mechanical testing requirements.
    Supports UTM preambles (comment lines starting with #), multiple delimiters,
    and automatic unit detection without corrupting high-ductility polymer strains.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Attempt reading CSV with standard delimiters and comment handling
    df: Optional[pd.DataFrame] = None
    delimiters = [",", ";", "\t", r"\s+"]

    for sep in delimiters:
        try:
            if isinstance(file_or_content, bytes):
                stream = io.BytesIO(file_or_content)
            elif isinstance(file_or_content, str):
                stream = io.StringIO(file_or_content)
            else:
                file_or_content.seek(0)
                stream = file_or_content

            temp_df = pd.read_csv(stream, sep=sep, comment="#", engine="python")
            if temp_df.shape[1] >= 2 and temp_df.shape[0] >= 1:
                df = temp_df
                break
        except Exception:
            continue

    if df is None or df.empty:
        return ValidationResult(
            is_valid=False,
            data_format="UNKNOWN",
            errors=["The uploaded file could not be parsed as a valid delimited CSV or is empty."],
        )

    # 2. Check minimum data row count
    if len(df) < 10:
        errors.append(f"File contains only {len(df)} data rows. Tensile testing analysis requires at least 10 data points.")

    # 3. Identify Columns
    cols = list(df.columns)
    strain_col = _match_column(cols, STRAIN_SYNONYMS)
    stress_col = _match_column(cols, STRESS_SYNONYMS)
    disp_col = _match_column(cols, DISPLACEMENT_SYNONYMS)
    force_col = _match_column(cols, FORCE_SYNONYMS)

    data_format = "UNKNOWN"

    if strain_col and stress_col:
        data_format = "STRESS_STRAIN"
    elif disp_col and force_col:
        data_format = "FORCE_DISPLACEMENT"
    elif len(cols) == 2:
        # Fallback to column names if only 2 columns exist
        col1_lower = str(cols[0]).lower()
        col2_lower = str(cols[1]).lower()
        if "load" in col2_lower or "force" in col2_lower or "stress" in col2_lower:
            if "stress" in col2_lower:
                data_format = "STRESS_STRAIN"
                strain_col = cols[0]
                stress_col = cols[1]
            else:
                data_format = "FORCE_DISPLACEMENT"
                disp_col = cols[0]
                force_col = cols[1]
        else:
            data_format = "STRESS_STRAIN"
            strain_col = cols[0]
            stress_col = cols[1]
            warnings.append(
                f"Columns '{cols[0]}' and '{cols[1]}' were mapped automatically as Strain and Stress. Please verify."
            )
    else:
        errors.append(
            f"Could not identify required columns in {cols}. Expected either: "
            "['Strain', 'Stress'] or ['Displacement', 'Force']."
        )
        return ValidationResult(is_valid=False, data_format="UNKNOWN", df=df, errors=errors)

    # 4. Clean and convert numeric types
    target_cols = [strain_col, stress_col] if data_format == "STRESS_STRAIN" else [disp_col, force_col]
    clean_df = df.copy()

    for col in target_cols:
        if col not in clean_df:
            continue
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    # Drop rows with NaN or infinite values in critical columns
    before_drop = len(clean_df)
    clean_df = clean_df.dropna(subset=[c for c in target_cols if c is not None])
    clean_df = clean_df[~clean_df[target_cols[0]].isin([np.inf, -np.inf])]
    clean_df = clean_df[~clean_df[target_cols[1]].isin([np.inf, -np.inf])]
    dropped = before_drop - len(clean_df)

    if dropped > 0:
        warnings.append(f"Dropped {dropped} non-numeric or blank rows.")

    if len(clean_df) < 10:
        errors.append("Fewer than 10 valid numeric data rows remain after dropping non-numeric values.")
        return ValidationResult(is_valid=False, data_format=data_format, df=clean_df, errors=errors, warnings=warnings)

    # 5. Unit Detection & Conversion Inspection
    detected_strain_unit = "ratio"
    detected_stress_unit = "MPa"
    detected_force_unit = "N"
    detected_displacement_unit = "mm"
    strain_is_percentage = False

    if data_format == "STRESS_STRAIN" and strain_col and stress_col:
        u_stress = extract_unit_from_header(strain_col if "stress" in strain_col.lower() else stress_col, "stress")
        if u_stress:
            detected_stress_unit = u_stress
            if u_stress.lower() != "mpa":
                warnings.append(f"Detected stress unit '{u_stress.upper()}'. Values will be converted to standard MPa.")

        u_strain = extract_unit_from_header(strain_col, "strain")
        max_strain_val = clean_df[strain_col].max()

        if u_strain == "%":
            strain_is_percentage = True
            detected_strain_unit = "%"
        elif u_strain == "ratio":
            strain_is_percentage = False
            detected_strain_unit = "ratio"
        else:
            # Unit not stated explicitly in header
            # High-ductility polymers (LDPE, PTFE) often reach strain > 1.5 ratio (150% - 700%).
            # Do NOT assume it is percentage unless it exceeds reasonable ratio bounds (e.g. > 15.0)
            if max_strain_val > 15.0:
                strain_is_percentage = True
                detected_strain_unit = "%"
                warnings.append(
                    f"Maximum strain value is {max_strain_val:.1f} without explicit unit in header. "
                    "Interpreted as percentage (%) values."
                )
            elif max_strain_val > 1.5:
                warnings.append(
                    f"Maximum strain value is {max_strain_val:.2f}. "
                    "Could be a high-ductility polymer in dimensionless ratio (mm/mm) or percentage (%). Please verify."
                )

        # Check negative stress
        min_stress = clean_df[stress_col].min()
        if min_stress < -5.0:
            warnings.append(f"Found negative stress values ({min_stress:.2f} MPa). May indicate pre-load compression or sensor drift.")

    elif data_format == "FORCE_DISPLACEMENT" and disp_col and force_col:
        u_force = extract_unit_from_header(force_col, "force")
        if u_force:
            detected_force_unit = u_force
            if u_force.lower() != "n":
                warnings.append(f"Detected force unit '{u_force}'. Values will be converted to standard N.")

        u_disp = extract_unit_from_header(disp_col, "displacement")
        if u_disp:
            detected_displacement_unit = u_disp
            if u_disp.lower() != "mm":
                warnings.append(f"Detected displacement unit '{u_disp}'. Values will be converted to standard mm.")

    return ValidationResult(
        is_valid=(len(errors) == 0),
        data_format=data_format,
        df=clean_df,
        strain_col=strain_col,
        stress_col=stress_col,
        displacement_col=disp_col,
        force_col=force_col,
        detected_strain_unit=detected_strain_unit,
        detected_stress_unit=detected_stress_unit,
        detected_force_unit=detected_force_unit,
        detected_displacement_unit=detected_displacement_unit,
        strain_is_percentage=strain_is_percentage,
        errors=errors,
        warnings=warnings,
    )
