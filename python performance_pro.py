# -*- coding: utf-8 -*-
# ==============================================================================
#  专业版业绩与绩效奖励统计程序 (Performance Tracker Pro)
#  作者: Gemini
#  版本: 2.0
#  功能: 数据持久化, 历史数据修改, 彩色UI, 智能进度跟踪
# ==============================================================================

import json
import os
import sys
from colorama import init, Fore, Style

# -- 初始化Colorama，让颜色在所有平台(Windows, Mac, Linux)上都能正常工作 --
init(autoreset=True)

class Config:
    """存放所有配置和常量"""
    DATA_FILE = "performance_data.json"
    START_YEAR = 2025
    START_MONTH = 2
    END_MONTH = 12
    MONTHLY_TARGET = 180000.0
    ANNUAL_TARGET = 2300000.0
    SURPLUS_BONUS_THRESHOLD = 100000.0
    SURPLUS_BONUS_AMOUNT = 10000.0

class Display:
    """用于格式化和彩色打印的辅助类"""
    @staticmethod
    def header(text):
        print(Fore.CYAN + Style.BRIGHT + f"\n{'='*10} {text} {'='*10}")

    @staticmethod
    def sub_header(text):
        print(Fore.YELLOW + f"\n--- {text} ---")

    @staticmethod
    def success(text):
        print(Fore.GREEN + text)

    @staticmethod
    def error(text):
        print(Fore.RED + text)

    @staticmethod
    def info(text):
        print(Fore.BLUE + text)
        
    @staticmethod
    def prompt(text):
        return input(Fore.YELLOW + Style.BRIGHT + text)

    @staticmethod
    def format_currency(amount):
        """格式化金额，正数绿色，负数红色"""
        color = Fore.GREEN if amount >= 0 else Fore.RED
        return f"{color}{amount:,.2f}{Style.RESET_ALL}"

class PerformanceTracker:
    """程序主逻辑类，封装所有功能"""

    def __init__(self):
        self.records = {}
        self.cumulative_profit = 0.0
        self.total_deductions = 0.0
        self._load_data()

    def _load_data(self):
        """从JSON文件加载数据，如果文件不存在则初始化"""
        if os.path.exists(Config.DATA_FILE):
            try:
                with open(Config.DATA_FILE, 'r', encoding='utf-8') as f:
                    # 将json中的字符串key转为integer key
                    self.records = {int(k): v for k, v in json.load(f).items()}
                Display.success(f"✅ 成功加载数据: {Config.DATA_FILE}")
                self._recalculate_totals()
            except (json.JSONDecodeError, IOError) as e:
                Display.error(f"⚠️ 加载文件失败: {e}。将以全新状态开始。")
                self.records = {}
        else:
            Display.info("ℹ️ 未找到历史数据文件，将开始新的记录。")

    def _save_data(self):
        """将当前数据保存到JSON文件"""
        try:
            with open(Config.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=4)
        except IOError as e:
            Display.error(f"❌ 严重错误：无法保存数据到文件！ {e}")

    def _recalculate_totals(self):
        """根据现有记录完全重新计算累计利润和总扣款，确保数据一致性"""
        self.cumulative_profit = 0.0
        self.total_deductions = 0.0
        # 按月份排序进行计算
        sorted_months = sorted(self.records.keys())
        for month in sorted_months:
            record = self.records[month]
            self.cumulative_profit += record['actual_profit']
            if record['performance_diff'] < 0:
                self.total_deductions += abs(record['performance_diff'])

    def _get_profit_input(self, prompt_text):
        """获取用户输入的利润，并进行验证"""
        while True:
            try:
                profit_input = Display.prompt(prompt_text)
                return float(profit_input) * 10000
            except ValueError:
                Display.error("   输入无效，请输入一个数字 (例如: 19.5 或 -2.5 代表亏损)。")

    def _update_month_record(self, month, actual_profit):
        """更新或创建一个月的记录"""
        performance_diff = actual_profit - Config.MONTHLY_TARGET
        self.records[month] = {
            "actual_profit": actual_profit,
            "performance_diff": performance_diff
        }
        Display.success(f"   {month}月数据已更新。")

    def _display_progress(self):
        """显示当前的总体进度"""
        Display.sub_header("当前年度进度")
        print(f"  累计利润: {Display.format_currency(self.cumulative_profit)}")
        
        remaining_to_target = Config.ANNUAL_TARGET - self.cumulative_profit
        if remaining_to_target > 0:
            print(f"  距离年度目标还差: {Display.format_currency(remaining_to_target)}")
        else:
            Display.success(f"  已超越年度目标！超出金额: {Display.format_currency(-remaining_to_target)}")
    
    def run(self):
        """程序主循环"""
        Display.header(f"{Config.START_YEAR}年度利润绩效跟踪系统 V2.0")
        self._display_progress()

        while True:
            next_month = self._get_next_month()

            if next_month > Config.END_MONTH:
                Display.success("\n🎉 所有月份的数据都已录入完毕！")
                self._display_final_summary()
                break

            action = Display.prompt(
                f"\n请选择操作: [E] 输入{next_month}月数据, [M] 修改历史数据, [Q] 退出程序 -> "
            ).upper()

            if action == 'E':
                self._handle_new_entry(next_month)
            elif action == 'M':
                self._handle_edit_entry()
            elif action == 'Q':
                break
            else:
                Display.error("无效的指令，请输入 E, M, 或 Q。")
        
        print("\n感谢使用，程序已退出。")

    def _get_next_month(self):
        """计算下一个需要输入的月份"""
        if not self.records:
            return Config.START_MONTH
        last_recorded_month = max(self.records.keys())
        return last_recorded_month + 1

    def _handle_new_entry(self, month):
        """处理新月份的数据录入"""
        Display.sub_header(f"录入 {month} 月数据")
        actual_profit = self._get_profit_input(f"  请输入 {month} 月的实际利润 (万元): ")
        self._update_month_record(month, actual_profit)
        self._recalculate_totals()
        self._save_data()
        self._display_progress()

    def _handle_edit_entry(self):
        """处理历史数据的修改"""
        if not self.records:
            Display.error("目前没有任何历史数据可以修改。")
            return
            
        Display.sub_header("修改历史数据")
        try:
            month_to_edit = int(Display.prompt(f"  请输入要修改的月份 ({min(self.records.keys())}-{max(self.records.keys())}): "))
            if month_to_edit not in self.records:
                Display.error(f"  错误：{month_to_edit}月的数据不存在。")
                return

            old_profit_str = f"{self.records[month_to_edit]['actual_profit']/10000:.2f} 万元"
            Display.info(f"  {month_to_edit}月的当前利润为: {old_profit_str}")
            
            new_profit = self._get_profit_input(f"  请输入 {month_to_edit} 月的新利润 (万元): ")
            self._update_month_record(month_to_edit, new_profit)
            
            Display.info("  正在重新计算全年数据...")
            self._recalculate_totals()
            self._save_data()
            Display.success("  数据修改并保存成功！")
            self._display_progress()

        except ValueError:
            Display.error("  无效的月份，请输入一个数字。")
            
    def _display_final_summary(self):
        """显示最终的年度总结报告"""
        Display.header("2025年度业绩总结报告")
        
        # 打印表头
        print(f"{'月份':<6}{'实际利润':>18}{'月度目标':>18}{'月度绩效':>20}")
        print("-" * 65)

        # 逐月打印数据
        for month in range(Config.START_MONTH, Config.END_MONTH + 1):
            if month in self.records:
                rec = self.records[month]
                print(f"{str(month)+'月':<5}"
                      f"{Display.format_currency(rec['actual_profit']):>25}"
                      f"{Display.format_currency(Config.MONTHLY_TARGET):>25}"
                      f"{Display.format_currency(rec['performance_diff']):>28}")
            else:
                # 如果某个月数据缺失，也显示出来
                 print(f"{str(month)+'月':<5}{Fore.YELLOW+' (数据缺失)':>25}")
        
        print("-" * 65)
        print(f"全年累计利润: {Display.format_currency(self.cumulative_profit):>25}")
        print(f"年度利润目标: {Display.format_currency(Config.ANNUAL_TARGET):>25}")
        
        # 最终奖金核算
        Display.sub_header("年终奖金核算")
        if self.cumulative_profit >= Config.ANNUAL_TARGET:
            Display.success("✅ 恭喜！已达成年度利润目标！")
            
            clawback_bonus = self.total_deductions
            print(f"  - 补发扣减绩效: {Display.format_currency(clawback_bonus)}")

            surplus_profit = self.cumulative_profit - Config.ANNUAL_TARGET
            surplus_bonus = (surplus_profit // Config.SURPLUS_BONUS_THRESHOLD) * Config.SURPLUS_BONUS_AMOUNT
            print(f"  - 超额达成奖励: {Display.format_currency(surplus_bonus)}")
            
            total_bonus = clawback_bonus + surplus_bonus
            print(Style.BRIGHT + f"  年终总奖励合计: {Display.format_currency(total_bonus)}")
        else:
            Display.error("❌ 未能达成年度利润目标。")
            print(f"  全年累计被扣减的绩效 {Display.format_currency(self.total_deductions)} 将不予补发。")

if __name__ == "__main__":
    tracker = PerformanceTracker()
    tracker.run()