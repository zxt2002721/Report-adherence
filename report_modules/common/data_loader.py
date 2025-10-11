
"""
数据加载器 - 负责文件读取和数据加载
"""

import json
import pandas as pd
from pathlib import Path
from report_modules.common import config


def load_json(path: Path) -> dict:
    """加载JSON文件"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pick_latest_json(dir_path: Path, suffix: str) -> Path | None:
    """选择最新的JSON文件"""
    files = sorted([p for p in dir_path.glob(f"*{suffix}")], 
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def find_memory_path_by_id(patient_id: str) -> Path:
    """根据患者ID查找memory文件路径"""
    exact = config.MEMORY_DIR / f"{patient_id}_memory.json"
    # import ipdb; ipdb.set_trace()
    if exact.exists(): 
        return exact
    
    cands = sorted(config.MEMORY_DIR.glob(f"{patient_id}*_memory.json"), 
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if cands: 
        return cands[0]
    
    raise FileNotFoundError(f"Could not find memory file for patient ID {patient_id} in {config.MEMORY_DIR}")


def load_physio_for_id(patient_id: str) -> pd.DataFrame:
    """根据患者ID加载生理数据"""
    if not config.PHYSIO_CSV.exists():
        raise FileNotFoundError(f"Missing CSV file: {config.PHYSIO_CSV}")
    
    df = pd.read_csv(config.PHYSIO_CSV)
    if "patient_id" not in df.columns:
        raise ValueError(f"CSV file is missing the required 'patient_id' column: {config.PHYSIO_CSV}")
    
    dfi = df[df["patient_id"].astype(str) == str(patient_id)].copy()
    if dfi.empty:
        raise ValueError(f"No records found for patient_id={patient_id} in the CSV file")
    
    if "date" in dfi.columns:
        dfi["date"] = pd.to_datetime(dfi["date"], errors="coerce")
        dfi = dfi.sort_values("date")
    
    return dfi


def load_patient_data(patient_id: str) -> tuple[dict, dict, pd.DataFrame]:
    """加载患者的所有数据：memory、dialogues、physio_data"""
    # 加载memory数据
    mem_path = find_memory_path_by_id(patient_id)
    memory = load_json(mem_path)
    
    # 加载对话数据（可选）
    dlg_path = config.DIALOGUE_DIR / f"{patient_id}_multiday.json"
    dialogues = load_json(dlg_path) if dlg_path.exists() else {}
    
    # 加载生理数据
    df_patient = load_physio_for_id(patient_id)
    
    return memory, dialogues, df_patient


def get_patient_id_from_args_or_latest(patient_id: str = None) -> tuple[str, Path]:
    """根据参数或选择最新的患者ID"""
    if patient_id:
        mem_path = find_memory_path_by_id(patient_id)
        return patient_id, mem_path
    else:
        mem_path = pick_latest_json(config.MEMORY_DIR, "_memory.json")
        if not mem_path:
            raise FileNotFoundError(f"No *_memory.json file found in {config.MEMORY_DIR}")
        patient_id = mem_path.name.replace("_memory.json", "")
        return patient_id, mem_path