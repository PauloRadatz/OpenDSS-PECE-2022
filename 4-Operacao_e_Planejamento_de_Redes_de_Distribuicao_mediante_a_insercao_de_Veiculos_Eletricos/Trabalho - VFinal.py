# -*- coding: utf-8 -*-
"""
Created on Wed Nov  2 21:58:26 2022

@author: danielly.araujo
"""

import os
import pathlib
import py_dss_interface
import random
import functions
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#localização do arquivo
script_path=os.path.dirname(__file__)
dss_file = pathlib.Path(script_path).joinpath("../Feeders","8500-Node", "Master.dss")

#criação do objeto para referenciar ao OpenDSS
dss = py_dss_interface.DSSDLL()


thevenin_pu = 1.045
load_mult = 0.3
pf=1
p_step = 5 
kva_to_kw = 1
valor_seed = 1685

pv_variacao_list = list()
fv_kw = list()
fv_kvar = list()
barras_fv = list()
quant_barras_mt = list()

total_p_feederhead = list()
total_q_feederhead = list()
losses_kw = list()
losses_kvar = list()
fv_total = list()

for variacao in np.arange(0.0, 1.1, 0.1):
    
    dss.text("clear")
    dss.text(f"Compile [{dss_file}]")

    dss.text("edit Reactor.MDV_SUB_1_HSB x=0.0000001 r=0.0000001")
    dss.text(r"edit Transformer.MDV_SUB_1 %loadloss=0.000001 xhl=0.0000001")
    dss.text(f"edit Vsource.SOURCE pu={thevenin_pu}")   
    dss.text(f"set loadmult = {load_mult}")
        
    dss.text (f'{"set controlmode=off"}')
    dss.text(f'{"batchedit capacitor..* enabled=no"}')

    dss.solution_solve()
    
    total_p_1 = -1*dss.circuit_total_power()[0]
    total_q_1 = -1*dss.circuit_total_power()[1]
    losses_kw_1 = dss.circuit_losses()[0] / 10**3
    losses_kvar_1 = dss.circuit_losses()[1] /10**3
    voltages_1 = dss.circuit_all_bus_vmag_pu()
    voltage_max_1 = max(voltages_1)
    voltage_min_1 = min(voltages_1)
    current_1 = dss.cktelement_currents_mag_ang()


    barras_hc_geral = list()
    barras_kv = dict()
    barras = dss.circuit_all_bus_names()


    for barra in barras:
        dss.circuit_set_active_bus(barra)
        barra_kv = dss.bus_kv_base()
        num_fases = len(dss.bus_nodes())
        
        if barra_kv > 1.0 and num_fases == 3 and barra!= 'sourcebus':
            barras_hc_geral.append(barra)
            barras_kv[barra] = barra_kv


    random.seed(valor_seed)        
    barras_hc = random.sample(barras_hc_geral, int(variacao*len(barras_hc_geral)))

    barras_fv_atual = list()
    for barra in barras_hc:
        functions.define_generator(dss=dss, bus=barra, kv=barras_kv[barra], kW = p_step)
        functions.add_bus_marker(dss=dss, bus=barra, color="red", size_marker=4)
        barras_fv_atual.append(barra)        
    quant_barras_mt = len(barras_fv_atual)

     
    dss.solution_solve()
    dss.text("interpolate")
    #dss.text("plot circuit Power max=2000 n n C1=$00FF0000")

    sobretensao = False
    sobrecarga = False
    v_limite = 1.05

    i=0
    while not sobretensao and not sobrecarga and i<1000:
        i += 1
        functions.increment_generator(dss, p_step, pf, i) 
        dss.solution_solve()
        tensoes = dss.circuit_all_bus_vmag_pu()
        v_max = max(tensoes)
        
        if v_max > v_limite:
            sobretensao = True

        dss.lines_first()
        for _ in range(dss.lines_count()):
            dss.circuit_set_active_element(f"line.{dss.lines_read_name()}")
            i_linha = dss.cktelement_currents_mag_ang()
            i_nom_linha = dss.lines_read_norm_amps()
 
            if (max(i_linha[0:12:2]) / i_nom_linha) > 1:
                sobrecarga = True
                break       
  
            dss.lines_next()

    functions.increment_generator(dss, p_step, pf, i-1)
    dss.solution_solve()
    penetration_level = (i - 1) * len(barras_hc) * p_step

    #Listas   
    pv_variacao_list.append(variacao)
    total_p_feederhead.append(-1 * dss.circuit_total_power()[0])
    total_q_feederhead.append(-1 * dss.circuit_total_power()[1])
    losses_kw.append(dss.circuit_losses()[0] / 10**3)
    losses_kvar.append(dss.circuit_losses()[1] /10**3)
    fv_kw.append(functions.get_total_power_generator(dss)[0]) 
    barras_fv.append(barras_fv_atual)
    barras.append(quant_barras_mt)
    
   
dicio = dict()
dicio["percentual de barras"] = pv_variacao_list
dicio["quantidade de barras utilizadas"] = quant_barras_mt
dicio["barras com fotovoltaico inserido"] = barras_fv
dicio["potencia fv (kW)"] = fv_kw
dicio["potencia subestacao (kW)"] = total_p_feederhead
dicio["Perdas (kW)"] = losses_kw
dicio["Perdas (kvar)"] = losses_kvar

df = pd.DataFrame.from_dict(dicio)

plt.figure(figsize=(10, 5))
grf = plt.bar(pv_variacao_list, fv_kw, width=0.025)
plt.xticks(pv_variacao_list)
plt.xlabel("Barras com V2G")
plt.ylabel("Potência V2G (kW)")
plt.bar_label(grf, fmt="%.00f", size=10, label_type="edge")
plt.title("Capacidade de Acomodação por Cenário")

plt.figure(figsize=(10, 5))
plt.plot(pv_variacao_list, fv_kw)
plt.plot(pv_variacao_list, total_p_feederhead)
plt.legend(['Potência V2G','Potência Alimentador'], fontsize=14)
plt.xticks(pv_variacao_list)
plt.xlabel("Barras com V2G")
plt.ylabel("Potência V2G  (kW)")
plt.title("Potência V2G e no Alimentador")


fig, ax = plt.subplots(figsize = (10, 5)) 
ax2 = ax.twinx() 
ax.plot(pv_variacao_list, fv_kw, marker = "*", color = 'g') 
ax2.plot(pv_variacao_list, total_p_feederhead, marker = "*", color = 'b') 
ax.set_xlabel("Barras com V2G") 
ax.set_ylabel("Potência V2G (kW)", color = 'g') 
ax2.set_ylabel('Potência de Saída do Alimentador (kW)', color = 'b') 
plt.xticks(pv_variacao_list)
plt.title("Potência V2G e no Alimentador")

fig, ax = plt.subplots(figsize = (10, 5)) 
ax2 = ax.twinx() 
a = ax.bar(pv_variacao_list, fv_kw, width=0.025, color = 'b') 
b = ax2.plot(pv_variacao_list, losses_kw, marker = "*", color = 'red') 
ax.set_xlabel("Barras com V2G") 
ax.set_ylabel("Potência V2G (kW)", color = 'b') 
ax2.set_ylabel('Perdas (kW)', color = 'red') 
plt.xticks(pv_variacao_list)
plt.title("Potência V2G e Perdas kW")
