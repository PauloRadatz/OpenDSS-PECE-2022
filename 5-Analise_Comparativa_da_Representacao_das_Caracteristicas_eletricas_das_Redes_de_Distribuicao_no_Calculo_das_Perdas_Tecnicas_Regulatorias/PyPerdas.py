# -*- coding: utf-8 -*-

"""
    @Author  : Júlio A. de Bitencourt
    @Email   : jabgil@hotmail.com
    @File    : PyPerdas.py
    @Software: PyCharm, Interpretador: Python 3.8
    @whatsApp: (51)997145721
    Programa de Cálculo das Perdas Técnicas das redes de distribuição MT e BT
    
    O cálculo é realizado para o ano civil, considerando três patamares de carga semanais (Dia útil, Sábado e domingo).

    O cálculo iterativo das perdas leva em consideração a diferença entre as cargas medidas
    e as Perdas Não Técnicas (PNT)

"""


import numpy as np
import py_dss_interface
import math as mt
import sys
import os
import pathlib
import csv
import DataBase as DB
import time


def Ler_Energias_Injetadas(Arq):
    cursor,con = db.database(Arq)
    sql = 'SELECT cod_id,ene_01,ene_02,ene_03,ene_04,ene_05,ene_06,ene_07,ene_08,ene_09,ene_10,ene_11,ene_12 FROM CTMT'
    cursor.execute(sql)
    lista_dict = dict()
    lista = cursor.fetchall()

    for (cod) in lista:
        Energias = []
        for item in cod[1:23]:
            Energias.append(float(item))
        lista_dict[str.rstrip(cod[0])] = Energias

    return lista_dict

def Ler_Consumos(Arq):
    arq = open(Arq)
    Dict_ConsumoBT = dict()
    Dict_ConsumoIP = dict()
    Dict_ConsumoMT = dict()
    Dict_MedidoresMT = dict()
    Dict_MedidoresBT = dict()

    linhas = arq.readlines()
    print('Carregando Consumo de Energias')
    for linha in linhas:
        lin = linha.split(';')
        print(lin)
        consumo = []
        for item in lin[1:13]:
            consumo.append(float(item))
        Dict_ConsumoMT[lin[0]] = consumo

        consumo = []
        for item in lin[13:25]:
            consumo.append(float(item))
        Dict_ConsumoBT[lin[0]] = consumo

        consumo = []
        for item in lin[25:37]:
            consumo.append(float(item))
        Dict_ConsumoIP[lin[0]] = consumo
        Dict_MedidoresMT[lin[0]] = float(lin[-2])
        Dict_MedidoresBT[lin[0]] = float(lin[-1])

    list_circuitos =list(Dict_ConsumoMT.keys())

    return list_circuitos,Dict_ConsumoMT,Dict_ConsumoBT,Dict_ConsumoIP,Dict_MedidoresMT,Dict_MedidoresBT

def Ler_Geracao(Arq):
    arq = open(Arq)
    Dict_GeracaoMT = dict()
    linhas = arq.readlines()
    print('Carregando Geração')
    for linha in linhas:
        lin = linha.split(';')
        geracao = []
        for item in lin[1:13]:
            geracao.append(float(item))
        Dict_GeracaoMT[lin[0]] = geracao
    return Dict_GeracaoMT

def Ler_Participa_Energias(Arq):
    arq = open(Arq)
    Dict_ParticipaEnergias_MT = dict()
    Dict_ParticipaEnergias_BT = dict()
    Dict_Dias = dict()

    linhas = arq.readlines()
    print('Carregando Participa Energias')
    for linha in linhas:
        #print(linha.split(';'))
        linBT = linha.split(';')[1:4]
        linMT = linha.split(';')[25:-1]
        linDias = linha.split(';')[4:7]

        Energias = []
        for item in linha.split(';')[1:4]:
            Energias.append(float(item))
        Dict_ParticipaEnergias_BT[linha.split(';')[0]] = Energias

        Energias = []
        for item in linha.split(';')[25:-1]:
            Energias.append(float(item))
        Dict_ParticipaEnergias_MT[linha.split(';')[0]] = Energias

        Dias = []
        for item in linha.split(';')[4:7]:
            Dias.append(int(item))
        Dict_Dias[linha.split(';')[0]] = Dias

    print(Dict_ParticipaEnergias_BT)
    print(Dict_ParticipaEnergias_MT)
    print(Dict_Dias)

    return Dict_ParticipaEnergias_BT,Dict_ParticipaEnergias_MT,Dict_Dias


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

def Compila_Circuito(dss_file):
    dss.text("ClearAll")
    dss.text("Compile [{}]".format(dss_file))

def Inicializa_Cargas():
    nUCBT = 0
    nUCMT = 0
    nIP   = 0
    TotalBT = 0
    TotalMT = 0
    TotalIP = 0

    iLoads = dss.loads_first()
    while iLoads >0:
        if dss.loads_read_kv() >= 1:
            load_name = dss.loads_read_name()
            dss.circuit_set_active_element("Load.{}".format(str(load_name)))
            voltages = dss.cktelement_voltages_mag_ang()[0]
            tpu = dss.cktelement_voltages_mag_ang()[0]/(dss.loads_read_kv()/mt.sqrt(3)*1000)
            nUCMT +=1
            TotalMT += dss.loads_read_kw()
        else:
            if 'IP' in dss.loads_read_name().upper():
                nIP +=1
                TotalIP += dss.loads_read_kw()
            else:
                nUCBT +=1
                TotalBT += dss.loads_read_kw()
        iLoads = dss.loads_next()
    return nUCBT,nUCMT,TotalBT,TotalIP,TotalMT

def AjustaCarga(pnt,pnt_bt,FPSemanaBT,FPSemanaMT,DiasNoMes,cargatotalBT,cargatotalMT):
    CargaBTkW = (pnt * pnt_bt/100 * FPSemanaBT / (0.6113 * DiasNoMes * 24))
    if cargatotalBT == 0:
        AjusteBT = 0
    else:
        AjusteBT = CargaBTkW / cargatotalBT

    CargaMTkW = (pnt * (100 - pnt_bt)/100 * FPSemanaMT / (0.6113 * DiasNoMes * 24))

    if cargatotalMT == 0:
        AjusteMT = 0
    else:
        AjusteMT = CargaMTkW / cargatotalMT

    # ...Compila circuito e Resetar o EnergyMeter.....
    Compila_Circuito(dss_file)
    dss.meters_reset()

    iLoads = dss.loads_first()
    while iLoads >0:
        if dss.loads_read_kv() >= 1:
            dss.loads_write_kw(dss.loads_read_kw()*(1+AjusteMT))
        else:
            if 'IP' not in dss.loads_read_name().upper() and 'med' not in dss.loads_read_name().upper():
                dss.loads_write_kw(dss.loads_read_kw() * (1 + AjusteBT))
        iLoads = dss.loads_next()

    dss.text("solve")


def EnergyMeter():
    PerdaTecnica = 0
    PerdaTrafos  = 0
    PerdaFerro   = 0
    PerdaCobre = 0
    PerdasBT     = 0
    PerdasMT     = 0
    EnergiaGerada  = 0
    EnergiaCalculada = 0
    CargaMTAjustada = 0
    CargaBTAjustada = 0
    CargaMTBTAjustada =0
    EnergyNames = dict()
    EnergyValues = dict()

    IDMeter=dss.meters_first()
    while IDMeter > 0:
        V = dss.meters_register_values()
        canal = dss.meters_register_names()
        for k in range(66):
           EnergyNames[k+1]  = canal[k]
           EnergyValues[k+1] = V[k]

        EnergiaCalculada = V[0]
        EnergiaGerada += V[28]
        PerdaTecnica  += V[12]
        PerdaTrafos   += V[23] 
        PerdaFerro    += V[18]
        PerdaCobre    = PerdaTrafos - PerdaFerro

        #...totalização das perdas nas redes BT e MT...
        for i in range(39,45):
            xCanal = canal[i].split(' ')[0]
            if xCanal[0:3] != 'Aux':
                if float(xCanal[0:4]) >1:
                    PerdasMT += V[i] 
                else:
                    PerdasBT += V[i]

        #...totalização das Cargas Ajustadas BT e MT...
        for i in range(60,66):
            xCanal = canal[i].split(' ')[0]
            if xCanal[0:3] != 'Aux':
                if float(xCanal[0:4]) >1:
                    CargaMTAjustada += V[i]
                else:
                    CargaBTAjustada += V[i]

        CargaMTBTAjustada += V[4]
        #...Reset do EnergyMeter....
        dss.meters_reset()
        IDMeter= dss.meters_next()

    return PerdaTecnica,PerdaTrafos,PerdaFerro,PerdaCobre,PerdasMT,PerdasBT,CargaMTAjustada,\
           CargaBTAjustada,CargaMTBTAjustada,EnergiaCalculada,EnergiaGerada


if __name__ == '__main__':
    EnergiaInjetadaTotal = 0
    EnergiaAjustadatotal = 0
    EnergiaGerada = 0
    ConsumoTotal = 0
    ConsumoTotalMT = 0
    ConsumoTotalAjustadoMT = 0
    ConsumoTotalAjustadoBT = 0
    ConsumoTotalBT = 0
    ConsumoTotalIP = 0
    CargaMedidores = 0
    PerdaTecnicaTotal = 0
    PerdaTotalTrafos = 0
    PerdaTotalFerro = 0
    PerdaTotalCobre = 0
    PerdaRedesMT = 0
    PerdaRedesBT = 0
    PerdaRamais = 0
    PNTTotal = 0
    Lista_Trafos_AjustaTap = []

    # ...Ler Energias Injetadas...    
    Arq = 'ArquivoEnergiaInjetada'
    ArqSaida = 'AquivoSaida.csv'
    f = open(ArqSaida, 'w', newline='', encoding='utf-8')
    w = csv.writer(f)
    Energia_injetada = Ler_Energias_Injetadas(Arq)
    print('Carregando Energias Injetadas nos Circuitos:')
    print(Energia_injetada)

    Arq = 'ArquivoConsumosenergia'
    Circuitos, ConsumoMT, ConsumoBT, ConsumoIP,MedidoresMT,MedidoresBT = Ler_Consumos(Arq)
    print('Lista de ', len(Circuitos), ' Alimentadores:  ', Circuitos)
    print('Carregando Consumo de Energias BT')
    print(ConsumoBT)
    print('Carregando Consumo de Energias MT')
    print(ConsumoMT)
    print('Carregando Consumo de Energias IP')
    print(ConsumoIP)
    print('Carregando Medidores MT')
    print(MedidoresMT)
    print('Carregando CMedidores BT')
    print(MedidoresBT)

    # ...Ler Geração MT...
    Arq = 'ArquivoGeração'
    GeracaoMT = Ler_Geracao(Arq)
    print('Carregando Geração MT')
    print(GeracaoMT)

    # ...Ler Paraticipações das Energias nos patamares semanais...
    Arq = 'ArquivoParticipaçãoEnergias'
    PE_BT,PE_MT,PE_Dias = Ler_Participa_Energias(Arq)
    
    psemana    = ['DU','SA','DO']
    nSemana    = [1,2,3]
    nMes       = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

    PNT_S_BT,PNT_BT = input('1) % PNT sobre o Mercado BT e 2) % PNT na BT:').split(" ")
    if PNT_BT != '':
        PNT_BT = float(PNT_BT)
        PNT_MT = 100.0 - PNT_BT
    else:
        PNT_BT = 100.0
        PNT_MT = 0.0

    PNT_S_BT = float(PNT_S_BT)

    #...definição do período de cálculo das perdas técnicas....
    Mesin,Mesfim = input('Mês inicial e Mês final:').split(" ")
    if Mesfim != '':
        Meses = range(int(Mesin),int(Mesfim)+1)
    else: Meses = [int(Mesin)]

    #   instancia a variável DSS linkando com as DLL do OpenDSS via
    dss = py_dss_interface.DSSDLL()
    start = time.time()
    
    Cabec1 =['Cicuito','Mes','Semana','En.Injetada',
            'GeracaoA4','Carga Total','CargaMT','CargaBT','CargaIP','EnCalculada','Geracao','Perda','En.Ajustada','Perda Ajustada',
             'PNT','Perda Trafos','Perda Ferro','PerdaCobre','PerdaBT','PerdaMT','MedidoresMT','MedidoresBT','CargaMTAjustada','CargaBTAjustada']

    cabec1 = '{:^10} {:3} {:^6} {:^12} {:^8} {:^12} {:^12} {:^12} {:^12} {:^12} {:^12} {:^12} {:^12} {:^12}'.format('Cicuito','Mês','Semana','En.Injetada',
            'GeraçãoA4','Carga Total','CargaMT','CargaBT','CargaIP','EnCalculada','Geração','Perda','En.Ajustada','Perda Ajustada')
    cabec2 = '{:^12} {:^12} {:^12} {:^12} {:^12} {:^12}'.format('PNT','Perda Trafos','Perda Ferro','PerdaCobre','PerdaBT','PerdaMT')
    cabec3 = '{:^10} {:^10} {:^12} {:^12}'.format('MedidoresMT','MedidoresBT','CargaMTAjustada','CargaBTAjustada')
    print(cabec1+cabec2+cabec3)
    w.writerow(Cabec1)

    for mes in Meses:
        for circuito in Circuitos:
            for semana in nSemana:
     
                #...direcionar o arquivo contendo os scripts do OpenDSS....
                dss_file = 'Master.dss'
                #...Carregar Circuito....
                Compila_Circuito(dss_file)

                #...EnergyMeter
                PerdaTecnica, PerdaTrafos, PerdaFerro, PerdaCobre, PerdasMT, PerdasBT,\
                CargaMTAjustada,CargaBTAjustada, CargaMTBTAjustada,EnergiaCalculada,EnergiaGerada = EnergyMeter()

                # ...Inicialica Cargas e geração.......
                UCBT,UCMT,CargaTotalBT,CargaTotalIP,CargaTotalMT = Inicializa_Cargas()

                listaConsumo = np.float_(ConsumoMT[circuito])
                cargaMT1 = listaConsumo[mes-1]
                pMT = PE_MT[str(mes)][semana-1]
                CargaMT = ConsumoMT[circuito][mes - 1] * PE_MT[str(mes)][semana-1]
                CargaBT = ConsumoBT[circuito][mes - 1] * PE_BT[str(mes)][semana - 1]
                GeracaoA4 = GeracaoMT[circuito][mes-1] * PE_MT[str(mes)][semana-1]
                CargaIP = ConsumoIP[circuito][mes - 1] /sum(PE_Dias[str(mes)]) * PE_Dias[str(mes)][semana-1]

                periodo = PE_Dias[str(mes)][semana - 1]
                CargaMedidorMT = MedidoresMT[circuito]/365 * PE_Dias[str(mes)][semana-1]
                CargaMedidorBT = MedidoresBT[circuito]/365 * PE_Dias[str(mes)][semana - 1]
                CargaMedidor = CargaMedidorMT + CargaMedidorBT
                Carga = CargaMT + CargaBT + CargaIP + CargaMedidor

                if CargaMT + CargaBT == 0:
                    FatorSemana = 1
                else:
                    FatorSemana = (CargaMT + CargaBT) / (ConsumoMT[circuito][mes - 1] +ConsumoBT[circuito][mes - 1])

                #...Perdas Iniciais..........
                PerdaTecnicaIni = PerdaTecnica
                EnergiaCalculadaIni = EnergiaCalculada + EnergiaGerada
                #EnergiaCalculadaIni = EnergiaCalculada
                if EnergiaCalculadaIni == 0:
                    pcPerdaTecnicaIni = 0
                else:
                    pcPerdaTecnicaIni = PerdaTecnicaIni / EnergiaCalculadaIni * 100
                pcPerdaTecnica = pcPerdaTecnicaIni
                PerdaTrafosIni = PerdaTrafos
                PerdaFerroIni  = PerdaFerro
                PerdaCobreIni  = PerdaCobre
                PerdasBTIni    = PerdasBT
                PerdasMTIni    = PerdasMT

                #...Carregar Energia Injetada no Circuito.....
                if PNT_S_BT == 0:
                    PNT_0 = 0
                    PNT = 0
                    EnergiaInjetada = Energia_injetada[circuito][mes-1]*FatorSemana
                else:
                    PNT = CargaBT *float(PNT_S_BT)/100
                    EnergiaInjetada = Carga + PerdaTecnica * periodo + PNT

                #...primeira iteração...PNT = 0

                iter = 1
                PNT = 0
                CargaTotal = Carga + PerdaTecnica * periodo
                EnergiaCalculadaTotal = CargaTotal + PNT
                Mismach = 1000
                PTec = PerdaTecnica * periodo

                if PNT_S_BT == 0:
                    PNT_0 = 0
                    PTec_0 = PTec
                    EnInj_0 = EnergiaInjetada
                    EnCalc = Carga + PTec_0 + PNT_0
                    EnCalc_0 = EnCalc
                    DeltaPNT = 0
                    PNT = 0

                #...Inicio do Processo Iterativo.........
                while abs(Mismach) > 500.0:
                    if PNT_S_BT == 0:
                        if Mismach > 0:
                            PNT = EnergiaInjetada - (Carga + PTec) - abs(Mismach)/2
                        else:
                            PNT = EnergiaInjetada - (Carga + PTec) + abs(Mismach)/2

                        AjustaCarga(PNT, PNT_BT, PE_BT[str(mes)][semana - 1], PE_MT[str(mes)][semana - 1],
                                    PE_Dias[str(mes)][semana - 1], CargaTotalBT, CargaTotalMT)
                        
                        # ...EnergyMeter....
                        PerdaTecnica, PerdaTrafos, PerdaFerro, PerdaCobre,PerdasMT, PerdasBT, \
                        CargaMTAjustada, CargaBTAjustada, CargaMTBTAjustada, EnergiaCalculada, EnergiaGerada = EnergyMeter()
                        
                        PTec    = PerdaTecnica * periodo
                        EnInj   = EnergiaInjetada - GeracaoA4
                        EnCalc  = Carga + PTec + PNT
                        Mismach = EnergiaInjetada - EnCalc

                    else:
                        PTec_0 = PTec
                        PNT = (CargaBT + CargaIP) * PNT_S_BT/100
                        #...Ajustar cargas em função das PNT....
                        AjustaCarga(PNT,PNT_BT,PE_BT[str(mes)][semana - 1], PE_MT[str(mes)][semana - 1],
                                    PE_Dias[str(mes)][semana-1],CargaTotalBT,CargaTotalMT)

                        #...EnergyMeter....
                        PerdaTecnica, PerdaTrafos, PerdaFerro, PerdaCobre, PerdasMT, PerdasBT, \
                        CargaMTAjustada, CargaBTAjustada, CargaMTBTAjustada, EnergiaCalculada, EnergiaGerada = EnergyMeter()

                        PTec = PerdaTecnica * periodo
                        EnergiaInjetada = Carga + PTec + PNT - GeracaoA4
                        Mismach = PTec - PTec_0

                    if dss.solution_read_converged():
                        ConvergeOpen = True
                    else:
                        ConvergeOpen = False

                    if not ConvergeOpen:
                        print(f"Circuito não convergiu: Mês {mes}  Alimentador:{circuito} "
                              f"  Semana: {semana}  ... {time.time() - start}")

                    EnergiaCalculadaTotal = Carga + PNT + PerdaTecnica * periodo - GeracaoA4
                    if EnergiaInjetada == 0:
                        pcPerdaTecnica = 0
                    else:
                        pcPerdaTecnica = PerdaTecnica * periodo / EnergiaInjetada * 100

                    iter +=1
                #...Fim do Processo Iterativo...

                #...Totalização das Energias e Cargas....
                EnergiaInjetadaTotal += EnergiaInjetada
                EnergiaAjustadatotal += EnCalc
                EnergiaGerada     += GeracaoA4
                PerdaTecnicaTotal += PerdaTecnica*periodo
                PerdaTotalTrafos  += PerdaTrafos*periodo
                PerdaTotalFerro   += PerdaFerro*periodo
                PerdaTotalCobre   += PerdaCobre*periodo
                PerdaRedesBT      += PerdasBT*periodo
                PerdaRedesMT      += PerdasMT*periodo
                PerdaRamais       += PerdasRamal*periodo

                ConsumoTotal   += Carga
                ConsumoTotalMT += CargaMT
                ConsumoTotalAjustadoMT += CargaMTAjustada*periodo
                ConsumoTotalAjustadoBT += CargaBTAjustada*periodo
                ConsumoTotalBT += CargaBT
                ConsumoTotalIP += CargaIP
                CargaMedidores += CargaMedidorMT+CargaMedidorBT
                PNTTotal       += PNT

                if PerdaTecnica == 0:
                    PerdaTecnica = PerdaTecnicaIni
                    pcPerdaTecnica = PerdaTecnica * periodo / EnergiaInjetada * 100
                    PNT = 0
                if EnergiaInjetada ==0:
                    pcPNT = 0
                else: pcPNT = PNT / EnergiaInjetada * 100

                ListaSaida =[circuito,nMes[mes-1],psemana[semana-1],EnergiaInjetada,GeracaoA4,Carga,CargaMT,CargaBT,CargaIP,EnergiaCalculada*periodo,EnergiaGerada*periodo,
                             PerdaTecnicaIni*periodo,EnCalc,PerdaTecnica*periodo,PNT,PerdaTrafos*periodo,PerdaFerro*periodo,PerdaCobre*periodo,
                             PerdasBT*periodo,PerdasMT*periodo,CargaMedidorMT,CargaMedidorBT,CargaMTAjustada*periodo,CargaBTAjustada*periodo]

                print(f'{circuito:^10} {nMes[mes-1]:>3} {psemana[semana-1]:^6} {EnergiaInjetada:>12,.2f} {GeracaoA4:>8,.2f} {Carga:>12,.2f} '
                      f'{CargaMT:>12,.2f} {CargaBT:>12,.2f} {CargaIP:>12,.2f} {EnergiaCalculada*periodo:>12,.2f} {EnergiaGerada*periodo:>12,.2f} '
                      #f'{PerdaTecnicaIni*periodo:>12,.2f} {EnergiaCalculada*periodo:>12,.2f} {PerdaTecnica*periodo:>12,.2f} {PNT:>12,.2f}'
                      f'{PerdaTecnicaIni*periodo:>12,.2f} {EnCalc:>12,.2f} {PerdaTecnica*periodo:>12,.2f} {PNT:>12,.2f}'
                      f'{PerdaTrafos*periodo:>12,.2f} {PerdaFerro*periodo:>12,.2f} {PerdaCobre*periodo:>12,.2f} {PerdasBT*periodo:>12,.2f}'
                      f'{PerdasMT*periodo:>12,.2f} {CargaMedidorMT:>12,.2f} {CargaMedidorBT:>12,.2f} '
                      f'{CargaMTAjustada*periodo:>12,.2f} {CargaBTAjustada*periodo:>12,.2f}')
                w.writerow(ListaSaida)

                #end = time.time()
                #print(f'Mês {mes}  Alimentador:{circuito}   Semana: {semana}  ... {end - start}')
    print(f'Energia Injetada: {EnergiaInjetadaTotal:>13,.2f}')
    print(f'Energia Gerada: {EnergiaGerada:>15,.2f}')
    print(f'Carga Total: {ConsumoTotal:>19,.2f}')
    print(f'   Carga MT: {ConsumoTotalMT:>19,.2f}')
    print(f'   Carga BT: {ConsumoTotalBT:>19,.2f}')
    print(f'   Carga IP: {ConsumoTotalIP:>19,.2f}')
    print(f'Perda Técnica: {PerdaTecnicaTotal:>16,.2f} {PerdaTecnicaTotal/EnergiaInjetadaTotal*100:>6,.3f} %')
    print(f' Trafos MT/BT: {PerdaTotalTrafos:>16,.2f} {PerdaTotalTrafos/EnergiaInjetadaTotal*100:>6,.3f} %')
    print(f'        Ferro: {PerdaTotalFerro:>16,.2f} {PerdaTotalFerro / EnergiaInjetadaTotal * 100:>6,.3f} %')
    print(f'        Cobre: {PerdaTotalCobre:>16,.2f} {PerdaTotalCobre / EnergiaInjetadaTotal * 100:>6,.3f} %')
    print(f' Redes MT    : {PerdaRedesMT:>16,.2f} {PerdaRedesMT / EnergiaInjetadaTotal * 100:>6,.3f} %')
    print(f' Redes BT    : {PerdaRedesBT:>16,.2f} {PerdaRedesBT / EnergiaInjetadaTotal * 100:>6,.3f} %')
    print(f'Perda Não Técnica: {PNTTotal:>12,.2f} {PNTTotal/EnergiaInjetadaTotal*100:>6,.3f} %')

    end = time.time()
    f.close()
    print(f'Fim do processo de cálculo das Perdas Técnicas ... {convert(end - start)}')
