"""数据存储：data.json 读写。"""
import json
import os

DATA_FILE = os.path.join(os.getcwd(), "data.json")


def _data_file():
    """数据文件路径，取当前工作目录（调用时计算，便于测试切换目录）。"""
    return os.path.join(os.getcwd(), "data.json")


class DataCorruptedError(Exception):
    """data.json 不是合法 JSON。"""


def load_records():
    """读取全部记录；文件不存在或为空返回空列表；JSON 损坏抛 DataCorruptedError。"""
    path = _data_file()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return []
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise DataCorruptedError("data.json 已损坏，不是合法的 JSON 文件（%s）" % e)


def save_records(records):
    """写入全部记录。"""
    with open(_data_file(), "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
