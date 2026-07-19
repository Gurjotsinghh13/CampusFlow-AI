import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.division import Division
from app.models.faculty import Faculty
from app.models.semester import Semester
from app.models.subject import Subject
from app.models.timetable import GeneratedTimetable, TimetableEntry


def _raise_in_use(entity_label: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{entity_label} is used by generated timetables and cannot be deleted",
    )


def _raise_in_use_update(entity_label: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{entity_label} is used by generated timetables and this field cannot be changed",
    )


def academic_year_is_used_by_timetables(db: Session, academic_year_id: uuid.UUID) -> bool:
    return (
        db.query(GeneratedTimetable.id)
        .filter(GeneratedTimetable.academic_year_id == academic_year_id)
        .first()
        is not None
    )


def semester_is_used_by_timetables(db: Session, semester_id: uuid.UUID) -> bool:
    division_entry = (
        db.query(TimetableEntry.id)
        .join(Division, TimetableEntry.division_id == Division.id)
        .filter(Division.semester_id == semester_id)
        .first()
    )
    subject_entry = (
        db.query(TimetableEntry.id)
        .join(Subject, TimetableEntry.subject_id == Subject.id)
        .filter(Subject.semester_id == semester_id)
        .first()
    )
    return division_entry is not None or subject_entry is not None


def division_is_used_by_timetables(db: Session, division_id: uuid.UUID) -> bool:
    return db.query(TimetableEntry.id).filter(TimetableEntry.division_id == division_id).first() is not None


def subject_is_used_by_timetables(db: Session, subject_id: uuid.UUID) -> bool:
    return db.query(TimetableEntry.id).filter(TimetableEntry.subject_id == subject_id).first() is not None


def faculty_is_used_by_timetables(db: Session, faculty_id: uuid.UUID) -> bool:
    return db.query(TimetableEntry.id).filter(TimetableEntry.faculty_id == faculty_id).first() is not None


def room_is_used_by_timetables(db: Session, room_id: uuid.UUID) -> bool:
    return db.query(TimetableEntry.id).filter(TimetableEntry.room_id == room_id).first() is not None


def ensure_used_entity_field_not_changed(
    *,
    entity_label: str,
    is_used: bool,
    changes: dict[str, object],
    protected_fields: set[str],
) -> None:
    if is_used and protected_fields.intersection(changes):
        _raise_in_use_update(entity_label)


def ensure_academic_year_not_used_by_timetables(db: Session, academic_year_id: uuid.UUID) -> None:
    if academic_year_is_used_by_timetables(db, academic_year_id):
        _raise_in_use("Academic year")


def ensure_semester_not_used_by_timetables(db: Session, semester_id: uuid.UUID) -> None:
    if semester_is_used_by_timetables(db, semester_id):
        _raise_in_use("Semester")


def ensure_department_not_used_by_timetables(db: Session, department_id: uuid.UUID) -> None:
    division_entry = (
        db.query(TimetableEntry.id)
        .join(Division, TimetableEntry.division_id == Division.id)
        .filter(Division.department_id == department_id)
        .first()
    )
    subject_entry = (
        db.query(TimetableEntry.id)
        .join(Subject, TimetableEntry.subject_id == Subject.id)
        .filter(Subject.department_id == department_id)
        .first()
    )
    faculty_entry = (
        db.query(TimetableEntry.id)
        .join(Faculty, TimetableEntry.faculty_id == Faculty.id)
        .filter(Faculty.department_id == department_id)
        .first()
    )
    if division_entry or subject_entry or faculty_entry:
        _raise_in_use("Department")


def ensure_division_not_used_by_timetables(db: Session, division_id: uuid.UUID) -> None:
    if division_is_used_by_timetables(db, division_id):
        _raise_in_use("Division")


def ensure_subject_not_used_by_timetables(db: Session, subject_id: uuid.UUID) -> None:
    if subject_is_used_by_timetables(db, subject_id):
        _raise_in_use("Subject")


def ensure_faculty_not_used_by_timetables(db: Session, faculty_id: uuid.UUID) -> None:
    if faculty_is_used_by_timetables(db, faculty_id):
        _raise_in_use("Faculty member")


def ensure_room_not_used_by_timetables(db: Session, room_id: uuid.UUID) -> None:
    if room_is_used_by_timetables(db, room_id):
        _raise_in_use("Room")
