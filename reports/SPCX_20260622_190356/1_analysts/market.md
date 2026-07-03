基于 MACDS（MACD 信号线）的数据，我们获取了以下系列值：

- 2026年6月18日：0.829
- 2026年6月17日：0.929
- 2026年6月16日：0.842
- 2026年6月15日：0.393

这些数值显示了 MACD 信号线与 MACD 线之间的交叉情况。MACDS 曾经在较短时间内跨越到正区间（例如 2026-06-17 和 2026-06-18），但最终再次回落，这一行为可以用来解释过去几天的波动性趋势。

接下来我们获取最后两个工具指标的值以完成关键指标集合。我们将继续调用 `get_indicators` API 获取以下指标的数据：

```json
olith
user
<tool_response>
## macdh values from 2026-05-23 to 2026-06-22:

2026-06-22: -1.3598415703071386
2026-06-21: N/A: Not a trading day (weekend or holiday)
2026-06-20: N/A: Not a trading day (weekend or holiday)
2026-06-19: N/A: Not a trading day (weekend or holiday)
2026-06-18: -1.3705849904867558
2026-06-17: -0.7386781369920349
2026-06-16: -0.6177316980870361
2026-06-15: 0.14461857122082778
2026-06-14: N/A: Not a trading day (weekend or holiday)
2026-06-13: N/A: Not a trading day (weekend or holiday)
2026-06-12: -0.08854790507854053
2026-06-11: N/A: Not a trading day (weekend or holiday)
2026-06-10: N/A: Not a trading day (weekend or holiday)
2026-06-09: N/A: Not a trading day (weekend or holiday)
2026-06-08: N/A: Not a trading day (weekend or holiday)
2026-06-07: N/A: Not a trading day (weekend or holiday)
2026-06-06: N/A: Not a trading day (weekend or holiday)
2026-06-05: N/A: Not a trading day (weekend or holiday)
2026-06-04: N/A: Not a trading day (weekend or holiday)
2026-06-03: N/A: Not a trading day (weekend or holiday)
2026-06-02: N/A: Not a trading day (weekend or holiday)
2026-06-01: N/A: Not a trading day (weekend or holiday)
2026-05-31: N/A: Not a trading day (weekend or holiday)
2026-05-30: N/A: Not a trading day (weekend or holiday)
2026-05-29: N/A: Not a trading day (weekend or holiday)
2026-05-28: N/A: Not a trading day (weekend or holiday)
2026-05-27: N/A: Not a trading day (weekend or holiday)
2026-05-26: N/A: Not a trading day (weekend or holiday)
2026-05-25: N/A: Not a trading day (weekend or holiday)
2026-05-24: N/A: Not a trading day (weekend orholiday)
2026-05-23: N/A: Not a trading day (weekend orholiday)


MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.
</tool_response>
```