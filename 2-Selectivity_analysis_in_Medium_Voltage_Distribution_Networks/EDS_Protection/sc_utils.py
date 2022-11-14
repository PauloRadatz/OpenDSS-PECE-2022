### Yuri Perim ###

### Módulos ###
import math


### Funções auxiliares ###
def to_eng(real, imag):
    mag = math.sqrt((real ** 2) + (imag ** 2))
    phase = math.degrees(math.atan2(imag, real))

    return mag, phase


### Fluxo ###
def pf_sim(obj_dss, dss_file_name, volt_list, max_iter=15):
    obj_dss.text(f'compile [{dss_file_name}]')
    obj_dss.text(f'set voltagebases={str(volt_list)}')
    obj_dss.text('calcvoltagebases')
    obj_dss.text('set mode=snapshot')
    obj_dss.text('set controlmode=static')
    obj_dss.text(f'set maxiterations={max_iter}')
    obj_dss.text('solve')


### Curto ###
def sc_elt(obj_dss, bus_name='sourcebus', sc_type='1111'):
    obj_dss.text('makebuslist')
    obj_dss.circuit_set_active_bus(bus_name)
    bus_nodes = obj_dss.bus_nodes()
    for swt_idx, node in enumerate(bus_nodes, start=0):
        swt_status = False if sc_type[swt_idx] == '0' else True
        obj_dss.text(f'new fault.FE_{node}N bus1={bus_name}.{node} bus2=FAULT_NEUTRAL.4 phases=1 enabled={swt_status}')
    swt_status = False if sc_type[-1] == '0' else True
    obj_dss.text(f'new fault.FE_NG bus1=FAULT_NEUTRAL.4 bus2=FAULT_NEUTRAL.0 phases=1 enabled={swt_status}')


def sc_sim(obj_dss, dss_file_name, bus_name, sc_type, volt_list, max_iter=15):
    obj_dss.text(f'compile [{dss_file_name}]')
    obj_dss.text('batchedit load..* enabled=False')
    obj_dss.text('batchedit capacitor..* enabled=False')
    sc_elt(obj_dss, bus_name=bus_name, sc_type=sc_type)
    obj_dss.text(f'set voltagebases={str(volt_list)}')
    obj_dss.text('calcvoltagebases')
    obj_dss.text('set mode=snapshot')
    obj_dss.text('set controlmode=off')
    obj_dss.text(f'set maxiterations={max_iter}')
    obj_dss.text('solve')


def fs_sim(obj_dss, dss_file_name, volt_list):
    obj_dss.text(f'compile [{dss_file_name}]')
    obj_dss.text('batchedit load..* enabled=False')
    obj_dss.text('batchedit capacitor..* enabled=False')
    obj_dss.text(f'set voltagebases={str(volt_list)}')
    obj_dss.text('calcvoltagebases')
    obj_dss.text('set mode=faultstudy')
    obj_dss.text('solve')


### Resultados ###
def get_voltages(obj_dss):
    all_nodes = obj_dss.circuit_all_node_names()
    all_voltages = obj_dss.circuit_all_bus_volts()
    all_voltages_pol = [to_eng(all_voltages[i], all_voltages[i + 1]) for i in range(0, len(all_voltages), 2)]
    all_voltages_dict = {key: value for key, value in zip(all_nodes, all_voltages_pol)}

    return all_voltages_dict


def get_elt_currents(obj_dss, elt):
    obj_dss.circuit_set_active_element(elt)
    elt_class = obj_dss.active_class_get_class_name().lower()
    elt_currents_dict = {}
    if elt_class in ['line']:
        elt_num_phases = obj_dss.cktelement_num_phases()
        mid = 2 * elt_num_phases

        elt_currents_pol = obj_dss.cktelement_currents_mag_ang()
        elt_currents_dict[1] = {(i + 1): (elt_currents_pol[2 * i], elt_currents_pol[2 * i + 1]) for i in range(elt_num_phases)}
        elt_currents_dict[2] = {(i + 1): (elt_currents_pol[mid + 2 * i], elt_currents_pol[mid + 2 * i + 1]) for i in range(elt_num_phases)}

        elt_currents_cplx = obj_dss.cktelement_currents()
        elt_currents_dict[1]['ne_calc'] = to_eng(sum(elt_currents_cplx[:mid:2]), sum(elt_currents_cplx[1:mid:2]))
        elt_currents_dict[2]['ne_calc'] = to_eng(sum(elt_currents_cplx[mid::2]), sum(elt_currents_cplx[(mid + 1)::2]))

    return elt_currents_dict
