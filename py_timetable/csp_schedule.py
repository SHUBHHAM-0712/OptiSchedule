from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import execute_values

from .ingest import load_assignment_map
from .db import fetch_all


@dataclass
class SlotInfo:
    slot_id: int
    day: str


@dataclass
class LectureVar:
    var_index: int
    assignment_id: int
    faculty_id: int
    batch_id: int
    course_id: int
    lecture_index: int
    batch_size: int


# ---------------- LOAD DATA ---------------- #

def load_slots(conn):
    rows = fetch_all(conn, "SELECT slot_id, day_of_week FROM time_matrix WHERE NOT is_blackout")
    return [SlotInfo(r["slot_id"], r["day_of_week"]) for r in rows]


def load_rooms(conn):
    return fetch_all(conn, "SELECT room_id, capacity FROM room ORDER BY capacity ASC")


def build_vars(rows):
    vars_ = []
    idx = 0
    for r in rows:
        lh = int(r["lecture_hours"])
        for k in range(lh):
            vars_.append(
                LectureVar(
                    idx,
                    r["assignment_id"],
                    r["faculty_id"],
                    r["batch_id"],
                    r["course_id"],
                    k,
                    r["batch_size"],
                )
            )
            idx += 1
    return vars_


# ---------------- GREEDY SCHEDULER ---------------- #

def greedy_assign(vars_, slots, rooms):
    assignment = {}

    faculty_busy = set()
    batch_busy = set()
    room_busy = set()

    for v in vars_:
        placed = False

        random.shuffle(slots)

        for s in slots:
            for r in rooms:
                if r["capacity"] < v.batch_size:
                    continue

                if (v.faculty_id, s.slot_id) in faculty_busy:
                    continue
                if (v.batch_id, s.slot_id) in batch_busy:
                    continue
                if (r["room_id"], s.slot_id) in room_busy:
                    continue

                # assign
                assignment[v.var_index] = (s.slot_id, r["room_id"])

                faculty_busy.add((v.faculty_id, s.slot_id))
                batch_busy.add((v.batch_id, s.slot_id))
                room_busy.add((r["room_id"], s.slot_id))

                placed = True
                break

            if placed:
                break

        if not placed:
            return None  # fail fast

    return assignment


# ---------------- MAIN ---------------- #

def run_scheduler(conn: PgConnection, label: str, source_csv: str, timeout_seconds=120, term=None):
    rows = load_assignment_map(conn, term=term)

    if not rows:
        raise RuntimeError("No data found")

    slots = load_slots(conn)
    rooms = load_rooms(conn)
    vars_ = build_vars(rows)

    # SORT: big batches first
    vars_.sort(key=lambda x: -x.batch_size)

    # Try multiple attempts
    solution = None
    for _ in range(10):
        solution = greedy_assign(vars_, slots.copy(), rooms)
        if solution:
            break

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO schedule_run (label, source_csv, status)
            VALUES (%s, %s, %s)
            RETURNING run_id
            """,
            (label, source_csv, "draft"),
        )
        run_id = cur.fetchone()[0]

    if not solution:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE schedule_run SET status='failed' WHERE run_id=%s",
                (run_id,),
            )
        return run_id, False, "Failed: Not enough slots/rooms"

    # insert results
    rows_to_insert = []
    for v in vars_:
        slot_id, room_id = solution[v.var_index]
        rows_to_insert.append(
            (run_id, v.assignment_id, v.batch_id, room_id, slot_id, v.lecture_index)
        )

    execute_values(
        conn.cursor(),
        """
        INSERT INTO master_timetable
        (run_id, assignment_id, batch_id, room_id, slot_id, lecture_index)
        VALUES %s
        """,
        rows_to_insert,
    )

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE schedule_run SET status='completed' WHERE run_id=%s",
            (run_id,),
        )

    return run_id, True, f"Scheduled {len(vars_)} lectures successfully"
