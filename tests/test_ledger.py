"""ledger 单元测试。运行：python -m unittest"""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from ledger import cli, core
from ledger.storage import DataCorruptedError


class LedgerTestCase(unittest.TestCase):
    """每个用例跑在独立临时目录，避免污染真实 data.json。"""

    def setUp(self):
        self._old_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self._old_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def run_cli(self, *argv):
        """执行 CLI，返回 (stdout, stderr, 退出码)。"""
        out, err = io.StringIO(), io.StringIO()
        code = 0
        try:
            with redirect_stdout(out), redirect_stderr(err):
                cli.main(list(argv))
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else (1 if e.code else 0)
        return out.getvalue(), err.getvalue(), code

    def read_data(self):
        with open(os.path.join(self.tmpdir, "data.json"), "r", encoding="utf-8") as f:
            return json.load(f)

    def write_data(self, content):
        with open(os.path.join(self.tmpdir, "data.json"), "w", encoding="utf-8") as f:
            f.write(content)


class TestAddAndSummary(LedgerTestCase):
    def test_add_then_summary_correct(self):
        """正常添加后汇总正确。"""
        self.run_cli("add", "100", "income", "工资", "2026-10-01")
        self.run_cli("add", "30.5", "expense", "餐饮", "2026-10-02")
        self.run_cli("add", "200", "income", "工资", "2026-09-15")  # 不同月

        out, _, code = self.run_cli("summary")
        self.assertEqual(code, 0)
        self.assertIn("总收入：300", out)
        self.assertIn("总支出：30.50", out)
        self.assertIn("结余：269.50", out)

        out, _, _ = self.run_cli("summary", "--month", "2026-10")
        self.assertIn("总收入：100", out)
        self.assertIn("总支出：30.50", out)

    def test_list_sorted_by_date(self):
        """list 按日期升序。"""
        self.run_cli("add", "1", "income", "a", "2026-10-05")
        self.run_cli("add", "2", "income", "b", "2026-10-01")
        out, _, _ = self.run_cli("list")
        self.assertLess(out.index("2026-10-01"), out.index("2026-10-05"))
        data = self.read_data()
        self.assertEqual([r["id"] for r in data], [1, 2])


class TestValidation(LedgerTestCase):
    def test_negative_amount_rejected(self):
        """金额为负数被拒绝，data.json 不变。"""
        self.run_cli("add", "50", "income", "工资", "2026-10-01")
        before = self.read_data()

        _, err, code = self.run_cli("add", "-5", "income", "工资", "2026-10-01")
        self.assertNotEqual(code, 0)
        self.assertIn("金额必须大于 0", err)
        self.assertEqual(self.read_data(), before)

        _, err, code = self.run_cli("add", "abc", "income", "工资", "2026-10-01")
        self.assertNotEqual(code, 0)
        self.assertIn("金额必须是数字", err)

        _, err, code = self.run_cli("add", "0", "income", "工资", "2026-10-01")
        self.assertNotEqual(code, 0)

    def test_invalid_date_rejected(self):
        """日期非法被拒绝。"""
        _, err, code = self.run_cli("add", "10", "income", "工资", "2026-13-01")
        self.assertNotEqual(code, 0)
        self.assertIn("日期格式错误", err)
        _, err, code = self.run_cli("add", "10", "income", "工资", "not-a-date")
        self.assertNotEqual(code, 0)
        # 单数字月/日被拒绝（回归：2026-9-1 曾被 strptime 接受，导致 --month 筛选丢失记录）
        _, err, code = self.run_cli("add", "10", "income", "工资", "2026-9-1")
        self.assertNotEqual(code, 0)
        self.assertIn("日期格式错误", err)
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, "data.json")))

    def test_invalid_type_rejected(self):
        """类型只能是 income 或 expense。"""
        _, err, code = self.run_cli("add", "10", "transfer", "工资", "2026-10-01")
        self.assertNotEqual(code, 0)
        self.assertIn("invalid choice", err)  # argparse choices 拦截
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, "data.json")))


class TestCorruptedData(LedgerTestCase):
    def test_corrupted_json_friendly_error(self):
        """data.json 损坏时友好报错，不抛堆栈，原文件不变。"""
        self.write_data("{not valid json!!")

        for argv in (["list"], ["summary"], ["add", "10", "income", "工资", "2026-10-01"], ["delete", "1"]):
            out, err, code = self.run_cli(*argv)
            self.assertNotEqual(code, 0, argv)
            self.assertIn("已损坏", err, argv)
            self.assertNotIn("Traceback", out + err, argv)

        self.write_data_content_unchanged()

    def write_data_content_unchanged(self):
        with open(os.path.join(self.tmpdir, "data.json"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "{not valid json!!")


class TestDelete(LedgerTestCase):
    def test_delete_existing(self):
        """删除成功，其余 id 不变。"""
        _, out1, _ = self.run_cli("add", "10", "income", "a", "2026-10-01")
        self.run_cli("add", "20", "expense", "b", "2026-10-02")

        _, _, code = self.run_cli("delete", "1")
        self.assertEqual(code, 0)
        data = self.read_data()
        self.assertEqual([r["id"] for r in data], [2])

        # 再添加，新 id 为 3（不复用 1）
        self.run_cli("add", "30", "income", "c", "2026-10-03")
        data = self.read_data()
        self.assertEqual([r["id"] for r in data], [2, 3])

    def test_delete_missing_id(self):
        """id 不存在时报错，退出码非 0。"""
        _, err, code = self.run_cli("delete", "999")
        self.assertNotEqual(code, 0)
        self.assertIn("id 不存在", err)


class TestMonthFilter(LedgerTestCase):
    def test_month_filter(self):
        """--month 只处理当月记录。"""
        self.run_cli("add", "100", "income", "a", "2026-10-01")
        self.run_cli("add", "50", "expense", "b", "2026-09-30")

        out, _, _ = self.run_cli("list", "--month", "2026-10")
        self.assertIn("2026-10-01", out)
        self.assertNotIn("2026-09-30", out)

        out, _, _ = self.run_cli("summary", "--month", "2026-09")
        self.assertIn("总收入：0", out)
        self.assertIn("总支出：50", out)

    def test_invalid_month_rejected(self):
        """月份格式不对时报错。"""
        _, err, code = self.run_cli("list", "--month", "2026-1")
        self.assertNotEqual(code, 0)
        self.assertIn("月份格式错误", err)

        _, err, code = self.run_cli("summary", "--month", "xx-yy")
        self.assertNotEqual(code, 0)
        self.assertIn("月份格式错误", err)


if __name__ == "__main__":
    unittest.main()
