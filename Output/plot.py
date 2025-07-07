# File    :   plot.py
# Time    :   <2025/03/11>
# Author  :   <zxy> 


# 绘制图像

import pandas as pd
import  matplotlib.pyplot as plt
import matplotlib.ticker as ticker


import numpy as np
import seaborn as sns

# 设置中文字体宋体
plt.rcParams['font.sans-serif'] = ['SimSun']  # 设置字体为宋体
plt.rcParams['axes.unicode_minus'] = False  # 显示负号

base_colors = ["#00C8FF", "#FF6B35", "#A663CC", "#4CB944", "#FFD166",
               "#6B9AC4", '#e377c2', '#7f7f7f', '#7f7f7f', '#17becf']
custom_colors_1= ['#e377c2', '#7f7f7f', '#17becf', '#4CB944', '#6B9AC4', '#e377c2']
custom_colors = [sns.desaturate(color,0.9) for color in base_colors]  # 0.6 是饱和度因子，可以根据需要调整
custom_colors_1 = [sns.desaturate(color,0.9) for color in custom_colors_1]  # 0.6 是饱和度因子，可以根据需要调整

# 创建一个点形式的表格
custom_dot = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'h']
# 绘制堆叠柱状图
def plot_stacked_bars_up_down(variables_up, variables_down, file_path):
    # 读取CSV文件
    df = pd.read_csv(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [var for var in variables_up + variables_down if var not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return
    
    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(9, 6.75))

    # 初始化底部和顶部高度数组
    bottom_up = np.zeros(len(df))
    top_down = np.zeros(len(df))

    # 绘制向上堆叠的柱状图
    for idx, variable in enumerate(variables_up):
        ax.bar(df.index, df[variable], bottom=bottom_up, width = 0.6,
                color=custom_colors[idx % len(custom_colors)], label=f'{variable}')
        bottom_up += df[variable]

    # 绘制向下堆叠的柱状图
    for idx, variable in enumerate(variables_down, start=len(variables_up)):
        ax.bar(df.index, -df[variable], bottom=-top_down, width=0.6,
               color=custom_colors[idx % len(custom_colors)], label=f'{variable}')
        top_down += df[variable]

    # 绘制电力负荷的折线图
    # ax.plot(df.index, df['G_load'], color='black', linestyle='-', marker='o', linewidth=2, label='Heating load')

    # 设置X轴和Y轴标签
    ax.set_xlabel('Hour(h)')
    ax.set_ylabel('Power(KW)')

    # 设置标题
    ax.set_title('')

    # 显示网格线
    ax.grid(True, linestyle='--', alpha=0.6)


    # 添加图例
    ax.legend(ncol = 2)
    ax.set_xticks(np.arange(0, 25, 4))
    ax.set_ylim([-5000,5000])

    # 自动调整布局并显示图表
    plt.tight_layout()
    
    # 调整y轴范围以适应所有的数据点
    ax.margins(y=0.1)  # Add some padding to the y-axis

    plt.show()
# 绘制堆叠柱状图
def plot_g_banlance(variables_up, variables_down,load,file_path):
    # 读取CSV文件
    df = pd.read_csv(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [var for var in variables_up + variables_down if var not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return
    
    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(9, 6.75))

    # 初始化底部和顶部高度数组
    bottom_up = np.zeros(len(df))
    top_down = np.zeros(len(df))
    labels = ['电锅炉供热','燃料电池供热','地源热泵供热','储热罐输出/输入']
    # 绘制向上堆叠的柱状图
    for idx, variable in enumerate(variables_up):
        ax.bar(df.index, df[variable], bottom=bottom_up, width = 0.6,
                color=custom_colors[idx % len(custom_colors)], label=labels[idx % len(labels)])
        bottom_up += df[variable]

    # 绘制向下堆叠的柱状图
    for idx, variable in enumerate(variables_down, start=len(variables_up)):
        ax.bar(df.index, -df[variable], bottom=-top_down, width=0.6,
               color=custom_colors[idx % len(custom_colors)-1])
        top_down += df[variable]

    # 绘制电力负荷的折线图
    # ax.plot(df.index, df['G_load'], color='black', linestyle='-', marker='o', linewidth=2, label='Heating load')
    
    ax.plot(
            df.index, df['G_load'], 
            color='black',
            linestyle='-', 
            marker='o',
            markersize=4,
            linewidth=2, 
            label='热负荷',
        )
    # 设置X轴和Y轴标签
    ax.set_xlabel('时间(h)',fontsize=20)
    ax.set_ylabel('热能(KWh)',fontsize=20)

    # 设置标题

    # 显示网格线
    # ax.grid(True, linestyle='--', alpha=0.6)

    # 在y轴0位置添加实现
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    # 添加图例
    ax.legend(ncol = 2,frameon=False,  # 去掉图例边框
        prop={'size': 15})
    ax.set_xticks(np.arange(0, 24, 1))
    ax.set_xlim([-1, 24])
    ax.set_ylim([-2000,5000])
    ax.tick_params(axis='both', which='major', labelsize=15)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
    # 自动调整布局并显示图表
    plt.tight_layout()
    
    # 调整y轴范围以适应所有的数据点
    ax.margins(y=0.1)  # Add some padding to the y-axis

    plt.show()
def plot_p_banlance(variables_up, variables_down,load,file_path):
    # 读取CSV文件
    df = pd.read_csv(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [var for var in variables_up + variables_down if var not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return
    
    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(9, 6.75))

    # 初始化底部和顶部高度数组
    bottom_up = np.zeros(len(df))
    top_down = np.zeros(len(df))
    labels_1 = ['购电','光伏出力','燃料电池供电','蓄电池输出/输入']
    label_2 = ['电解槽用电','电锅炉用电','地源热泵用电','']
    # 绘制向上堆叠的柱状图
    for idx, variable in enumerate(variables_up):
        ax.bar(df.index, df[variable], bottom=bottom_up, width = 0.6,
                color=custom_colors[idx], label=labels_1[idx])
        bottom_up += df[variable]

    # 绘制向下堆叠的柱状图
    for idx, variable in enumerate(variables_down):
        ax.bar(df.index, -df[variable], bottom=-top_down, width=0.6,
               color=custom_colors_1[idx],label=label_2[idx])
        top_down += df[variable]

    # 绘制电力负荷的折线图
    # ax.plot(df.index, df['G_load'], color='black', linestyle='-', marker='o', linewidth=2, label='Heating load')
    
    ax.plot(
            df.index, df['P_Dr'], 
            color='black',
            linestyle='-', 
            marker='o',
            markersize=4,
            linewidth=2, 
            label='电负荷',
        )
    # 设置X轴和Y轴标签
    ax.set_xlabel('时间(h)',fontsize=20)
    ax.set_ylabel('电功率(kW)',fontsize=20)

    # 设置标题

    # 显示网格线
    # ax.grid(True, linestyle='--', alpha=0.6)

    # 在y轴0位置添加实现
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    # 添加图例
    ax.legend(ncol = 2,frameon=False,  # 去掉图例边框
        prop={'size': 15})
    ax.set_xticks(np.arange(0, 24, 1))
    ax.set_xlim([-1, 24])
    ax.set_ylim([-6500,6500])
    ax.tick_params(axis='both', which='major', labelsize=15)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
    # 自动调整布局并显示图表
    plt.tight_layout()
    
    # 调整y轴范围以适应所有的数据点
    ax.margins(y=0.1)  # Add some padding to the y-axis

    plt.show()
# 绘制阶梯图
def plot_step_chart(var: list, file_path):
    # 读取CSV文件
    df = pd.read_csv(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [v for v in var if v not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return

    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(9, 6.75))  # 设置图形大小
    
    labels = ['储热罐温度','供热管网温度']


    # 绘制每个变量的阶梯图
    for idx, variable in enumerate(var):
        x = df.index.values
        y = df[variable].values
        
        # 为每个时段插入一个中间点
        x_mid = (x[:-1] + x[1:]) / 2
        
        # 绘制阶梯图
        ax.step(x, y, where='post', color=custom_colors[idx % len(custom_colors)], linestyle='-.', linewidth=2, label=labels[idx % len(labels)])
        
        # 将点标记在每个时段的中间位置
        ax.plot(x_mid, y[:-1], color=custom_colors[idx % len(custom_colors)], linestyle='None', marker=custom_dot[idx % len(custom_colors)], markersize=4)

    # 设置横纵坐标起始值和间隔
    ax.set_xticks(np.arange(0, 25, 1))
    # ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))  
    # 设置X轴和Y轴标签
    ax.set_xlabel('时间(h)',fontsize=20)
    ax.set_ylabel('温度(℃)',fontsize=20)
    ax.set_xlim([0, 24])
    ax.set_ylim([45, 58])
    # 设置标题
    # ax.set_title('')

    # 显示网格线
    ax.grid(True, linestyle=':', alpha=0.6)

    # 添加图例
    ax.legend(        loc = 'upper left',
        frameon=False,  # 去掉图例边框
        prop={'size': 20})
    ax.tick_params(axis='both', which='major', labelsize=15)

    plt.tight_layout()
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)  # 设置边框线宽度为2
    # 显示图片
    # 自动调整布局并显示图表
    plt.tight_layout()

    # 显示图表
    plt.show()

# 绘制折线图
def plot_line_chart(var: list,file_path):
    # 读取CSV文件
    df = pd.read_csv(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [v for v in var if v not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return

    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(9, 6.75))  # 设置图形大小
    labels = ['原始电负荷']
    # 绘制每个变量的折线图
    for idx, variable in enumerate(var):
        ax.plot(
            df.index, df[variable], 
            color=custom_colors[idx % len(custom_colors)], 
            linestyle='-', 
            marker=custom_dot[idx % len(custom_dot)], 
            markersize=6,
            linewidth=2, 
            label=labels[idx % len(labels)],
        )

    # 设置X轴和Y轴标签
    ax.set_xlabel('时间(h)',fontsize=20)
    ax.set_ylabel('原始电负荷(kW)',fontsize=20)
    ax.tick_params(axis='both', which='major', labelsize=15)
    ax.set_xticks(np.arange(0, 24, 1))
    ax.set_ylim([0, 2500])
    # 添加图例
    ax.legend(
        loc= 'upper left',
        frameon=False,  # 去掉图例边框
        prop={'size': 20})
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)  # 设置边框线宽度为1.5
    plt.tight_layout()
    plt.show()
    
def plot_bess(var: list, variables_up, variables_down,file_path):

    df = pd.read_csv(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [v for v in var if v not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return

    # 创建一个新的图形
    fig, ax1 = plt.subplots(figsize=(9, 6.75))  # 左侧y轴 (柱状图)
    ax2 = ax1.twinx()  # 右侧y轴 (折线图)
    labels = ['Soc of Bess']
    for idx, variable in enumerate(var):
        x = df.index.values
        y = df[variable].values
        
        # 为每个时段插入一个中间点
        x_mid = (x[:-1] + x[1:]) / 2
        
        # 绘制阶梯图
        ax2.step(x, y/2000, where='post', color='black', linestyle='-.', linewidth=2, label='SOC')
        
        # 将点标记在每个时段的中间位置
        ax2.plot(x_mid, y[:-1]/2000, color='black', linestyle='None', marker=custom_dot[idx % len(custom_colors)], markersize=4)


    # 设置X轴和Y轴标签
    ax1.set_xlabel('时间(h)',fontsize=20)
    ax1.set_ylabel('电量(kWh)',fontsize=20)
    ax2.set_ylabel('SOC(%)',fontsize=20)
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))  

    # 设置标题
    # ax.set_title('Variables Over Time')

    # 绘制堆叠柱图
    bottom_up = np.zeros(len(df))
    top_down = np.zeros(len(df))
    bar_positions = np.arange(len(df)) + 0.5  # 柱状图的横坐标位置
    # 绘制向上堆叠的柱状图
    for idx, variable in enumerate(variables_up):
        ax1.bar(
            bar_positions, 
            df[variable], 
            bottom=bottom_up, 
            color=custom_colors[idx+2 % len(custom_colors)], 
            label='蓄电池储电',
            width = 0.6
        )
        bottom_up += df[variable]

    # 绘制向下堆叠的柱状图
    for idx, variable in enumerate(variables_down):
        ax1.bar(
            df.index+0.5, 
            -df[variable], 
            bottom=-top_down, 
            color=custom_colors[idx+3 % len(custom_colors)],
            label='蓄电池放电',
            width = 0.6
    )
        top_down += df[variable]

        # 显示网格线
    # ax1.grid(True, linestyle='--', alpha=0.6)

    ax1.set_xticks(np.arange(0, 25, 1))
    ax1.set_xlim([0, 24])
    ax1.set_ylim([-2000,2000 ])
    ax1.axhline(y=0, color='black', linestyle='-')
    # 添加图例
    # 合并两个轴的图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines = lines1 + lines2
    labels = labels1 + labels2

    # 添加图例并调整位置
    ax1.legend(
        lines, labels, 
        loc = 'upper left',
        frameon=False,  # 去掉图例边框
        prop={'size': 15}
    )
    ax1.tick_params(axis='both', which='major', labelsize=15)

    ax2.tick_params(axis='both', which='major', labelsize=15)
    for spine in ax1.spines.values():
        spine.set_linewidth(1.5)
    plt.tight_layout()
    plt.show()

def plot_DR(var: list, variables_up,variables_down,file_path):

    df = pd.read_csv(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [v for v in var if v not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return

    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(9, 6.75))  # 左侧y轴 (柱状图)
    labels = ['原始电负荷','DR后电负荷','削减电负荷']
    for idx, variable in enumerate(var):
        x = df.index
        y = df[variable]
        
        ax.plot(
            x, y, 
            color=base_colors[idx % len(base_colors)], 
            linestyle='-.', 
            linewidth=2, 
            label=labels[idx % len(labels)],
            marker=custom_dot[idx % len(base_colors)],
            markersize=4
            )
        


    # 设置X轴和Y轴标签
    ax.set_xlabel('时间(h)',fontsize=20)
    ax.set_ylabel('电能(kWh)',fontsize=20)

    # 设置标题

    # 绘制堆叠柱图
    bottom_up = np.zeros(len(df))
    top_down = np.zeros(len(df))
    bar_positions = np.arange(len(df))  # 柱状图的横坐标位置
    # 绘制向上堆叠的柱状图
    for idx, variable in enumerate(variables_up):
        ax.bar(
            bar_positions, 
            df[variable], 
            bottom=bottom_up, 
            color=base_colors[idx+3 % len(base_colors)], 
            label='调度入负荷',
            width = 0.6
        )
        bottom_up += df[variable]

    # 绘制向下堆叠的柱状图
    for idx, variable in enumerate(variables_down):
        ax.bar(
            df.index+0.5, 
            -df[variable], 
            bottom=-top_down, 
            color=base_colors[idx+4 % len(base_colors)],
            label='调度出负荷',
            width = 0.6
    )
        top_down += df[variable]

        # 显示网格线
    # ax1.grid(True, linestyle='--', alpha=0.6)

    ax.set_xticks(np.arange(0, 24, 1))
    ax.set_xlim([0, 24])
    # ax.set_yticks(np.arange(-500, 2500, 500))
    ax.set_yticks(np.arange(-400, 2400, 200))

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    # 添加图例

    # ax.grid(True, linestyle='--', alpha=0.6)
    # 添加图例并调整位置
    ax.tick_params(axis='both', which='major', labelsize=15)

    ax.legend( frameon=False,  # 去掉图例边框
        prop={'size': 15})
    plt.tight_layout()
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)  # 设置边框线宽度为2
    plt.show()

def plot_SolarAndTem(var_tem: list, var_solar,file_path):

    df = pd.read_csv(file_path)

    # 创建一个新的图形
    _, ax1 = plt.subplots(figsize=(9, 6.75))  # 左侧y轴 (柱状图)
    ax2 = ax1.twinx()  # 右侧y轴 (折线图)

    for idx, variable in enumerate(var_tem):
        x = df.index.values
        y = df[variable].values
        
        # 为每个时段插入一个中间点
        x_mid = (x[:-1] + x[1:]) / 2
        
        # 绘制阶梯图
        ax1.step(x, y, where='post', color='black', linestyle='-.', linewidth=2, label='室外温度')
        
        # # 将点标记在每个时段的中间位置
        # ax1.plot(x_mid, y[:-1], color='black', linestyle='None', marker=custom_dot[idx % len(custom_colors)], markersize=3)


    # 设置X轴和Y轴标签
    ax1.set_xlabel('时间(h)',fontsize=20)
    ax1.set_ylabel('室外温度(℃)',fontsize=20)
    # ax2.set_ylabel('太阳辐射强度(kW/m2)')
    ax2.set_ylabel('太阳辐射强度(kW/m$^2$)',fontsize=20)


    bar_positions = np.arange(len(df)) + 0.5  # 折线图的横坐标位置
    
    for idx, variable in enumerate(var_solar):
        ax2.plot(
            bar_positions, df[variable], 
            color=custom_colors[idx % len(custom_colors)], 
            linestyle='-', 
            marker='o', 
            markersize=6,
            linewidth=2, 
            label='太阳辐射强度',
            # 设置字体大小
        )
    
        # 显示网格线
    # ax1.grid(True, linestyle='--', alpha=0.6)

    ax1.set_xticks(np.arange(0, 25, 4))
    ax1.set_xlim([0, 24])
    ax1.set_ylim([-5,15])
    # 添加图例
    # 合并两个轴的图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines = lines1 + lines2
    labels = labels1 + labels2
    ax1.tick_params(axis='both', which='major', labelsize=15)

    ax2.tick_params(axis='both', which='major', labelsize=15)
    # 添加图例并调整位置
    ax1.legend(
        lines, labels, 
        loc = 'upper left',
        frameon=False,  # 去掉图例边框
        prop={'size': 20}
    )
    ax1.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    for spine in ax1.spines.values():
        spine.set_linewidth(1.5)  # 设置边框线宽度为2
    plt.show()


# 绘制氢能流动：柱状图+折线图，类似与bess
def plot_Hydrogen(var,variables_up,variables_down,file_path):
    df = pd.read_csv(file_path)
# 检查所有变量名是否存在于DataFrame中
    missing_vars = [v for v in var if v not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return

    # 创建一个新的图形
    fig, ax1 = plt.subplots(figsize=(9, 6.75))  # 左侧y轴 (柱状图)
    ax2 = ax1.twinx()  # 右侧y轴 (折线图)
    labels = ['电解槽制氢','系统购氢']
    for idx, variable in enumerate(var):
        x = df.index.values
        y = df[variable].values
        
        # 为每个时段插入一个中间点
        x_mid = (x[:-1] + x[1:]) / 2
        
        # 绘制阶梯图
        ax2.step(x, y/240, where='post', color='black', linestyle='-.', linewidth=2, label='储氢罐储氢量')
        
        # 将点标记在每个时段的中间位置
        ax2.plot(x_mid, y[:-1]/240, color='black', linestyle='None', marker=custom_dot[idx % len(custom_colors)], markersize=4)


    # 设置X轴和Y轴标签
    ax1.set_xlabel('时间(h)',fontsize=20)
    ax1.set_ylabel('氢量(kg)',fontsize=20)
    ax2.set_ylabel('储氢罐储氢量(%)',fontsize=20)
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))  

    # 设置标题
    # ax.set_title('Variables Over Time')

    # 绘制堆叠柱图
    bottom_up = np.zeros(len(df))
    top_down = np.zeros(len(df))
    bar_positions = np.arange(len(df)) + 0.5  # 柱状图的横坐标位置
    # 绘制向上堆叠的柱状图
    for idx, variable in enumerate(variables_up):
        ax1.bar(
            bar_positions, 
            df[variable], 
            bottom=bottom_up, 
            color=custom_colors[idx % len(custom_colors)], 
            label=labels[idx % len(labels)],
            width = 0.6
        )
        bottom_up += df[variable]

    # 绘制向下堆叠的柱状图
    for idx, variable in enumerate(variables_down):
        ax1.bar(
            df.index+0.5, 
            -df[variable], 
            bottom=-top_down, 
            color=custom_colors[idx+2 % len(custom_colors)],
            label='燃料电池耗氢',
            width = 0.6
    )
        top_down += df[variable]

        # 显示网格线
    # ax1.grid(True, linestyle='--', alpha=0.6)

    ax1.set_xticks(np.arange(0, 25, 1))
    ax1.set_xlim([0, 24])
    ax1.set_ylim([-150,150 ])
    ax1.axhline(y=0, color='black', linestyle='-')
    # 添加图例
    # 合并两个轴的图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines = lines1 + lines2
    labels = labels1 + labels2

    # 添加图例并调整位置
    ax1.legend(
        lines, labels, 
        loc = 'lower left',
        frameon=False,  # 去掉图例边框
        prop={'size': 15}
    )
    ax1.tick_params(axis='both', which='major', labelsize=15)

    ax2.tick_params(axis='both', which='major', labelsize=15)
    for spine in ax1.spines.values():
        spine.set_linewidth(1.5)
    plt.tight_layout()
    plt.show()

def plot_room_tem(var: list, file_path):
    # 读取CSV文件
    df = pd.read_excel(file_path)

    # 检查所有变量名是否存在于DataFrame中
    missing_vars = [v for v in var if v not in df.columns]
    if missing_vars:
        print(f"Error: The following variables do not exist in the CSV file: {', '.join(missing_vars)}")
        return

    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(9, 6.75))  # 设置图形大小
    
    labels = ['地源热泵','电锅炉','燃料电池','空气源热泵']


    # 绘制每个变量的阶梯图
    for idx, variable in enumerate(var):

        x = df.index.values.tolist()
        print(df.index)
        y = df[variable].values.tolist()
        x.append(24)
        y.append(y[-1])
        x_mid=[]
        # 为每个时段插入一个中间点
        for i in range(len(x)-1):

            x_mid.append((x[i]+x[i+1])/2)
        
        # 绘制阶梯图
        ax.step(x, y, where='post', color=custom_colors[idx % len(custom_colors)], linestyle='-.', linewidth=2, label=labels[idx % len(labels)])
        
        # 将点标记在每个时段的中间位置
        ax.plot(x_mid, y[:-1], color=custom_colors[idx % len(custom_colors)], linestyle='None', marker=custom_dot[idx % len(custom_colors)], markersize=4)


    ax.set_xticks(np.arange(0, 25, 1))
    # ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))  
    # 设置X轴和Y轴标签
    ax.set_xlabel('时间(h)',fontsize=20)
    ax.set_ylabel('出水温度(℃)',fontsize=20)
    ax.set_xlim([0, 24])
    ax.set_ylim([30, 60])
    # 设置标题
    # ax.set_title('')

    # 显示网格线
    # ax.grid(True, linestyle=':', alpha=0.6)

    # 添加图例
    ax.legend(        loc = 'upper left',
        frameon=False,  # 去掉图例边框
        prop={'size': 15})
    ax.tick_params(axis='both', which='major', labelsize=15)

    plt.tight_layout()
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)  # 设置边框线宽度为2
    # 显示图片
    # 自动调整布局并显示图表
    plt.tight_layout()

    # 显示图表
    plt.show()
# 绘制需求响应可调度负荷经济补偿机制图
def plot_dr_cost():
    lam_s_in = [0.077,0.077,0.077,0.077,0.077,0.077,0.077,0.077,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.056,0.056]

    lam_s_out = [0,0,0,0,0,0,0,0, 0.063,0.063,0.063,0.063, 0.049,0.049,0.049,0.049,0.049,0.049,0.105,0.105,0.105,0.105,0,0]

    # 绘制lam_s_in折线图
    # 绘制lam_s_out折线图
    fig, ax = plt.subplots(figsize=(9, 6.75))  # 设置图形大小
    ax.plot(
        range(len(lam_s_in)), lam_s_in, 
        color='black', 
        linestyle='-', 
        marker=custom_dot[0], 
        markersize=6,
        linewidth=2, 
        label='电负荷调度入',
    )
    # 在同一张图上绘制第二条折线
    ax.plot(
        range(len(lam_s_out)), lam_s_out, 
        color='red', 
        linestyle='-', 
        marker=custom_dot[1], 
        markersize=6,
        linewidth=2, 
        label='电负荷调度出',
    )
    ax.set_xticks(np.arange(0, 25, 1))
    ax.set_xlim([0, 23])
    ax.legend(

        loc = 'upper left',
        frameon=False,  # 去掉图例边框
        prop={'size': 20}
    )
    ax.tick_params(axis='both', which='major', labelsize=15)

    ax.set_xlabel('时间(h)',fontsize=20)
    ax.set_ylabel('补偿价格(元/kWh)',fontsize=20)
    # ax.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)  # 设置边框线宽度为2
    # 显示图片
    plt.show()

if __name__ == '__main__':

    # result_file_path='D:\code_py\Optimization\edge-cloud-distrubuted-opt\Centralized-solution-v2\output/result-24h-ce.csv'
    result_file_path='contral-opt\control-optimization\Output\dict_opt_plot.xls'
    input_file_path='D:\code_py\Optimization\edge-cloud-distrubuted-opt\Centralized-solution-v2\input/input-24h.csv'
    # plot_stacked_bars_up_down(['P_pv','P_fc','P_buy'],[],file_path)
    # plot_step_chart(['Tem_ht','Tem_de'],result_file_path)
    # plot_SolarAndTem(['Temenv'],['solar'],input_file_path)
    
    # plot_p_banlance(['P_buy','P_pv','P_fc','P_bdisc'],['P_el','P_eb','P_ghp','P_bch'],['P_Dr'],result_file_path)
    # plot_g_banlance(['G_eb','G_fc','G_ghp','G_ht_out'],['G_ht_in'],['G_load'],result_file_path)
    # input_file_path='D:\code_py\Optimization\edge-cloud-distrubuted-opt\Centralized-solution-v2\input/input-24h.csv'
    # plot_step_chart(['Tem'],result_file_path)
    # plot_bess(['Soc_b'],['P_bch'],['P_bdisc'],result_file_path)
    # plot_DR(['Ploadnew1','P_Dr','P_c'],['P_s_in'],['P_s_out'],result_file_path)
    # plot_dr_cost()
    # plot_line_chart(['G_load'],result_file_path)

    # plot_Hydrogen(['H_hst'],['H_el','H_buy'],['H_fc'],result_file_path)
    plot_room_tem(['t_ghp','t_eb',"t_fc","t_ahp"],result_file_path)