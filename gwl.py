"""Global Warming Level functions"""

import xarray as xr
import pandas as pd
import numpy as np
import yaml
import urllib.request
import os

def get_GWL_syear_eyear(CMIP,GCM,ensemble,pathway,GWL):
    """Returns the start and end year of the Global Warming Level timeslice for the specified GWL, GCM, ensemble and pathway.
    This script searches the global warming levels calculated by Mathias Hauser:\
    https://github.com/mathause/cmip_warming_levels/tree/main

    Author: Mitchell Black (mitchell.black@bom.gov.au)

    Parameters
    ----------
    CMIP : str
        Version of CMIP [options: 'CMIP5', 'CMIP6']
    GCM : str
        Name of the global climate model
    ensemble : str
        Name of GCM ensemble member (e.g., 'r1i1p1f1')
    pathway : str
        Emissions pathway [options: 'rcp26', 'rcp45', 'rcp85', 'ssp126', 'ssp245', 'ssp370', 'ssp585']
    GWL : str or float
        Required Global Warming Level [options: 1.0, 1.2, 1.5, 2.0, 3.0, 4.0]

    Returns
    -------
    int : syear, eyear
       Start and end year of corresponding 20-year GWL timeslice
    """

    assert CMIP.lower() in ['cmip5','cmip6']
    assert pathway.lower() in ['rcp26','rcp45','rcp85','ssp126','ssp245','ssp370','ssp585']
    assert float(GWL) in [1.0,1.2,1.5,2.0,3.0,4.0]
    
    yaml = read_GWL_yaml_file(CMIP)

    df = pd.json_normalize(yaml,record_path=f'warming_level_{int(float(GWL)*10)}')

    assert GCM in df['model'].unique(), f"Model {model} not recognised. GWLs available for the following models: {df['model'].unique()}"
        
    df = df[ (df.model == GCM) & (df.ensemble == ensemble) & (df.exp == pathway) ]
    if df.empty:
        raise ValueError(f'GWL {GWL} not calculated for {CMIP,GCM,ensemble,pathway}')
    elif df.shape[0] > 1:
        raise ValueError(f'Multiple entries for {CMIP,GCM,ensemble,pathway} GWL {GWL}\N{DEGREE SIGN}C. Check source file.')
    elif df.end_year.values.flatten() == 9999:
        raise ValueError(f'{CMIP,GCM,ensemble,pathway} did not reach GWL {GWL}\N{DEGREE SIGN}C.')
    else:
        return df[['start_year','end_year']].values.flatten()

def read_GWL_yaml_file(CMIP)
    """Reads the yaml file from Matthias's repo

    Author: Mitchell Black (mitchell.black@bom.gov.au)

    Parameters
    ----------
    CMIP : str
        Version of CMIP [options: 'CMIP5', 'CMIP6']

    Returns
    -------
    yaml : dict
        yaml file opened in safe mode (effectively a dictionary of dictinaries)
    """
    
    repodir = __file__.rsplit('/', 1)[0]
    fpath = f"{repodir}/cmip_warming_levels/warming_levels/{CMIP.lower()}_all_ens/{CMIP.lower()}_warming_levels_all_ens_1850_1900.yml"
    if not os.path.exists(fpath):
        raise ValueError('You have not properly cloned the gwl repository! Go back and use the command \033[1m `git submodule update --init` \033[0m')   

    with open(fpath) as f:
        tidied =  (
            f.read()
                .replace("# {","- {")
                .replace("} -- did not reach 1.0°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 1.2°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 1.5°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 2.0°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 3.0°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 4.0°C",", start_year: 9999, end_year: 9999}")
        )
    
        return yaml.safe_load(tidied)

def get_GWL_lookup_table(CMIP):
    """Reads the yaml file from Matthias's repo and returns as a pandas dataframe

    Author: Mitchell Black (mitchell.black@bom.gov.au)

    Parameters
    ----------
    CMIP : str
        Version of CMIP [options: 'CMIP5', 'CMIP6']

    Returns
    -------
    yaml : dict
        yaml file opened in safe mode (effectively a dictionary of dictinaries)
    """

    yml = utils.gwl.get_GWL_lookup_table('CMIP6')
    appended_df = []
    for gwl in yml.keys():
        df = pd.DataFrame(yml[gwl])
        df.insert(1,'GWL',gwl)
        appended_df.append(df)
        del(df)
    
    df = pd.concat(appended_df,axis=0,ignore_index=True)
    df['GWL'] = df['GWL'].str.replace('warming_level_','gwl')
    
    return df

def get_GWL_timeslice(ds,CMIP,GCM,ensemble,pathway,GWL):
    """Returns the 20-year timeslice of a data array corresponding to the desired Global Warming Level.

    Author: Mitchell Black (mitchell.black@bom.gov.au)
    
    Parameters
    ----------
    ds : xarray DataArray or DataSet
        Input array from which to take the 20-year timeslice
    CMIP : str
        Version of CMIP [options: 'CMIP5', 'CMIP6']
    GCM : str
        Name of the global climate model
    ensemble : str
        Name of GCM ensemble member (e.g., 'r1i1p1f1')
    pathway : str
        Emissions pathway [options: 'rcp26', 'rcp45', 'rcp85', 'ssp126', 'ssp245', 'ssp370', 'ssp585']
    GWL : str or float
        Required Global Warming Level [options: 1.0, 1.2, 1.5, 2.0, 3.0, 4.0]

    Returns
    -------
    ds : xarray DataArray or DataSet
       Subsampled data array corresponding to the desired Global Warming Level.
    """

    syear,eyear = get_GWL_syear_eyear(CMIP,GCM,ensemble,pathway,GWL)
    return ds.sel(time=slice('{}-01-01'.format(int(syear)),'{}-12-31'.format(int(eyear))))
