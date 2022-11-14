import math

import pandas as pd
import py_dss_interface as dss_interface
import pathlib
import os
import csv
import numpy as np

# define classe do objeto CurvaPV
class CurvaPV:
    def __init__(self, line):
        # inicia o objeto
        self.ID = int(line[0])
        self.xarray = line[1]
        self.yarray = line[2]
        self.DeterminaNPTS()

    def DeterminaNPTS(self):
        # determina numero de pontos, que vai ser um a mais do que o numero de espaços
        self.NPTS = self.xarray.count(" ") + 1

# define classe do objeto ResultadoCurvaPV
class ResultadoCurvaPV:
    def __init__(self):
        # inicia objeto
        self.caso = None
        self.perdasTotal = None
        self.HouveSubtensao = None
        self.HouveSobretensao = None


# define classe que controle a inteligencia do PICO
class PICOmind:
    def __init__(self, diretorioAlvo):
        # inicia a inteligencia
        self.diretorioAlvo = diretorioAlvo
        self.IniciaOpenDSS()
        self.DeterminaDiretorioRede()
        self.DeterminaDiretorioCurvas()
        self.DeterminaDiretorioPV()
        self.DeterminaLisCurvas()
        self.DeterminaMaster()
        self.CompilaMaster(False)
        self.IniciaDictResultados()
        # inicia parametro do caminho do PV
        self.pvPath = None
        # inicia a lista de casos
        self.IniciaLisCasos()




    def IniciaOpenDSS(self):
        self.dss = dss_interface.DSSDLL()

    def DeterminaDiretorioRede(self):
        self.diretorioRede = pathlib.Path(self.diretorioAlvo).joinpath("Rede")

    def DeterminaDiretorioCurvas(self):
        self.diretorioCurvas = pathlib.Path(self.diretorioAlvo).joinpath("Curvas")

    def DeterminaDiretorioPV(self):
        self.diretorioPV = pathlib.Path(self.diretorioAlvo).joinpath("PV")

    def CompilaMaster(self, solve=False):
        # primeiro limpa o OpenDss
        self.dss.text("Clear")
        # compila a rede, sem PV
        self.dss.text(f"compile [{self.master}]")
        # apos compilar a rede, força a configuracao do cálculo
        self.ConfiguraCalculo()
        # verifica se deve dar um solve
        if (solve):
            # da um solve
            self.dss.text("solve")

    def ConfiguraCalculo(self):
        # define comando para o numero maximo iteracoes de controle
        comando = "set maxcontroli = 2000"
        # manda pro OpenDSS
        self.dss.text(comando)
        # define comando para o modo
        comando = "set mode = daily"
        # manda pro OpenDSS
        self.dss.text(comando)
        # define comando para o tamanho do passo
        comando = "set stepsize = 1h"
        # manda pro OpenDSS
        self.dss.text(comando)
        # define comando para o numero de patamares
        comando = "set number = 24"
        # manda pro OpenDSS
        self.dss.text(comando)
        # define comando para o modo de controle
        comando = "set controlmode = static"
        # manda pro OpenDSS
        self.dss.text(comando)
        # define comando para o arquivo DI
        comando = "set demandinterval = true"
        # manda pro OpenDSS
        self.dss.text(comando)
        # define comando para o DIVerbose
        comando = "set DIVerbose = true"
        # manda pro OpenDSS
        self.dss.text(comando)
        # define comando para o relatorio de excessao de tensao
        comando = "set voltexceptionreport = true"
        # manda pro OpenDSS
        self.dss.text(comando)



    def DeterminaMaster(self):
        # inicia master
        self.master = None
        # percorre os arquivos do diretorio que possui rede
        for path in os.listdir(self.diretorioRede):
            # verifica se existe esse arquivo
            if (os.path.isfile(os.path.join(self.diretorioRede, path))):
                # verifica se o arquivo possui o nome MASTER nele
                if ("MASTER" in path.upper()):
                    # se tiver, achei o master da rede
                    self.master = pathlib.Path(self.diretorioRede).joinpath(path)
                    break

    def InserePV(self, solve=False, casoBase=False):
        # verifica se ja foi atribuido o caminho do PV
        if (not self.pvPath):
            # se ainda nao foi pega o primeiro arquivo do diretorio do PV
            self.pvPath = os.listdir(self.diretorioPV)[0]
            # completao caminho do PV
            self.pvPath = pathlib.Path(self.diretorioPV).joinpath(self.pvPath)
        # insere o PV na rede
        self.dss.text(f"redirect [{self.pvPath}]")
        # verifica se é o caso base = com PV sem InvControl
        if (casoBase):
            # se for, desativa o InvControl
            self.dss.text("edit InvControl.VoltVar enabled=false")
        # altera o valor da potencia PV
        self.AlteraPotenciaPV()
        if (solve):
            # da um solve
            self.dss.text("solve")
            # com o solve dado, ele pode determinar o nome do circuito
            self.DeterminaNomeCircuito()

    def IniciaLisCasos(self):
        # inicia a lista
        self.lisCasos = []
        # preenche ela com casos possiveis
        for i in range(50, 3550, 50):
            self.lisCasos.append(i)


    def DeterminaNomeCircuito(self):
        # pega o nome do circuito
        self.nomeCircuito = self.dss.circuit_name()

    def AlteraPotenciaPV(self):
        # prepara a string para editar o pmpp do pv
        comandoEdit = f"edit PVSystem.PV Pmpp={self.casoAtual}"
        # edita o pmpp do pv
        self.dss.text(comandoEdit)
        # prepara a string para editar o kVA do pv
        comandoEdit = f"edit PVSystem.PV kVA={self.casoAtual}"
        # edita o kVA do pv
        self.dss.text(comandoEdit)


    def DeterminaLisCurvas(self):
        # inicia lista de curvas
        self.lisCurvas = []
        # pega o primeiro arquivo do diretorio de curvas
        curvasPath = os.listdir(self.diretorioCurvas)[0]
        # abre o arquivo
        with open(pathlib.Path(self.diretorioCurvas).joinpath(curvasPath), "r") as curvasFile:
            # pega as linhas desse arquivo
            lines = csv.reader(curvasFile, delimiter=";")
            # percorre as linhas desse arquivo
            for line in lines:
                # verifica se é o cabeçalho, se for, pula
                if (line[0] == "// ID"):
                    continue
                # cria um objeto CurvaPV e adiciona à lista de curvas
                self.lisCurvas.append(CurvaPV(line))
        curvasFile.close()

    def SalvaResultados(self, curva):
        # cria objeto de resultado
        resultado = ResultadoCurvaPV()
        resultado.caso = self.casoAtual

        # verifica se foi passada um objeto curva
        if (curva):
            # se foi, pega o id dela
            id = curva.ID
            # determina se houve barras com subtensao ou sobretensao
            avaliaTensao = self.AvaliaTensao()
        # se nao foi, adota -1 e salva como o resultado base
        else:
            id = -1
            self.resultadoBase = resultado
            # determina se houve barras com subtensao ou sobretensao salvando as infos do caso base
            avaliaTensao = self.AvaliaTensao(True)


        # determina as perdas totais da rede
        resultado.perdasTotal = self.DeterminaPerdasTotais()

        # salva os resultados da avalicao de tensao
        resultado.HouveSubtensao = avaliaTensao[0]
        resultado.HouveSobretensao = avaliaTensao[1]

        #salva o resultado
        self.dictResultados[id] = resultado


    def SalvaResultadosCSV(self, cabecalho):
        # salva os resultados do dicionario em um csv
        with open('Resultados.csv', 'a') as f:
            # verifica se deve escrever o cabecalho
            if (cabecalho):
                # escreve o cabeçalho
                f.write("%s,%s,%s,%s,%s\n" %("Caso", "ID", "Perdas", "Subtensao", "Sobretensao"))
            # escreve o conteudo
            for key in self.dictResultados.keys():
                f.write("%i,%i,%f,%i,%i\n" %(self.dictResultados[key].caso, key, self.dictResultados[key].perdasTotal, self.dictResultados[key].HouveSubtensao, self.dictResultados[key].HouveSobretensao))

    def AvaliaTensao(self, casoBase=False):
        # le o arquivo DI_VoltExceptions_1
        caminhoDI = pathlib.Path(self.diretorioRede).joinpath(self.nomeCircuito)
        caminhoDI = pathlib.Path(caminhoDI).joinpath("DI_yr_0")
        caminhoDI = pathlib.Path(caminhoDI).joinpath("DI_VoltExceptions_1.csv")
        df = pd.read_csv(caminhoDI, sep=',')
        # pega o numero de barras por patamar em que houve subtensao
        lisSubTensao = df.iloc[:,1].tolist()
        # pega o numero de barras por patamar em que houve sobretensao
        lisSobreTensao = df.iloc[:,3].tolist()
        # se for o caso base, salva nele as listas
        if (casoBase):
            self.resultadoBase.lisSubTensao = lisSubTensao
            self.resultadoBase.lisSobreTensao = lisSobreTensao
        # assume que nao houve subtensao
        houveSubtensao = False
        # percorre a lista de subtensao
        for i in range(len(lisSubTensao)):
            if (lisSubTensao[i] > self.resultadoBase.lisSubTensao[i]):
                houveSubtensao = True
                break
        # assume que nao houve sobretensao
        houveSobretensao = False
        # percorre a lista de sobretensao
        for i in range(len(lisSobreTensao)):
            if (lisSobreTensao[i] > self.resultadoBase.lisSobreTensao[i]):
                houveSobretensao = True
                break



        return [houveSubtensao, houveSobretensao]

    def DeterminaPerdasTotais(self):
        # le o arquivo DI_SystemMeter_1
        caminhoDI = pathlib.Path(self.diretorioRede).joinpath(self.nomeCircuito)
        caminhoDI = pathlib.Path(caminhoDI).joinpath("DI_yr_0")
        caminhoDI = pathlib.Path(caminhoDI).joinpath("DI_SystemMeter_1.csv")
        df = pd.read_csv(caminhoDI, sep=',')
        # retorna a perda total diaria
        return sum(df.iloc[:,5])


    def IniciaDictResultados(self):
        # cria lista de resultados
        self.dictResultados = {}

    def Executa(self):
        # percorre a lista de casos
        for caso in self.lisCasos:
            # define o caso atual
            self.casoAtual = caso
            # reinicia o opendss
            self.ReiniciaOpenDSS(True, True)
            # com master compilado, PV inserido salva os resultado que servirão como base para esse caso
            self.SalvaResultados(None)
            # percorre a lista de curvas
            for curva in self.lisCurvas:
                # executa para a curva analisada
                self.ExecutaCurva(curva)
                # salva o resultado
                self.SalvaResultados(curva)
            # com os resultados no dicionario de resultados, salva eles em um .csv
            self.SalvaResultadosCSV(caso == 50)

    def ImportaMelhorResultado(self):
        # importa os resultados em um dataframe
        df = pd.read_csv('Resultados.csv', sep=',', encoding = "ISO-8859-1")
        # retira do dataframe qualquer linha em que a tensao tenha piorado (com excessao do caso base)
        df = df.drop(df[(df["Subtensao"] == 1) | (df["Sobretensao"] == 1) & (df["ID"] != -1)].index)
        # ordena o dataframe por perdas
        df = df.sort_values("Perdas")
        # pega o melhor resultado
        melhorResultado = df.iloc[0]

        return melhorResultado



    def ExecutaCurva(self, curva):
        # reinicia o OpenDSS
        self.ReiniciaOpenDSS()
        # prepara a string para editar o eixo x
        comandoEdit = f"edit XYcurve.curvaVoltVar xarray={curva.xarray}"
        # edita o eixo x
        self.dss.text(comandoEdit)
        # prepara a string para editar o eixo y
        comandoEdit = f"edit XYcurve.curvaVoltVar yarray={curva.yarray}"
        # edita o eixo y
        self.dss.text(comandoEdit)
        # prepara a string para editar NPTS
        comandoEdit = f"edit XYcurve.curvaVoltVar npts={curva.NPTS}"
        # edita o NPTS
        self.dss.text(comandoEdit)
        # da um solve
        self.dss.text("solve")

    def ReiniciaOpenDSS(self, solve=False, casoBase=False):
        # recompila o master
        self.CompilaMaster()
        # reinsere o PV
        self.InserePV(solve, casoBase)


    def DeterminaMelhorResultado(self):
        # inicia melhor nota com a nota da rede sem inversor
        melhorNota = self.dictResultados.get(-1)
        self.melhorID = -1
        # percorre o dicionario
        for curvaID in self.dictResultados:
            # verifica se a nota da curva analisada é maior que melhor nota ate agora
            if (self.dictResultados.get(curvaID) > melhorNota):
                # se sim, atualiza a melhor nota e o melhor ID
                melhorNota = self.dictResultados.get(curvaID)
                self.melhorID = curvaID
