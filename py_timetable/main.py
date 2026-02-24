from __future__ import annotations

from pathlib import Path

from .io_utils import (
    read_courses_from_csv,
    write_slots_csv,
    write_timetable_csv,
    write_program_timetable_csv,
    write_faculty_timetable_csv,
)
from .slot_generator import build_slots
from .timetable_generator import make_timetable


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=== Python Time-Table Generator ===")

    # 1. Input CSV
    input_name = input("Enter the name of the input CSV file in 'input/' (e.g. winter.csv): ").strip()
    input_path = input_dir / input_name

    if not input_path.exists():
        print(f"ERROR: Input file '{input_path}' does not exist.")
        return

    courses = read_courses_from_csv(input_path)
    print(f"Loaded {len(courses)} courses from {input_path.name}")

    # 2. Build slots
    slots = build_slots(courses)
    print(f"Created {len(slots)} slots")

    # 3. Ask for output filenames
    slots_csv_name = input("Enter the name of CSV file to save the slots in 'output/' (e.g. slots.csv): ").strip()
    tt_csv_name = input("Enter the name of CSV file for overall timetable in 'output/' (e.g. timetable.csv): ").strip()

    slots_csv_path = output_dir / slots_csv_name
    tt_csv_path = output_dir / tt_csv_name

    # 4. Write slots and timetable
    write_slots_csv(slots, slots_csv_path)
    tt = make_timetable(slots)
    write_timetable_csv(tt, tt_csv_path)

    print(f"Slots written to: {slots_csv_path}")
    print(f"Overall timetable written to: {tt_csv_path}")

    # 5. Extra views: program-wise or faculty-wise
    print("\nExtra timetables:")
    print("1. Program-wise time-table")
    print("2. Faculty-wise time-table")
    print("0. Skip")
    choice = input("Enter choice (0/1/2): ").strip()

    if choice == "1":
        program = input("Enter program (e.g. ICTA): ").strip()
        try:
            sem = int(input("Enter semester (e.g. 2): ").strip())
        except ValueError:
            print("Invalid semester; skipping program-wise timetable.")
            return
        prog_csv_name = input(
            "Enter CSV file name to store program-wise timetable in 'output/' (e.g. prog_tt.csv): "
        ).strip()
        prog_csv_path = output_dir / prog_csv_name
        write_program_timetable_csv(slots, tt, program, sem, prog_csv_path)
        print(f"Program-wise timetable written to: {prog_csv_path}")

    elif choice == "2":
        faculty = input("Enter faculty short name (e.g. BK): ").strip()
        fac_csv_name = input(
            "Enter CSV file name to store faculty-wise timetable in 'output/' (e.g. fac_tt.csv): "
        ).strip()
        fac_csv_path = output_dir / fac_csv_name
        write_faculty_timetable_csv(slots, tt, faculty, fac_csv_path)
        print(f"Faculty-wise timetable written to: {fac_csv_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
