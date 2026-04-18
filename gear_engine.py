import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_PRESSURE_ANGLE = 20.0
MODULE_COMPARE_TOLERANCE = 1e-4
VALUE_TOLERANCE = 1e-3
ANGLE_TOLERANCE = 1e-6
TOOTH_INFERENCE_TOLERANCE = 0.05


class InputError(Exception):
    """Raised when the entered gear data cannot be solved safely."""


@dataclass(frozen=True)
class GearInputs:
    module: Optional[float] = None
    teeth: Optional[float] = None
    pressure_angle: Optional[float] = None
    pitch_diameter: Optional[float] = None
    outside_diameter: Optional[float] = None
    root_diameter: Optional[float] = None
    base_diameter: Optional[float] = None
    addendum: Optional[float] = None
    dedendum: Optional[float] = None
    circular_pitch: Optional[float] = None
    tooth_thickness: Optional[float] = None

    @classmethod
    def from_dict(cls, values: Dict[str, Optional[float]]) -> "GearInputs":
        return cls(**values)

    def as_dict(self) -> Dict[str, Optional[float]]:
        return {
            "module": self.module,
            "teeth": self.teeth,
            "pressure_angle": self.pressure_angle,
            "pitch_diameter": self.pitch_diameter,
            "outside_diameter": self.outside_diameter,
            "root_diameter": self.root_diameter,
            "base_diameter": self.base_diameter,
            "addendum": self.addendum,
            "dedendum": self.dedendum,
            "circular_pitch": self.circular_pitch,
            "tooth_thickness": self.tooth_thickness,
        }


@dataclass(frozen=True)
class GearResult:
    module: float
    teeth: int
    pressure_angle: float
    pitch_diameter: float
    outside_diameter: float
    root_diameter: float
    base_diameter: float
    addendum: float
    dedendum: float
    circular_pitch: float
    tooth_thickness: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "module": self.module,
            "teeth": float(self.teeth),
            "pressure_angle": self.pressure_angle,
            "pitch_diameter": self.pitch_diameter,
            "outside_diameter": self.outside_diameter,
            "root_diameter": self.root_diameter,
            "base_diameter": self.base_diameter,
            "addendum": self.addendum,
            "dedendum": self.dedendum,
            "circular_pitch": self.circular_pitch,
            "tooth_thickness": self.tooth_thickness,
        }


FIELD_LABELS = {
    "module": "Module",
    "teeth": "Number of teeth",
    "pressure_angle": "Pressure angle",
    "pitch_diameter": "Pitch diameter",
    "outside_diameter": "Outside diameter",
    "root_diameter": "Root diameter",
    "base_diameter": "Base diameter",
    "addendum": "Addendum",
    "dedendum": "Dedendum",
    "circular_pitch": "Circular pitch",
    "tooth_thickness": "Tooth thickness",
}

FIELD_UNITS = {
    "module": "mm",
    "teeth": "",
    "pressure_angle": "deg",
    "pitch_diameter": "mm",
    "outside_diameter": "mm",
    "root_diameter": "mm",
    "base_diameter": "mm",
    "addendum": "mm",
    "dedendum": "mm",
    "circular_pitch": "mm",
    "tooth_thickness": "mm",
}


def is_positive(value: Optional[float]) -> bool:
    return value is not None and value > 0


def infer_integer(value: float, source_name: str) -> int:
    rounded = round(value)
    if abs(value - rounded) > TOOTH_INFERENCE_TOLERANCE:
        raise InputError(
            f"{source_name} implies a non-integer tooth count ({value:.3f}). "
            "Check the entered dimensions or tooth count."
        )
    if rounded <= 0:
        raise InputError("Number of teeth must be greater than zero.")
    return int(rounded)


def _validate_consistent_candidates(candidates: Iterable[Tuple[str, float]], tolerance: float) -> float:
    candidate_list = list(candidates)
    if not candidate_list:
        raise InputError("No candidates were available for this calculation.")

    reference_name, reference_value = candidate_list[0]
    for name, value in candidate_list[1:]:
        if abs(value - reference_value) > tolerance:
            raise InputError(
                f"{FIELD_LABELS.get(name, name)} conflicts with "
                f"{FIELD_LABELS.get(reference_name, reference_name)}."
            )
    return reference_value


def derive_module_from_inputs(values: GearInputs) -> Optional[float]:
    candidates: List[Tuple[str, float]] = []

    if is_positive(values.module):
        candidates.append(("module", values.module))
    if is_positive(values.addendum):
        candidates.append(("addendum", values.addendum))
    if is_positive(values.dedendum):
        candidates.append(("dedendum", values.dedendum / 1.25))
    if is_positive(values.circular_pitch):
        candidates.append(("circular_pitch", values.circular_pitch / math.pi))
    if is_positive(values.tooth_thickness):
        candidates.append(("tooth_thickness", (2 * values.tooth_thickness) / math.pi))

    if not candidates:
        return None

    return _validate_consistent_candidates(candidates, MODULE_COMPARE_TOLERANCE)


def derive_teeth_from_inputs(values: GearInputs, module: float) -> Optional[int]:
    candidates: List[Tuple[str, int]] = []

    if is_positive(values.teeth):
        candidates.append(("teeth", infer_integer(values.teeth, "Number of teeth")))
    if is_positive(values.pitch_diameter):
        candidates.append(("pitch_diameter", infer_integer(values.pitch_diameter / module, "Pitch diameter")))
    if is_positive(values.outside_diameter):
        candidates.append(
            ("outside_diameter", infer_integer((values.outside_diameter / module) - 2, "Outside diameter"))
        )
    if is_positive(values.root_diameter):
        candidates.append(
            ("root_diameter", infer_integer((values.root_diameter / module) + 2.5, "Root diameter"))
        )

    if not candidates:
        return None

    reference_name, reference_value = candidates[0]
    for name, value in candidates[1:]:
        if value != reference_value:
            raise InputError(
                f"{FIELD_LABELS.get(name, name)} conflicts with "
                f"{FIELD_LABELS.get(reference_name, reference_name)}."
            )
    return reference_value


def derive_module_and_teeth_from_diameters(values: GearInputs) -> Tuple[Optional[float], Optional[int]]:
    pd = values.pitch_diameter
    od = values.outside_diameter
    rd = values.root_diameter

    if is_positive(pd) and is_positive(od):
        module = (od - pd) / 2
        if module <= 0:
            raise InputError("Outside diameter must be greater than pitch diameter.")
        return module, infer_integer(pd / module, "Pitch diameter")

    if is_positive(pd) and is_positive(rd):
        module = (pd - rd) / 2.5
        if module <= 0:
            raise InputError("Pitch diameter must be greater than root diameter.")
        return module, infer_integer(pd / module, "Pitch diameter")

    if is_positive(od) and is_positive(rd):
        module = (od - rd) / 4.5
        if module <= 0:
            raise InputError("Outside diameter must be greater than root diameter.")
        pitch_diameter = od - (2 * module)
        return module, infer_integer(pitch_diameter / module, "Outside and root diameters")

    return None, None


def calculate_standard_spur_gear(module: float, teeth: int, pressure_angle_deg: float) -> GearResult:
    pitch_diameter = module * teeth
    outside_diameter = module * (teeth + 2)
    root_diameter = module * (teeth - 2.5)
    addendum = module
    dedendum = 1.25 * module
    circular_pitch = math.pi * module
    tooth_thickness = circular_pitch / 2
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle_deg))

    return GearResult(
        module=module,
        teeth=teeth,
        pressure_angle=pressure_angle_deg,
        pitch_diameter=pitch_diameter,
        outside_diameter=outside_diameter,
        root_diameter=root_diameter,
        base_diameter=base_diameter,
        addendum=addendum,
        dedendum=dedendum,
        circular_pitch=circular_pitch,
        tooth_thickness=tooth_thickness,
    )


def validate_against_entered_values(entered: GearInputs, calculated: GearResult) -> None:
    entered_values = entered.as_dict()
    calculated_values = calculated.as_dict()

    for field_name, entered_value in entered_values.items():
        if entered_value is None:
            continue

        calculated_value = calculated_values[field_name]
        if field_name == "teeth":
            if infer_integer(entered_value, "Number of teeth") != calculated.teeth:
                raise InputError("Entered tooth count conflicts with the solved gear.")
            continue

        tolerance = ANGLE_TOLERANCE if field_name == "pressure_angle" else VALUE_TOLERANCE
        if abs(entered_value - calculated_value) > tolerance:
            raise InputError(
                f"{FIELD_LABELS[field_name]} conflicts with the solved gear. "
                "Review the entered dimensions."
            )


def auto_solve_gear(values: Dict[str, Optional[float]]) -> GearResult:
    inputs = GearInputs.from_dict(values)
    pressure_angle = inputs.pressure_angle

    if pressure_angle is None:
        pressure_angle = DEFAULT_PRESSURE_ANGLE
    if pressure_angle <= 0 or pressure_angle >= 45:
        raise InputError("Pressure angle must be between 0 and 45 degrees.")

    module = derive_module_from_inputs(inputs)
    teeth = None

    if module is not None:
        if module <= 0:
            raise InputError("Module must be greater than zero.")
        teeth = derive_teeth_from_inputs(inputs, module)

    if module is None or teeth is None:
        inferred_module, inferred_teeth = derive_module_and_teeth_from_diameters(inputs)
        if module is None and inferred_module is not None:
            module = inferred_module
        if teeth is None and inferred_teeth is not None:
            teeth = inferred_teeth

    if module is None or teeth is None:
        raise InputError(
            "Not enough independent inputs. Try one of these combinations:\n"
            "- module + teeth\n"
            "- pitch diameter + teeth\n"
            "- outside diameter + teeth\n"
            "- pitch diameter + outside diameter\n"
            "- pitch diameter + root diameter\n"
            "- outside diameter + root diameter\n"
            "- addendum + teeth\n"
            "- circular pitch + teeth"
        )

    if teeth < 3:
        raise InputError("Use at least 3 teeth for a valid spur gear calculation.")

    result = calculate_standard_spur_gear(module, teeth, pressure_angle)
    validate_against_entered_values(inputs, result)
    return result


def format_result_value(field_name: str, value: float) -> str:
    if field_name == "teeth":
        return str(int(round(value)))

    unit = FIELD_UNITS[field_name]
    if unit:
        return f"{value:.4f} {unit}"
    return f"{value:.4f}"


def entered_fields_summary(values: Dict[str, Optional[float]]) -> List[str]:
    lines: List[str] = []
    for field_name, value in values.items():
        if value is None:
            continue
        label = FIELD_LABELS[field_name]
        if field_name == "teeth":
            lines.append(f"{label}: {int(round(value))}")
        elif field_name == "pressure_angle":
            lines.append(f"{label}: {value:.4f} deg")
        else:
            lines.append(f"{label}: {value:.4f} mm")
    return lines
