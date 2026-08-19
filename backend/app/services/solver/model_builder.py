from dataclasses import dataclass
from uuid import UUID

from ortools.sat.python import cp_model

from app.services.solver.data_types import SolverInput
from app.utils.timeline import is_block_continuous

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
    CP-SAT model for academic timetable generation.
    - Enforces strict hard constraints (no overlaps, room capacity, workload caps, continuous practicals, no lunch crossing).
    - Optimizes for schedule quality (compact student/faculty schedules, minimized idle gaps, balanced daily loads, sensible distribution).
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
                    # Hard constraint: Multi-period sessions (e.g. 2h practicals) must be continuous
                    # and must NEVER cross the lunch break boundary.
                    if req.duration_periods > 1 and self.data.period_slots:
                        if not is_block_continuous(start_period, req.duration_periods, self.data.period_slots):
                            continue

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
                    f"No valid (day, time, faculty, room) combination exists for session '{req.key}' - "
                    "check room capacity, faculty assignment, and lunch break constraints"
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

    def _add_gap_minimization_terms(
        self,
        *,
        entity_label: str,
        entity_ids: list[UUID],
        by_day_period_map: dict[tuple[UUID, int, int], list[cp_model.IntVar]],
        penalty_weight: int,
        terms: list,
    ) -> None:
        """
        Penalize internal idle gaps between early and late classes on the same day.
        A period p (1 <= p <= P-2) is an internal gap if there is at least one class
        earlier in the day and at least one class later in the day, but period p itself is empty.
        """
        n_periods = self.data.periods_per_day
        if n_periods < 3:
            return

        for entity_id in entity_ids:
            for day_idx in range(len(self.data.days)):
                # Get occupancy indicator for each period p
                occ_vars: list[cp_model.IntVar] = []
                for p in range(n_periods):
                    vars_at_p = by_day_period_map.get((entity_id, day_idx, p), [])
                    if not vars_at_p:
                        occ_vars.append(self.model.NewConstant(0))
                    elif len(vars_at_p) == 1:
                        occ_vars.append(vars_at_p[0])
                    else:
                        # sum(vars_at_p) is at most 1 due to no-overlap constraints
                        occ_var = self.model.NewBoolVar(f"{entity_label}_occ_{entity_id}_{day_idx}_{p}")
                        self.model.Add(occ_var == sum(vars_at_p))
                        occ_vars.append(occ_var)

                # For periods 1 to n_periods - 2, check if earlier and later classes exist
                for p in range(1, n_periods - 1):
                    earlier_vars = occ_vars[:p]
                    later_vars = occ_vars[p + 1:]

                    has_earlier = self.model.NewBoolVar(f"{entity_label}_has_earlier_{entity_id}_{day_idx}_{p}")
                    has_later = self.model.NewBoolVar(f"{entity_label}_has_later_{entity_id}_{day_idx}_{p}")
                    is_gap = self.model.NewBoolVar(f"{entity_label}_gap_{entity_id}_{day_idx}_{p}")

                    # has_earlier is true if at least one earlier period is occupied
                    self.model.AddMaxEquality(has_earlier, earlier_vars)
                    # has_later is true if at least one later period is occupied
                    self.model.AddMaxEquality(has_later, later_vars)

                    # is_gap >= has_earlier + has_later - 1 - occ_vars[p]
                    # If has_earlier=1, has_later=1, and occ_vars[p]=0, then is_gap must be 1.
                    self.model.Add(is_gap >= has_earlier + has_later - 1 - occ_vars[p])

                    terms.append(penalty_weight * is_gap)

    def _add_quality_objective(self) -> None:
        """
        Comprehensive quality objective:
        1. Student Schedule Compactness (Minimize division idle gaps between classes) - Weight 100
        2. Faculty Schedule Compactness (Minimize faculty idle gaps between lectures) - Weight 50
        3. Division Daily Load Balancing (Distribute weekly sessions across working days) - Weight 30
        4. Faculty Daily Load Balancing - Weight 15
        5. Mild Core Hours Preference (Penalize extreme late periods >= 5 mildly) - Weight 2
        """
        terms = []

        # 1. Division Schedule Compactness (Gap Minimization)
        self._add_gap_minimization_terms(
            entity_label="div",
            entity_ids=list(self.data.divisions.keys()),
            by_day_period_map=self._by_division_day_period,
            penalty_weight=100,
            terms=terms,
        )

        # 2. Faculty Schedule Compactness (Gap Minimization)
        self._add_gap_minimization_terms(
            entity_label="fac",
            entity_ids=list(self.data.faculty.keys()),
            by_day_period_map=self._by_faculty_day_period,
            penalty_weight=50,
            terms=terms,
        )

        # 3. Division Daily Load Balancing
        for division_id, division in self.data.divisions.items():
            loads = self._daily_load_vars(
                entity_label="division",
                entity_id=division_id,
                day_pairs=self._by_division_day,
                upper_bound=self.data.periods_per_day,
            )
            terms.append(
                30
                * self._load_spread_penalty(
                    entity_label="division",
                    entity_id=division_id,
                    loads=loads,
                    upper_bound=self.data.periods_per_day,
                )
            )

        # 4. Faculty Daily Load Balancing
        for faculty_id, faculty in self.data.faculty.items():
            loads = self._daily_load_vars(
                entity_label="faculty",
                entity_id=faculty_id,
                day_pairs=self._by_faculty_day,
                upper_bound=faculty.max_daily_lectures,
            )
            terms.append(
                15
                * self._load_spread_penalty(
                    entity_label="faculty",
                    entity_id=faculty_id,
                    loads=loads,
                    upper_bound=faculty.max_daily_lectures,
                )
            )

        # 5. Core Hours Preference (Mild soft weight on extreme late periods >= 5)
        for key, var in self.assignment_vars.items():
            if key.start_period >= 5:
                terms.append((key.start_period - 4) * 2 * var)

        if terms:
            self.model.Minimize(sum(terms))
