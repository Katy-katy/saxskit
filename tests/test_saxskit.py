from __future__ import print_function
import os
import glob
from collections import OrderedDict

import numpy as np

from saxskit import saxs_math, saxs_fit, saxs_classify, saxs_regression

def test_guinier_porod():
    qvals = np.arange(0.01,1.,0.01)
    Ivals = saxs_math.guinier_porod(qvals,20,4,120)
    assert isinstance(Ivals,np.ndarray)

def test_spherical_normal_saxs():
    qvals = np.arange(0.01,1.,0.01)
    Ivals = saxs_math.spherical_normal_saxs(qvals,20,0.2)
    assert isinstance(Ivals,np.ndarray)
    Ivals = saxs_math.spherical_normal_saxs(qvals,20,0.)
    assert isinstance(Ivals,np.ndarray)

def test_profile_spectrum():
    datapath = os.path.join(os.path.dirname(__file__),
        'test_data','solution_saxs','precursors','precursors_0.csv')
    test_data = open(datapath,'r')
    q_I_gp = np.loadtxt(test_data,dtype=float,delimiter=',')
    prof = saxs_math.profile_spectrum(q_I_gp)
    gp_prof = saxs_math.guinier_porod_profile(q_I_gp)

    datapath = os.path.join(os.path.dirname(__file__),
        'test_data','solution_saxs','spheres','spheres_0.csv')
    test_data = open(datapath,'r')
    q_I_sph = np.loadtxt(test_data,dtype=float,delimiter=',')
    prof = saxs_math.profile_spectrum(q_I_sph)
    sph_prof = saxs_math.spherical_normal_profile(q_I_sph)
    #assert isinstance(prof,dict)

    pops = OrderedDict.fromkeys(saxs_math.population_keys)
    pops.update(dict(guinier_porod=1,spherical_normal=1))
    I_tot = q_I_gp[:,1] + q_I_sph[:,1]
    q_I_tot = np.vstack([q_I_gp[:,1],I_tot]).T
    sxf = saxs_fit.SaxsFitter(q_I_tot,pops)
    print('Initial fit ...')
    params,rpt = sxf.fit()
    print('MC anneal ...')
    better_params,last_params,rpt = sxf.MC_anneal_fit(params,0.01,100,0.2)
    print('Final fit ...')
    final_params,rpt = sxf.fit(better_params)
    print('Population-specific profiling ...')
    pop_profs = saxs_math.population_profiles(q_I_tot,pops,better_params)

def test_classifier():
    model_file_path = os.path.join(os.getcwd(),'saxskit','modeling_data','models_test.yml')
    sxc = saxs_classify.SaxsClassifier(model_file_path)
    for data_type in ['precursors','spheres']:
        data_path = os.path.join(os.getcwd(),'tests','test_data','solution_saxs',data_type)
        data_files = glob.glob(os.path.join(data_path,'*.csv'))
        for fpath in data_files:
            print('testing classifier on {}'.format(fpath))
            q_I = np.loadtxt(fpath,delimiter=',')
            prof = saxs_math.profile_spectrum(q_I)
            pops = sxc.run_classifier(prof)
            if data_type == 'spheres':
                sph_prof = saxs_math.spherical_normal_profile(q_I)
            if data_type == 'precursors':
                gp_prof = saxs_math.guinier_porod_profile(q_I)
            for pk,pop in pops.items():
                print('\t{} populations: {} ({} certainty)'.format(pk,pop[0],pop[1]))

# TODO: next, test_regressions()

