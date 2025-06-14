'''
Author: gwyxjtu
Date: 2022-06-06 20:10:39
LastEditors: guo-4060ti 867718012@qq.com
LastEditTime: 2025-06-14 13:14:17
FilePath: \control-optimization\optimization_24h.py
Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.

Copyright (c) 2022 by gwyxjtu 867718012@qq.com, All Rights Reserved. 
'''
'''
                       ::
                      :;J7, :,                        ::;7:
                      ,ivYi, ,                       ;LLLFS:
                      :iv7Yi                       :7ri;j5PL
                     ,:ivYLvr                    ,ivrrirrY2X,
                     :;r@Wwz.7r:                :ivu@kexianli.
                    :iL7::,:::iiirii:ii;::::,,irvF7rvvLujL7ur
                   ri::,:,::i:iiiiiii:i:irrv177JX7rYXqZEkvv17
                ;i:, , ::::iirrririi:i:::iiir2XXvii;L8OGJr71i
              :,, ,,:   ,::ir@mingyi.irii:i:::j1jri7ZBOS7ivv,
                 ,::,    ::rv77iiiriii:iii:i::,rvLq@huhao.Li
             ,,      ,, ,:ir7ir::,:::i;ir:::i:i::rSGGYri712:
           :::  ,v7r:: ::rrv77:, ,, ,:i7rrii:::::, ir7ri7Lri
          ,     2OBBOi,iiir;r::        ,irriiii::,, ,iv7Luur:
        ,,     i78MBBi,:,:::,:,  :7FSL: ,iriii:::i::,,:rLqXv::
        :      iuMMP: :,:::,:ii;2GY7OBB0viiii:i:iii:i:::iJqL;::
       ,     ::::i   ,,,,, ::LuBBu BBBBBErii:i:i:i:i:i:i:r77ii
      ,       :       , ,,:::rruBZ1MBBqi, :,,,:::,::::::iiriri:
     ,               ,,,,::::i:  @arqiao.       ,:,, ,:::ii;i7:
    :,       rjujLYLi   ,,:::::,:::::::::,,   ,:i,:,,,,,::i:iii
    ::      BBBBBBBBB0,    ,,::: , ,:::::: ,      ,,,, ,,:::::::
    i,  ,  ,8BMMBBBBBBi     ,,:,,     ,,, , ,   , , , :,::ii::i::
    :      iZMOMOMBBM2::::::::::,,,,     ,,,,,,:,,,::::i:irr:i:::,
    i   ,,:;u0MBMOG1L:::i::::::  ,,,::,   ,,, ::::::i:i:iirii:i:i:
    :    ,iuUuuXUkFu7i:iii:i:::, :,:,: ::::::::i:i:::::iirr7iiri::
    :     :rk@Yizero.i:::::, ,:ii:::::::i:::::i::,::::iirrriiiri::,
     :      5BMBBBBBBSr:,::rv2kuii:::iii::,:i:,, , ,,:,:i@petermu.,
          , :r50EZ8MBBBBGOBBBZP7::::i::,:::::,: :,:,::i;rrririiii::
              :jujYY7LS0ujJL7r::,::i::,::::::::::::::iirirrrrrrr:ii:
           ,:  :@kevensun.:,:,,,::::i:i:::::,,::::::iir;ii;7v77;ii;i,
           ,,,     ,,:,::::::i:iiiii:i::::,, ::::iiiir@xingjief.r;7:i,
        , , ,,,:,,::::::::iiiiiiiiii:,:,:::::::::iiir;ri7vL77rrirri::
         :,, , ::::::::i:::i:::i:i::,,,,,:,::i:i:::iir;@Secbone.ii:::
'''

import json
import pprint
import pandas as pd
from cpeslog.log_code import _logging
from Model.optimization_day import OptimizationDay,to_csv


if __name__ == '__main__':


    # g_load={'g_load_18':([3800]*11+[2200]*7+[3800]*6)*60,
    # #         'g_load_26':([2500]*11+[1600]*7+[2500]*6)*60,
    #         # 'g_load_32':([3200]*11+[2000]*7+[3200]*6)*60
    
    #         }
    # pd.DataFrame(g_load).to_csv('hh38.csv')
    _logging.info('start')
    time_length=24*5
    try:
        with open("Config/config.json", "rb") as f:
            input_json = json.load(f)
    except BaseException as E:
        _logging.error('读取config失败,错误原因为{}'.format(E))
        raise Exception
    # 读取输入excel
    try:
        load = pd.read_excel('input_720/input_720h.xls')
    except BaseException as E:
        _logging.error('读取input_720h的excel失败,错误原因为{}'.format(E))
        raise Exception
    try:
        sto = pd.read_excel('input_720/input_now.xls')
    except BaseException as E:
        _logging.error('读取input_now的excel失败,错误原因为{}'.format(E))
        raise Exception
    try:
        sto_end = pd.read_excel('input_720/input_end.xls')

    except BaseException as E:
        _logging.error('读取input_end的excel失败,错误原因为{}'.format(E))
        raise Exception
    sto_end['time']=time_length
    sto_end.index = [time_length]
    # 优化主函数
    # try:
    dict_control,dict_plot = OptimizationDay(parameter_json=input_json, load_json=load, begin_time = 0, time_scale=time_length, storage_begin_json=sto, storage_end_json=sto_end)
    # except BaseException as E:
    #     _logging.error('优化主函数执行失败，错误原因为{}'.format(E))
    #     raise Exception
    #print(dict_control)
    #print(dict_plot)
    
    # 写入输出Excel
    to_csv(dict_control,"dict_opt_plot")
        # to_csv(dict_plot,"dict_opt_plot_24h")
