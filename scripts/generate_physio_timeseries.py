# -*- coding: utf-8 -*-
"""Utility to synthesize physio time-series rows for patients produced by LLM pipelines."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import random

CSV_HEADER = [
    "patient_id",
    "date",
    "sbp",
    "dbp",
    "hr",
    "spo2",
    "weight_kg",
    "height_cm",
    "bmi",
    "fbg",
    "ppg",
    "hba1c",
    "ldl",
    "hdl",
    "tg",
    "egfr",
    "scr",
    "med_taken",
    "med_deviation_min",
    "diet_ok",
    "exercise_done",
    "notes",
    "device_bp",
    "device_glucose",
]

DEVICE_BP_OPTIONS = ["home_cuff", "clinic_auto", "ambulatory"]
DEVICE_GLUCOSE_OPTIONS = ["glucometer", "cgm", "lab"]


@dataclass
class PatientProfile:
    """Minimal fields we care about when synthesising vitals."""

    patient_id: str
    sex: str
    age: int
    height_cm: float
    comorbidities: Sequence[str]

    @staticmethod
    def from_json(profile_path: Path) -> "PatientProfile":
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
        basic = payload.get("basic_info", {})
        disease = payload.get("disease_info", {})
        comorbidities = [entry.get("disease_name", "") for entry in disease.get("comorbidities", [])]
        height_cm = basic.get("height_cm")
        if not height_cm:
            height_cm = 168 if basic.get("sex") == "男" else 160
        return PatientProfile(
            patient_id=basic.get("patient_id", profile_path.stem),
            sex=basic.get("sex", "未知"),
            age=int(basic.get("age", 60)),
            height_cm=float(height_cm),
            comorbidities=tuple(filter(None, comorbidities)),
        )


def deterministic_random(patient_id: str, day_index: int) -> random.Random:
    seed_material = f"{patient_id}-{day_index}".encode("utf-8")
    digest = hashlib.sha256(seed_material).digest()
    seed = int.from_bytes(digest[:8], "big")
    return random.Random(seed)


def base_metrics(profile: PatientProfile) -> Dict[str, float]:
    sbp = 128
    dbp = 80
    fbg = 6.0
    ppg = 8.0
    hba1c = 6.8
    ldl = 2.6
    bmi = 25.0
    egfr = 85
    scr = 70

    if any("高血压" in item for item in profile.comorbidities):
        sbp += 12
        dbp += 7
    if any("糖尿病" in item for item in profile.comorbidities):
        fbg = 7.5
        ppg = 9.5
        hba1c = 7.5
    if any("肾" in item for item in profile.comorbidities):
        egfr = 65
        scr = 95
    if profile.sex == "男":
        bmi = 25.5
    else:
        bmi = 24.0

    weight = bmi * (profile.height_cm / 100) ** 2

    return {
        "sbp": sbp,
        "dbp": dbp,
        "fbg": fbg,
        "ppg": ppg,
        "hba1c": hba1c,
        "ldl": ldl,
        "hdl": 1.2,
        "tg": 1.7,
        "egfr": egfr,
        "scr": scr,
        "weight": weight,
        "bmi": bmi,
        "hr": 72,
        "spo2": 96,
    }


def synthesize_day(profile: PatientProfile, base: Dict[str, float], current_date: date, day_index: int) -> Dict[str, object]:
    rng = deterministic_random(profile.patient_id, day_index)
    jitter = lambda val, spread, integer=False: int(round(rng.gauss(val, spread))) if integer else round(rng.gauss(val, spread), 1)

    weight = round(max(40.0, rng.gauss(base["weight"], 0.6)), 1)
    bmi = round(weight / (profile.height_cm / 100) ** 2, 1)
    sbp = max(95, jitter(base["sbp"], 6, True))
    dbp = max(55, jitter(base["dbp"], 4, True))
    hr = max(48, jitter(base["hr"], 6, True))
    spo2 = min(99, max(90, jitter(base["spo2"], 1.5, True)))
    fbg = round(max(3.8, rng.gauss(base["fbg"], 0.6)), 1)
    ppg = round(max(fbg, rng.gauss(base["ppg"], 0.7)), 1)
    hba1c = round(max(5.5, rng.gauss(base["hba1c"], 0.2)), 1)
    ldl = round(max(1.5, rng.gauss(base["ldl"], 0.3)), 1)
    hdl = round(max(0.7, rng.gauss(base["hdl"], 0.1)), 1)
    tg = round(max(0.4, rng.gauss(base["tg"], 0.4)), 1)
    egfr = max(30, jitter(base["egfr"], 6, True))
    scr = max(40, jitter(base["scr"], 6, True))

    med_taken = 1 if rng.random() > 0.2 else 0
    med_deviation = jitter(25 if med_taken else 90, 20, True)
    diet_ok = 1 if rng.random() > 0.35 else 0
    exercise_done = 1 if rng.random() > 0.45 else 0

    note_candidates = [
        "",
        "起床晚导致服药延后",
        "家庭聚餐偏咸",
        "轻微气促，已休息",
        "夜间睡眠不佳",
    ]
    notes = rng.choice(note_candidates)

    device_bp = rng.choice(DEVICE_BP_OPTIONS)
    device_glucose = rng.choice(DEVICE_GLUCOSE_OPTIONS)

    return {
        "patient_id": profile.patient_id,
        "date": current_date.isoformat(),
        "sbp": sbp,
        "dbp": dbp,
        "hr": hr,
        "spo2": spo2,
        "weight_kg": weight,
        "height_cm": round(profile.height_cm, 1),
        "bmi": bmi,
        "fbg": fbg,
        "ppg": ppg,
        "hba1c": hba1c,
        "ldl": ldl,
        "hdl": hdl,
        "tg": tg,
        "egfr": egfr,
        "scr": scr,
        "med_taken": med_taken,
        "med_deviation_min": max(0, med_deviation),
        "diet_ok": diet_ok,
        "exercise_done": exercise_done,
        "notes": notes,
        "device_bp": device_bp,
        "device_glucose": device_glucose,
    }


def generate_timeseries(profile: PatientProfile, days: int) -> List[Dict[str, object]]:
    base = base_metrics(profile)
    start = date.today() - timedelta(days=days - 1)
    rows = []
    for idx in range(days):
        target_date = start + timedelta(days=idx)
        rows.append(synthesize_day(profile, base, target_date, idx))
    return rows


def load_existing(patient_csv: Path) -> Dict[str, List[Dict[str, str]]]:
    if not patient_csv.exists():
        return {}
    data: Dict[str, List[Dict[str, str]]] = {}
    with patient_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            pid = row.get("patient_id")
            if not pid:
                continue
            data.setdefault(pid, []).append(row)
    return data


def write_dataset(records: Iterable[Dict[str, object]], output_path: Path, existing: Dict[str, List[Dict[str, str]]], overwrite: bool) -> None:
    merged: Dict[str, List[Dict[str, object]]] = {}
    for pid, rows in existing.items():
        if overwrite:
            continue
        merged[pid] = list(rows)
    for row in records:
        merged.setdefault(row["patient_id"], []).append(row)
    flat: List[Dict[str, object]] = []
    for rows in merged.values():
        flat.extend(rows)
    flat.sort(key=lambda r: (r["patient_id"], r["date"]))
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        writer.writeheader()
        for row in flat:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic physio rows for LLM-enhanced patients.")
    parser.add_argument("--source", default="data/output_llm_enhanced/patient_profiles", help="Directory with patient profile JSON files.")
    parser.add_argument("--out", default="data/output/patient_physio_timeseries.csv", help="Destination CSV file.")
    parser.add_argument("--days", type=int, default=14, help="Number of days to generate per patient.")
    parser.add_argument("--overwrite", action="store_true", help="Rewrite existing patients instead of skipping them.")
    args = parser.parse_args()

    source_dir = Path(args.source)
    if not source_dir.exists():
        raise SystemExit(f"Source directory not found: {source_dir}")

    profiles = [p for p in source_dir.glob("*.json") if p.is_file()]
    if not profiles:
        raise SystemExit(f"No patient profiles found under {source_dir}")

    existing = load_existing(Path(args.out))

    new_rows: List[Dict[str, object]] = []
    for profile_path in profiles:
        profile = PatientProfile.from_json(profile_path)
        if profile.patient_id in existing and not args.overwrite:
            continue
        new_rows.extend(generate_timeseries(profile, args.days))

    if not new_rows and not args.overwrite:
        print("No new patients to append.")
        return

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_dataset(new_rows, output_path, existing, args.overwrite)
    print(f"Wrote {len(new_rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
