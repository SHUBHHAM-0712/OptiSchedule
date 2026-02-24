from __future__ import annotations

import heapq
from typing import List, Tuple

from .models import Slot


def _have_common_faculty(a: Slot, b: Slot) -> bool:
    return bool(set(a.faculties) & set(b.faculties))


def make_timetable(slots: List[Slot]) -> List[List[int]]:
    """Create a 5x5 timetable of slot IDs.

    Roughly mirrors the C++ priority-queue-based algorithm:
    - Each slot appears a number of times equal to its lecture_length.
    - A slot doesn't repeat in the same day.
    - A faculty shouldn't have two consecutive lectures on the same day.
    - Remaining cells get filled with 0 (Free).
    """
    if not slots:
        return [[0] * 5 for _ in range(5)]

    total_required_boxes = sum(s.lecture_length for s in slots)
    total_boxes = 5 * 5

    # Max-heap by remaining lectures (priority).
    # Python heapq is min-heap, so store (-remaining, slot_id).
    heap: List[Tuple[int, int]] = []
    for s in slots:
        heapq.heappush(heap, (-s.lecture_length, s.slot_id))

    filler_count = max(0, total_boxes - total_required_boxes)
    if filler_count > 0:
        heapq.heappush(heap, (-filler_count, 0))  # slot_id 0 = Free

    # Map slot_id -> Slot for quick lookup
    slot_by_id = {s.slot_id: s for s in slots}

    timetable: List[List[int]] = [[0] * 5 for _ in range(5)]

    for day in range(5):  # columns
        used_today = set()  # slot_ids already used today
        prev_slot_id = 0
        for period in range(5):  # rows
            if not heap:
                timetable[period][day] = 0
                continue

            # Try to pick a suitable slot from the heap.
            temp: List[Tuple[int, int]] = []
            chosen: Tuple[int, int] | None = None

            while heap:
                neg_rem, slot_id = heapq.heappop(heap)
                remaining = -neg_rem

                # If no remaining occurrences, skip.
                if remaining <= 0:
                    continue

                # Avoid repeating same slot in a day.
                if slot_id in used_today and slot_id != 0:
                    temp.append((neg_rem, slot_id))
                    continue

                # Avoid consecutive lecture by same faculty on same day.
                if (
                    slot_id != 0
                    and prev_slot_id != 0
                    and prev_slot_id in slot_by_id
                    and slot_id in slot_by_id
                ):
                    prev_slot = slot_by_id[prev_slot_id]
                    cur_slot = slot_by_id[slot_id]
                    if _have_common_faculty(prev_slot, cur_slot):
                        temp.append((neg_rem, slot_id))
                        continue

                # Accept this slot.
                chosen = (neg_rem, slot_id)
                break

            # Push back all temporarily removed candidates.
            for item in temp:
                heapq.heappush(heap, item)

            if chosen is None:
                # No suitable slot found; leave this cell Free.
                timetable[period][day] = 0
                prev_slot_id = 0
                continue

            neg_rem, slot_id = chosen
            remaining = -neg_rem

            # Place the slot
            timetable[period][day] = slot_id
            used_today.add(slot_id)
            prev_slot_id = slot_id

            # Decrease remaining count and push back if still > 0.
            remaining -= 1
            if remaining > 0:
                heapq.heappush(heap, (-remaining, slot_id))

    return timetable
