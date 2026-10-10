# ledger

简单命令行记账工具。单用户、单币种，纯 Python 标准库，数据保存在当前目录 `data.json`。

## 安装

```bash
pip install -e .
```

## 运行

### 添加记录

```bash
ledger add 金额 income|expense 分类 日期 [-n 备注]
```

示例：

```bash
ledger add 5000 income 工资 2026-10-10 -n 十月工资
ledger add 35.5 expense 餐饮 2026-10-10 -n 午饭
ledger add 300 expense 交通 2026-10-08
```

### 删除记录

```bash
ledger delete 1
```

### 列出记录

按日期升序，可按月筛选（`--month YYYY-MM`）：

```bash
ledger list
ledger list --month 2026-10
```

### 汇总

输出总收入、总支出和结余，可按月筛选：

```bash
ledger summary
ledger summary --month 2026-10
```

## 测试

```bash
python -m unittest
```

## 示例输出

```
$ ledger list
id    日期        类型      分类          金额  备注
1     2026-10-08  支出      交通           300
2     2026-10-10  收入      工资          5000  十月工资
3     2026-10-10  支出      餐饮          35.50  午饭

$ ledger summary
总收入：5000
总支出：335.50
结余：4664.50
```

## 结构

```
ledger/
├── cli.py       # 命令行入口
├── core.py      # 业务逻辑（添加/删除/列出/汇总）
└── storage.py   # 数据存储（data.json 读写）
tests/
└── test_ledger.py  # 单元测试
```
