### Yuri Perim ###

### Módulos ###
import numpy as np
from scipy.interpolate import interp1d


### Funções auxiliares ###
def get_tcc_curves(obj_dss, dss_file_name, dss_tcc):
    obj_dss.text(f'compile [{dss_file_name}]')
    obj_dss.text(f'redirect {dss_tcc}')
    obj_dss.circuit_set_active_class('tcc_curve')

    tcc_dict = {}
    for tcc_curve in obj_dss.active_class_all_names():
        c_array = np.array(obj_dss.text(f'? tcc_curve.{tcc_curve}.c_array').strip('[ ]').split(), dtype=float)
        t_array = np.array(obj_dss.text(f'? tcc_curve.{tcc_curve}.t_array').strip('[ ]').split(), dtype=float)
        tcc_dict[tcc_curve.lower()] = {'c_array': c_array,
                                       't_array': t_array}

    return tcc_dict


def get_ctrlelt_tcc_func(prot_node_dict, pdelt_ctrlelt_dict, tcc_dict):
    ctrlelt = set(prot_node_dict.keys()).pop()
    pdelt = prot_node_dict[ctrlelt]['pdelt']

    ctrlelt_type = pdelt_ctrlelt_dict[pdelt]['type']
    if ctrlelt_type == 'fuse':
        rated_current = pdelt_ctrlelt_dict[pdelt]['settings']['rated_current']
        tcc_curve = pdelt_ctrlelt_dict[pdelt]['settings']['tcc_curve']

        c_array_log = np.log10(rated_current * tcc_dict[tcc_curve]['c_array'])
        t_array_log = np.log10(tcc_dict[tcc_curve]['t_array'])
        tcc_func = interp1d(c_array_log, t_array_log, kind='cubic', bounds_error=False, fill_value=np.Inf)
        ph_tcc_func_aux = tcc_func
        gr_tcc_func_aux = tcc_func
    elif ctrlelt_type == 'recloser':
        phase_trip = pdelt_ctrlelt_dict[pdelt]['settings']['phase_trip']
        phase_tcc_curve = pdelt_ctrlelt_dict[pdelt]['settings']['phase_tcc_curve']
        phase_time_dial = pdelt_ctrlelt_dict[pdelt]['settings']['phase_time_dial']

        ph_c_array_log = np.log10(phase_trip * tcc_dict[phase_tcc_curve]['c_array'])
        ph_t_array_log = np.log10(phase_time_dial * tcc_dict[phase_tcc_curve]['t_array'])
        ph_tcc_func_aux = interp1d(ph_c_array_log, ph_t_array_log, kind='cubic', bounds_error=False, fill_value=np.Inf)

        ground_trip = pdelt_ctrlelt_dict[pdelt]['settings']['ground_trip']
        ground_tcc_curve = pdelt_ctrlelt_dict[pdelt]['settings']['ground_tcc_curve']
        ground_time_dial = pdelt_ctrlelt_dict[pdelt]['settings']['ground_time_dial']

        gr_c_array_log = np.log10(ground_trip * tcc_dict[ground_tcc_curve]['c_array'])
        gr_t_array_log = np.log10(ground_time_dial * tcc_dict[ground_tcc_curve]['t_array'])
        gr_tcc_func_aux = interp1d(gr_c_array_log, gr_t_array_log, kind='cubic', bounds_error=False, fill_value=np.Inf)

    ph_tcc_func = lambda x: 10 ** ph_tcc_func_aux(np.log10(x))
    gr_tcc_func = lambda x: 10 ** gr_tcc_func_aux(np.log10(x))

    return ph_tcc_func, gr_tcc_func


### Tempo ###
def compute_time(prot_node_dict, pdelt_ctrlelt_dict, tcc_dict, elt_currents_dict):
    ph_tcc_func, gr_tcc_func = get_ctrlelt_tcc_func(prot_node_dict, pdelt_ctrlelt_dict, tcc_dict)

    ctrlelt = set(prot_node_dict.keys()).pop()
    pdelt = prot_node_dict[ctrlelt]['pdelt']

    monitored_terminal = pdelt_ctrlelt_dict[pdelt]['monitored_terminal']
    ph_current = max([mag for cond, (mag, _) in elt_currents_dict[monitored_terminal].items() if isinstance(cond, int)])
    ne_calc_current = elt_currents_dict[monitored_terminal]['ne_calc'][0]

    return sorted([(ph_current, ph_tcc_func(ph_current)), (ne_calc_current, gr_tcc_func(ne_calc_current))], key=lambda x: x[1], reverse=False)[0]
