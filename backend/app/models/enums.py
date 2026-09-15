"""Shared enumerations."""

from __future__ import annotations

import enum


class StudyStatus(str, enum.Enum):
    """Lifecycle status of a single study day."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    SKIPPED = "SKIPPED"

    @classmethod
    def from_raw(cls, value: str | None) -> "StudyStatus":
        """Best-effort parse of a status string from Excel or API input.

        Tolerates casing, spaces, and common synonyms. Falls back to
        NOT_STARTED for blanks. Raises ValueError for unrecognised values.
        """
        if value is None:
            return cls.NOT_STARTED
        normalised = str(value).strip().upper().replace(" ", "_").replace("-", "_")
        if not normalised or normalised in {"NONE", "NAN"}:
            return cls.NOT_STARTED

        aliases = {
            "NOT_STARTED": cls.NOT_STARTED,
            "NOTSTARTED": cls.NOT_STARTED,
            "TODO": cls.NOT_STARTED,
            "PENDING": cls.NOT_STARTED,
            "IN_PROGRESS": cls.IN_PROGRESS,
            "INPROGRESS": cls.IN_PROGRESS,
            "PROGRESS": cls.IN_PROGRESS,
            "DOING": cls.IN_PROGRESS,
            "DONE": cls.DONE,
            "COMPLETE": cls.DONE,
            "COMPLETED": cls.DONE,
            "FINISHED": cls.DONE,
            "SKIP": cls.SKIPPED,
            "SKIPPED": cls.SKIPPED,
        }
        if normalised in aliases:
            return aliases[normalised]
        raise ValueError(f"Invalid status: {value!r}")
