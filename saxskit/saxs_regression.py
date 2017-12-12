from collections import OrderedDict
from sklearn import preprocessing,linear_model
import yaml
import os
import numpy as np

from . import saxs_math

class SaxsRegressor(object):
    """A set of regression models to be used on SAXS spectra"""

    def __init__(self,yml_file=None):
        if yml_file is None:
            p = os.path.abspath(__file__)
            d = os.path.dirname(p)
            yml_file = os.path.join(d,'modeling_data','scalers_and_models_regression.yml')

        s_and_m_file = open(yml_file,'rb')
        s_and_m = yaml.load(s_and_m_file)

        reg_models_dict = s_and_m['models']
        scalers_dict = s_and_m['scalers']

        self.models = OrderedDict.fromkeys(saxs_math.parameter_keys)
        self.scalers = OrderedDict.fromkeys(saxs_math.parameter_keys)
        reg_models = reg_models_dict.keys()
        for model_name in reg_models:
            model_params = reg_models_dict[model_name]
            scaler_params = scalers_dict[model_name]
            if scaler_params is not None:
                s = preprocessing.StandardScaler()
                self.set_param(s,scaler_params)
                m = linear_model.SGDRegressor()
                self.set_param(m,model_params)
            self.models[model_name] = m
            self.scalers[model_name] = s

    # helper function - to set parametrs for scalers and models
    def set_param(self, m_s, param):
        for k, v in param.items():
            if isinstance(v, list):
                setattr(m_s, k, np.array(v))
            else:
                setattr(m_s, k, v)

    def predict_params(self,populations,features, q_I):
        """Apply self.models and self.scalers to features.

        Parameters
        ----------
        features : dictionary
            dictionary of features and their values of a test sample

        Returns
        -------
        flags : dict
            dictionary of with predicted parameters
        """
        features = np.array(list(features.values())).reshape(1,-1)
        flags = OrderedDict.fromkeys(saxs_math.parameter_keys)
        if populations['unidentified'][0] == 1:
            return flags # all flags are "None"

        if populations['spherical_normal'][0] == 1:
            if self.scalers['r0_sphere'] != None:
                x_bd = self.scalers['r0_sphere'].transform(features)
                f_bd = self.models['r0_sphere'].predict(x_bd)
                flags['r0_sphere'] = f_bd

            if self.scalers['sigma_sphere'] != None:
                additional_features = saxs_math.spherical_normal_profile(q_I)
                additional_features = np.array(list(additional_features.values())).reshape(1,-1)
                ss_features = np.append(features, additional_features)
                x_bd = self.scalers['sigma_sphere'].transform(ss_features.reshape(1, -1))
                f_bd = self.models['sigma_sphere'].predict(x_bd)
                flags['sigma_sphere'] = f_bd


        if populations['guinier_porod'][0] == 1:
            if self.scalers['rg_gp'] != None:
                additional_features = saxs_math.guinier_porod_profile(q_I)
                additional_features = np.array(list(additional_features.values())).reshape(1,-1)
                rg_features = np.append(features, additional_features)
                x_bd = self.scalers['rg_gp'].transform(rg_features.reshape(1, -1))
                f_bd = self.models['rg_gp'].predict(x_bd)
                flags['rg_gp'] = f_bd

        return flags

