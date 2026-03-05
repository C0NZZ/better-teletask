from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional


@dataclass
class SeriesData:
    series_id: int
    series_name: Optional[str] = None
    lecturer_ids: Optional[list[int]] = None


@dataclass
class LecturerData:
    lecturer_id: int
    lecturer_name: Optional[str] = None


@dataclass
class LectureData:
    lecture_id: int
    language: Optional[str] = None
    date: Optional[date] = None
    lecturer_ids: Optional[list[int]] = None
    series_id: Optional[int] = None
    semester: Optional[str] = None
    duration: Optional[timedelta] = None
    title: Optional[str] = None
    video_mp4: Optional[str] = None
    desktop_mp4: Optional[str] = None
    podcast_mp4: Optional[str] = None


@dataclass
class VttFile:
    id: int
    lecture_id: int
    language: str
    is_original_lang: bool
    vtt_data: bytes
    txt_data: bytes
    asr_model: Optional[str] = None
    compute_type: Optional[str] = None
    creation_date: Optional[datetime] = None


@dataclass
class VttLine:
    id: int
    vtt_file_id: int
    series_id: int
    language: str
    lecturer_ids: list[int]
    line_number: int
    ts_start: int
    ts_end: int
    content: str


@dataclass
class ApiKey:
    api_key: str
    person_name: Optional[str] = None
    person_email: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    status: Optional[str] = "active"
    id: Optional[int] = None


@dataclass
class BlacklistEntry:
    lecture_id: int
    reason: Optional[str] = None
    times_tried: int = 1
    creation_date: Optional[datetime] = None


@dataclass
class SearchResult:
    vtt_file_id: int
    lecture_id: int
    series_id: int
    series_name: Optional[str]
    language: str
    line_number: int
    ts_start: int
    ts_end: int
    content: str
    similarity: float
