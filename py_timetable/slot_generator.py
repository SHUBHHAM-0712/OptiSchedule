from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .models import Course, Slot


PROGRAMS = ["ICTA", "ICTB", "CS", "MNC", "EVD"]


def _count_n_lecture_courses(
    courses: List[Course], program: str, semester: int
) -> Dict[int, int]:
    """Count how many 1/2/3-lecture *core* courses exist for a program+sem."""
    counts: Dict[int, int] = {1: 0, 2: 0, 3: 0}
    for c in courses:
        if not c.is_core:
            continue
        if c.program != program or c.semester != semester:
            continue
        if c.lecture_count in (1, 2, 3):
            counts[c.lecture_count] += 1
    return counts


def compute_slot_requirements(courses: List[Course]) -> Dict[int, int]:
    """Replicate C++ logic that finds max # of 1/2/3 lecture courses per program/sem.

    Returns a dict mapping lecture_length -> required number of slots.
    """
    max_for_len: Dict[int, int] = {1: 0, 2: 0, 3: 0}

    for prog in PROGRAMS:
        for sem in range(1, 9):
            counts = _count_n_lecture_courses(courses, prog, sem)
            for length in (1, 2, 3):
                if counts[length] > max_for_len[length]:
                    max_for_len[length] = counts[length]

    return max_for_len


def build_slots(courses: List[Course]) -> List[Slot]:
    """Create slots and assign course groups (by code), following C++ constraints."""
    # Group courses by code (similar to Hash::chain in C++).
    by_code: Dict[str, List[Course]] = defaultdict(list)
    for c in courses:
        by_code[c.code].append(c)

    requirements = compute_slot_requirements(courses)

    # Total slots = max 1-lecture + max 2-lecture + max 3-lecture
    total_slots = sum(requirements[length] for length in (1, 2, 3))

    # Create slots: first 3-lecture, then 2-lecture, then 1-lecture
    slots: List[Slot] = []
    slot_id = 1
    for length in (3, 2, 1):
        for _ in range(requirements[length]):
            slots.append(Slot(slot_id=slot_id, lecture_length=length))
            slot_id += 1

    # Track which course codes have already been fully slotted.
    assigned_codes: Dict[str, bool] = {code: False for code in by_code}

    # For each slot, try to add as many course-code groups as possible.
    for slot in slots:
        for code, group in by_code.items():
            if assigned_codes[code]:
                continue
            if not group:
                continue
            # All courses of this code should have same lecture_count.
            if group[0].lecture_count != slot.lecture_length:
                continue
            if not group[0].is_core:
                continue
            if not slot.can_add_course_group(group):
                continue
            slot.add_course_group(group)
            assigned_codes[code] = True

    return slots
