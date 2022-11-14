import os
import pathlib
from Classes import PICOmind


# definição da main
def main(args=None):
    # pega o valor passado pra main
    diretorioAlvo = args
    # verifica se nao foi passado um caminho
    if (not diretorioAlvo):
        # se nao foi, define o diretorio de "instalacao" como o diretorio em que o script está
        diretorioAlvo = os.path.dirname(os.path.abspath(__file__))
    # define o diretorioAlvo
    diretorioAlvo = pathlib.Path(diretorioAlvo).joinpath("Alvo")
    # cria a inteligencia do PICO
    picoMind = PICOmind(diretorioAlvo)
    # executa o PICO
    picoMind.Executa()
    # abre o arquivo de resultados e pega o melhor
    melhorResultado = picoMind.ImportaMelhorResultado()
    print("%s%i"%("O melhor resultado é obtido com a curva de ID igual a ",melhorResultado['ID']))
    # verifica se o melhor resultado possui ID igual a -1
    if (melhorResultado['ID'] == -1):
        print(f"Não foi possível encontrar um resultado que diminuísse as perdas do Caso Base, que são {melhorResultado['Perdas']} kWh")
    else:
        print("%s%i%s%f%s" % ("A curva de ID igual a ",melhorResultado['ID']," diminui as perdas em ",picoMind.resultadoBase.perdasTotal - melhorResultado['Perdas']," kWh, por dia"))

# verifica se é um script a ser executado
if __name__ == '__main__':
    #main("C:\Program Files\OpenDSS\IEEETestCases\123Bus") ## teste
    # executa main
    main()