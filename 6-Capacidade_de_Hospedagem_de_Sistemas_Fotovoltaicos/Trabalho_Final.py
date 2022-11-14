import sys
import subprocess

arquivos = ['Trabalho_Final_GER01.py','Trabalho_Final_GER02.py','Trabalho_Final_GER03.py','Trabalho_Final_GER123.py']
processos = []

for arquivo in arquivos:
    processo = subprocess.Popen([sys.executable, arquivo])
    processos.append(processo)

for processo in processos:
    processo.wait()

print('here')