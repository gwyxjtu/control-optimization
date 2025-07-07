'''
Author: guo-4060ti 867718012@qq.com
Date: 2025-06-16 20:19:09
LastEditTime: 2025-06-21 10:33:52
LastEditors: guo-4060ti 867718012@qq.com
FilePath: \control-optimization\Model\optimization_day.py
Description: 雪花掩盖着哽咽叹息这离别
'''

'''
    开源版本，使用SCIP优化求解器,SCIP 混合整数规划求解器的 Python 接口‌
    pyscipopt version:  5.2.1
    SCIP version:       9.1

'''     

import pyscipopt as opt


from arrow import get
import gurobipy as gp
from gurobipy import GRB
import numpy as np
from pandas import period_range
from sympy import per
import xlwt
import random
import pandas as pd
from cpeslog.log_code import _logging




def get_index(temperature, eta_dict):
    """获取温度对应的效率，根据最临近的温度来获取

    Args:
        temperature (_type_): 温度
        eta_dict (_type_): 效率字典，键为温度，值为对应的效率

    Returns:
        eta_device: 对应温度的设备效率
    """
    if temperature in eta_dict:
        eta_device = eta_dict[temperature]
    else:
        # 如果温度不在字典中，找到最接近的温度
        closest_temp = min(eta_dict.keys(), key=lambda x: abs(x - temperature))
        eta_device = eta_dict[closest_temp]
    return eta_device




def crf(year):
    i = 0.08
    crf = ((1+i)**year)*i/((1+i)**year-1)
    return crf


def to_csv(res, filename):
    """生成excel输出文件

    Args:
        res (_type_): 结果json，可以包括list和具体值
        filename (_type_): 文件名，不用加后缀
    """
    items = list(res.keys())
    wb = xlwt.Workbook()
    total = wb.add_sheet('test')
    for i in range(len(items)):
        total.write(0,i,items[i])
        if type(res[items[i]]) == list:
            sum = 0
            #print(items[i])
            for j in range(len(res[items[i]])):
                total.write(j+1,i,float((res[items[i]])[j]))
        else:
            #print(items[i])
            total.write(1,i,float(res[items[i]]))
    wb.save("Output\\"+filename+".xls")


def get_data(data_file="input_720\yulin_water_load.xlsx"):
    """获取负荷数据

    Args:
        data_file: 负荷数据文件路径

    Returns:
        input_data: 包含电负荷、电热负荷、冷负荷、生活热水负荷和光伏发电出力

    """
    datas = pd.read_excel(data_file)
    P_DE = list(datas['电负荷kW'].fillna(0))
    G_DE = list(datas['供暖热负荷(kW)'].fillna(0))
    Q_DE = list(datas['冷负荷(kW)'].fillna(0))
    H_DE = list(datas['生活热水负荷kW'].fillna(0))
    R_PV = list(datas['pv'].fillna(0))
    m_date = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    d_date = [sum(m_date[:i]) for i in range(12)]
    d_date.append(8760)
    P_DE = np.array([P_DE[24 * (15 + d_date[i]):24 * (15 + d_date[i] + 2)] for i in range(12)]).flatten().tolist()
    G_DE = np.array([G_DE[24 * (15 + d_date[i]):24 * (15 + d_date[i] + 2)] for i in range(12)]).flatten().tolist()
    Q_DE = np.array([Q_DE[24 * (15 + d_date[i]):24 * (15 + d_date[i] + 2)] for i in range(12)]).flatten().tolist()
    H_DE = np.array([H_DE[24 * (15 + d_date[i]):24 * (15 + d_date[i] + 2)] for i in range(12)]).flatten().tolist()
    R_PV = np.array([R_PV[24 * (15 + d_date[i]):24 * (15 + d_date[i] + 2)] for i in range(12)]).flatten().tolist()


    G_DE = [g*0.8 if g>2000 else g for g in G_DE]
    G_DE = [g*0.8 for g in G_DE]
    # R_PV = np.array([0.01 for _ in range(24)])
    # R_PV = [110.0074,  90.7150,  70.9062,  50.1641,  10.8078,  0.0000,  0.0000,  0.0000,
    #         0.6954,  0.0000,  0.0000,  0.0000,  0.0000,  0.0000,  0.0000,  0.0000,
    #         0.0000,  0.0000,  0.6624,  40.6319,  80.6814, 110.0320, 120.0893, 120.0621]
    # ap = [6.8751163, 25.203173, 58.663414, 46.23391, 15.5059395,
    #       6.236669, 24.959608, 61.725365, 397.1714, 512.21313,
    #       541.71594, 543.034, 543.6432, 543.6956, 543.73737,
    #       543.749, 543.75507, 498.0086, 211.71872, 47.75662,
    #       10.515502, 0., 0., 0.7397275]
    # a = [2.2726438e-03, 2.5604947e-03, 2.1851407e-03, 1.4123279e-03,
    #      1.6957275e-03, 1.4187992e-03, 0.0000000e+00, 2.5465543e+00,
    #      2.5188656e+01, 4.9726315e+01, 6.7844383e+01, 7.9719009e+01,
    #      8.6602310e+01, 8.6813011e+01, 8.2082542e+01, 7.0972374e+01,
    #      5.3855186e+01, 3.1476366e+01, 7.4239097e+00, 2.7517034e-03,
    #      2.5769279e-03, 2.1478247e-03, 2.7413550e-03, 2.6083612e-03]
    # R_PV = [i / 106 for i in a]
    # P_DE = [p/10 for p in P_DE]
    # G_DE = [g/10 for g in G_DE]
    # Q_DE = [q/10 for q in Q_DE]
    # H_DE = [h/10 for h in H_DE]
    input_data = {"P_DE": P_DE, "G_DE": G_DE, "Q_DE": Q_DE, "H_DE": H_DE, "R_PV": R_PV}
    return input_data


# TODO: 修改为pyscipopt的优化模型
def opt_day(parameter_json, load_json, begin_time, time_scale, storage_begin_json, storage_end_json):
    """计算优化问题，时间尺度不定，输入包括末时刻储能。

    Args:
        parameter_json (_type_): 输入config文件中读取的参数
        load_json (_type_): 预测的负荷向量
        time_scale (_type_): 计算的小时
        storage_begin_json (_type_): 初始端储能状态
        storage_end_json (_type_): 末端储能状态
    """
    # 常量
    c_water = 4.2e3 / 3600  # 水的比热容 (kWh/(t·K))
    M = 1e12  # 大数
    
    # 初始化设备效率参数
    try:        
        # GHP, 浅层地源热泵
        # eta_ghp = parameter_json['device']['ghp']['eta_ghp']
        eta_pump_ghp = parameter_json['device']['ghp']['eta_pump']
        # EB, 电锅炉
        eta_eb = parameter_json['device']['eb']['eta_eb']
        eta_pump_eb = parameter_json['device']['eb']['eta_pump']
        # AHP, 空气源热泵
        eta_ahp = parameter_json['device']['ahp']['eta_ahp']
            # 拟合得到的ahp cop计算式：cop=k_t_env*t_env + k_t_out*t_out
        k_t_env = parameter_json['device']['ahp']['k_t_env']
        k_t_ahp = parameter_json['device']['ahp']['k_t_ahp']
        eta_ahp_base = parameter_json['device']['ahp']['eta_ahp_base']
        eta_pump_ahp = parameter_json['device']['ahp']['eta_pump']
        # FC, 燃料电池
        eta_fc_p = parameter_json['device']['fc']['eta_p']
        # eta_fc_g = parameter_json['device']['fc']['eta_g']
        eta_pump_fc = parameter_json['device']['fc']['eta_pump']
        # g_p_ratio_200 = parameter_json['device']['fc']['power_200']['g_p_ratio']
        # g_p_ratio_400 = parameter_json['device']['fc']['power_400']['g_p_ratio']
        # g_p_ratio_600 = parameter_json['device']['fc']['power_600']['g_p_ratio']
        k_g_p_200 = parameter_json['device']['fc']['power_200']['k_g_p'] 
        b_g_p_200 = parameter_json['device']['fc']['power_200']['b_g_p']  
        k_g_p_400 = parameter_json['device']['fc']['power_400']['k_g_p']
        b_g_p_400 = parameter_json['device']['fc']['power_400']['b_g_p']
        k_g_p_600 = parameter_json['device']['fc']['power_600']['k_g_p']
        b_g_p_600 = parameter_json['device']['fc']['power_600']['b_g_p'] 
        # HT, 储热罐
        eta_ht_loss = parameter_json['device']['ht']['eta_loss']
        # eta_pump_ht = parameter_json['device']['ht']['eta_pump']
        # BS, 蓄电池
        # eta_bs_loss = parameter_json['device']['bs']['eta_loss']
        # PV, 光伏
        eta_pv = parameter_json['device']['pv']['eta_pv']
        # PIPE, 管网
        eta_pipe_loss = parameter_json['device']['pipe']['eta_loss']
        eta_pump_pipe = parameter_json['device']['pipe']['eta_pump']
        # GTW, 地热井
        m_gtw = parameter_json['device']['gtw']['water_max']
        t_gtw_in_min = parameter_json['device']['gtw']['t_in_min']  # 地热井进水温度

    except BaseException as E:
        _logging.error('读取config.json中设备效率参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化容量参数
    try:
        p_ghp_max = parameter_json['device']['ghp']['power_max']  # 浅层地源热泵额定功率
        p_eb_max = parameter_json['device']['eb']['power_max']  # 电锅炉额定功率
        p_ahp_max = parameter_json['device']['ahp']['power_max']  # 空气源热泵额定功率
        p_fc_max = parameter_json['device']['fc']['power_max']  # 燃料电池额定功率
        m_ht_sto = parameter_json['device']['ht']['water_max']  # 储热罐水量
        p_bs_sto_ub = parameter_json['device']['bs']['power_max']  # 蓄电池储能上限
        p_bs_sto_lb = parameter_json['device']['bs']['power_min']  # 蓄电池储能下限
        p_pv_max = parameter_json['device']['pv']['power_max']  # 光伏发电装机容量
    except BaseException as E:
        _logging.error('读取config.json中设备容量参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化边界上下限参数
    try:
        t_ht_sto_ub = parameter_json['device']['ht']['t_max']
        t_ht_sto_lb = parameter_json['device']['ht']['t_min']
        t_de_ub = parameter_json['device']['pipe']['t_max']  # 管网供回水温度上限
        t_de_lb = parameter_json['device']['pipe']['t_min']  # 管网供回水温度下限
        t_ghp_ub = parameter_json['device']['ghp']['t_max']  # 浅层地源热泵出水温度上限
        t_ghp_lb = parameter_json['device']['ghp']['t_min']  # 浅层地源热泵出水温度下限
        t_eb_ub = parameter_json['device']['eb']['t_max']  # 电锅炉出水温度上限
        t_eb_lb = parameter_json['device']['eb']['t_min']  # 电锅炉出水温度下限
        t_ahp_ub = parameter_json['device']['ahp']['t_max']  # 空气源热泵出水温度上限
        t_ahp_lb = parameter_json['device']['ahp']['t_min']  # 空气源热泵出水温度下限
        t_fc_ub = parameter_json['device']['fc']['t_max']  # 燃料电池出水温度上限
        t_fc_lb = parameter_json['device']['fc']['t_min']  # 燃料电池出水温度下限

        m_ghp_ub = parameter_json['device']['ghp']['water_max']  # 浅层地源热泵循环水量上限
        m_ghp_lb = parameter_json['device']['ghp']['water_min']  # 浅层地源热泵循环水量下限
        m_eb_ub = parameter_json['device']['eb']['water_max']
        m_eb_lb = parameter_json['device']['eb']['water_min']
        m_ahp_ub = parameter_json['device']['ahp']['water_max']
        m_ahp_lb = parameter_json['device']['ahp']['water_min']
        m_fc_ub = parameter_json['device']['fc']['water_max']
        m_fc_lb = parameter_json['device']['fc']['water_min']
        m_ht_ub = parameter_json['device']['ht']['water_max']
        m_ht_lb = parameter_json['device']['ht']['water_min']
        m_de_ub = parameter_json['device']['pipe']['water_max']  # 管网循环水量上限
        m_de_lb = parameter_json['device']['pipe']['water_min']  # 管网循环水量下限
    except BaseException as E:
        _logging.error('读取config.json中边界上下限参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化价格
    try:
        lambda_ele_in = parameter_json['price']['ele_TOU_price']
        lambda_ele_in = lambda_ele_in * (int(time_scale / 24))
        # lambda_ele_out = parameter_json['price']['power_sale']
        hydrogen_price = parameter_json['price']['hydrogen_price']
        p_demand_price = parameter_json['price']['demand_electricity_price']
    except BaseException as E:
        _logging.error('读取config.json中价格参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化负荷
    try:
        input_data = get_data()
        
        p_load = list(input_data['P_DE'])
        period = time_scale
        # g_load = [list(input_data['G_DE'])[i] + list(input_data['H_DE'])[i] for i in range(period)]
        g_load = list(input_data['G_DE'])
        q_load = list(input_data['Q_DE'])
        pv_generation = list(input_data['R_PV'])
        # NOTE: 认为此为环境温度，是否正确？可以
        t_env = list(load_json['ambient_temperature'])  # 读环境温度
        g_func= list(load_json['g函数值'])
    except BaseException as E:
        _logging.error('读取负荷文件中电冷热光参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化储能
    # t_ht_start=17

    # try:
    #     # hydrogen_bottle_max_start = storage_begin_json['hydrogen_bottle_max'][begin_time]  #气瓶
    #     # hst_kg_start = storage_begin_json['hst_kg'][begin_time]  # 缓冲罐剩余氢气
    #     t_ht_start = storage_begin_json['t_ht'][begin_time]  # 热水罐
    #     # t_ct_start = storage_begin_json['t_ct'][begin_time]  # 冷水罐
    #     t_de_start = storage_begin_json['t_de'][begin_time]  # 末端


    #     # hydrogen_bottle_max_final = storage_end_json['hydrogen_bottle_max'][begin_time+time_scale] #气瓶
    #     # hst_kg_final = storage_end_json['hst_kg'][begin_time+time_scale]  # 缓冲罐剩余氢气
    #     t_ht_final = storage_end_json['t_ht'][begin_time+time_scale]  # 热水罐
    #     # t_ct_final = storage_end_json['t_ct'][begin_time+time_scale]  # 冷水罐
    # except BaseException as E:
    #     _logging.error('读取储能容量初始值和最终值失败,错误原因为{}'.format(E))
    #     raise Exception

    # 建立SCIP模型

    model_scip = opt.Model("bilinear")


    # 通过 gurobi 建立模型
    model = gp.Model("bilinear")

    # 添加变量
    opex = model_scip.addVar(vtype='C', lb=0, name="opex")  # 总运行成本
    opex_t = [model_scip.addVar(vtype='C', lb=0, name=f"opex[{t}]") for t in range(period)]  # 每个时段的运行成本
    # opex = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="opex")
    # opex_t = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"opex[{t}]") for t in range(period)]  # 每个时段的运行成本
    # 工况变量
    z_pur = [model_scip.addVar(vtype='B', name=f"z_pur[{t}]") for t in range(period)]
    z_ghp_ht = [model_scip.addVar(vtype='B', name=f"z_ghp_ht[{t}]") for t in range(period)]
    z_ghp_de = [model_scip.addVar(vtype='B', name=f"z_ghp_de[{t}]") for t in range(period)]
    z_eb_ht = [model_scip.addVar(vtype='B', name=f"z_eb_ht[{t}]") for t in range(period)]
    z_eb_de = [model_scip.addVar(vtype='B', name=f"z_eb_de[{t}]") for t in range(period)]
    z_fc_ht = [model_scip.addVar(vtype='B', name=f"z_fc_ht[{t}]") for t in range(period)]
    z_fc_de = [model_scip.addVar(vtype='B', name=f"z_fc_de[{t}]") for t in range(period)]
    # z_pur = [model.addVar(vtype=GRB.BINARY, name=f"z_pur[{t}]") for t in range(period)]  # 是否从电网买电
    # z_ghp_ht = [model.addVar(vtype=GRB.BINARY, name=f"z_ghp_ht[{t}]") for t in range(period)]  # 浅层地源热泵给储热罐蓄热
    # z_ghp_de = [model.addVar(vtype=GRB.BINARY, name=f"z_ghp_de[{t}]") for t in range(period)]  # 浅层地源热泵给末端供热
    # z_eb_ht = [model.addVar(vtype=GRB.BINARY, name=f"z_eb_ht[{t}]") for t in range(period)]  # 电锅炉给储热罐蓄热
    # z_eb_de = [model.addVar(vtype=GRB.BINARY, name=f"z_eb_de[{t}]") for t in range(period)]  # 电锅炉给末端供热
    # z_fc_ht = [model.addVar(vtype=GRB.BINARY, name=f"z_fc_ht[{t}]") for t in range(period)]  # 燃料电池给储热罐蓄热
    # z_fc_de = [model.addVar(vtype=GRB.BINARY, name=f"z_fc_de[{t}]") for t in range(period)]  # 燃料电池给末端供热
    # NOTE: 没看明白储热罐的工况，是不能同时给末端供热和蓄热吗？对
    z_ht_sto = [model_scip.addVar(vtype='B', name=f"z_ht_sto[{t}]") for t in range(period)]
    # z_ht_sto = [model.addVar(vtype=GRB.BINARY, name=f"z_ht_sto[{t}]") for t in range(period)]  # 储热罐蓄热
    # 电网
    p_pur = [model_scip.addVar(vtype='C', lb=0, name=f"p_pur[{t}]") for t in range(period)]  # 从电网购电量
    # p_pur = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur[{t}]") for t in range(period)]  # 从电网购电量
    # 氢源
    h_pur = [model_scip.addVar(vtype='C', lb=0, name=f"h_pur[{t}]") for t in range(period)]
    # h_pur = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur[{t}]") for t in range(period)]  # 购氢量
    # 末端
    t_de = [model_scip.addVar(vtype='C', lb=t_de_lb, ub=t_de_ub, name=f"t_de[{t}]") for t in range(period)]
    # t_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_de_lb, ub=t_de_ub, name=f"t_de[{t}]") for t in range(period)]  # 末端供回水温度
    # GHP
    z_ghp = [model_scip.addVar(vtype='B', name=f"z_ghp[{t}]") for t in range(period)]
    # z_ghp = [model.addVar(vtype=GRB.BINARY, name=f"z_ghp[{t}]") for t in range(period)]  # 是否启用浅层地源热泵
    # p_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=p_ghp_max,
    #                       name=f"p_ghp[{t}]") for t in range(period)]  # 浅层地源热泵功率
    
    g_ghp = [model_scip.addVar(vtype='C', lb=0, name=f"g_ghp[{t}]") for t in range(period)]
    g_ghp_ht = [model_scip.addVar(vtype='C', lb=0, name=f"g_ghp_ht[{t}]") for t in range(period)]
    g_ghp_de = [model_scip.addVar(vtype='C', lb=0, name=f"g_ghp_de[{t}]") for t in range(period)]
    t_ghp = [model_scip.addVar(vtype='C', lb=0, name=f"t_ghp[{t}]") for t in range(period)]
    m_ghp = [model_scip.addVar(vtype='C', lb=m_ghp_lb, ub=m_ghp_ub,
                               name=f"m_ghp[{t}]") for t in range(period)]
    p_pump_ghp = [model_scip.addVar(vtype='C', lb=0, name=f"p_pump_ghp[{t}]") for t in range(period)]
    eta_ghp = [model_scip.addVar(vtype='C', lb=0, name=f"cop_ghp[{t}]") for t in range(period)]
    # g_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ghp[{t}]") for t in range(period)]  # 浅层地源热泵供热量
    # g_ghp_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ghp_ht[{t}]") for t in range(period)]  # 浅层地源热泵给储热罐蓄热量
    # g_ghp_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ghp_de[{t}]") for t in range(period)]  # 浅层地源热泵给末端供热量
    # t_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ghp[{t}]") for t in range(period)]  # 浅层地源热泵出水温度
    # m_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=m_ghp_lb, ub=m_ghp_ub,
    #                       name=f"m_ghp[{t}]") for t in range(period)]  # 浅层地源热泵循环水量
    # p_pump_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_ghp[{t}]") for t in range(period)]  # 浅层地源热泵循环泵功率
    # eta_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cop_ghp[{t}]") for t in range(period)]  # 浅层地源热泵性能系数
    # GTW
    t_gtw_in = [model_scip.addVar(vtype='C', lb=t_gtw_in_min, name=f"t_gtw_in[{t}]") for t in range(period)]
    t_gtw_out = [model_scip.addVar(vtype='C', lb=t_gtw_in_min, name=f"t_gtw_out[{t}]") for t in range(period)]
    t_b = [model_scip.addVar(vtype='C', lb=0, name=f"t_b[{t}]") for t in range(period)]
    g_gtw = [model_scip.addVar(vtype='C', lb=0, name=f"g_gtw[{t}]") for t in range(period)]
    # t_gtw_in = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_gtw_in_min, name=f"t_gtw_in[{t}]") for t in range(period)]  # 地热井进水温度
    # t_gtw_out = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_gtw_in_min, name=f"t_gtw_out[{t}]") for t in range(period)]  # 地热井出水温度
    # t_b = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_b[{t}]") for t in range(period)]  # 地热井温度
    # g_gtw = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_gtw[{t}]") for t in range(period)]
    # EB
    p_eb = [model_scip.addVar(vtype='C', lb=0, ub=p_eb_max, name=f"p_eb[{t}]") for t in range(period)]
    g_eb = [model_scip.addVar(vtype='C', lb=0, name=f"g_eb[{t}]") for t in range(period)]
    g_eb_ht = [model_scip.addVar(vtype='C', lb=0, name=f"g_eb_ht[{t}]") for t in range(period)]
    g_eb_de = [model_scip.addVar(vtype='C', lb=0, name=f"g_eb_de[{t}]") for t in range(period)]
    t_eb = [model_scip.addVar(vtype='C', lb=t_eb_lb, ub=t_eb_ub, name=f"t_eb[{t}]") for t in range(period)]
    m_eb = [model_scip.addVar(vtype='C', lb=m_eb_lb, ub=m_eb_ub,
                              name=f"m_eb[{t}]") for t in range(period)]
    p_pump_eb = [model_scip.addVar(vtype='C', lb=0, name=f"p_pump_eb[{t}]") for t in range(period)]
    # p_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=p_eb_max,
    #                      name=f"p_eb[{t}]") for t in range(period)]
    # g_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb[{t}]") for t in range(period)]
    # g_eb_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb_ht[{t}]") for t in range(period)]
    # g_eb_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb_de[{t}]") for t in range(period)]
    # t_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_eb_lb,ub=t_eb_ub, name=f"t_eb[{t}]") for t in range(period)]
    # m_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=m_eb_lb, ub=m_eb_ub,
    #                      name=f"m_eb[{t}]") for t in range(period)]
    # p_pump_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_eb[{t}]") for t in range(period)]
    # AHP
    p_ahp = [model_scip.addVar(vtype='C', lb=0, ub=p_ahp_max,
                              name=f"p_ahp[{t}]") for t in range(period)]
    g_ahp = [model_scip.addVar(vtype='C', lb=0, name=f"g_ahp[{t}]") for t in range(period)]
    t_ahp = [model_scip.addVar(vtype='C', lb=t_ahp_lb,ub=t_ahp_ub, name=f"t_ahp[{t}]") for t in range(period)]
    m_ahp = [model_scip.addVar(vtype='C', lb=m_ahp_lb, ub=m_ahp_ub,
                              name=f"m_ahp[{t}]") for t in range(period)]
    eta_ahp = [model_scip.addVar(vtype='C', lb=0, name=f"cop_ahp[{t}]") for t in range(period)]
    p_pump_ahp = [model_scip.addVar(vtype='C', lb=0, name=f"p_pump_ahp[{t}]") for t in range(period)]     
    # p_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=p_ahp_max,
    #                       name=f"p_ahp[{t}]") for t in range(period)]
    # g_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ahp[{t}]") for t in range(period)]
    # t_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_ahp_lb,ub=t_ahp_ub, name=f"t_ahp[{t}]") for t in range(period)]
    # m_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=m_ahp_lb, ub=m_ahp_ub,
    #                       name=f"m_ahp[{t}]") for t in range(period)]
    # eta_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"cop_ahp[{t}]") for t in range(period)]  # 空气源热泵性能系数
    # p_pump_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_ahp[{t}]") for t in range(period)]
    # FC
    m_h_fc = [model_scip.addVar(vtype='C', lb=0, name=f"m_h_fc[{t}]") for t in range(period)]
    p_fc = [model_scip.addVar(vtype='C', lb=0, ub=p_fc_max,
                              name=f"p_fc[{t}]") for t in range(period)]
    g_fc = [model_scip.addVar(vtype='C', lb=0, name=f"g_fc[{t}]") for t in range(period)]
    g_fc_ht = [model_scip.addVar(vtype='C', lb=0, name=f"g_fc_ht[{t}]") for t in range(period)]
    g_fc_de = [model_scip.addVar(vtype='C', lb=0, name=f"g_fc_de[{t}]") for t in range(period)]
    t_fc = [model_scip.addVar(vtype='C', lb=t_fc_lb,ub=t_fc_ub, name=f"t_fc[{t}]") for t in range(period)]
    m_fc = [model_scip.addVar(vtype='C', lb=m_fc_lb, ub=m_fc_ub,
                              name=f"m_fc[{t}]") for t in range(period)]
    p_pump_fc = [model_scip.addVar(vtype='C', lb=0, name=f"p_pump_fc[{t}]") for t in range(period)]
    # m_h_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_h_fc[{t}]") for t in range(period)]  # 燃料电池耗氢量
    # p_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=p_fc_max,
    #                      name=f"p_fc[{t}]") for t in range(period)]
    # g_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc[{t}]") for t in range(period)]
    # g_fc_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc_ht[{t}]") for t in range(period)]
    # g_fc_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc_de[{t}]") for t in range(period)]
    # t_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_fc_lb,ub=t_fc_ub, name=f"t_fc[{t}]") for t in range(period)]
    # m_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=m_fc_lb, ub=m_fc_ub,
    #                      name=f"m_fc[{t}]") for t in range(period)]  # 燃料电池循环水量
    # p_pump_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_fc[{t}]") for t in range(period)]
    # HT
    g_ht = [model_scip.addVar(vtype='C', lb=0, name=f"g_ht[{t}]") for t in range(period)]
    t_ht_sto = [model_scip.addVar(vtype='C', lb=t_ht_sto_lb, ub=t_ht_sto_ub,
                                  name=f"t_ht_sto[{t}]") for t in range(period)]
    t_ht = [model_scip.addVar(vtype='C', lb=0, ub=t_ht_sto_ub, name=f"t_ht[{t}]") for t in range(period)]
    m_ht = [model_scip.addVar(vtype='C', lb=m_ht_lb, ub=m_ht_ub,
                              name=f"m_ht[{t}]") for t in range(period)]
    # g_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ht[{t}]") for t in range(period)]  # 储热罐给末端供热量
    # t_ht_sto = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_ht_sto_lb, ub=t_ht_sto_ub,
    #                          name=f"t_ht_sto[{t}]") for t in range(period)]  # 储热罐蓄热温度
    # t_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0,ub=t_ht_sto_ub, name=f"t_ht[{t}]") for t in range(period)]  # 储热罐出水温度
    # m_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=m_ht_lb, ub=m_ht_ub,
    #                      name=f"m_ht[{t}]") for t in range(period)]  # 储热罐循环水量
    # p_pump_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_ht[{t}]") for t in range(period)]
    # BS
    p_bs_sto = [model_scip.addVar(vtype='C', lb=p_bs_sto_lb, ub=p_bs_sto_ub,
                              name=f"p_bs_sto[{t}]") for t in range(period)]
    p_bs_ch = [model_scip.addVar(vtype='C', lb=0, ub=p_bs_sto_ub-p_bs_sto_lb,
                              name=f"p_bs_ch[{t}]") for t in range(period)]
    p_bs_dis = [model_scip.addVar(vtype='C', lb=0, ub=p_bs_sto_ub-p_bs_sto_lb,
                              name=f"p_bs_dis[{t}]") for t in range(period)]
    # p_bs_sto = [model.addVar(vtype=GRB.CONTINUOUS, lb=p_bs_sto_lb, ub=p_bs_sto_ub,
    #                          name=f"p_bs_sto[{t}]") for t in range(period)]  # 蓄电池储能量
    # p_bs_ch = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=p_bs_sto_ub-p_bs_sto_lb,
    #                         name=f"p_bs_ch[{t}]") for t in range(period)]  # 蓄电池充电功率
    # p_bs_dis = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=p_bs_sto_ub-p_bs_sto_lb,
    #                          name=f"p_bs_dis[{t}]") for t in range(period)]  # 蓄电池放电功率
    # PIPE
    t_supply = [model_scip.addVar(vtype='C', lb=0, name=f"t_supply[{t}]") for t in range(period)]  
    m_de = [model_scip.addVar(vtype='C', lb=m_de_lb, ub=m_de_ub,
                              name=f"m_de[{t}]") for t in range(period)]
    M_de = 100000  # 管网内水量
    T_de = [model_scip.addVar(vtype='C', lb=t_de_lb, name=f"T_de[{t}]") for t in range(period)]  # 管网内平均水温
    p_pump_pipe = [model_scip.addVar(vtype='C', lb=0, name=f"p_pump_pipe[{t}]") for t in range(period)]  # 管网循环泵功率
    # t_supply = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_supply[{t}]") for t in range(period)]  # 供水温度
    # m_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=m_de_lb, ub=m_de_ub,
    #                      name=f"m_de[{t}]") for t in range(period)]  # 管网循环水量
    # M_de = 100000 # 管网内水量
    # T_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=t_de_lb, name=f"T_de[{t}]") for t in range(period)]  # 管网内平均水温
    # p_pump_pipe = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_pipe[{t}]") for t in range(period)]  # 管网循环泵功率
    # PV
    p_pv = [model_scip.addVar(vtype='C', lb=0, name=f"p_pv[{t}]") for t in range(period)]  # 光伏发电功率
    # p_pv = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pv[{t}]") for t in range(period)]  # 光伏发电功率

    # 添加约束
    # TODO: 修改约束形式
    # model.addConstr(z_ghp[5] == 1)
    # 能量平衡
    model.addConstrs(p_pur[t] + p_pv[t] + p_fc[t] + p_bs_dis[t]
                     == p_load[t] + z_ghp[t]*p_ghp_max + p_eb[t] + p_ahp[t] + p_bs_ch[t]
                     + p_pump_ghp[t] + p_pump_eb[t] + p_pump_ahp[t] + p_pump_fc[t] + p_pump_pipe[t]
                     for t in range(period))
    # NOTE: 确认 M^{DE} 和 t^{MP} 指代是否正确
    # NOTE: 要添加工况约束吧，不然有问题
    model.addConstrs(g_ghp_de[t] + g_eb_de[t] + g_ahp[t] + g_fc_de[t] + g_ht[t]
                     == g_load[t]# + c_water * M_de * (T_de[t + 1] - T_de[t])
                     for t in range(period ))
    # NOTE: 末时刻请果哥确认
    # model.addConstr(z_ghp_de[-1]*g_ghp_de[-1] + z_eb_de[-1]*g_eb_de[-1] + g_ahp[-1] + z_fc_de[-1]*g_fc_de[-1] + g_ht[-1]
    #                 == g_load[-1] )#+ c_water * M_de * (T_de[0] - T_de[-1]))
    model.addConstrs(h_pur[t] == m_h_fc[t] for t in range(period))  # 氢源购氢量等于燃料电池耗氢量
    # 流量平衡
    # NOTE: 如何处理蓄热的流量平衡？文档中未体现。蓄热不用管，因为蓄热没有混水问题，用能量形式就够了
    model.addConstrs(m_ghp[t] + m_eb[t] + m_ahp[t] + m_fc[t] + m_ht[t] == m_de[t] for t in range(period))
    # fix m
    model.addConstrs(m_ghp[t] == m_ghp_lb for t in range(period))  # 固定减小复杂度
    model.addConstrs(m_eb[t] ==  m_eb_lb for t in range(period))  # 固定减小复杂度
    model.addConstrs(m_ahp[t] == m_ahp_lb for t in range(period))  # 固定减小复杂度
    model.addConstrs(m_fc[t] ==  m_fc_lb for t in range(period))  # 固定减小复杂度
    model.addConstrs(m_ht[t] ==  m_ht_lb for t in range(period))  # 固定减小复杂度
    model.addConstrs(m_de[t] ==  m_de_lb for t in range(period))  # 固定减小复杂度
    
    model.addConstrs(m_ghp[t] * t_ghp[t] + m_eb[t] * t_eb[t] + m_ahp[t] * t_ahp[t] + m_fc[t] * t_fc[t]
                     + m_ht[t] * t_ht[t] == m_de[t] * t_supply[t] for t in range(period))
    # model.addConstrs(g_load[t] == g_ahp[t] + g_ghp_de[t] + g_eb_de[t] + g_fc_de[t] + g_ht[t] for t in range(period))  # 末端供热量等于各设备供热量之和
    # 工况约束
    model.addConstrs(p_pur[t] <= z_pur[t] * M for t in range(period))
    model.addConstrs(g_ghp[t] == z_ghp_ht[t] * g_ghp_ht[t] + z_ghp_de[t] * g_ghp_de[t] for t in range(period))
    model.addConstrs(z_ghp_de[t] + z_ghp_ht[t] == z_ghp[t] for t in range(period))
    model.addConstrs(g_eb[t] == z_eb_ht[t] * g_eb_ht[t] + z_eb_de[t] * g_eb_de[t] for t in range(period))
    model.addConstrs(z_eb_de[t] + z_eb_ht[t] <= 1 for t in range(period))
    model.addConstrs(g_fc[t] == z_fc_ht[t] * g_fc_ht[t] + z_fc_de[t] * g_fc_de[t] for t in range(period))
    model.addConstrs(z_fc_de[t] + z_fc_ht[t] <= 1 for t in range(period))
    model.addConstrs(g_ghp_ht[t] + g_eb_ht[t] + g_fc_ht[t] <= z_ht_sto[t] * M for t in range(period))
    model.addConstrs(g_ht[t] <= (1 - z_ht_sto[t]) * M for t in range(period))

    # 设备约束
    # GHP
    # NOTE: 这怎么建动态效率模型？用 getVal 来读温度吗？温度就是变量
    model.addConstrs(g_ghp[t] == eta_ghp[t] * z_ghp[t] * p_ghp_max for t in range(period))
    # NOTE: t^{DE} 是固定值吗？目前先按变量建模。变量
    model.addConstrs(g_ghp[t]*z_ghp_de[t] == c_water * m_ghp[t] * (t_ghp[t] - t_de[t]) for t in range(period))
    model.addConstrs(p_pump_ghp[t] == eta_pump_ghp * m_ghp[t] for t in range(period))
    model.addConstrs(g_gtw[t]==g_ghp[t] - z_ghp[t] * p_ghp_max for t in range(period))
    # NOTE: 缺乏 GTW 约束描述，目前暂未建立 t^{GTW} 的关系
    for t in range(period):
        model.addConstr(eta_ghp[t]==2+0.1209*t_gtw_out[t])
        model.addConstr(g_gtw[t]==c_water*m_gtw*(t_gtw_out[t]-t_gtw_in[t]))
        model.addConstr(t_gtw_out[t]==0.2*(t_gtw_out[t]-t_b[t])+t_b[t])

    model.addConstr(t_b[0]==10.5-(1000/(2*np.pi*2.07*200*192))*(g_gtw[0])*g_func[0])
    for t in range(1,period):
        model.addConstr(t_b[t]==10.5-(1000/(2*np.pi*2.07*200*192))*gp.quicksum((g_gtw[j]-g_gtw[j-1])*g_func[t-j] for j in range(t+1)))

    # EB
    model.addConstrs(g_eb[t] == eta_eb * p_eb[t] for t in range(period))
    model.addConstrs(g_eb[t]*z_eb_de[t] == c_water * m_eb[t] * (t_eb[t] - t_de[t]) for t in range(period))
    model.addConstrs(p_pump_eb[t] == eta_pump_eb * m_eb[t] for t in range(period))
    # AHP
    # NOTE: 修改空气源热泵的效率计算
        # 一共有5个计算分区，顺序与表格一致
    for t in range(period):
        if t_env[t] < -15:
            model.addConstr(eta_ahp[t] == eta_ahp_base[0] + k_t_env[0] * t_env[t] + k_t_ahp[0] * t_ahp[t])
        elif t_env[t] < 0 and t_env[t] >= -15:
            model.addConstr(eta_ahp[t] == eta_ahp_base[1] + k_t_env[1] * t_env[t] + k_t_ahp[1] * t_ahp[t])
        elif t_env[t] < 15 and t_env[t] >= 0:
        #     z_ahp_cop=[model.addVar(vtype=GRB.BINARY, name=f"z_ahp_cop[{t}]") for t in range(period)]
        #     model.addConstr(eta_ahp[t] <= eta_ahp_base[2] + k_t_env[2] * t_env[t] + k_t_ahp[2] * t_ahp[t] + z_ahp_cop[t]*M)
        #     model.addConstr(eta_ahp[t] >= eta_ahp_base[2] + k_t_env[2] * t_env[t] + k_t_ahp[2] * t_ahp[t] - z_ahp_cop[t]*M)

        #     model.addConstr(eta_ahp[t] <= eta_ahp_base[3] + k_t_env[3] * t_env[t] + k_t_ahp[3] * t_ahp[t] + (1-z_ahp_cop[t])*M)
        #     model.addConstr(eta_ahp[t] >= eta_ahp_base[3] + k_t_env[3] * t_env[t] + k_t_ahp[3] * t_ahp[t] - (1-z_ahp_cop[t])*M)

            model.addGenConstrPWL(t_ahp[t],eta_ahp[t],[0,45,100],
                                  [eta_ahp_base[2] + k_t_env[2] * t_env[t] + k_t_ahp[2] * 0,
                                    eta_ahp_base[2] + k_t_env[2] * t_env[t] + k_t_ahp[2] * 45,
                                    eta_ahp_base[3] + k_t_env[3] * t_env[t] + k_t_ahp[3] * 100]
                                )
        else:
            model.addConstr(eta_ahp[t] == eta_ahp_base[4] + k_t_env[4] * t_env[t] + k_t_ahp[4] * t_ahp[t] for t in range(period))

    # model.addConstrs(eta_ahp[t] == eta_ahp_base + k_t_env * t_env[t] + k_t_ahp * t_ahp[t] for t in range(period))
    model.addConstrs(g_ahp[t] == eta_ahp[t] * p_ahp[t] for t in range(period))
    model.addConstrs(g_ahp[t] == c_water * m_ahp[t] * (t_ahp[t] - t_de[t]) for t in range(period))
    model.addConstrs(p_pump_ahp[t] == eta_pump_ahp * m_ahp[t] for t in range(period))
    # FC
    # NOTE: 修改了FC热计算
    model.addConstrs(p_fc[t] == eta_fc_p * m_h_fc[t] for t in range(period))
    for t in range(period):
        model.addGenConstrPWL(
            p_fc[t], g_fc[t], 
            [0, 200, 400, 600], 
            [0, k_g_p_200 * 200 + b_g_p_200, k_g_p_400 * 400 + b_g_p_400, k_g_p_600 * 600 + b_g_p_600]
            )

    # model.addConstrs(g_fc[t] == eta_fc_g * m_h_fc[t] for t in range(period))
    model.addConstrs(g_fc[t]*z_fc_de[t] == c_water * m_fc[t] * (t_fc[t] - t_de[t]) for t in range(period))
    model.addConstrs(p_pump_fc[t] == eta_pump_fc * m_fc[t] for t in range(period))
    # HT
    # NOTE: 文档中该公式是否有问题？
    model.addConstrs(z_ghp_ht[t]*g_ghp_ht[t] + z_eb_ht[t]*g_eb_ht[t] + z_fc_ht[t]*g_fc_ht[t] - g_ht[t]
                     == c_water * m_ht_sto * (t_ht_sto[t + 1] - t_ht_sto[t]) + eta_ht_loss * (t_ht_sto[t] - t_env[t])
                     for t in range(period - 1))
    model.addConstr(z_ghp_ht[-1]*g_ghp_ht[-1] + z_eb_ht[t]*g_eb_ht[-1] + z_fc_ht[t]*g_fc_ht[-1] - g_ht[-1]
                    == c_water * m_ht_sto * (t_ht_sto[0] - t_ht_sto[-1]) + eta_ht_loss * (t_ht_sto[-1] - t_env[23]))
    # NOTE: 建模可否省略为 g^{HW} = c * m^{HW} * (t^{HW} - t^{DE})？可以
    model.addConstrs(g_ht[t] == c_water * m_ht[t] * (t_ht[t] - t_de[t])
                     for t in range(period))
    # model.addConstrs(p_pump_ht[t] == eta_pump_ht * m_ht[t] for t in range(period))
    # BS
    model.addConstrs(p_bs_sto[t + 1] - p_bs_sto[t] == p_bs_ch[t] - p_bs_dis[t] for t in range(period - 1))
    model.addConstr(p_bs_sto[0] - p_bs_sto[-1] == p_bs_ch[-1] - p_bs_dis[-1])
    # PV
    model.addConstrs(p_pv[t] == eta_pv * p_pv_max * pv_generation[t] for t in range(period))
    # PIPE
    model.addConstrs(g_load[t] == c_water * m_de[t] * (t_supply[t] - t_de[t]) #+ eta_pipe_loss * (t_supply[t] - t_env[t])
                     for t in range(period))
    model.addConstrs(p_pump_pipe[t] == eta_pump_pipe * m_de[t] for t in range(period))

        # # 工况约束
        # model.addConstr(z_a[i]*g_ht[i]>=0)
        # model.addConstr(g_ht[i]+z_b[i]*g_eb[i]+z_c[i]*g_fc[i]+z_d[i]*g_hp[i]+z_e[i]*(g_fc[i]+g_hp[i])>=0)
        # model.addConstr(z_a[i]+z_b[i]+z_c[i]+z_d[i]+z_e[i]==1)
        # #燃料电池不能给水箱蓄
        # model.addConstr(z_c[i]==0)
        # model.addConstr(z_e[i]==0)

        #给末端供热的约束
    # model.addConstr(c*m_de*(t_de[i]-t_de_l[i]) == g_ht[i]*z_a[i]+g_eb[i]*(1-z_b[i])+g_fc[i]*(1-z_c[i]-z_e[i])+g_hp[i]*(1-z_d[i]-z_e[i])-g_load[i]-de_loss*(t_de_l[i]-43)*m_de)

    # opex
    model.addConstrs(opex_t[t] == hydrogen_price * h_pur[t] + lambda_ele_in[t] * p_pur[t] for t in range(period))
    model.addConstr(opex == gp.quicksum(opex_t[t] for t in range(period)))  # 总运行成本
    # 设置目标函数
    z_sum = gp.quicksum(z_pur[t] + z_ghp_ht[t] + z_ghp_de[t] + z_eb_ht[t] + z_eb_de[t] + z_fc_ht[t] + z_fc_de[t] + z_ht_sto[t] for t in range(period))
    model.setObjective(opex + z_sum, GRB.MINIMIZE)
    model.params.NonConvex = 2
    model.params.MIPGap = 0.02
    # model.params.TimeLimit=300
    model.Params.LogFile = "testlog.log"

    model.optimize()

    if model.status == GRB.INFEASIBLE or model.status == 4:
        print('Model is infeasible')
        model.computeIIS()
        model.write(r'Temp\model.ilp')
        print("Irreducible inconsistent subsystem is written to file 'model.ilp'")
        exit(0)

    # NOTE: 输出未处理
    # 计算一些参数
    # opex_without_opt = [lambda_ele_in[i]*(p_load[i]+q_load[i]/k_hp_q+g_load[i]/k_eb) for i in range(period)]
    # 重新构建输出
        
    dict_control = {
        "opex": opex.x,
        "opex_t": [v.x for v in opex_t],
        "z_pur": [v.x for v in z_pur],
        "z_ghp_ht": [v.x for v in z_ghp_ht],
        "z_ghp_de": [v.x for v in z_ghp_de],
        "z_eb_ht": [v.x for v in z_eb_ht],
        "z_eb_de": [v.x for v in z_eb_de],
        "z_fc_ht": [v.x for v in z_fc_ht],
        "z_fc_de": [v.x for v in z_fc_de],
        "z_ht_sto": [v.x for v in z_ht_sto],
        "p_pv": [v.x for v in p_pv],
        "p_pur": [v.x for v in p_pur],
        "h_pur": [v.x for v in h_pur],
        't_supply': [v.x for v in t_supply],
        "t_de": [v.x for v in t_de],
        "p_ghp": [v.x*p_ghp_max for v in z_ghp],
        "g_ghp": [v.x for v in g_ghp],
        "g_ghp_ht": [v.x for v in g_ghp_ht],
        "g_ghp_de": [v.x for v in g_ghp_de],
        "t_gtw_in": [v.x for v in t_gtw_in],
        "t_gtw_out": [v.x for v in t_gtw_out],
        "t_b": [v.x for v in t_b],
        "eta_ghp": [v.x for v in eta_ghp],
        "t_ghp": [v.x for v in t_ghp],
        "m_ghp": [v.x for v in m_ghp],
        "p_pump_ghp": [v.x for v in p_pump_ghp],
        "p_eb": [v.x for v in p_eb],
        "g_eb": [v.x for v in g_eb],
        "g_eb_ht": [v.x for v in g_eb_ht],
        "g_eb_de": [v.x for v in g_eb_de],
        "t_eb": [v.x for v in t_eb],
        "m_eb": [v.x for v in m_eb],
        "p_pump_eb": [v.x for v in p_pump_eb],
        "p_ahp": [v.x for v in p_ahp],
        "cop_ahp": [v.x for v in eta_ahp],
        "g_ahp": [v.x for v in g_ahp],
        "t_ahp": [v.x for v in t_ahp],
        "m_ahp": [v.x for v in m_ahp],
        "p_pump_ahp": [v.x for v in p_pump_ahp],
        "m_h_fc": [v.x for v in m_h_fc],
        "p_fc": [v.x for v in p_fc],
        "g_fc": [v.x for v in g_fc],
        "g_fc_ht": [v.x for v in g_fc_ht],
        "g_fc_de": [v.x for v in g_fc_de],
        "t_fc": [v.x for v in t_fc],
        "m_fc": [v.x for v in m_fc],
        "p_pump_fc": [v.x for v in p_pump_fc],
        "g_ht": [v.x for v in g_ht],
        "t_ht_sto": [v.x for v in t_ht_sto],
        "t_ht": [v.x for v in t_ht],
        "m_ht": [v.x for v in m_ht],
        "p_bs_sto": [v.x for v in p_bs_sto],
        "p_bs_ch": [v.x for v in p_bs_ch],
        "p_bs_dis": [v.x for v in p_bs_dis],
        "m_de": [v.x for v in m_de],
        'sup':[t_ahp[t].x*m_ahp[t].x+t_eb[t].x*m_eb[t].x+t_fc[t].x*m_fc[t].x+t_ghp[t].x*m_ghp[t].x+t_ht[t].x*m_ht[t].x for t in range(period)],
        'demand':[t_supply[t].x*m_de[t].x for t in range(period)],
    }
    # dict_control = {# 负荷
    #     'time':[begin_time+i for i in range(period)],
    #     # 运行工况输出
    #     'status':[15 for i in range(period)], #设备运行别问，问就是全开
    # }
    # dict_plot = {
    #     # operational day cost
    #     'opex_without_system':sum(opex_without_opt),#没有能源站的运行成本，负荷直接加
    #     'opex_without_opt':sum([h_pur[i].x for i in range(period)])*hydrogen_price + sum([max(0,p_load[i]-p_pv[i].x)*lambda_ele_in[i] for i in range(period)]),# 未经优化的运行成本
    #     'opex':sum([opex[i].x for i in range(period)]),# 经优化的运行成本
    #     'op_save_part':sum([opex[i].x for i in range(period)])/sum(opex_without_opt),

    #     # 综合能效
    #     'renewable_energy_part':sum([p_pv[i].x + p_fc[i].x for i in range(period)])/sum([p_pv[i].x + p_fc[i].x + p_pur[i].x for i in range(period)]), #可再生能源占比
    #     'efficiency':sum(p_load+q_load+g_load)/sum([p_pv[i].x + 33.3 * h_fc[i].x for i in range(period)]),

    #     #ele
    #     'p_pur':[p_pur[i].x for i in range(period)],#电网下电
    #     'p_pv':[p_pv[i].x for i in range(period)],#光伏
    #     'p_fc':[p_fc[i].x for i in range(period)],#燃料电池

    #     'p_hp':[p_hp[i].x for i in range(period)],#热泵
    #     'p_eb':[p_eb[i].x for i in range(period)],#电锅炉
    #     'p_pump':[p_pump[i].x for i in range(period)],#水泵
    #     'p_el':[p_el[i].x for i in range(period)],
    #     'p_load':p_load,
    #     #hydrogen
    #     'h_hst':[h_sto[i].x for i in range(period)],
    #     'h_sto_l':[h_sto_l[i].x for i in range(period)],
    #     'h_pur':[h_pur[i].x for i in range(period)],
    #     'h_el':[h_el[i].x for i in range(period)],
    #     'h_fc':[h_fc[i].x for i in range(period)],
    #     'h_tube':[hydrogen_bottle_max_start - sum([h_pur[i].x for i in range(j)]) for j in range(period)],
    #     #thermal
    #     't_ht':[t_ht[i].x for i in range(period)],  
    #     'g_ht':[c*m_ht*(t_ht[i].x - t_ht_l[i].x) for i in range(period)],

    #     'g_load':g_load,
    #     'g_hp':[g_hp[i].x for i in range(period)],
    #     'g_eb':[g_eb[i].x for i in range(period)],
    #     'g_fc':[g_fc[i].x for i in range(period)],

    #     # cold
    #     't_ct':[t_ct[i].x for i in range(period)],
    #     'q_ct':[c * m_ct * (t_ct[i].x - t_ct_l[i].x) for i in range(period)],
    #     'q_hp':[q_hp[i].x for i in range(period)],
    #     'q_load':q_load,
    # }
    dict_load = {
        'p_load': p_load,
        'g_load': g_load,
        'q_load': q_load,
        'pv_generation': pv_generation,
        't_env': t_env,
        'g_func': g_func
    }
    return dict_control, dict_load


if __name__ == '__main__':
    pass
    # opt_day()
