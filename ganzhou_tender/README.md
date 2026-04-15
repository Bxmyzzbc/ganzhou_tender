# 赣州市招标公告爬虫

多数据源政府采购/招标公告爬取系统，抓取赣州市当日新发布的全部公告，自动去重整合，输出结构化 JSON 供 AI 分析筛选 ICT 类项目。

---

## 功能特点

- **多数据源整合**：江西省公共资源交易平台（jxsggzy）、中国政府采购网（ccgp）
- **当日全量抓取**：每个数据源只抓当天新发布的公告，不限制条数
- **智能去重**：基于项目名称相似度的内容去重（跨数据源）+ 标题去重
- **结构化输出**：统一 JSON 格式，包含标题、时间、URL、正文内容
- **高效快速**：两个数据源合计约 15-20 秒完成

---

## 项目结构

```
anyuan_tender/
├── main.py                 # 主程序入口
│
├── 数据源爬虫/
│   ├── crawler_jxsggzy.py  # 江西省公共资源交易平台（API，全量抓取后按日期筛选）
│   └── crawler_ccgp.py     # 中国政府采购网（Scrapling，公开招标类型）
│
├── 处理模块/
│   └── content_dedup.py   # 内容去重（项目名称相似度 ≥ 70%）
│
├── output/                 # 抓取结果输出目录
├── logs/                   # 日志目录
└── view_results.py         # 快速查看最近结果
```

---

## 数据来源

| 数据源 | 技术方案 | 网址 | 备注 |
|--------|---------|------|------|
| 江西省公共资源交易平台 | requests API | jxsggzy.cn | 速度快，有 URL，关键词"赣州 招标" |
| 中国政府采购网 | Scrapling（JS 渲染） | ccgp.gov.cn | 只抓公开招标类型（bidType=1），有 URL |

---

## 处理流程

```
抓取各数据源（当日全量）
    ↓
[步骤1] 内容去重（项目名称相似度 ≥ 70%，跨数据源）
    ↓
[步骤2] 标题去重
    ↓
[步骤3] 按发布时间降序排序
    ↓
[步骤4] 输出结构化 JSON
```

---

## 安装依赖

```bash
pip install scrapling requests
```

> scrapling 会自动下载 Chromium 浏览器（约 150MB）

---

## 使用方法

```bash
cd anyuan_tender
python main.py
```

运行后在 `output/result_YYYY-MM-DD.json` 生成结果文件。

---

## 输出格式

```json
{
  "date": "2026-04-15",
  "total_count": 38,
  "sources": {
    "jxsggzy": 41,
    "ccgp": 5
  },
  "announcements": [
    {
      "title": "赣州天中招标代理有限公司关于江西省全南县教育体育局全南县高级职业技术学校实训设备更新改造项目...",
      "publish_date": "2026-04-15",
      "url": "http://www.jxsggzy.cn/jyxx/002006/002006001/20260415/aef4090e.html",
      "content": "项目概况：...（完整正文内容，jxsggzy有，ccgp暂无）",
      "source": "jxsggzy"
    }
  ]
}
```

**字段说明：**
- `title`：公告标题
- `publish_date`：发布时间（YYYY-MM-DD）
- `url`：详情页链接
- `content`：正文内容（jxsggzy 有完整内容，ccgp 暂无）
- `source`：数据来源（jxsggzy / ccgp）

---

## 注意事项

1. **首次运行**：scrapling 需要下载 Chromium，约 150MB
2. **运行时长**：两个数据源合计约 15-20 秒
3. **ccgp 公开招标类型**：ccgp 搜索使用 `bidType=1`（公开招标），只返回竞争性磋商/谈判等以外的公开招标公告
4. **内容字段**：jxsggzy 有完整正文，ccgp 暂无正文内容，AI 分析时主要依赖标题
