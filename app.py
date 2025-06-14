# -*- coding: utf-8 -*-
# ==============================================================================
#  业绩与绩效奖励统计程序 (网页版 V2 - 使用Session State)
# ==============================================================================
import streamlit as st
import json
import os
import pandas as pd

# --- 配置 ---
class Config:
    # ... (Config类内容保持不变) ...
    DATA_FILE = "performance_data.json"
    START_YEAR = 2025
    START_MONTH = 2
    END_MONTH = 12
    MONTHLY_TARGET = 180000.0
    ANNUAL_TARGET = 2300000.0
    SURPLUS_BONUS_THRESHOLD = 100000.0
    SURPLUS_BONUS_AMOUNT = 10000.0


# --- 数据加载/保存函数 ---
def load_data():
    if os.path.exists(Config.DATA_FILE):
        with open(Config.DATA_FILE, 'r', encoding='utf-8') as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}

def save_data(records):
    with open(Config.DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

# --- 主应用界面 ---
st.set_page_config(page_title="业绩跟踪程序", layout="wide")
st.title(f"📈 {Config.START_YEAR}年度业绩与绩效跟踪程序")

# --- 使用Session State来管理数据 ---
# 如果 'records' 不在会话内存中，说明是第一次加载，从文件读取
if 'records' not in st.session_state:
    st.session_state['records'] = load_data()

# --- 侧边栏用于输入 ---
st.sidebar.header("数据录入/修改")
all_months = [f"{m}月" for m in range(Config.START_MONTH, Config.END_MONTH + 1)]

# 计算默认选中的月份
# 如果有记录，默认选中下一个月；否则选中第一个月
if st.session_state['records']:
    next_month_index = len(st.session_state['records']) % len(all_months)
else:
    next_month_index = 0

selected_month_str = st.sidebar.selectbox("选择月份", all_months, index=next_month_index)
profit_input = st.sidebar.number_input(f"输入 {selected_month_str} 利润 (万元)", min_value=-1000.0, step=1.0, format="%.2f")

if st.sidebar.button("💾 保存/更新", use_container_width=True):
    month = int(selected_month_str.replace('月',''))
    actual_profit = profit_input * 10000
    performance_diff = actual_profit - Config.MONTHLY_TARGET
    
    # 直接更新会话内存中的数据
    st.session_state['records'][month] = {
        "actual_profit": actual_profit,
        "performance_diff": performance_diff
    }
    # 将更新后的内存数据保存到文件
    save_data(st.session_state['records'])
    st.sidebar.success(f"{selected_month_str} 数据已保存！") # 在这里，因为我们用了session state，success消息通常不会引起错误
    # 如果想更保险，也可以换成 st.rerun()

# --- 主面板用于显示 ---
# 直接从会话内存中读取数据来展示，不再需要每次都计算
records_to_display = st.session_state['records']
cumulative_profit = sum(rec['actual_profit'] for rec in records_to_display.values())
total_deductions = sum(abs(rec['performance_diff']) for rec in records_to_display.values() if rec['performance_diff'] < 0)
remaining_to_target = Config.ANNUAL_TARGET - cumulative_profit

# KPI指标卡
col1, col2, col3 = st.columns(3)
# ... (这部分显示逻辑和之前完全一样) ...
col1.metric("累计利润", f"{cumulative_profit:,.2f} 元")
col2.metric("年度目标差距", f"{remaining_to_target:,.2f} 元", delta=f"{cumulative_profit - Config.ANNUAL_TARGET:,.2f}", delta_color="normal")
col3.metric("累计绩效扣减", f"{total_deductions:,.2f} 元")


# ... (后续的表格显示和年终总结代码和之前完全一样, 只是数据源是 records_to_display) ...
st.markdown("---")
st.subheader("月度数据详情")
if records_to_display:
    df_data = []
    for m in sorted(records_to_display.keys()):
        rec = records_to_display[m]
        df_data.append({
            "月份": f"{m}月",
            "实际利润 (元)": rec['actual_profit'],
            "月度目标 (元)": Config.MONTHLY_TARGET,
            "月度绩效 (元)": rec['performance_diff']
        })
    df = pd.DataFrame(df_data)
    st.dataframe(df.style.format("{:,.2f}", subset=["实际利润 (元)", "月度目标 (元)", "月度绩效 (元)"]), use_container_width=True)

if len(records_to_display) >= Config.END_MONTH - Config.START_MONTH + 1:
    #... (年终总结逻辑不变) ...
    st.subheader("🏆 年终奖金核算")
    if cumulative_profit >= Config.ANNUAL_TARGET:
        clawback = total_deductions
        surplus = ((cumulative_profit - Config.ANNUAL_TARGET) // Config.SURPLUS_BONUS_THRESHOLD) * Config.SURPLUS_BONUS_AMOUNT
        total_bonus = clawback + surplus
        st.success(f"恭喜！已达成年度目标！")
        st.markdown(f"""
        - **补发扣减绩效**: <font color='green'>{clawback:,.2f} 元</font>
        - **超额达成奖励**: <font color='green'>{surplus:,.2f} 元</font>
        - **年终总奖励合计**: <font color='blue' style='font-weight:bold;'>{total_bonus:,.2f} 元</font>
        """, unsafe_allow_html=True)
    else:
        st.error("未能达成年度利润目标，不补发扣减绩效。")