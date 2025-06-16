#!/usr/bin/env python3.7
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
    wb.save("Output/"+filename+".xls")


# TODO: 添加选取日期的输入参数
def get_data(data_file="Input_720/yulin_water_load.xlsx"):
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
    # period = time_scale
    
    # 初始化设备效率参数
    try:
        # TODO: 动态效率如何建模？
        # GHP, 浅层地源热泵
        eta_ghp = parameter_json['device']['ghp']['eta_ghp']
        eta_pump_ghp = parameter_json['device']['ghp']['eta_pump']
        # EB, 电锅炉
        eta_eb = parameter_json['device']['eb']['eta_eb']
        eta_pump_eb = parameter_json['device']['eb']['eta_pump']
        # AHP, 空气源热泵
        eta_ahp = parameter_json['device']['ahp']['eta_ahp']
        eta_pump_ahp = parameter_json['device']['ahp']['eta_pump']
        # FC, 燃料电池
        eta_fc_p = parameter_json['device']['fc']['eta_p']
        eta_fc_g = parameter_json['device']['fc']['eta_g']
        eta_pump_fc = parameter_json['device']['fc']['eta_pump']
        # HT, 储热罐
        eta_ht_loss = parameter_json['device']['ht']['eta_loss']
        # TODO: 是否需要储热罐循环泵功率？
        # eta_pump_ht = parameter_json['device']['ht']['eta_pump']
        # TODO: 是否需要地热井？
        # BS, 蓄电池

        # PIPE, 管网
        eta_pipe_loss = parameter_json['device']['pipe']['eta_loss']
        eta_pump_pipe = parameter_json['device']['pipe']['eta_pump']

    except BaseException as E:
        _logging.error('读取config.json中设备效率参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化容量参数
    try:
        P_ht = parameter_json['device']['ht']['energy']
        # m_ct = parameter_json['device']['ct']['water_max']
        m_de = parameter_json['device']['de']['water_max']
        m_gtw=parameter_json['device']['gtw']['water_max']
        P_PV = parameter_json['device']['pv']['power_max']
        # k_gtw_fluid=877/898*m_gtw/400-0.0297
        k_gtw_fluid=0.12
        p_fc_max = parameter_json['device']['fc']['power_max']
        p_el_max = parameter_json['device']['el']['power_max']
        k_el = parameter_json['device']['el']['beta_el']
        p_eb_max = parameter_json['device']['eb']['power_max']
        # a_pv = parameter_json['device']['pv']['area_max']
        # hst_max = parameter_json['device']['hst']['sto_max']
        p_hp_max = parameter_json['device']['hp']['power_max']
    except BaseException as E:
        _logging.error('读取config.json中设备容量参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化边界上下限参数
    try:
        t_ht_max = parameter_json['device']['ht']['t_max']
        t_ht_min = parameter_json['device']['ht']['t_min']
        # t_ct_max = parameter_json['device']['ct']['t_max']
        # t_ct_min = parameter_json['device']['ct']['t_min']
        t_de_max = parameter_json['device']['de']['t_max']
        t_de_min = parameter_json['device']['de']['t_min']
        t_gtw_in_min=parameter_json['device']['gtw']['t_in_min']
        # t_ht_wetbulb = parameter_json['device']['ht']['t_wetbulb']
        # t_ct_wetbulb = parameter_json['device']['ct']['t_wetbulb']
        # slack_ht = parameter_json['device']['ht']['end_slack']
        # slack_ct = parameter_json['device']['ct']['end_slack']
        # slack_hsto = parameter_json['device']['hst']['end_slack']
        tem_diff=parameter_json['device']['de']['temperature_difference']#读取供回水温度差
    except BaseException as E:
        _logging.error('读取config.json中边界上下限参数失败,错误原因为{}'.format(E))
        raise Exception

    # 初始化价格
    try:
        lambda_ele_in = parameter_json['price']['ele_TOU_price']
        lambda_ele_in = lambda_ele_in*(int(time_scale/24))
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
        period = len(p_load)
        # g_load = [list(input_data['G_DE'])[i] + list(input_data['H_DE'])[i] for i in range(period)]
        g_load = list(input_data['G_DE'])
        q_load = list(input_data['Q_DE'])
        pv_generation = list(input_data['R_PV'])
        
        t_tem = list(load_json['ambient_temperature']) #读环境温度
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

    # 通过 gurobi 建立模型
    model = gp.Model("bilinear")

    # 添加变量
    opex = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="opex")
    opex_t = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"opex[{t}]") for t in range(period)]  # 每个时段的运行成本
    # 工况变量
    z_pur = [model.addVar(vtype=GRB.BINARY, name=f"z_pur[{t}]") for t in range(period)]  # 是否从电网买电
    z_ghp_ht = [model.addVar(vtype=GRB.BINARY, name=f"z_ghp_ht[{t}]") for t in range(period)]  # 浅层地源热泵给储热罐蓄热
    z_ghp_de = [model.addVar(vtype=GRB.BINARY, name=f"z_ghp_de[{t}]") for t in range(period)]  # 浅层地源热泵给末端供热
    z_eb_ht = [model.addVar(vtype=GRB.BINARY, name=f"z_eb_ht[{t}]") for t in range(period)]  # 电锅炉给储热罐蓄热
    z_eb_de = [model.addVar(vtype=GRB.BINARY, name=f"z_eb_de[{t}]") for t in range(period)]  # 电锅炉给末端供热
    z_fc_ht = [model.addVar(vtype=GRB.BINARY, name=f"z_fc_ht[{t}]") for t in range(period)]  # 燃料电池给储热罐蓄热
    z_fc_de = [model.addVar(vtype=GRB.BINARY, name=f"z_fc_de[{t}]") for t in range(period)]  # 燃料电池给末端供热
    # TODO: 没看明白储热罐的工况，是不能同时给末端供热和蓄热吗？
    z_ht_sto = [model.addVar(vtype=GRB.BINARY, name=f"z_ht_sto[{t}]") for t in range(period)]  # 储热罐蓄热
    # 电网
    p_pur = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur[{t}]") for t in range(period)]  # 从电网购电量
    # 氢源
    h_pur = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur[{t}]") for t in range(period)]  # 购氢量
    # 末端
    t_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_de[{t}]") for t in range(period)]  # 末端供回水温度
    # GHP
    p_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_ghp[{t}]") for t in range(period)]  # 浅层地源热泵功率
    g_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ghp[{t}]") for t in range(period)]  # 浅层地源热泵供热量
    g_ghp_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ghp_ht[{t}]") for t in range(period)]  # 浅层地源热泵给储热罐蓄热量
    g_ghp_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ghp_de[{t}]") for t in range(period)]  # 浅层地源热泵给末端供热量
    t_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ghp[{t}]") for t in range(period)]  # 浅层地源热泵出水温度
    m_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_ghp[{t}]") for t in range(period)]  # 浅层地源热泵循环水量
    p_pump_ghp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_ghp[{t}]") for t in range(period)]  # 浅层地源热泵循环泵功率
    # EB
    p_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_eb[{t}]") for t in range(period)]
    g_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb[{t}]") for t in range(period)]
    g_eb_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb_ht[{t}]") for t in range(period)]
    g_eb_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_eb_de[{t}]") for t in range(period)]
    t_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_eb[{t}]") for t in range(period)]
    m_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_eb[{t}]") for t in range(period)]
    p_pump_eb = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_eb[{t}]") for t in range(period)]
    # AHP
    p_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_ahp[{t}]") for t in range(period)]
    g_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ahp[{t}]") for t in range(period)]
    t_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ahp[{t}]") for t in range(period)]
    m_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_ahp[{t}]") for t in range(period)]
    p_pump_ahp = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_ahp[{t}]") for t in range(period)]
    # FC
    m_h_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_h_fc[{t}]") for t in range(period)]  # 燃料电池耗氢量
    p_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc[{t}]") for t in range(period)]
    g_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc[{t}]") for t in range(period)]
    g_fc_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc_ht[{t}]") for t in range(period)]
    g_fc_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc_de[{t}]") for t in range(period)]
    t_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_fc[{t}]") for t in range(period)]
    m_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_fc[{t}]") for t in range(period)]  # 燃料电池循环水量
    p_pump_fc = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_fc[{t}]") for t in range(period)]
    # HT
    g_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_ht[{t}]") for t in range(period)]  # 储热罐给末端供热量
    t_ht_sto = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht_sto[{t}]") for t in range(period)]  # 储热罐蓄热温度
    t_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht[{t}]") for t in range(period)]  # 储热罐出水温度
    m_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_ht[{t}]") for t in range(period)]  # 储热罐循环水量
    # p_pump_ht = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_ht[{t}]") for t in range(period)]
    # BS
    p_bs_sto = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_bs_sto[{t}]") for t in range(period)]  # 蓄电池储能量
    p_bs_ch = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_bs_ch[{t}]") for t in range(period)]  # 蓄电池充电功率
    p_bs_dis = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_bs_dis[{t}]") for t in range(period)]  # 蓄电池放电功率
    # PIPE
    t_supply = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_supply[{t}]") for t in range(period)]  # 供水温度
    m_de = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_de[{t}]") for t in range(period)]  # 管网循环水量
    p_pump_pipe = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump_pipe[{t}]") for t in range(period)]  # 管网循环泵功率
    # PV
    p_pv = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pv[{t}]") for t in range(period)]  # 光伏发电功率
    # TODO: PVT 要管吗？

    # 添加约束
    # if hydrogen_bottle_max_final - hydrogen_bottle_max_start>=-1:
    #     model.addConstr(gp.quicksum(h_pur) <= hydrogen_bottle_max_final - hydrogen_bottle_max_start)
    # else:
    #     model.addConstr(gp.quicksum(h_pur) == 0)
    #print(storage_end_json['end_slack'][0])
    # if storage_end_json['end_slack'][begin_time+time_scale] == False:
    #     model.addConstr(t_ht[-1] == t_ht_final)
    #     # model.addConstr(t_ct[-1] == t_ct_final)
    #     # model.addConstr(h_sto[-1] == hst_kg_final)
    # else:
    #     model.addConstr(t_ht[-1] >= t_ht_start * (1-slack_ht))
    #     model.addConstr(t_ht[-1] <= t_ht_start * (1+slack_ht))
    #     # model.addConstr(t_ct[-1] >= t_ct_start * (1-slack_ct))
    #     # model.addConstr(t_ct[-1] <= t_ct_start * (1+slack_ct))
    #     # model.addConstr(h_sto[-1] >= hst_kg_start * (1-slack_hsto))
    #     # model.addConstr(h_sto[-1] <= hst_kg_start * (1+slack_hsto))
    # # 储能约束
    # model.addConstr(g_l[0] == t_ht_start)
    # model.addConstr(q_l[0] == t_de_start)
    # model.addConstr(g_gtw_l[0] == 0)
    # model.addConstr(t_ct_l[0] == t_ct_start)
    # model.addConstr(h_sto_l[0] == hst_kg_start)
    # model.addConstr(t_ht[-1] >= t_ht_final)

    model.addConstrs(g[i] == g_l[i+1] for i in range(period-1))
    model.addConstrs(h[i] == h_l[i+1] for i in range(period-1))
    model.addConstrs(q[i] == q_l[i+1] for i in range(period-1))
    model.addConstrs(g_gtw[i] == g_gtw_l[i+1] for i in range(period-1))
    model.addConstr(g[period-1] == g_l[0])
    model.addConstr(h[period-1] == h_l[0])
    model.addConstr(q[period-1] == q_l[0])
    model.addConstr(g_gtw[period-1] == g_gtw_l[0])

    
    # model.addConstr(gp.quicksum(z_hp)<=period*10/24)
    # 能量平衡
    # model.addConstr(p_fc[i] + p_pur[i] + p_pv[i] == p_el[i] + p_eb[i] + p_hp[i]  + p_pump[i] + p_load[i])
    model.addConstrs(p_fc[i] + p_pv[i] == p_eb[i] + p_hp_max*(z_hp_g[i]+z_hp_q[i]) + p_load[i] + p_el[i] for i in range(period))
    model.addConstrs(
        g_eb[i] + g_fc[i] + g_hp[i] + g_OU[i] - g_IN[i] - g_HP_IN[i] -
        g_load[i] == 0 for i in range(period)
    )
    model.addConstrs(q_hp[i] + q_OU[i] - q_IN[i] - q_load[i] == 0 for i in range(period))

        #model.addConstr(c*m_ht*(t_ht[i] - t_ht_l[i] - ht_loss * (t_ht_l[i] - t_ht_wetbulb)) + g_load[i] == g_fc[i] + g_hp[i] + g_eb[i])
        # model.addConstr(g_load[i] == g_fc[i] + g_hp[i] + g_eb[i] + g_ht[i])

        #model.addConstr(c*m_ct*(t_ct[i] - t_ct_l[i] - ct_loss * (t_ct_l[i] - t_ct_wetbulb)) + q_hp[i] == q_load[i])
    # model.addConstr(c*m_ct*(t_ct[i] - t_ct_l[i]) + q_hp[i] == q_load[i])

    model.addConstrs(h_el[i] + h_OU[i] + h_pur[i] - h_IN[i] - h_fc[i] == 0 for i in range(period))
    




        # # 工况约束
        # model.addConstr(z_a[i]*g_ht[i]>=0)
        # model.addConstr(g_ht[i]+z_b[i]*g_eb[i]+z_c[i]*g_fc[i]+z_d[i]*g_hp[i]+z_e[i]*(g_fc[i]+g_hp[i])>=0)
        # model.addConstr(z_a[i]+z_b[i]+z_c[i]+z_d[i]+z_e[i]==1)
        # #燃料电池不能给水箱蓄
        # model.addConstr(z_c[i]==0)
        # model.addConstr(z_e[i]==0)

        #给末端供热的约束
    # model.addConstr(c*m_de*(t_de[i]-t_de_l[i]) == g_ht[i]*z_a[i]+g_eb[i]*(1-z_b[i])+g_fc[i]*(1-z_c[i]-z_e[i])+g_hp[i]*(1-z_d[i]-z_e[i])-g_load[i]-de_loss*(t_de_l[i]-43)*m_de)





    # 每一时段约束

    # 上下限约束
    # model.addConstr(t_ht[i] >= t_ht_min)
    model.addConstrs(g[i] <= P_ht for i in range(period))
    model.addConstrs(q[i] <= P_ht for i in range(period))
    # model.addConstr(t_ct[i] >= t_ct_min)
    # model.addConstr(t_ct[i] <= t_ct_max)
    model.addConstrs(t_gtw_in[i]>=t_gtw_in_min for i in range(period))
    # model.addConstr(t_de[i] >= t_de_min)
    # model.addConstr(t_de[i] <= t_de_max)
    model.addConstrs(p_fc[i] <= p_fc_max for i in range(period))
    model.addConstrs(p_el[i] <= p_el_max for i in range(period))
    model.addConstrs(p_eb[i] <= p_eb_max for i in range(period))
    # model.addConstr(p_hp[i] <= p_hp_max)

    # 能量平衡

    # 设备约束
    ## fc
    # model.addConstr(p_fc[i] <= p_fc_max)
    model.addConstrs(p_fc[i] == k_fc_p * h_fc[i] for i in range(period))
    model.addConstrs(g_fc[i] == k_fc_g * h_fc[i] for i in range(period))


    
    ## hp
    # model.addConstr(p_hp[i] <= p_hp_max)
    # model.addConstr(q_hp[i] == k_hp_q * p_hp[i])
    
    model.addConstrs(g_hp[i] <= cop_hp[i]*p_hp_max*z_hp_g[i] for i in range(period))
    model.addConstrs(cop_hp[i] == 3 + 0.1209*t_gtw_out[i] for i in range(period))
    model.addConstrs(q_hp[i] <= k_hp_q*p_hp_max*z_hp_q[i] for i in range(period))
    # model.addConstrs(g_HP_IN[i]<=p_hp_max*z_hp_i[i] for i in range(period))
    
    # model.addConstrs(g_gtw[i] == (g_hp[i]-p_hp_max)*z_hp_g[i] - (q_hp[i]+p_hp_max)*z_hp_q[i] for i in range(period))
    model.addConstrs(g_gtw[i] == (cop_hp[i]*p_hp_max-p_hp_max)*z_hp_g[i] - (k_hp_q*p_hp_max+p_hp_max)*z_hp_q[i] - g_HP_IN[i] for i in range(period))
    model.addConstrs(z_hp_g[i]+z_hp_q[i]<=1 for i in range(period))

    model.addConstrs(g_gtw[i] == c*m_gtw*(t_gtw_out[i] - t_gtw_in[i]) for i in range(period))
    model.addConstrs(t_gtw_out[i] == k_gtw_fluid*(t_gtw_in[i]-t_b[i])+t_b[i] for i in range(period))
    # model.addConstrs(t_b[i] == 9.5-(1000/(2*np.pi*2.07*200*192))*gp.quicksum((g_gtw[j%period]-g_gtw_l[j%period])*g_func[(i-j)%(7*24)] for j in range(i+1-7*24,i+1)) for i in range(period))
    model.addConstrs(t_b[i] == 9.5-(1000/(2*np.pi*2.07*200*192))*gp.quicksum((g_gtw[j]-g_gtw_l[j])*g_func[(i-j)] for j in range(max(i-30*24,0),i)) for i in range(period))
    # for d in range(period//24):
    #     model.addConstrs(t_b[d*24 + i] == 10-(1000/(2*np.pi*2.07*200*192))*gp.quicksum((g_gtw[d*24+j%24]-g_gtw_l[d*24+j%24])*g_func[(i-j)%(24*7)] for j in range(24*7)) for i in range(24))
        # model.addConstr(t_b[d*24]==t_b[(d*24+24)%288])
    model.addConstrs(t_b[i]>=5 for i in range(period))
    # model.addConstrs(t_gtw_in[i]==10 for i in range(period))
    model.addConstrs(t_b[i]<=15 for i in range(period))
    ## el
    model.addConstrs(p_el[i] <= p_el_max for i in range(period))
    model.addConstrs(h_el[i] == k_el * p_el[i] for i in range(period))
    ## eb
    model.addConstrs(p_eb[i] <= p_eb_max for i in range(period))
    model.addConstrs(g_eb[i] == k_eb * p_eb[i] for i in range(period))
    ## pump
    #model.addConstr(p_pump[i] == k_pump * mass_flow[i])
    ## pv
    # model.addConstr(p_pv[i] <= solar[i] * a_pv * k_pv)
    model.addConstrs(p_pv[i] <= P_PV*pv_generation[i] for i in range(period))

    ## ht
    ### ht温度变化
    # model.addConstr(c*m_ht*(t_ht[i]-t_ht_l[i])==-g_ht[i]-ht_loss*(t_ht_l[i]-t_tem[i])*m_ht)
    # ### ht供热温度约束
    # model.addConstr(t_ht_l[i]-t_de_l[i]+tem_diff/2>=100*(z_ht_de[i]-1))
    # model.addConstr(g_ht[i]<=c*m_de*(t_ht_l[i]-t_de_l[i])*z_ht_de[i])
    # # model.addConstr(t_ht_l[i]-45>=100*(z_ht_de[i]-1))
    # model.addConstr(t_ht_l[i]-45<=100*(z_ht_de[i]))
    # model.addConstr(g_ht[i]<=c*m_de*(t_ht_l[i]-45)*z_ht_de[i])

    model.addConstrs(g[i] - (0.95) * g_l[i] == g_IN[i] - g_OU[i] for i in range(period))
    model.addConstrs(q[i] - (0.95) * q_l[i] == q_IN[i] - q_OU[i] for i in range(period))
    model.addConstrs(h[i] - (0.99) * h_l[i] == h_IN[i] - h_OU[i] for i in range(period))
    ## opex 
    model.addConstrs(opex[i] == hydrogen_price * h_pur[i] for i in range(period))
    # set objective
    
    model.setObjective(gp.quicksum(opex), GRB.MINIMIZE)
    # model.setObjective(gp.quicksum(opex), GRB.MINIMIZE)
    model.params.NonConvex = 2
    model.params.MIPGap = 0.02
    # model.params.TimeLimit=300
    model.Params.LogFile = "testlog.log"

    model.optimize()

    if model.status == GRB.INFEASIBLE or model.status == 4:
        print('Model is infeasible')
        model.computeIIS()
        model.write('Temp\model.ilp')
        print("Irreducible inconsistent subsystem is written to file 'model.ilp'")
        exit(0)

    # 计算一些参数
    # opex_without_opt = [lambda_ele_in[i]*(p_load[i]+q_load[i]/k_hp_q+g_load[i]/k_eb) for i in range(period)]
    dict_control = {# 负荷
        # 'time':begin_time,
        # thermal binary
        # 'b_hp':[1 if p_hp[i].x > 0 else 0 for i in range(period)],
        # 'b_eb':[1 if p_eb[i].x > 0 else 0 for i in range(period)],
        # # -1代表储能，1代表供能
        # 'b_ht':[-1 if t_ht[i].x > t_ht_l[i].x else 1 if t_ht[i].x > t_ht_l[i].x else 0  for i in range(period)],
        # # 'b_ct':[1 if t_ct[i].x > t_ct_l[i].x else -1 if t_ct[i].x > t_ht_l[i].x else 0  for i in range(period)],
        # 'b_fc':[1 if p_fc[i].x > 0 else 0 for i in range(period)],

        # ele
        'opex':[opex[i].x for i in range(period)],
        # 'p_demand_price':p_demand_price*p_demand_max.x/24/30*time_scale,
        # 'operation_mode':[z_a[i].x*1+z_b[i].x*2+z_c[i].x*3+z_d[i].x*4+z_e[i].x*5 for i in range(period)],
        'p_eb':[p_eb[i].x for i in range(period)],
        'p_fc':[p_fc[i].x for i in range(period)],
        'p_el':[p_el[i].x for i in range(period)],
        'p_hp':[p_hp_max*(z_hp_g[i].x+z_hp_q[i].x) for i in range(period)],
        'p_pv':[p_pv[i].x for i in range(period)],
        'z_hp_g':[z_hp_g[i].x for i in range(period)],
        'z_hp_q':[z_hp_q[i].x for i in range(period)],
        # 'p_pur':[p_pur[i].x for i in range(period)],
        'p_load':[p_load[i] for i in range(period)],
        # 'lambda_ele_in':[lambda_ele_in[i]for i in range(period)],
        'g_fc':[g_fc[i].x for i in range(period)],
        'g_eb':[g_eb[i].x for i in range(period)],
        'g_hp':[g_hp[i].x for i in range(period)],
        'g':[g[i].x for i in range(period)],
        'g_load':[g_load[i] for i in range(period)],
        'g_IN':[g_IN[i].x for i in range(period)],
        'g_OU':[g_OU[i].x for i in range(period)],
        'g_HP_IN':[g_HP_IN[i].x for i in range(period)],

        # 'z_ht_de':[z_ht_de[i].x for i in range(period)],
        'h_pur':[h_pur[i].x for i in range(period)],
        'cop_hp':[cop_hp[i].x for i in range(period)],
        'g_gtw':[g_gtw[i].x for i in range(period)],
        'g_gtw_l':[g_gtw_l[i].x for i in range(period)],
        't_gtw_out':[t_gtw_out[i].x for i in range(period)],
        't_gtw_in':[t_gtw_in[i].x for i in range(period)],
        't_b':[t_b[i].x for i in range(period)],
        'q_hp':[q_hp[i].x for i in range(period)],
        'q_load':[q_load[i] for i in range(period)],
        'q':[q[i].x for i in range(period)],
        'q_IN':[q_IN[i].x for i in range(period)],
        'q_OU':[q_OU[i].x for i in range(period)],

        'h_el':[h_el[i].x for i in range(period)],
        'h':[h[i].x for i in range(period)],
        'p_el':[p_el[i].x for i in range(period)],
        'h_IN':[h_IN[i].x for i in range(period)],
        'h_OU':[h_OU[i].x for i in range(period)],
        # 't_ht':[t_ht[i].x for i in range(period)],
        # 't_de':[t_de[i].x for i in range(period)],
        # 'p_el':[p_el[i].x for i in range(period)],
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
    dict_plot = {
        # 'hour':[i+1 for i in range(period)],
        # # operational day cost
        # 'opex_without_opt':[h_pur[i].x*hydrogen_price+max(0,p_load[i]-p_pv[i].x)*lambda_ele_in[i] for i in range(period)],# 未经优化的运行成本

        # #ele
        # 'p_fc':[p_fc[i].x for i in range(period)],#燃料电池

        # 'p_hp':[z_hp[i].x for i in range(period)],#热泵
        # 'p_eb':[p_eb[i].x for i in range(period)],#电锅炉
        # # 'p_el':[p_el[i].x for i in range(period)],
        # #hydrogen
        # # 'h_hst':[h_sto[i].x for i in range(period)],
        # #thermal
        # 't_ht':[t_ht[i].x for i in range(period)],  
    }
    return dict_control,dict_plot




if __name__ == '__main__':
    opt_day()


# period = len(g_de)
# # Create a new model
# m = gp.Model("bilinear")

# # Create variables
# ce_h = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="ce_h")

# m_ht = m.addVar(vtype=GRB.CONTINUOUS, lb=10, name="m_ht") # capacity of hot water tank

# t_ht = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_ht{t}") for t in range(period)] # temperature of hot water tank

# t_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_fc{t}") for t in range(period)] # outlet temperature of fuel cells cooling circuits

# g_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_fc{t}") for t in range(period)] # heat generated by fuel cells

# p_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_fc{t}") for t in range(period)]

# fc_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="fc_max") # rated heat power of fuel cells

# el_max = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="el_max") # rated heat power of fuel cells

# t_de = [m.addVar(vtype=GRB.CONTINUOUS, lb=0,name=f"t_de{t}") for t in range(period)] # outlet temparature of heat supply circuits

# h_fc = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_fc{t}") for t in range(period)] # hydrogen used in fuel cells

# m_fc = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_fc") # fuel cells water

# m_el = m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"m_el") # fuel cells water


# g_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"g_el{t}") for t in range(period)] # heat generated by Electrolyzer

# h_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_el{t}") for t in range(period)] # hydrogen generated by electrolyzer

# p_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_el{t}") for t in range(period)] # power consumption by electrolyzer

# t_el = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_el{t}") for t in range(period)] # outlet temperature of electrolyzer cooling circuits

# h_sto = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_sto{t}") for t in range(period)] # hydrogen storage

# h_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"h_pur{t}") for t in range(period)] # hydrogen purchase

# p_pur = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pur{t}") for t in range(period)] # power purchase

# p_sol = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_sol{t}") for t in range(period)] # power purchase

# area_pv = m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub = 1000, name=f"area_pv")

# p_pump = [m.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"p_pump{t}") for t in range(period)] 

# hst = m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub = 1000, name=f"hst")

# #m.addConstr(m_el+m_fc <= 0.001*m_ht)
# for i in range(int(period/24)-1):
#     m.addConstr(t_ht[i*24+24] == t_ht[24*i])
# m.addConstr(t_ht[-1] == t_ht[0])
# #m.addConstr(h_sto[0] == 0)
# m.addConstr(h_sto[-1] == h_sto[0])
# for i in range(period - 1):
#     m.addConstr(m_ht * (t_ht[i + 1] - t_ht[i]) == 
#         m_fc * (t_fc[i] - t_ht[i]) + m_el * (t_el[i] - t_ht[i]) - m_de[i] * (t_ht[i] - t_de[i]))
#     m.addConstr(h_sto[i+1] - h_sto[i] == h_pur[i] + h_el[i] - h_fc[i])
    
# m.addConstr(m_ht * (t_ht[0] - t_ht[i]) == m_fc * (t_fc[i] - t_ht[i]) + m_el * (t_el[i] - t_ht[i]) - m_de[i] * (t_ht[i] - t_de[i]))
# m.addConstr(h_sto[0] - h_sto[-1] == h_pur[-1] + h_el[-1] - h_fc[-1])
# m.addConstr(t_ht[0] == 55)
# for i in range(period):
#     m.addConstr(t_de[i] >= 40)
#     m.addConstr(p_eb[i] + p_el[i] + p_sol[i] + p_pump[i] + p_load[i]== p_pur[i] + p_fc[i] + k_pv*area_pv*r[i])
#     m.addConstr(g_fc[i] <= 18 * h_fc[i])
#     m.addConstr(p_pump[i] == 3.5/1000 * (m_fc+m_de[i]+m_el))#热需求虽然低，水泵耗电高。
#     m.addConstr(p_fc[i] <= 18 * h_fc[i])#氢燃烧产电
#     m.addConstr(h_el[i] <= k_el * p_el[i])
#     m.addConstr(g_el[i] <= 0.2017*p_el[i])
#     m.addConstr(g_fc[i] == c_kWh * m_fc * (t_fc[i] - t_ht[i]))
#     m.addConstr(g_el[i] == c_kWh * m_el * (t_el[i] - t_ht[i]))
#     m.addConstr(t_fc[i] <= 75)
#     m.addConstr(t_el[i] <= 75)
#     m.addConstr(h_sto[i]<=hst)
#     m.addConstr(h_el[i]<=hst)
#     #m.addConstr(t_ht[i] >= 50)
#     m.addConstr(p_fc[i] <= fc_max)
#     m.addConstr(p_el[i] <= el_max)
#     m.addConstr(g_de[i] == c_kWh * m_de[i] * (t_ht[i] - t_de[i]))
#     #m.addConstr(m_fc <= m_ht)
# # m.addConstr(m_fc[i] == m_ht/3)
# # m.addConstr(m_ht >= 4200*100)
# # m.addConstr(t_ht[i] <= 80)#强化条件


# # m.setObjective( crf_pv * cost_pv*area_pv+ crf_el*cost_el*el_max
# #     +crf_hst * hst*cost_hst +crf_water* cost_water_hot*m_ht + crf_fc *cost_fc * fc_max + lambda_h*gp.quicksum(h_pur)*365+ 
# #     365*gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(24)])-365*gp.quicksum(p_sol)*lambda_ele_out , GRB.MINIMIZE)
# m.setObjective( crf_pv * cost_pv*area_pv+ crf_el*cost_el*el_max
#     +crf_hst * hst*cost_hst +crf_water* cost_water_hot*m_ht + crf_fc *cost_fc * fc_max + lambda_h*gp.quicksum(h_pur)*365/7+ 
#     gp.quicksum([p_pur[i]*lambda_ele_in[i] for i in range(period)])*365/7-gp.quicksum(p_sol)*lambda_ele_out*365/7, GRB.MINIMIZE)
# #-gp.quicksum(p_sol)*lambda_ele_out 
# # First optimize() call will fail - need to set NonConvex to 2
# m.params.NonConvex = 2
# m.params.MIPGap = 0.05
# # m.optimize()
# #m.computeIIS()
# try:
#     m.optimize()
# except gp.GurobiError:
#     print("Optimize failed due to non-convexity")

# # Solve bilinear model
# # m.params.NonConvex = 2
# # m.optimize()

# #m.printAttr('x')
# m.write('sol_winter.mst')
# # Constrain 'x' to be integral and solve again
# # x.vType = GRB.INTEGER
# # m.optimize()

# # m.printAttr('x')

# wb = xlwt.Workbook()
# result = wb.add_sheet('result')
# alpha_ele = 1.01
# alpha_heat = 0.351
# ce_c = np.sum(p_load)*alpha_ele + np.sum(g_de)*alpha_heat
# #c_cer == lambda_carbon*(ce_c - ce_h)
# p_pur_tmp = m.getAttr('x', p_pur)
# p_sol_tmp = m.getAttr('x', p_sol)
# ce_h_1 = np.sum(p_pur_tmp)*alpha_ele - np.sum(p_sol_tmp)*alpha_ele


# item1 = ['m_ht','m_fc','m_el','fc_max','el_max']
# item2 = [g_el,g_fc,p_el,p_fc,p_pur,p_pump,p_sol,t_ht,t_el,h_el,h_fc,t_fc,t_de,h_sto,h_pur]
# a_pv = m.getVarByName('area_pv').getAttr('x')
# item3 = [[k_pv*a_pv*r[i] for i in range(len(r))],p_load,g_de]
# item3_name = ['p_pv','p_load','g_de']
# print(m.getAttr('x', p_el))
# for i in range(len(item1)):
#     result.write(0,i,item1[i])
#     result.write(1,i,m.getVarByName(item1[i]).getAttr('x'))
# for i in range(len(item2)):
#     tmp = m.getAttr('x', item2[i])
#     result.write(0,i+len(item1),item2[i][0].VarName[:-1])
#     for j in range(len(tmp)):
#         result.write(j+1,i+len(item1),tmp[j])

# for i in range(3):
#     tmp = item3[i]
#     result.write(0,i+len(item1)+len(item2),item3_name[i])
#     for j in range(len(tmp)):
#         result.write(j+1,i+len(item1)+len(item2),tmp[j])

# t_ht = m.getAttr('x', t_ht)
# m_ht = m.getVarByName('m_ht').getAttr('x')
# res = []
# for i in range(len(t_ht)-1):
#     res.append(c*m_ht*(t_ht[i+1] - t_ht[i])/3.6/1000000)
# res.append(c*m_ht*(t_ht[0]-t_ht[-1])/3.6/1000000)
# result.write(0,3+len(item1)+len(item2),'g_ht')
# for j in range(len(res)):
#     result.write(j+1,3+len(item1)+len(item2),res[j])
# result.write(0,4+len(item1)+len(item2),'cer')
# result.write(1,4+len(item1)+len(item2),(ce_c - ce_h_1))

# wb.save("sol_season_12day_729.xls")
# #print(m.getJSONSolution())







