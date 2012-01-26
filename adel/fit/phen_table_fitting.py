# -*- coding: latin-1 -*-
'''
This module provides functions to calculate PhenTable values.

Created on 28 nov. 2011

@author: cchambon
'''

import numpy
import pandas

def create_id_phen_list(id_phen_from_axis_table_list):
    '''
    Create list of id_phen.
    :Parameters:
        - `id_phen_from_axis_table_list` : the id_phen list from axis table.
    :Types:
        - `id_phen_from_axis_table_list` : list
        
    :return: The new completed id_phen list.
    :rtype: list
    '''
    id_phen_set = set(id_phen_from_axis_table_list)
    id_phen_list = []
    for id_phen in id_phen_set:
        N_phyt = int(id_phen[-2:])
        for i in range(N_phyt + 1):
            id_phen_list.append(id_phen)
    id_phen_list.sort()
    return id_phen_list


def create_index_rel_phytomer_list(id_phen_list):
    '''
    Create list of index_rel_phytomer.
    :Parameters:
        - `id_phen_list` : the id_phen list.
    :Types:
        - `id_phen_list` : list
        
    :return: The index_rel_phytomer list.
    :rtype: list
    '''
    index_rel_phytomer_list = []
    i = 0
    while i < len(id_phen_list):
        N_phyt = id_phen_list[i][-2:]
        N_phyt_float = float(N_phyt)
        for j in range(int(N_phyt) + 1):
            index_rel_phytomer_list.append(j / N_phyt_float)    
        i = i + j + 1
    return index_rel_phytomer_list


def create_TT_col_phytomer_list(TT_parameters_dataframe, flowering_dTT_dataframe, calculation_method='linear'):
    '''
    Create list of TT_col_phytomer. TT_parameters_dataframe may be not completely filled, in which case the missing observations will be fitted. 
    See the documentation for more information about the observations which have to be specified, and the ones which can be missing.  
    :Parameters:
        - `TT_parameters_dataframe` : A table of parameters with the following headers: 
            * id_phen: The identifier made from concatenation of cohort number and N_phyt. This column is ordered in descending order and contains no duplicate.
            * a_cohort: The slope of phytomer emergence. This parameter has to be specified for (at least) the first dataframe row. 
            * TT_col_0: The Thermal Time for Haun Stage equal to 0. This parameter has to be specified for (at least) the first dataframe row. 
                       Hypothesis: Same cohort axes have the same emergence date. Thus, for each cohort, only the first observation 
                       has to be filled. Filling several observations for the same cohort is unexpected. 
            * TT_HS_break: The Thermal Time when the slope of phytomers emergence is changing. This parameter has to be specified for (at 
                           least) the first dataframe row. 
                           For each following row, if this parameter is unspecified, then the value of the preceding row is used.
                           This parameter is needed only for 'bilinear' calculation method.
            * TT_HS_NFF: The Thermal Time for Haun Stage equal to the total number of vegetative phytomers formed on an axis.
                         This parameter has to be specified for (at least) the first dataframe row.
        - `flowering_dTT_dataframe` : A table of parameters with the following headers: 
            * id_phen: The identifier made from concatenation of cohort number and N_phyt. This column contains only identifiers for 
            which the N_phyt is the most frequent in the AxisTable. This column is ordered in descending order and contains no duplicate.
            * dTT_flo_MS: The thermal time delta between the main stem flowering and current raw tiller flowering. 
        - `calculation_method` : The type of the method used for the calculation. Can be either 'linear' or 'bilinear'.
    :Types:
        - `TT_parameters_dataframe` : pandas.DataFrame
        - `flowering_dTT_dataframe` : pandas.DataFrame
        - `calculation_method` : str
        
    :return: The TT_col_phytomer list.
    :rtype: list
    '''
    assert calculation_method in ('linear', 'bilinear')
    # Fill TT_parameters_dataframe['a_cohort]. 
    # --> The user fills at least one row for the main stem (i.e. 'a_cohort', 'TT_col_0', 'TT_HS_break', 'TT_HS_NFF')
    # The a_cohort value is always specified for the first row. --> wrong
    # For each following row, propagate last valid value forward to next valid. --> wrong
    # 
    TT_parameters_dataframe['a_cohort'] = TT_parameters_dataframe['a_cohort'].fillna()
    # Fill TT_parameters_dataframe['TT_col_0].
    # The TT_col_0 value is always specified for the first row and same cohort axes have the same emergence date. --> wrong
    TT_parameters_dataframe['cohort_number'] = TT_parameters_dataframe['id_phen'].astype(str)
    TT_parameters_grouped_dataframe = TT_parameters_dataframe.groupby('cohort_number')
    for name, group in TT_parameters_grouped_dataframe:
        if name == '1':
            # It's the main stems (i.e. the first cohort axes): propagate last valid value forward to next valid.
            filled_group = group['TT_col_0'].fillna()
            TT_parameters_dataframe['TT_col_0'] = TT_parameters_dataframe['TT_col_0'].combine_first(filled_group)
        else:
            # It's a secondary cohort: TT_col_0 is identical whatever N_phyt value.
            current_cohort = float(name)
            current_a_cohort = group['a_cohort'][0]
            main_stem_TT_col_0 = TT_parameters_grouped_dataframe.get_group('1')['TT_col_0'][0]
            current_cohort_TT_col_0 = main_stem_TT_col_0 + (current_cohort - (1.6 * current_a_cohort)) / current_a_cohort # TODO: check with Mariem that it's the good equation.
            filled_group = group['TT_col_0'].fillna(current_cohort_TT_col_0)
            TT_parameters_dataframe['TT_col_0'] = TT_parameters_dataframe['TT_col_0'].combine_first(filled_group)
    # Fill TT_parameters_dataframe['TT_HS_break']. 
    # The TT_HS_break value is always specified for the first row. -> wrong
    # For each following row, propagate last valid value forward to next valid. -> wrong
    TT_parameters_dataframe['TT_HS_break'] = TT_parameters_dataframe['TT_HS_break'].fillna()
    # Fill TT_parameters_dataframe['TT_HS_NFF']. 
    # The TT_HS_NFF value is always specified for the first row.
    flowering_dTT_dataframe['cohort_number'] = flowering_dTT_dataframe['id_phen'].astype(str)
    flowering_dTT_grouped_dataframe = flowering_dTT_dataframe.groupby('cohort_number')
    for name, group in TT_parameters_grouped_dataframe:
        if name == '1':
            # It's the main stems (i.e. the first cohort axes).
            for i in group.index[1:]:
                preceding_main_stem_TT_HS_NFF = group['TT_HS_NFF'][i-1]
                current_a_cohort = group['a_cohort'][i]
                group['TT_HS_NFF'][i] = preceding_main_stem_TT_HS_NFF + 1.0 / (4 * current_a_cohort)
        else:
            # It's a secondary cohort.
            for i in group.index:
                main_stem_TT_HS_NFF = TT_parameters_grouped_dataframe.get_group('1')['TT_HS_NFF'][0] # TODO: check with Mariem that it's 0.
                current_flowering_dTT = flowering_dTT_grouped_dataframe.get_group(name)['dTT_flo_MS'][0]
                group['TT_HS_NFF'][i] = main_stem_TT_HS_NFF + current_flowering_dTT
        TT_parameters_dataframe['TT_HS_NFF'] = TT_parameters_dataframe['TT_HS_NFF'].combine_first(group['TT_HS_NFF'])
        
    TT_col_phytomer_list = []
    if calculation_method == 'linear':
        for i in TT_parameters_dataframe.index:
            TT_col_0_i = TT_parameters_dataframe['TT_col_0'][i]
            a_cohort_i = TT_parameters_dataframe['a_cohort'][i]
            phytomer_indexes = range(int(str(int(TT_parameters_dataframe['id_phen'][i]))[-2:]) + 1)
            for j in phytomer_indexes:
                TT_col_phytomer_i_j = TT_col_0_i + j / a_cohort_i
                TT_col_phytomer_list.append(TT_col_phytomer_i_j)
    else: # bilinear calculation method
        for i in TT_parameters_dataframe.index:
            a_cohort_i = TT_parameters_dataframe['a_cohort'][i]
            TT_HS_break_i = TT_parameters_dataframe['TT_HS_break'][i]
            TT_col_0_i = TT_parameters_dataframe['TT_col_0'][i]
            HS_break_i = a_cohort_i * (TT_HS_break_i - TT_col_0_i)
            N_phyt_i = int(str(int(TT_parameters_dataframe['id_phen'][i]))[-2:])
            TT_HS_NFF_i = TT_parameters_dataframe['TT_HS_NFF'][i]
            b_cohort_i = (N_phyt_i - HS_break_i) / (TT_HS_NFF_i - TT_HS_break_i)
            phytomer_indexes = range(N_phyt_i + 1)
            for j in phytomer_indexes: 
                if j <= HS_break_i:
                    TT_col_phytomer_i_j = TT_col_0_i + j / a_cohort_i
                else:
                    TT_col_phytomer_i_j = TT_HS_break_i + (j - HS_break_i) / b_cohort_i
                TT_col_phytomer_list.append(TT_col_phytomer_i_j)
    
    # clean TT_parameters_dataframe and flowering_dTT_dataframe
    TT_parameters_dataframe.pop('cohort_number')
    flowering_dTT_dataframe.pop('cohort_number')    
    
    return TT_col_phytomer_list
    
    
def find_most_frequent_id_phen_list(id_phen_from_axis_table_list):
    '''
    Find the most frequent id_phen identifier of each cohort.
    :Parameters:
        - `id_phen_from_axis_table_list` : the id_phen identifiers from AxisTable.
    :Types:
        - `id_phen_from_axis_table_list` : list
        
    :return: The most frequent id_phen identifiers.
    :rtype: list
    '''
    id_phen_set = set(id_phen_from_axis_table_list)
    id_phen_dict = dict([(id_phen[:-2], []) for id_phen in id_phen_set])
    for id_phen in id_phen_set:
        cohort_number = id_phen[:-2]
        number_of_occurrences_of_id_phen = id_phen_from_axis_table_list.count(id_phen)
        N_phyt_of_current_cohort = id_phen[-2:]
        id_phen_dict[cohort_number].append((number_of_occurrences_of_id_phen, N_phyt_of_current_cohort))
    most_frequent_id_phen_list = []
    for cohort_number, N_phyt_occurrences in id_phen_dict.items():
        N_phyt_occurrences.sort()
        most_frequent_id_phen_list.append(''.join([cohort_number, N_phyt_occurrences[-1][1]]))
    most_frequent_id_phen_list.sort()
    return most_frequent_id_phen_list


if __name__ == "__main__":

    ''' ToDo � lire directemenet � partir de la table axe_Table '''        
    id_phen_from_axis_table_list = ['111' , '409' , '507' , '608' , '607' , '111' , '408' , '508' , '607' , '111' , '408' , '508' , '607' , '607' , '110' , '407' , '507' , '606' , '606' , '705' , '111' , '409' , '507' , '607' , '607' , '111' , '408' , '507' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '110' , '407' , '507' , '606' , '606' , '705' , '111' , '408' , '507' , '607' , '111' , '408' , '507' , '607' , '607' , '111' , '508' , '607' , '111' , '408' , '508' , '607' , '608' , '707' , '111' , '409' , '507' , '607' , '607' , '706' , '110' , '407' , '506' , '606' , '110' , '506' , '606' , '111' , '408' , '508' , '607' , '608' , '111' , '408' , '507' , '607' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '508' , '607' , '706' , '111' , '408' , '507' , '607' , '111' , '408' , '508' , '607' , '111' , '408' , '508' , '607' , '111' , '408' , '508' , '706' , '111' , '508' , '607' , '111' , '408' , '508' , '111' , '409' , '507' , '607' , '607' , '706' , '110' , '408' , '507' , '606' , '111' , '507' , '607' , '111' , '408' , '507' , '607' , '607' , '112' , '409' , '508' , '608' , '608' , '707' , '110' , '407' , '507' , '606' , '606' , '110' , '408' , '506' , '606' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '507' , '607' , '607' , '111' , '507' , '607' , '111' , '408' , '508' , '607' , '111' , '507' , '607' , '707' , '110' , '407' , '507' , '606' , '606' , '706' , '111' , '408' , '507' , '111' , '408' , '507' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '110' , '407' , '506' , '606' , '111' , '408' , '507' , '607' , '607' , '110' , '407' , '506' , '606' , '606' , '112' , '409' , '608' , '608' , '111' , '507' , '607' , '111' , '408' , '507' , '607' , '110' , '407' , '507' , '606' , '606' , '110' , '407' , '507' , '606' , '606' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '508' , '607' , '111' , '408' , '508' , '607' , '607' , '111' , '409' , '508' , '607' , '607' , '111' , '408' , '507' , '607' , '110' , '407' , '506' , '606' , '606' , '111' , '409' , '508' , '607' , '607' , '111' , '408' , '508' , '607' , '706' , '111' , '408' , '507' , '608' , '607' , '111' , '408' , '507' , '608' , '111' , '409' , '507' , '607' , '111' , '409' , '508' , '607' , '607' , '707' , '111' , '408' , '508' , '607' , '607' , '110' , '407' , '507' , '606' , '111' , '408' , '508' , '607' , '111' , '408' , '507' , '607' , '607' , '707' , '111' , '408' , '508' , '607' , '111' , '408' , '507' , '607' , '607' , '706' , '111' , '408' , '507' , '607' , '111' , '408' , '507' , '607' , '111' , '408' , '507' , '607' , '607' , '706' , '111' , '409' , '508' , '607' , '707' , '110' , '407' , '507' , '606' , '606' , '111' , '408' , '508' , '607' , '111' , '408' , '508' , '607' , '607' , '110' , '407' , '506' , '606' , '606' , '111' , '408' , '508' , '607' , '607' , '111' , '409' , '507' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '706' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '507' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '110' , '408' , '506' , '606' , '606' , '110' , '407' , '507' , '606' , '111' , '409' , '508' , '607' , '607' , '111' , '408' , '507' , '607' , '707' , '111' , '408' , '507' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '110' , '407' , '507' , '606' , '606' , '706' , '111' , '409' , '507' , '607' , '111' , '408' , '507' , '607' , '707' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '508' , '607' , '607' , '111' , '408' , '507' , '607' , '607' , '111' , '408' , '508' , '607' , '111' , '507' , '608' , '111' , '409' , '508' , '607' , '607' , '110' , '407' , '507' , '606' , '606' , '111' , '508' ]

    id_phen_list = create_id_phen_list(id_phen_from_axis_table_list)

    index_rel_phytomer_list = create_index_rel_phytomer_list(id_phen_list)
    
    # prepare the minimum parameters for TT_col_phytomer_list creation
    id_phen_without_duplicate_list = list(set(id_phen_list))
    id_phen_without_duplicate_list.sort()
    
    a_cohort_list = [numpy.nan for i in range(len(id_phen_without_duplicate_list) - 1)]
    a_cohort_list.insert(0, 0.0102)
	
    TT_col_0_list = [numpy.nan for i in range(len(id_phen_without_duplicate_list) - 1)]
    TT_col_0_list.insert(0, 0.0)
	
    TT_HS_break_list = [numpy.nan for i in range(len(id_phen_without_duplicate_list) - 1)]
    TT_HS_break_list.insert(0, 588.0)
	
    TT_HS_NFF_list = [numpy.nan for i in range(len(id_phen_without_duplicate_list) - 1)]
    TT_HS_NFF_list.insert(0, 1078.0)
	
    TT_parameters_array = numpy.array([id_phen_without_duplicate_list, a_cohort_list, TT_col_0_list, TT_HS_break_list, TT_HS_NFF_list]).transpose()
	
    TT_parameters_dataframe = pandas.DataFrame(TT_parameters_array, columns=['id_phen', 'a_cohort', 'TT_col_0', 'TT_HS_break', 'TT_HS_NFF'], dtype=float)
	
    most_frequent_id_phen_list = find_most_frequent_id_phen_list(id_phen_from_axis_table_list)
	
    dTT_flo_MS_list = [i * 7.0 for i in range(1, len(most_frequent_id_phen_list) + 1)] # ??? c'est quoi (i*7.0)
	
    flowering_dTT_array = numpy.array([most_frequent_id_phen_list, dTT_flo_MS_list]).transpose()
    flowering_dTT_dataframe = pandas.DataFrame(flowering_dTT_array, columns=['id_phen', 'dTT_flo_MS'], dtype=float)
    # create TT_col_phytomer_list with linear calculation method
    TT_col_phytomer_linear_list = create_TT_col_phytomer_list(TT_parameters_dataframe, flowering_dTT_dataframe, calculation_method='linear')
    # create TT_col_phytomer_list with bilinear calculation method
    TT_col_phytomer_bilinear_list = create_TT_col_phytomer_list(TT_parameters_dataframe, flowering_dTT_dataframe, calculation_method='bilinear')
    
    phen_table_linear_array = numpy.array([id_phen_list, index_rel_phytomer_list, TT_col_phytomer_linear_list]).transpose()
    phen_table_linear_dataframe = pandas.DataFrame(phen_table_linear_array, columns=['id_phen', 'index_rel_phytomer', 'TT_col_phytomer'])
    
    phen_table_bilinear_array = numpy.array([id_phen_list, index_rel_phytomer_list, TT_col_phytomer_bilinear_list]).transpose()
    phen_table_bilinear_dataframe = pandas.DataFrame(phen_table_bilinear_array, columns=['id_phen', 'index_rel_phytomer', 'TT_col_phytomer'])
    
    import tempfile
    from openalea.core.path import path
    fitting_results_directory = path(tempfile.mkdtemp(suffix='_fitting_results'))
    
    TT_parameters_filepath = fitting_results_directory/'TT_parameters.csv'
    TT_parameters_dataframe.to_csv(TT_parameters_filepath, na_rep='NA', index=False)
    
    flowering_dTT_filepath = fitting_results_directory/'flowering_dTT.csv'
    flowering_dTT_dataframe.to_csv(flowering_dTT_filepath, na_rep='NA', index=False)
    
    phen_table_linear_filepath = fitting_results_directory/'phen_table_linear.csv'
    phen_table_linear_dataframe.to_csv(phen_table_linear_filepath, na_rep='NA', index=False)
    
    phen_table_bilinear_filepath = fitting_results_directory/'phen_table_bilinear.csv'
    phen_table_bilinear_dataframe.to_csv(phen_table_bilinear_filepath, na_rep='NA', index=False)
    
    print 'The results has been saved in %s' % fitting_results_directory
    
    import os
    os.system("start %s" % TT_parameters_filepath.abspath())
    os.system("start %s" % flowering_dTT_filepath.abspath())
    os.system("start %s" % phen_table_linear_filepath.abspath())
    os.system("start %s" % phen_table_bilinear_filepath.abspath())
    


