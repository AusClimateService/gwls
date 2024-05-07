"""Global Warming Level functions"""

import xarray as xr
import pandas as pd
import numpy as np
import yaml
import urllib.request

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
    
    fpath = f"https://raw.githubusercontent.com/mathause/cmip_warming_levels/main/warming_levels/{CMIP.lower()}_all_ens/{CMIP.lower()}_warming_levels_all_ens_1850_1900.yml"

    with urllib.request.urlopen(fpath) as f:
        tidied =  (
            f.read().decode('utf-8')
                .replace("# {","- {")
                .replace("} -- did not reach 1.0°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 1.2°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 1.5°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 2.0°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 3.0°C",", start_year: 9999, end_year: 9999}")
                .replace("} -- did not reach 4.0°C",", start_year: 9999, end_year: 9999}")
        )
    
        df = pd.json_normalize(yaml.safe_load(tidied),record_path=f'warming_level_{int(float(GWL)*10)}')

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
