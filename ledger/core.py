"""业务逻辑：添加、删除、列出、汇总。"""
import datetime

from . import storage


def _validate_date(date_str):
    """校验日期格式 YYYY-MM-DD（严格两位月、两位日），非法则抛 ValueError。"""
    if not (isinstance(date_str, str) and len(date_str) == 10
            and date_str[4] == "-" and date_str[7] == "-"):
        raise ValueError("日期格式错误，应为 YYYY-MM-DD：%s" % date_str)
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("日期格式错误，应为 YYYY-MM-DD：%s" % date_str)


def validate_month(month_str):
    """校验月份格式 YYYY-MM（严格两位月份），返回 (year, month)，非法则抛 ValueError。"""
    if not (isinstance(month_str, str) and len(month_str) == 7 and month_str[4] == "-"):
        raise ValueError("月份格式错误，应为 YYYY-MM：%s" % month_str)
    try:
        dt = datetime.datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        raise ValueError("月份格式错误，应为 YYYY-MM：%s" % month_str)
    return dt.year, dt.month


def add_record(amount, record_type, category, date, note=""):
    """添加一条记录，返回其 id。删除后已有 id 保持不变（取历史最大 id + 1）。"""
    if record_type not in ("income", "expense"):
        raise ValueError("类型必须是 income 或 expense：%s" % record_type)
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("金额必须是数字：%s" % amount)
    if amount <= 0:
        raise ValueError("金额必须大于 0：%s" % amount)
    _validate_date(date)

    records = storage.load_records()
    next_id = max((r["id"] for r in records), default=0) + 1
    record = {
        "id": next_id,
        "date": date,
        "type": record_type,
        "category": category,
        "amount": amount,
        "note": note,
    }
    records.append(record)
    storage.save_records(records)
    return next_id


def delete_record(record_id):
    """按 id 删除记录；id 不存在抛 ValueError。"""
    try:
        record_id = int(record_id)
    except (TypeError, ValueError):
        raise ValueError("id 必须是整数：%s" % record_id)

    records = storage.load_records()
    for i, r in enumerate(records):
        if r["id"] == record_id:
            del records[i]
            storage.save_records(records)
            return
    raise ValueError("id 不存在：%d" % record_id)


def _filter_by_month(records, month):
    """按 YYYY-MM 筛选记录；month 为 None 返回全部。"""
    if month is None:
        return records
    year, mon = validate_month(month)
    prefix = "%04d-%02d" % (year, mon)
    return [r for r in records if r["date"].startswith(prefix)]


def list_records(month=None):
    """按日期升序返回记录（同日按 id 升序），可按月筛选。"""
    records = _filter_by_month(storage.load_records(), month)
    return sorted(records, key=lambda r: (r["date"], r["id"]))


def summary(month=None):
    """返回 (总收入, 总支出, 结余)，可按月筛选。"""
    income = 0.0
    expense = 0.0
    for r in _filter_by_month(storage.load_records(), month):
        if r["type"] == "income":
            income += r["amount"]
        else:
            expense += r["amount"]
    return income, expense, income - expense
