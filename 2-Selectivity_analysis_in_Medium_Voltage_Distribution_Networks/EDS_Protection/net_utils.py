### Yuri Perim ###

### Módulos ###
import os
import numpy as np
import pandas as pd
import networkx as nx


### Funções auxiliares ###
def get_fuses(obj_dss, dss_file_name, dss_tcc, dss_fuses):
    obj_dss.text(f'compile [{dss_file_name}]')
    obj_dss.text(f'redirect {dss_tcc}')
    obj_dss.text(f'redirect {dss_fuses}')

    pdelt_fuse_dict = {}
    for fuse in obj_dss.fuses_all_names():
        obj_dss.fuses_write_name(fuse)
        obj_dss.circuit_set_active_element(f'fuse.{fuse}')
        pdelt = obj_dss.fuses_read_monitored_obj().lower()
        ctrlelt = obj_dss.dsselement_name().lower()
        monitored_terminal = obj_dss.fuses_read_monitored_term()
        rated_current = float(obj_dss.fuses_read_rated_current())
        tcc_curve = obj_dss.fuses_read_tcc_curve().lower()
        pdelt_fuse_dict[pdelt] = {'name': ctrlelt,
                                  'type': 'fuse',
                                  'monitored_terminal': monitored_terminal,
                                  'settings': {'rated_current': rated_current,
                                               'tcc_curve': tcc_curve}}

    return pdelt_fuse_dict


def get_reclosers(obj_dss, dss_file_name, dss_tcc, dss_reclosers):
    obj_dss.text(f'compile [{dss_file_name}]')
    obj_dss.text(f'redirect {dss_tcc}')
    obj_dss.text(f'redirect {dss_reclosers}')

    pdelt_recloser_dict = {}
    for recloser in obj_dss.reclosers_all_names():
        obj_dss.reclosers_write_name(recloser)
        obj_dss.circuit_set_active_element(f'recloser.{recloser}')
        pdelt = obj_dss.reclosers_read_monitored_obj().lower()
        ctrlelt = obj_dss.dsselement_name().lower()
        monitored_terminal = obj_dss.reclosers_read_monitored_term()
        property_names = obj_dss.dsselement_all_property_names()
        phase_trip = float(obj_dss.reclosers_read_phase_trip())
        phase_tcc_curve_idx = property_names.index('PhaseDelayed') + 1
        phase_tcc_curve = obj_dss.dssproperties_read_value(str(phase_tcc_curve_idx)).lower()
        phase_time_dial_idx = property_names.index('TDPhDelayed') + 1
        phase_time_dial = float(obj_dss.dssproperties_read_value(str(phase_time_dial_idx)))
        ground_trip = float(obj_dss.reclosers_read_ground_trip())
        ground_tcc_curve_idx = property_names.index('GroundDelayed') + 1
        ground_tcc_curve = obj_dss.dssproperties_read_value(str(ground_tcc_curve_idx)).lower()
        ground_time_dial_idx = property_names.index('TDGrDelayed') + 1
        ground_time_dial = float(obj_dss.dssproperties_read_value(str(ground_time_dial_idx)))
        pdelt_recloser_dict[pdelt] = {'name': ctrlelt,
                                      'type': 'recloser',
                                      'monitored_terminal': monitored_terminal,
                                      'settings': {'phase_trip': phase_trip,
                                                   'phase_tcc_curve': phase_tcc_curve,
                                                   'phase_time_dial': phase_time_dial,
                                                   'ground_trip': ground_trip,
                                                   'ground_tcc_curve': ground_tcc_curve,
                                                   'ground_time_dial': ground_time_dial}}

    return pdelt_recloser_dict


### Grafos ###
def ckt_build_graph(obj_dss, dss_file_name):
    # Circuito
    obj_dss.text(f'compile [{dss_file_name}]')
    obj_dss.text('makebuslist')

    # Matriz de incidência
    obj_dss.text('calcincmatrix_o')
    obj_dss.text('export incmatrix')
    obj_dss.text('export incmatrixrows')
    obj_dss.text('export incmatrixcols')

    dir_name = os.path.dirname(dss_file_name)
    circuit_name = obj_dss.circuit_name()
    incmatrix = os.path.join(dir_name, f'{circuit_name}_Inc_Matrix.csv')
    df = pd.read_csv(incmatrix)
    incmatrixrows = os.path.join(dir_name, f'{circuit_name}_Inc_Matrix_Rows.csv')
    rows = np.loadtxt(incmatrixrows, dtype='object', skiprows=1)
    incmatrixcols = os.path.join(dir_name, f'{circuit_name}_Inc_Matrix_Cols.csv')
    cols = np.loadtxt(incmatrixcols, dtype='object', skiprows=1)

    # Lista de arcos
    edge_list = pd.merge(df[df['Value'] == 1], df[df['Value'] == -1], how='inner', on='Row', suffixes=('_src', '_dst'))
    edge_list = edge_list[['Row', 'Col_src', 'Col_dst']]
    rows_dict = {i: row for i, row in enumerate(rows)}
    cols_dict = {i: col for i, col in enumerate(cols)}
    edge_list.replace(to_replace={'Row': rows_dict, 'Col_src': cols_dict, 'Col_dst': cols_dict}, inplace=True)

    # Grafo
    G = nx.DiGraph()
    for edge in edge_list.itertuples(index=False):
        G.add_edge(edge.Col_src, edge.Col_dst, pdelt=edge.Row.lower())

    return G


def prot_build_graph(G, pdelt_ctrlelt_dict):
    P = nx.DiGraph()
    end_buses = [bus for bus in G.nodes() if (G.in_degree(bus) == 1 and G.out_degree(bus) == 0)]
    for end_bus in end_buses:
        actual_bus = end_bus
        opt_flag = True
        stack = set()
        while actual_bus != 'sourcebus' and opt_flag:
            upstream_bus = set(G.predecessors(actual_bus)).pop()
            actual_edge = G.get_edge_data(upstream_bus, actual_bus)['pdelt']
            if actual_edge in pdelt_ctrlelt_dict.keys():
                src = pdelt_ctrlelt_dict[actual_edge]['name']
                if stack:
                    dst = stack.pop()
                    prot_edge = (src, dst)
                    if prot_edge in P.edges():
                        opt_flag = False
                    else:
                        P.add_node(src, pdelt=actual_edge, sc_bus=actual_bus)
                        P.add_edge(*prot_edge)
                    dst = src
                else:
                    dst = src
                    P.add_node(dst, pdelt=actual_edge, sc_bus=actual_bus)
                stack.add(dst)
            actual_bus = upstream_bus

    return P
