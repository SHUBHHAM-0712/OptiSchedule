from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from .models import Course, Slot


def _parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def read_courses_from_csv(path: str | Path) -> List[Course]:
    path = Path(path)
    courses: List[Course] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            # Expect: code, name, L-T-P-C, type, faculty, program, sem
            if len(row) < 7:
                continue

            code = row[0].strip()
            name = row[1].strip()
            ltp = row[2].strip()
            course_type = row[3].strip()
            faculty = row[4].strip()
            program = row[5].strip()
            sem_str = row[6].strip()

            # Extract L part from L-T-P-C, e.g. 3-0-0-3 -> 3
            lecture_count = 0
            if ltp:
                try:
                    lecture_count = int(ltp.split("-")[0])
                except (IndexError, ValueError):
                    lecture_count = 0

            semester = _parse_int(sem_str, default=0)

            courses.append(
                Course(
                    code=code,
                    name=name,
                    lecture_count=lecture_count,
                    course_type=course_type,
                    faculty=faculty,
                    program=program,
                    semester=semester,
                )
            )

    return courses


def write_slots_csv(slots: List[Slot], path: str | Path) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for slot in slots:
            writer.writerow([f"Slot : M{slot.slot_id}"])
            writer.writerow(["SEM", "PROGRAM", "CODE", "LECTURE", "TYPE", "FACULTY"])
            for c in slot.courses:
                writer.writerow(
                    [
                        f"Sem-{c.semester}",
                        c.program,
                        c.code,
                        slot.lecture_length,
                        c.course_type,
                        c.faculty,
                    ]
                )
            writer.writerow([])


def write_timetable_csv(tt: list[list[int]], path: str | Path) -> None:
    """Write a 5x5 timetable of slot IDs (0 = Free)."""
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_hour = 8
        for row in range(5):
            time_label = f"{start_hour}:00 - {start_hour}:50"
            row_vals: list[str] = [time_label]
            for col in range(5):
                slot_id = tt[row][col]
                if slot_id == 0:
                    row_vals.append("Free")
                else:
                    row_vals.append(f"M{slot_id}")
            writer.writerow(row_vals)
            start_hour += 1


def write_program_timetable_csv(
    slots: List[Slot],
    tt: list[list[int]],
    program: str,
    semester: int,
    path: str | Path,
) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([f"Time-Table For {program} Sem-{semester}"])
        writer.writerow(["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

        start_hour = 8
        for row in range(5):
            time_label = f"{start_hour}:00 - {start_hour}:50"
            row_vals: list[str] = [time_label]
            for col in range(5):
                slot_id = tt[row][col]
                if slot_id == 0:
                    row_vals.append("Free")
                    continue
                slot = next((s for s in slots if s.slot_id == slot_id), None)
                if slot is None:
                    row_vals.append("Free")
                    continue
                # Find course for this program/sem in slot
                course = next(
                    (
                        c
                        for c in slot.courses
                        if c.program == program and c.semester == semester
                    ),
                    None,
                )
                row_vals.append(course.code if course else "Free")
            writer.writerow(row_vals)
            start_hour += 1


def write_faculty_timetable_csv(
    slots: List[Slot],
    tt: list[list[int]],
    faculty: str,
    path: str | Path,
) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([f"Time-Table For {faculty}"])
        writer.writerow(["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

        start_hour = 8
        for row in range(5):
            time_label = f"{start_hour}:00 - {start_hour}:50"
            row_vals: list[str] = [time_label]
            for col in range(5):
                slot_id = tt[row][col]
                if slot_id == 0:
                    row_vals.append("Free")
                    continue
                slot = next((s for s in slots if s.slot_id == slot_id), None)
                if slot is None:
                    row_vals.append("Free")
                    continue
                # Find course taught by this faculty in the slot
                course = next((c for c in slot.courses if c.faculty == faculty), None)
                row_vals.append(course.code if course else "Free")
            writer.writerow(row_vals)
            start_hour += 1
