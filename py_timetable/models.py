from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class Course:
    code: str
    name: str
    lecture_count: int  # L part of L-T-P-C
    course_type: str
    faculty: str
    program: str
    semester: int

    @property
    def is_core(self) -> bool:
        return self.course_type.strip().lower() == "core"


@dataclass
class Slot:
    """A teaching slot that groups the same course code across programs/sems."""

    slot_id: int
    lecture_length: int  # 1, 2, or 3
    courses: List[Course] = field(default_factory=list)

    # Internal flags to avoid duplicates for (program, semester)
    _prog_sem_filled: Dict[Tuple[str, int], bool] = field(default_factory=dict, init=False, repr=False)

    def can_add_course_group(self, courses: List[Course]) -> bool:
        """Check if an entire code-group (same code across programs/sems) can fit here.

        Constraints (mirroring C++ logic):
        - lecture_length must match
        - only core courses
        - at most one course per (program, semester) in this slot
        - no professor (faculty) teaches more than one course in this slot
        """
        if not courses:
            return False

        # All courses of this code should have same lecture_length and type.
        first = courses[0]
        if first.lecture_count != self.lecture_length:
            return False
        if not first.is_core:
            return False

        existing_faculties = {c.faculty for c in self.courses}

        # Check program/semester and faculty constraints
        for c in courses:
            key = (c.program, c.semester)
            if self._prog_sem_filled.get(key, False):
                return False
            if c.faculty in existing_faculties:
                return False

        return True

    def add_course_group(self, courses: List[Course]) -> None:
        for c in courses:
            self.courses.append(c)
            self._prog_sem_filled[(c.program, c.semester)] = True

    @property
    def faculties(self) -> List[str]:
        return [c.faculty for c in self.courses]

    @property
    def program_sem_pairs(self) -> List[Tuple[str, int]]:
        return [(c.program, c.semester) for c in self.courses]
