"""命令行入口。"""
import argparse
import sys

from . import core
from .storage import DataCorruptedError


def _fmt_amount(x):
    """金额显示：整数不带小数点，其余保留两位。"""
    if x == int(x):
        return str(int(x))
    return "%.2f" % x


def _cmd_add(args):
    record_id = core.add_record(
        amount=args.amount,
        record_type=args.type,
        category=args.category,
        date=args.date,
        note=args.note or "",
    )
    print("已添加记录，id=%d" % record_id)


def _cmd_delete(args):
    core.delete_record(args.id)
    print("已删除记录，id=%d" % args.id)


def _cmd_list(args):
    records = core.list_records(month=args.month)
    if not records:
        print("暂无记录")
        return
    print("%-4s  %-10s  %-7s  %-10s  %10s  %s" % ("id", "日期", "类型", "分类", "金额", "备注"))
    for r in records:
        print(
            "%-4d  %-10s  %-7s  %-10s  %10s  %s"
            % (r["id"], r["date"], "收入" if r["type"] == "income" else "支出",
               r["category"], _fmt_amount(r["amount"]), r["note"])
        )


def _cmd_summary(args):
    income, expense, balance = core.summary(month=args.month)
    if args.month:
        print("月份：%s" % args.month)
    print("总收入：%s" % _fmt_amount(income))
    print("总支出：%s" % _fmt_amount(expense))
    print("结余：%s" % _fmt_amount(balance))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ledger", description="简单命令行记账工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加一条记录")
    p_add.add_argument("amount", help="金额")
    p_add.add_argument("type", choices=["income", "expense"], help="类型：income 或 expense")
    p_add.add_argument("category", help="分类")
    p_add.add_argument("date", help="日期（YYYY-MM-DD）")
    p_add.add_argument("-n", "--note", default="", help="备注（可选）")
    p_add.set_defaults(func=_cmd_add)

    p_del = sub.add_parser("delete", help="按 id 删除记录")
    p_del.add_argument("id", type=int, help="要删除的记录 id")
    p_del.set_defaults(func=_cmd_delete)

    p_list = sub.add_parser("list", help="按日期列出全部记录")
    p_list.add_argument("--month", default=None, help="只显示该月记录（YYYY-MM）")
    p_list.set_defaults(func=_cmd_list)

    p_sum = sub.add_parser("summary", help="总收入、总支出、结余")
    p_sum.add_argument("--month", default=None, help="只统计该月记录（YYYY-MM）")
    p_sum.set_defaults(func=_cmd_summary)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ValueError, DataCorruptedError) as e:
        print("错误：%s" % e, file=sys.stderr)
        sys.exit(1)
