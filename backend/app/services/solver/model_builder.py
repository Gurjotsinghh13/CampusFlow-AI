from dataclasses import dataclass
from uuid import UUID

from ortools.sat.python import cp_model

from app.services.solver.data_types import SolverInput

MAX_MODEL_VARIABLES = 2_000_000


@dataclass(frozen=True)
class AssignmentKey:
    requirement_key: str
    day_idx: int
    start_period: int
    faculty_id: UUID
    room_id: UUID


class ModelTooLargeError(Exception):
    pass


class CPSATModelBuilder:
    """
    One boolean variable per (requirement, day, start_period, faculty, room) candidate.
    Exactly one candidate is chosen per requirement. No-overlap is enforced by
    capping the number of "occupying" booleans to 1 for every (resource, day, period)
    triple, which correctly handles multi-period practical sessions.
    """

    def __init__(self, data: SolverInput):
        self.data = data
        self.model = cp_model.CpModel()
        self.assignment_vars: dict[AssignmentKey, cp_model.IntVar] = {}
        self._by_requirement: dict[str, list[AssignmentKey]] = {}
        self._by_faculty_day_period: dict[tuple[UUID, int, int], list[cp_model.IntVar]] = {}
        self._by_room_day_period: dict[tuple[UUID, int, int], list[cp_model.IntVar]] = {}
        self._by_division_day_period: dict[tuple[UUID, int, int], list[cp_model.IntVar]] = {}
        self._by_division_subject_type_day: dict[tuple[UUID, UUID, str, int], list[cp_model.IntVar]] = {}
        self._by_division_day: dict[tuple[UUID, int], list[tuple[cp_model.IntVar, int]]] = {}
        self._by_faculty_day: dict[tuple[UUID, int], list[tuple[cp_model.IntVar, int]]] = {}
        self._by_faculty_week: dict[UUID, list[tuple[cp_model.IntVar, int]]] = {}

    def build(self) -> cp_model.CpModel:
        self._create_variables()
        self._add_exactly_one_per_requirement()
        self._add_session_symmetry_breaking()
        self._add_no_overlap_constraints()
        self._add_subject_spread_constraints()
        self._add_workload_constraints()
        self._add_quality_objective()
        return self.model

    def _create_variables(self) -> None:
        n_days = len(self.data.days)
        var_count = 0

        for req in self.data.requirements:
            self._by_requirement[req.key] = []
            for day_idx in range(n_days):
                for start_period in range(0, self.data.periods_per_day - req.duration_periods + 1):
                    for faculty_id in req.eligible_faculty_ids:
                        for room_id in req.eligible_room_ids:
                            var_count += 1
                            if var_count > MAX_MODEL_VARIABLES:
                                raise ModelTooLargeError(
                                    "Timetable search space is too large for this dataset. "
                                    "Reduce the number of subjects, sessions, or eligible "
                                    "faculty/rooms, or increase working days / periods."
                                )
                            key = AssignmentKey(req.key, day_idx, start_period, faculty_id, room_id)
                            var = self.model.NewBoolVar(
                                f"x_{req.key}_{day_idx}_{start_period}_{faculty_id}_{room_id}"
                            )
                            self.assignment_vars[key] = var
                            self._by_requirement[req.key].append(key)

                            for offset in range(req.duration_periods):
                                p = start_period + offset
                                self._by_faculty_day_period.setdefault((faculty_id, day_idx, p), []).append(var)
                                self._by_room_day_period.setdefault((room_id, day_idx, p), []).append(var)
                                self._by_division_day_period.setdefault(
                                    (req.division_id, day_idx, p), []
                                ).append(var)

                            self._by_faculty_day.setdefault((faculty_id, day_idx), []).append(
                                (var, req.duration_periods)
                            )
                            self._by_faculty_week.setdefault(faculty_id, []).append((var, req.duration_periods))
                            self._by_division_day.setdefault((req.division_id, day_idx), []).append(
                                (var, req.duration_periods)
                            )
                            self._by_division_subject_type_day.setdefault(
                                (req.division_id, req.subject_id, req.session_type.value, day_idx), []
                            ).append(var)

    def _add_exactly_one_per_requirement(self) -> None:
        for req in self.data.requirements:
            keys = self._by_requirement.get(req.key, [])
            if not keys:
                raise ModelTooLargeError(
                    "No valid (day, time, faculty, room) combination exists for one of the "
                    "required sessions - check constraints and room capacity"
                )
            self.model.AddExactlyOne(self.assignment_vars[k] for k in keys)

    def _add_session_symmetry_breaking(self) -> None:
        requirement_groups: dict[tuple[str, str, str], list[tuple[int, str]]] = {}
        for req in self.data.requirements:
            group_key = (str(req.division_id), str(req.subject_id), req.session_type.value)
            requirement_groups.setdefault(group_key, []).append((req.session_index, req.key))

        for reqs in requirement_groups.values():
            if len(reqs) < 2:
                continue

            previous_position = None
            for _session_index, req_key in sorted(reqs):
                position = sum(
                    (key.day_idx * self.data.periods_per_day + key.start_period) * self.assignment_vars[key]
                    for key in self._by_requirement[req_key]
                )
                if previous_position is not None:
                    self.model.Add(previous_position <= position)
                previous_position = position

    def _add_no_overlap_constraints(self) -> None:
        for group in (self._by_faculty_day_period, self._by_room_day_period, self._by_division_day_period):
            for vars_ in group.values():
                if len(vars_) > 1:
                    self.model.Add(sum(vars_) <= 1)

    def _add_subject_spread_constraints(self) -> None:
        for vars_ in self._by_division_subject_type_day.values():
            if len(vars_) > 1:
                self.model.AddAtMostOne(vars_)

    def _add_workload_constraints(self) -> None:
        for (faculty_id, _day_idx), pairs in self._by_faculty_day.items():
            max_daily = self.data.faculty[faculty_id].max_daily_lectures
            self.model.Add(sum(var * duration for var, duration in pairs) <= max_daily)

        for faculty_id, pairs in self._by_faculty_week.items():
            max_weekly = self.data.faculty[faculty_id].max_weekly_lectures
            self.model.Add(sum(var * duration for var, duration in pairs) <= max_weekly)

    def _daily_load_vars(
        self,
        *,
        entity_label: str,
        entity_id: UUID,
        day_pairs: dict[tuple[UUID, int], list[tuple[cp_model.IntVar, int]]],
        upper_bound: int,
    ) -> list[cp_model.IntVar]:
        loads = []
        for day_idx in range(len(self.data.days)):
            load = self.model.NewIntVar(0, upper_bound, f"{entity_label}_load_{entity_id}_{day_idx}")
            pairs = day_pairs.get((entity_id, day_idx), [])
            if pairs:
                self.model.Add(load == sum(var * duration for var, duration in pairs))
            else:
                self.model.Add(load == 0)
            loads.append(load)
        return loads

    def _load_spread_penalty(
        self,
        *,
        entity_label: str,
        entity_id: UUID,
        loads: list[cp_model.IntVar],
        upper_bound: int,
    ):
        max_load = self.model.NewIntVar(0, upper_bound, f"{entity_label}_max_load_{entity_id}")
        min_load = self.model.NewIntVar(0, upper_bound, f"{entity_label}_min_load_{entity_id}")
        self.model.AddMaxEquality(max_load, loads)
        self.model.AddMinEquality(min_load, loads)
        return max_load - min_load

    def _add_quality_objective(self) -> None:
        # Balance the week before preferring earlier periods. The previous objective
        # rewarded earlier days too strongly, which could pack valid schedules toward
        # the beginning of the week.
        terms = []

        for division_id in self.data.divisions:
            loads = self._daily_load_vars(
                entity_label="division",
                entity_id=division_id,
                day_pairs=self._by_division_day,
                upper_bound=self.data.periods_per_day,
            )
            terms.append(
                50
                * self._load_spread_penalty(
                    entity_label="division",
                    entity_id=division_id,
                    loads=loads,
                    upper_bound=self.data.periods_per_day,
                )
            )

        for faculty_id, faculty in self.data.faculty.items():
            loads = self._daily_load_vars(
                entity_label="faculty",
                entity_id=faculty_id,
                day_pairs=self._by_faculty_day,
                upper_bound=faculty.max_daily_lectures,
            )
            terms.append(
                20
                * self._load_spread_penalty(
                    entity_label="faculty",
                    entity_id=faculty_id,
                    loads=loads,
                    upper_bound=faculty.max_daily_lectures,
                )
            )

        for key, var in self.assignment_vars.items():
            terms.append(key.start_period * var)
        if terms:
            self.model.Minimize(sum(terms))
