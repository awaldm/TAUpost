#/usr/bin/python
"""
Compute turbulence anisotropy quantities for a 2D planar time series from a TAU solution

Data input: consecutive time series data in plt format

Data output: one plt file each containing the anisotropy tensor, the eigenvalues and the barycentric coordinates

Required input:

case_name: string
    input for conf.WakeCaseParams() in order to obtain the parameters for the data reader
plane: string
    name of the plane to be read from the input data files
data_type: str
    typically just CRM_LSS
WCalign: bool
    set to True to rotate by angle of attack, set to False to align with precomputed wake centerline direction

Andreas Waldmann, 2020

"""


import os, sys


import time
import shutil
import numpy as np
import matplotlib.mlab as mlab
import matplotlib as mpl
import pyTecIO_AW.tecreader as tecreader
import matplotlib.pyplot as plt
import wake_analysis.wake_config as conf
import tecplot as tp
import scipy.signal
import wake_analysis.helpers.wake_stats as ws



######################################################################
if __name__ == "__main__":
    ##################################################
    # Set up computation parameters

    # Selector string for the config file
    case_name = 'CRM_v38h_DDES_dt100_ldDLR_CFL2_eigval015_pswitch1_tau2017_2'

    # Plane name
    plane = 'eta0603'

    # Case type, mainly for reference attributes
    case_type = 'CRM_LSS'

    #di = 10

    ##################################################

    # Get parameter dict from config file based on above input
    par = conf.WakeCaseParams(case_name, plane, case_type)
    
    # Get the data time series. The uvw data are arrays of shape (n_points, n_samples). dataset is a Tecplot dataset.
    u,v,w,dataset = tecreader.get_series(par.plt_path, par.zonelist, par.start_i, par.end_i, read_velocities=True,read_cp=False, read_vel_gradients=False, stride = par.di, parallel=False)
    print('done reading. shape of u: ' + str(u.shape))
    n_samples = u.shape[-1]


    # Get the coordinates as arrays
    x,y,z = tecreader.get_coordinates(dataset, caps=True)


    # Carry out rotation to the inflow direction
    print('point of model rotation:')
    print('x_PMR: ' +str(par.x_PMR))
    print('z_PMR: ' +str(par.z_PMR))

    ws.rotate_dataset(dataset, par.x_PMR, par.z_PMR, par.aoa)
    x_WT, z_WT = ws.transform_wake_coords(x,z, par.x_PMR, par.z_PMR, par.aoa)
    u_WT, w_WT = ws.rotate_velocities(u,v,w, par.x_PMR, par.z_PMR, par.aoa)

    # We need reynolds stresses for anisotropy calculation
    uu,vv,ww,uv,uw,vw = ws.calc_rstresses(u_WT,v,w_WT)
    mean_u = np.mean(u_WT, axis=-1)
    mean_v = np.mean(v, axis=-1)
    mean_w = np.mean(w_WT, axis=-1)

    kt = 0.5* (uu + vv + ww)

    # Compute the anisotropy tensor
    a_uu, a_vv, a_ww, a_uv, a_uw, a_vw = ws.compute_atensor(uu, vv, ww, uv, uw, vw, kt)
    # Compute second and third invariants of the anisotropy tensor 
    invar2, invar3, ev = ws.compute_anisotropy_invariants(a_uu, a_vv, a_ww, a_uv, a_uw, a_vw)
    # Compute barycentric coordinates
    C, xb, yb = ws.compute_anisotropy_barycentric(ev)


    print('shape of C: ' + str(C.shape))



    # Save the results

    newvar=dict()
    newvar['a_uu'] = a_uu
    newvar['a_vv'] = a_vv
    newvar['a_ww'] = a_ww
    newvar['a_uv'] = a_uv
    newvar['a_uw'] = a_uw
    newvar['a_vw'] = a_vw
    varnames = newvar.keys()
    filename = par.res_path + case_name+'_'+par.plane+'_anisotropy_tensor.plt'
    tecreader.save_plt(newvar, dataset, filename, addvars = True, removevars = True)

    newvar=dict()
    newvar['ev1'] = ev[0,:]
    newvar['ev2'] = ev[1,:]
    newvar['ev3'] = ev[2,:]
    varnames = newvar.keys()
    filename = par.res_path + case_name+'_'+par.plane+'_anisotropy_eigvals.plt'
    tecreader.save_plt(newvar, dataset, filename, addvars = True, removevars = True)


    newvar = dict()
    newvar['C1'] = C[0,:]
    newvar['C2'] = C[1,:]
    newvar['C3'] = C[2,:]
    varnames = newvar.keys()
    filename = par.res_path + case_name+'_'+par.plane+'_anisotropy_components.plt'
    tecreader.save_plt(newvar, dataset, filename, addvars = True, removevars = True)
    