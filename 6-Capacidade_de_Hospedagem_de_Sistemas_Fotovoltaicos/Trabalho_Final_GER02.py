#Curso: Análise de Fluxo de Potência através do OPENDSS
#Professor: Paulo Radatz
#Aluno:Alcides Henrique Leite Santos e Vinicius Minini Barbosa

import pandas as pd
import py_dss_interface
import matplotlib.pyplot as plt
import numpy as np




circuit_pu = 1.04
load_mult= 0.3
Barra_GER02 = ('l3104830')
Medidor_de_Energia = ( 'Line.ln5815900-1 1')
Penetração_W = 1500
Taxa_Crescimento_Percentual = 0.3
Planejamento = 5


dss_file = r"C:\Program Files\OpenDSS\IEEETestCases\8500-Node\Master.dss"
dss = py_dss_interface.DSSDLL()



def process(geração_kw):
    dss.text(f"Compile [{dss_file}]")

    dss.text(f"New Energymeter.Medidor {Medidor_de_Energia}")

    # TheveniEquivalente

    dss.text(f"edit vsource.source pu={circuit_pu}")
    dss.text("edit Reactor.MDV_SUB_1_HSB X=0.0000001")
    dss.text("edit Transformer.MDV_SUB_1 %loadloss=0.0000001 xhl=0.00000001")

    # Controlelements
    dss.text("set controlmode=off")
    dss.text("batchedit capacitor..* enabled=no")

    # Loadmodels
    dss.text(f"batchedit load..* mode=1")
    dss.text("batchedit load..* vmaxpu=1.25")
    dss.text("batchedit load..* vminpu=0.75")

    # Load Condition
    dss.text(f"set loadmult={load_mult}")

    dss.text("Set Maxiteration=100")
    dss.text("Set maxcontrolit=100")

    dss.text(f"AddBusMarker bus={Barra_GER02} color=yellow size=8 code=15")
    # tornar o a potencia do gerador como uma variável
    dss.text(f"New generator.GER02 phases=3 bus1={Barra_GER02} kv=12.47 pf=1 kw={geração_kw}")
    #dss.text(f"New generator.GER02 phases=3 bus1={Barra_GER02} kv=12.47 pf=1 kw={geração_kw}")
    #dss.text(f"New generator.GER02 phases=3 bus1={Barra_GER02} kv=12.47 pf=1 kw={geração_kw}")
    dss.solution_solve()
    dss.text(f"plot circuit")


    # Variáveis do CKT
    #Achar e classificar cada nó do CKT;
    nodes = (dss.circuit_all_node_names())
    # Encontrar todas as tensões em PU do CKT;
    voltages = (dss.circuit_all_bus_vmag_pu())
    #Encontrar a potência total do CKT;
    total_pote_kw= -1 * dss.circuit_total_power()[0]
    #Encontrar a potência (KVAR) do CKT;
    total_pote_kvar = -1 * dss.circuit_total_power()[1]
    #Encontrar a perda total em W do CKT;
    perdas_kw = dss.circuit_losses()[0] / 10 ** 3
    #Encontrar a perda total em KVAR do CKT;
    perdas_kvar = dss.circuit_losses()[1] / 10 ** 3
    #Encontrar todas as tensões em PU do CKT;
    voltage_max = max(np.array(dss.circuit_all_bus_vmag_pu()))
    #Endereçar a tensão máxima do CKT;
    voltage_max_barra = voltages.index(voltage_max)
    #Encontrar o nome da barra que contém a maior tensão através do endereçamento anterior
    local_barra_max = nodes[voltage_max_barra].split(".")[0]
    # Encontrar a tensão mínima em PU do CKT;
    voltage_min = min(np.array(dss.circuit_all_bus_vmag_pu()))
    #Endereçar a tensão mínima do CKT;
    voltage_min_barra = voltages.index(voltage_min)
    #Encontrar o nome da barra que contém a menor tensão através do endereçamento anterior
    local_barra_min = nodes[voltage_min_barra].split(".")[0]

    #Crescimento de Barras que contém sub e sobretensão!
    voltages_array = np.array(voltages)
    nodes_array = np.array(nodes)
    Sub_Tensão = list(nodes_array[voltages_array < 0.93])
    Sobre_Tensão = list(nodes_array[voltages_array> 1.05])
    Quan_Barra_Sub_Tensão = len(Sub_Tensão)
    Quan_Barra_Sobre_Tensão = len(Sobre_Tensão)


    #Marcar barra que possui maior tensão em P.U
    #dss.text(f"AddBusMarker bus={local_barra_max} color=red size=8 code=15")
    #dss.text(f"AddBusMarker bus={local_barra_min} color=yellow size=8 code=15")
    #dss.text("plot circuit ph = all")

    #Ativando a Barra,achando qual linha está ligada nessa barra e ativando também a linha.
    dss.circuit_set_active_bus(Barra_GER02)
    Linha_GER02 = " ".join(dss.bus_line_list()[0:1]).lower().capitalize()
    dss.circuit_set_active_element (Linha_GER02)

    #Potência total em W e KVAR a montante no ponto onde é ligado o GERADOR01
    Pot_W_Montante_GER02 = sum(np.array(dss.cktelement_powers()[0:6:2]))
    #Potência em KVAR total a montante no ponto onde é ligado o GERADOR01
    Pot_KVAR_Montante_GER02 = sum(np.array(dss.cktelement_powers()[1:6:2]))

    #Máxima tensão em P.U da barra que se conecta o GER02
    Tensão_Barra_GER02 = max(np.array(dss.bus_pu_vmag_angle()[0:6:2]))

    #Achar as perdas de cada LINHA ; verificar pelas barras talvez
    Perdas_W_Linha_GER02_STR = str(dss.cktelement_losses()[0:1]).strip('[]')
    Perdas_W_Linha_GER02_Eval = eval(Perdas_W_Linha_GER02_STR)
    Perdas_W_Linha_GER02 = format(Perdas_W_Linha_GER02_Eval, '.0f')

    Perdas_KVAR_Linha_GER02_STR = str(dss.cktelement_losses()[1:2]).strip('[]')
    Perdas_KVAR_Linha_GER02_Eval = eval(Perdas_KVAR_Linha_GER02_STR)
    Perdas_KVAR_Linha_GER02 = format(Perdas_KVAR_Linha_GER02_Eval, '.0f')

    # Alarme de corrente acima da emergencial!
    # dss.cktelement_currents() - a corrente vem em modo retangular- Atenção
    Corrente_Linha_GER02 = max(np.array(dss.cktelement_currents_mag_ang()[0:6:2]))
    Alarme_Corrente_Linha_GER02 = dss.cktelement_read_emerg_amps()

    Linha_Jusante_GER02 = " ".join(dss.bus_line_list()[1]).lower().capitalize()
    dss.circuit_set_active_element(Linha_Jusante_GER02)
    Pot_W_Jusante_GER02 = dss.cktelement_powers()[1] * 10





    #bus_1_voltages_mag = (dss.cktelement_voltages_mag_ang()[0:6:2])
    #bus_1_voltages_ang = (dss.cktelement_voltages_mag_ang()[1:6:2])
    #bus_2_voltage_mag = np.array(dss.cktelement_voltages_mag_ang()[6:12:2])
    #bus_2_voltages_ang = np.array(dss.cktelement_voltages_mag_ang()[7:12:2])







    return total_pote_kw,total_pote_kvar,perdas_kw,\
           perdas_kvar,voltage_max,voltage_min,local_barra_max,\
           local_barra_min,Tensão_Barra_GER02,Pot_W_Montante_GER02,\
           Pot_KVAR_Montante_GER02,Corrente_Linha_GER02,Alarme_Corrente_Linha_GER02,\
           Quan_Barra_Sub_Tensão,Quan_Barra_Sobre_Tensão,Perdas_W_Linha_GER02,Perdas_KVAR_Linha_GER02,Pot_W_Jusante_GER02

def gera_crescimento_percentual(Penetração_W, Taxa_Crescimento_Percentual , max_items=None):

        x = Penetração_W
        y = 0
        while max_items is None or y < max_items:
            yield int(x)
            x += x * Taxa_Crescimento_Percentual
            y += 1

for item in gera_crescimento_percentual(Penetração_W, Taxa_Crescimento_Percentual, Planejamento):
        resultado_2 =item

geração_Kw_List = list(gera_crescimento_percentual(Penetração_W,Taxa_Crescimento_Percentual, Planejamento))
geração_Kw_List.insert(0,0)


total_pote_w = list()
total_pote_kvar = list()
perdas_kw = list()
perdas_kvar = list()
voltage_max = list()
voltage_min = list()
local_barra_max = list()
local_barra_min = list()
Tensão_Barra_GER02 = list()
Pot_W_Montante_GER02 = list()
Po_KVAR_Montante_GER02 = list()
Corrente_Linha_GER02 = list()
Alarme_Corrente_Linha_GER02 = list()
Quan_Barra_Sub_Tensão = list()
Quan_Barra_Sobre_Tensão = list()
Perdas_W_Linha_GER02 = list()
Perdas_KVAR_Linha_GER02 = list()
Pot_W_Jusante_GER02 = list()




for geração_kw in geração_Kw_List:
    resultado_2 = process(geração_kw)
    total_pote_w.append(resultado_2[0])
    total_pote_kvar.append(resultado_2[1])
    perdas_kw.append(resultado_2[2])
    perdas_kvar.append(resultado_2[3])
    voltage_max.append(resultado_2[4])
    voltage_min.append(resultado_2[5])
    local_barra_max.append(resultado_2[6])
    local_barra_min.append(resultado_2[7])
    Tensão_Barra_GER02.append(resultado_2[8])
    Pot_W_Montante_GER02.append(resultado_2[9])
    Po_KVAR_Montante_GER02.append(resultado_2[10])
    Corrente_Linha_GER02.append(resultado_2[11])
    Alarme_Corrente_Linha_GER02.append(resultado_2[12])
    Quan_Barra_Sub_Tensão.append(resultado_2[13])
    Quan_Barra_Sobre_Tensão.append(resultado_2[14])
    Perdas_W_Linha_GER02.append(resultado_2[15])
    Perdas_KVAR_Linha_GER02.append(resultado_2[16])
    Pot_W_Jusante_GER02.append(resultado_2[17])

#Dicionários dos dados Gerais
Dados_Gerais = dict()
Dados_Gerais["Potência da G.D KW"] = geração_Kw_List
Dados_Gerais["Potência em KW"] = total_pote_w
Dados_Gerais["Potência em KVAR"] = total_pote_kvar
Dados_Gerais["Perdas em KW"] = perdas_kw
Dados_Gerais["Perdas em KVAR"] = perdas_kvar
Dados_Gerais["Tensão Máxima"] = voltage_max
Dados_Gerais["Tensão Mínima"] = voltage_min
#Dicionário dos dados de Tensão Máxima em PU do circuito em geral
Dados_Tensão_Max= dict()
Dados_Tensão_Max["Potência da G.D KW"] = geração_Kw_List
Dados_Tensão_Max["Tensão Máxima"]= voltage_max
Dados_Tensão_Max["Localização"]= local_barra_max
#Dicionário dos dados de Tensão Miníma em PU do circuito em geral
Dados_Tensão_Min= dict()
Dados_Tensão_Min["Potência da G.D KW"] = geração_Kw_List
Dados_Tensão_Min["Tensão Mínima"]= voltage_min
Dados_Tensão_Min["Localização"]= local_barra_min
#Dicionário da quantidade de barras do ckt em geral que possuem sub e sobre tensão
Quantidade_Barras_Su_Sobre_Tensão = dict()
Quantidade_Barras_Su_Sobre_Tensão["Potência da G.D KW"] = geração_Kw_List
Quantidade_Barras_Su_Sobre_Tensão["Quantidade de Barras com SubTensão"] = Quan_Barra_Sub_Tensão
Quantidade_Barras_Su_Sobre_Tensão["Quantidade de Barras com Sobretensão"] = Quan_Barra_Sobre_Tensão
#Dicionário da tensão em PU da Barra que é ligada o GERADO02
Dados_Tensão_PU_Barra_GER02 = dict()
Dados_Tensão_PU_Barra_GER02["Potência da G.D KW"] = geração_Kw_List
Dados_Tensão_PU_Barra_GER02["Tensão em PU da Barra do GER02 "] = Tensão_Barra_GER02
#Dicionário que contém os dados de fluxo de potência a montante e jusante do GER02
Dados_Potência_W_Montante_Jusante_GER02 = dict()
Dados_Potência_W_Montante_Jusante_GER02["Potência da G.D KW"] = geração_Kw_List
Dados_Potência_W_Montante_Jusante_GER02["Fluxo a montante em KW"] = Pot_W_Montante_GER02
Dados_Potência_W_Montante_Jusante_GER02["Fluxo a jusante em KW"] = Pot_W_Jusante_GER02
#Dicionário com as Perdas em W e KVAR da Linha que o GER02 se encontra conectado
Dados_Perdas_W_Linha_GER02 = dict()
Dados_Perdas_W_Linha_GER02["Potência da G.D KW"] = geração_Kw_List
Dados_Perdas_W_Linha_GER02["Perdas em KW"] = Perdas_W_Linha_GER02
Dados_Perdas_W_Linha_GER02["Perdas em KVAR"] = Perdas_KVAR_Linha_GER02
#Dicionário do módulo da corrente
Dados_Corrente_Linha_GER02 = dict()
Dados_Corrente_Linha_GER02["Potência da G.D KW"] = geração_Kw_List
Dados_Corrente_Linha_GER02["Módulo da Corrente"] = Corrente_Linha_GER02
#Todos os dataframes
Tabela_Dados_Gerais = pd.DataFrame().from_dict(Dados_Gerais)
Tabela_Tensão_Max = pd.DataFrame().from_dict(Dados_Tensão_Max)
Tabela_Tensão_Min = pd.DataFrame().from_dict(Dados_Tensão_Min)
Tabela_Quantidade_Barras_Su_Sobre_Tensão = pd.DataFrame().from_dict(Quantidade_Barras_Su_Sobre_Tensão)
Tabela_Tensão_PU_Barra_GER02 = pd.DataFrame().from_dict(Dados_Tensão_PU_Barra_GER02)
Tabela_Potência_W_Montante_Jusante_GER02 = pd.DataFrame().from_dict(Dados_Potência_W_Montante_Jusante_GER02)
Tabela_Perdas_Linha_GER02 = pd.DataFrame().from_dict(Dados_Perdas_W_Linha_GER02)
Tabela_Corrente_Linha_GER02 = pd.DataFrame().from_dict(Dados_Corrente_Linha_GER02)


#Montagem do gráfico 1
DadosCKT2, grafico = plt.subplots(nrows=3, ncols=2 , sharex=True)
DadosCKT2.suptitle('Dados Gerais do CKT 02', color="black")
grafico[0, 0].plot(Tabela_Dados_Gerais["Potência da G.D KW"], Tabela_Dados_Gerais["Potência em KW"], color="green", label="Potência em KW")
grafico[0,0].set_title("Gráfico GERADO2")
grafico[0, 1].plot(Tabela_Dados_Gerais["Potência da G.D KW"], Tabela_Dados_Gerais["Potência em KVAR"],color="green", label="Potência em KVAR")
grafico[1, 0].plot(Tabela_Dados_Gerais["Potência da G.D KW"], Tabela_Dados_Gerais["Perdas em KW"], color="red", label="Perdas em KW")
grafico[1, 1].plot(Tabela_Dados_Gerais["Potência da G.D KW"], Tabela_Dados_Gerais["Perdas em KVAR"],color="red",label="Perdas em KVAR")
grafico[2, 0].plot(Tabela_Dados_Gerais["Potência da G.D KW"], Tabela_Dados_Gerais["Tensão Máxima"],color="blue", label="Tensão Máxima")
grafico[2, 0].plot([Tabela_Dados_Gerais["Potência da G.D KW"].min(), Tabela_Dados_Gerais["Potência da G.D KW"].max()],[1.05, 1.05], color="blue", label="1.05")
grafico[2, 1].plot(Tabela_Dados_Gerais["Potência da G.D KW"], Tabela_Dados_Gerais["Tensão Mínima"], color="black", label="Tensão Mínima")
grafico[2, 1].plot([Tabela_Dados_Gerais["Potência da G.D KW"].min(), Tabela_Dados_Gerais["Potência da G.D KW"].max()],[0.95,0.95], color="black",label="0.95")

#Montagem do gráfico 2
DadosGER02, grafico1 = plt.subplots(nrows=2,ncols=2,sharex=True)
DadosGER02.suptitle('Dados no local de instalação do GER02')
grafico1[0,0].plot(Tabela_Perdas_Linha_GER02["Potência da G.D KW"],Tabela_Perdas_Linha_GER02["Perdas em KW"],color="red",label="Perdas em KW")
grafico1[0,1].plot(Tabela_Potência_W_Montante_Jusante_GER02["Potência da G.D KW"],Tabela_Potência_W_Montante_Jusante_GER02["Fluxo a montante em KW"],color="orange",label="Fluxo a Montade em KW")
grafico1[0,1].plot(Tabela_Potência_W_Montante_Jusante_GER02["Potência da G.D KW"],Tabela_Potência_W_Montante_Jusante_GER02["Fluxo a jusante em KW"],color="red", label="Fluxo a Jusante em KW")
grafico1[1,0].plot(Tabela_Corrente_Linha_GER02["Potência da G.D KW"],Tabela_Corrente_Linha_GER02["Módulo da Corrente"], color="black",label="Módulo da Corrente")
grafico1[1,0].axhline(600, color="purple",label="Alarme de Corrente")
grafico1[1,1].plot(Tabela_Tensão_PU_Barra_GER02["Potência da G.D KW"],Tabela_Tensão_PU_Barra_GER02["Tensão em PU da Barra do GER02 "], color="blue",label="Tensão Pu")
grafico1[1,1].axhline(1.05,color="brown",label="Tensão Máxima")
grafico1[1,1].axhline(0.95,color="black",label="Tensão Mínima")



for edicao in grafico:
    for ed in edicao:
        ed.set_xlabel("Nível de Geração (KW)")
        ed.legend()
        ed.grid(True)


for edicao1 in grafico1:
    for ed1 in edicao1:
        ed1.set_xlabel("Nível de Geração (KW)")
        ed1.legend()
        ed1.grid(True)


DadosCKT2.tight_layout()
DadosGER02.tight_layout()
plt.show()


print('here')


