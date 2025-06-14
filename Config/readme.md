<!--
 * @Author: working-guo 867718012@qq.com
 * @Date: 2023-07-28 09:59:12
 * @LastEditors: guo_MateBookPro 867718012@qq.com
 * @LastEditTime: 2023-07-30 23:54:53
 * @FilePath: /optimization/Config/readme.md
 * @Description: 人一生会遇到约2920万人,两个人相爱的概率是0.000049,所以你不爱我,我不怪你.
 * Copyright (c) 2023 by ${git_name} email: ${git_email}, All Rights Reserved.
-->
# **设备参数配置**
- 主要内容：用于配置设备模型对应的参数。



## **0. 模型目录**
本代码负责优化决策部分的设备运行决策。日前决策在每日0时运行，根据下一日的光照强度和负荷预测水平，决策得到下一日设备运行策略；日内决策在日内每小时运行，根据未来四小时负荷和光照，决策得到4小时的设备运行策略。


**1. 氢能系统模型**
+ [燃料电池](###0)
+ [电解槽](###1)
+ [储氢罐](###2)

**2. 暖通系统模型**
+ [太阳能集热器](###3)
+ [电锅炉](###4)
+ [冷水机组](###5)
+ [地源热泵](###6)
+ [空气源热泵](###7)
+ [储热罐](###8)
+ [储冷罐](###9)
+ [相变储热箱](###10)

**3. 电气系统模型**
+ [光伏](###11)
+ [风电](###12)
+ [电化学储能](###13)

## **1. 氢能系统模型**

### 燃料电池

#### 数学模型

$$
p^{fc}_t=\eta_p^{fc}*h^{fc}_t,\forall t,  \\
g^{fc}_t=\theta^{ex}*\eta_g^{fc}*h^{fc}_t,\forall t, \\
p^{fc}_t \leq P^{fc} ,\forall t

$$
其中$p^{fc}_t，g^{fc}_t，h^{fc}_t$分别是燃料电池$t$时刻发电量，产热量，耗氢量。

#### 配置文件及说明
```        
"fc":
    {
        "power_max":600,

        "eta_fc_p":15,
        "eta_fc_g":16.6,
        "theta_ex":0.95,
        "comment":"fuel cell"
    }
```
分别对应上述公式中的$P^{fc},\eta_p^{fc},\eta_g^{fc},\theta^{ex}$，comment为配置备注。


### 电解槽
#### 数学模型

$$
h^{el}_t=\beta^{el}*p^{fc}_t,\forall t,  \\
p^{el}_t \leq P^{el} ,\forall t

$$
其中$p^{el}_t，h^{el}_t$分别是电解槽$t$时刻用电量，产氢量。

#### 配置文件及说明
```        
"el":
    {
        "power_max":55,
        "beta_el":0.0182,
    },
```
分别对应上述公式中的$P^{fc},\beta^{el}$。

### 储氢罐
#### 数学模型

$$
h^{sto}_{t+1} - h^{sto}_{t}=h^{el}_t+h^{pur}_t-h^{fc}_t,\forall t,  \\
p^{el}_t \leq P^{el} ,\forall t

$$
其中$h^{sto}_{t},h^{pue}_{t}$分别是储氢罐$t$时刻用电量，产氢量。

#### 配置文件及说明
```        
"hst":
    {
        "sto_max":121.8,
        "end_slack":0.2,
        "comment":"hydrogen buffer storage tank"
    },
```
分别对应上述公式中的$P^{fc},\beta^{el}$。


## 2. 暖通系统模型

### 太阳能集热器
#### 数学模型

$$
g^{sc}_{t}=G^{sc}*g^{sc,fo}_t,\forall t,
$$
其中$g^{sc}_t，g^{sc,fo}_t$分别是集热器$t$时刻实际产热量和单位预测产热量。

#### 配置文件及说明
```        
"sc":
    {
        "heat_max":100000,
        "comment":"solar collector"
    }, 
```
对应上述公式中的$G^{sc}$。

### 电锅炉
#### 数学模型

$$
g^{eb}_{t}=\beta^{eb}*p^{eb}_t,\forall t,  \\
p^{eb}_t \leq P^{eb} ,\forall t
$$
其中$p^{eb}_t，g^{el}_t$分别是电锅炉$t$时刻用电量，产热量。

#### 配置文件及说明
```        
"eb":
    {
        "power_max":1200,
        "beta_eb":0.9,
        "comment":"electric boiler"
    }, 
```
分别对应上述公式中的$P^{eb},\beta^{eb}$。

### 冷水机组

#### 数学模型

$$
q^{ec}_{t}=\beta^{e}*p^{ec}_t,\forall t,  \\
p^{ec}_t \leq P^{ec} ,\forall t
$$
其中$p^{ec}_t，q^{ec}_t$分别是冷水机组$t$时刻用电量，制冷量。

#### 配置文件及说明
```        
"ec":
    {
        "power_max":1200,
        "beta_ec":0.9,
        "comment":"electric chiller"
    },
```
分别对应上述公式中的$P^{ec},\beta^{ec}$。

### 地源热泵
#### 数学模型

$$
g^{ghp}_{t}=\beta^{ghpg}*p^{ghp,g}_{t},\forall t,  \\
q^{ghp}_{t}=\beta^{ghpq}*p^{ghp,q}_{t},\forall t,  \\
p^{ghp}_{t}=p^{ghp,g}_{t}+p^{ghp,q}_{t},\forall t,  \\
p^{ghp}_t \leq P^{ghp} ,\forall t
$$
其中$g^{ghp}_{t}，q^{ghp}_{t}，p^{ghp}_{t}$分别是地源热泵$t$时刻产热量，制冷量，用电量。$p^{ghp,g}_{t},p^{ghp,q}_{t}$分别是地源热泵用于制热和制冷的耗电量。

#### 配置文件及说明
```        
"ghp":
    {
        "power_max":500,

        "beta_ghpg":3.54,
        "beta_ghpq":4,
        "comment":"ground source heat pump"
    },
```
分别对应上述公式中的$P^{ghp},\beta^{ghpg},\beta^{ghq}$。

### 空气源热泵
#### 数学模型
$$
g^{hp}_{t}=\beta^{hpg}*p^{hp,g}_{t},\forall t,  \\
q^{hp}_{t}=\beta^{hpq}*p^{hp,q}_{t},\forall t,  \\
p^{hp}_{t}=p^{hp,g}_{t}+p^{hp,q}_{t},\forall t,  \\
p^{hp}_t \leq P^{hp} ,\forall t
$$
其中$g^{hp}_{t}，q^{hp}_{t}，p^{hp}_{t}$分别是空气源热泵$t$时刻产热量，制冷量，用电量。$p^{hp,g}_{t},p^{hp,q}_{t}$分别是空气源热泵用于制热和制冷的耗电量。

#### 配置文件及说明
```        
"ghp":
    {
        "power_max":500,

        "beta_hpg":3.54,
        "beta_hpq":4,
        "comment":"ground source heat pump"
    },
```
分别对应上述公式中的$P^{ghp},\beta^{ghpg},\beta^{ghq}$。
### 地热井
#### 数学模型
$$
\sum g^{ghp}_{t} = \sum (p^{ghp}_{t} + p^{ghp,q}_{t}+p^{gr}_{t}),
$$
其中$p^{gr}_{t}$是$t$时段向地热井的灌热量。

#### 配置文件及说明
```        
"gtw":
    {
        "number_max":200,
        "comment":"ground thermal well"
    },
```
`number_max`为地热井数目.
### 储热罐
#### 数学模型

$$
g^{ht}_t = c*m^{ht}*(t^{ht}_{t+1}-t^{ht}_{t}),\forall t,  \\
t^{ht,min}  \leq t^{ht}_t \leq t^{ht,max} ,\forall t

$$
其中$t^{ht}_t，g^{ht}_t$分别是储热罐$t$时刻水温，换热量。

#### 配置文件及说明
```        
"ht":
    {
        "water_max":100000,


        "t_max":82,
        "t_min":4,
        "miu_loss":0.02,
        "end_slack":0.2,
        "comment":"water tank"
    },
```
分别对应上述公式中的$m^{ht},t^{ht,max} ,t^{ht,min}$。`miu_loss`含义是换热损失系数，

### 储冷罐
#### 数学模型

$$
q^{ht}_t = c*m^{ct}*(t^{ct}_{t+1}-t^{ct}_{t}),\forall t,  \\
t^{ct,min}  \leq t^{ct}_t \leq t^{ct,max} ,\forall t

$$
其中$t^{ct}_t，q^{ct}_t$分别是储冷罐$t$时刻水温，换热量。

#### 配置文件及说明
```        
"ct":
    {
        "water_max":100000,

        "t_max":15,
        "t_min":4,
        "t_wetbulb":10,
        "miu_loss":0.05,
        "end_slack":0.2,
        "comment":"cooling water tank"
    },
```
分别对应上述公式中的$m^{ct},t^{ct,max} ,t^{ct,min}$。`miu_loss`含义是换热损失系数，

### 相变储热箱
#### 数学模型

$$
g^{xb}_{t} = s^{xb}_{t+1}-s^{xb}_{t},\forall t,  \\
g^{xb}_t  \leq G^{xb}  ,\forall t,\\
s^{xb}_t \leq S^{xb},\forall t
$$
其中$g^{xb}_t，s^{xb}_t$分别是相变储热$t$时刻换热量和储热量。

#### 配置文件及说明
```
"xb":
    {
        "s_max":1000,
        "g_max":100
    },
```
分别对应上述公式中的$S^{xb},G^{xb}$。
## 3. 电气系统模型

### 光伏

#### 数学模型

$$
p^{pv}_{t} = P^{pv}*p^{pv,fo}_{t},\forall t,  \\

$$
其中$p^{pv}_t，p^{pv,fo}_t$分别是光伏$t$时刻光伏发电量和单位光伏发电预测量。
#### 配置文件及说明
```
"pv":
    {
        "power_max":10000,
    }
```
对应上述公式中的$P^{pv}$。
### 风电
#### 数学模型

$$
p^{wd}_{t} = P^{wd}*p^{wd,fo}_{t},\forall t,  \\

$$
其中$p^{wd}_t，p^{wd,fo}_t$分别是风电$t$时刻风电发电量和单位风电发电预测量。
#### 配置文件及说明
```
"wd":
    {
        "power_max":10000,
    }
```
对应上述公式中的$P^{wd}$。
### 电化学储能
#### 数学模型

$$
p^{bs}_{t} = s^{bs}_{t+1}-s^{bs}_{t},\forall t,  \\
p^{bs}_t  \leq P^{bs}  ,\forall t,\\
s^{bs}_t \leq S^{bs},\forall t
$$
其中$p^{bs}_t，s^{bs}_t$分别是蓄电池$t$时刻供电\用电量和储电量。

#### 配置文件及说明
```
"bs":
    {
        "sto_max":10000,
        "power_max":1000,
    },
```
分别对应上述公式中的$S^{bs},P^{bs}$。