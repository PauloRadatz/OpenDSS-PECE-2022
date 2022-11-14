import pandas as pd
import py_dss_interface
import os
import pathlib

def do_energy_allocation(dss: py_dss_interface.DSSDLL, energy_kwh, error_kwh, mode):

    global total_power, total_losses

    energy_factor = 0

    for i in range(1000):

        update_load(dss, energy_factor)

        if mode == 'fund':
            dss.text('Set mode=daily')
            dss.solution_solve()
            total_power = dss.meters_register_values()[0]
            total_losses = dss.meters_register_values()[12]
            delta_energy_kwh = energy_kwh - total_power
            energy_factor = delta_energy_kwh / energy_kwh
            dss.meters_reset()
            if abs(delta_energy_kwh) < error_kwh:
                break

        elif mode == 'harm':

            total_power = 0
            total_losses = 0

            for hour in range(24):
                dss.loads_first()
                for _ in range(dss.loads_count()):
                    dss.loads_write_spectrum(dss.loads_read_spectrum().replace(dss.loads_read_spectrum().split('_')[-1], f'H{hour}'))
                    dss.loads_next()

                dss.text("set mode=daily")
                dss.text(f"set hour={hour} number=1")
                dss.solution_solve()
                total_power += dss.meters_register_values()[0]
                total_losses += dss.meters_register_values()[12]

                for harmonic in range(2, 25, 1):
                    dss.text("set mode=harmonic")
                    dss.text(f"set harmonic={harmonic}")
                    dss.solution_solve()
                    dss.text('Sample')
                    total_power += dss.meters_register_values()[0]
                    total_losses += dss.meters_register_values()[12]

            delta_energy_kwh = energy_kwh - total_power
            energy_factor = delta_energy_kwh / energy_kwh
            dss.meters_reset()
            if abs(delta_energy_kwh) < error_kwh:
                break

def update_load(dss: py_dss_interface.DSSDLL, energy_factor):
    dss.loads_first()
    for _ in range(dss.loads_count()):
        dss.loads_write_kw(float(dss.loads_read_kw() * (1 + energy_factor)))
        dss.loads_write_kvar(float(dss.loads_read_kvar() * (1 + energy_factor)))
        dss.loads_next()

script_path = os.path.dirname(os.path.abspath(__file__))

dss_file = str(pathlib.Path(script_path).joinpath("Alimentador", "ckt5", "Master_ckt5.dss"))

dss = py_dss_interface.DSSDLL()

dss.text(f"compile [{dss_file}]")

dss.lines_first()
dss.text(f'New Monitor.M element={dss.cktelement_name()} terminal=1 mode=1 ppolar=no')

dss.text('Redirect Loadshape_P.dss')
dss.text('Redirect Spectrums.dss')
dss.text('Batchedit Load.. pf=0.92')

load_names_list = dss.loads_all_names().copy()
load_kv_list = list()
load_kw_list = list()
load_bus_list = list()
load_pf_list = list()
load_type_list = list()
load_spectrum_list = list()

dss.loads_first()
for _ in range(dss.loads_count()):
    load_kw_list.append(dss.loads_read_kw())
    load_bus_list.append(dss.cktelement_read_bus_names())
    load_pf_list.append(dss.loads_read_pf())

    if 'Res' in dss.loads_read_yearly():
        if dss.loads_read_kw() <= 5:
            if dss.cktelement_read_bus_names()[0].split('.')[1] == '1':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type1_WD_A spectrum=RES-Type1_WD_A_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '2':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type1_WD_B spectrum=RES-Type1_WD_B_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '3':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type1_WD_C spectrum=RES-Type1_WD_C_H0')
        elif dss.loads_read_kw() > 5 and dss.loads_read_kw() <= 10:
            if dss.cktelement_read_bus_names()[0].split('.')[1] == '1':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type2_WD_A spectrum=RES-Type2_WD_A_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '2':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type2_WD_B spectrum=RES-Type2_WD_B_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '3':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type2_WD_C spectrum=RES-Type2_WD_C_H0')
        elif dss.loads_read_kw() > 10:
            if dss.cktelement_read_bus_names()[0].split('.')[1] == '1':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type3_WD_A spectrum=RES-Type3_WD_A_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '2':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type3_WD_B spectrum=RES-Type3_WD_B_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '3':
                dss.text(f'edit {dss.cktelement_name()} daily=RES-Type3_WD_C spectrum=RES-Type3_WD_C_H0')
    elif 'Com' in dss.loads_read_yearly():
        if dss.loads_read_kw() <= 5:
            if dss.cktelement_read_bus_names()[0].split('.')[1] == '1':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type1_WD_A spectrum=COM-Type1_WD_A_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '2':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type1_WD_B spectrum=COM-Type1_WD_B_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '3':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type1_WD_C spectrum=COM-Type1_WD_C_H0')
        elif dss.loads_read_kw() > 5 and dss.loads_read_kw() <= 10:
            if dss.cktelement_read_bus_names()[0].split('.')[1] == '1':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type2_WD_A spectrum=COM-Type2_WD_A_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '2':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type2_WD_B spectrum=COM-Type2_WD_B_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '3':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type2_WD_C spectrum=COM-Type2_WD_C_H0')
        elif dss.loads_read_kw() > 10 and dss.loads_read_kw() <= 15:
            if dss.cktelement_read_bus_names()[0].split('.')[1] == '1':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type3_WD_A spectrum=COM-Type3_WD_A_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '2':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type3_WD_B spectrum=COM-Type3_WD_B_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '3':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type3_WD_C spectrum=COM-Type3_WD_C_H0')
        elif dss.loads_read_kw() > 15:
            if dss.cktelement_read_bus_names()[0].split('.')[1] == '1':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type4_WD_A spectrum=COM-Type3_WD_A_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '2':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type4_WD_B spectrum=COM-Type3_WD_B_H0')
            elif dss.cktelement_read_bus_names()[0].split('.')[1] == '3':
                dss.text(f'edit {dss.cktelement_name()} daily=COM-Type4_WD_C spectrum=COM-Type3_WD_C_H0')

    load_type_list.append(dss.loads_read_daily())
    load_spectrum_list.append(dss.loads_read_spectrum())

    dss.loads_next()

loads_table =pd.DataFrame(list(zip(load_names_list, load_bus_list, load_kw_list, load_pf_list, load_type_list, load_spectrum_list)), columns=['Load Name', 'Bus', 'kW', 'pf', 'Type', 'Spectrum'])
loads_table =loads_table.sort_values(['Bus'])

dss.text('save circuit')

case_list = list()
total_power_list = list()
total_losses_list = list()
percentual_losses_list = list()
percentual_difference_list = list()
note_list = list()

energy_kwh = 200000
error_kwh = 1

dss_file = str(pathlib.Path(script_path).joinpath("Alimentador", "ckt5", "ckt5", "Master.dss"))
dss.text(f"compile [{dss_file}]")

mode = 'fund'
total_power = 0
total_losses = 0
do_energy_allocation(dss, energy_kwh, error_kwh, mode)

dss.text('Set mode=daily')
dss.solution_solve()
dss.text('Plot monitor object=M channels=(1 3 5)')
dss.text('Plot monitor object=M channels=(2 4 6)')

case_list.append('1')
total_power_list.append(total_power)
total_losses_list.append(total_losses)
percentual_losses_list.append(total_losses_list[-1] / total_power_list[-1] * 100)
percentual_difference_list.append('-')
note_list.append('PF=0.92 (Base Case)')

dss.text(f"compile [{dss_file}]")
dss_loadshape_file = str(pathlib.Path(script_path).joinpath("Alimentador", "ckt5", "Loadshape_PQ.dss"))
dss.text(f"redirect [{dss_loadshape_file}]")

mode = 'fund'
do_energy_allocation(dss, energy_kwh, error_kwh, mode)

dss.text('Set mode=daily')
dss.solution_solve()
dss.text('Plot monitor object=M channels=(1 3 5)')
dss.text('Plot monitor object=M channels=(2 4 6)')

case_list.append('2')
total_power_list.append(total_power)
total_losses_list.append(total_losses)
percentual_losses_list.append(total_losses_list[-1] / total_power_list[-1] * 100)
percentual_difference_list.append((percentual_losses_list[-1] / percentual_losses_list[0] - 1) * 100)
note_list.append('Pmult and Qmult')

dss.text(f"compile [{dss_file}]")

mode = 'harm'
do_energy_allocation(dss, energy_kwh, error_kwh, mode)

dss.text('Set mode=daily')
dss.solution_solve()
dss.text('Plot monitor object=M channels=(1 3 5)')
dss.text('Plot monitor object=M channels=(2 4 6)')

case_list.append('3')
total_power_list.append(total_power)
total_losses_list.append(total_losses)
percentual_losses_list.append(total_losses_list[-1] / total_power_list[-1] * 100)
percentual_difference_list.append((percentual_losses_list[-1] / percentual_losses_list[0] - 1) * 100)
note_list.append('Harmonic - %SeriesRL=50')

dss.text(f"compile [{dss_file}]")
dss.text(f"redirect [{dss_loadshape_file}]")

mode = 'harm'
do_energy_allocation(dss, energy_kwh, error_kwh, mode)

dss.text('Set mode=daily')
dss.solution_solve()
dss.text('Plot monitor object=M channels=(1 3 5)')
dss.text('Plot monitor object=M channels=(2 4 6)')

case_list.append('4')
total_power_list.append(total_power)
total_losses_list.append(total_losses)
percentual_losses_list.append(total_losses_list[-1] / total_power_list[-1] * 100)
percentual_difference_list.append((percentual_losses_list[-1] / percentual_losses_list[0] - 1) * 100)
note_list.append('Pmult and Qmult + Harmonic - %SeriesRL=50')

results_table =pd.DataFrame(list(zip(case_list, total_power_list, total_losses_list, percentual_losses_list, percentual_difference_list, note_list)), columns=['Case', 'Total Power (kWh)', 'Total Losses (kWh)', 'Total Losses (%)', 'Percentual Difference (%)', 'Notes'])
results_table.to_csv(fr'{script_path}\Resultados.csv', index=False)

