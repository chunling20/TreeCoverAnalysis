from osgeo import gdal, ogr, osr
import os
import random
import argparse
import numpy as np
import pandas as pd
from mpi4py import MPI

def listdatas(pathin):
    """
    List all valid tree cover files in the given directory.
    Only include files with years between 1990 and 2020.
    """
    a = []
    datas = os.listdir(pathin)
    for i in datas:
        if i[-4:] == '.tif' and int(i.split('_')[1][0:4]) >= 1990 and int(i.split('_')[1][0:4]) <= 2020:
            fn_i = pathin + '/' + i
            print(fn_i)
            a.append(fn_i)
    return a

def multi_stat_tcc_dem(pathin_tcc, dem, pathout,start):
    """
    Compute mean TCC values within a specific DEM elevation range.
    
    Args:
        pathin_tcc: Directory containing tree cover files.
        dem: Path to DEM raster.
        pathout: Output directory for results.
        start: Lower bound of elevation range.
    """
   
    tccs = listdatas(pathin_tcc)

    ds_dem = gdal.Open(dem)
    in_band_dem = ds_dem.GetRasterBand(1)
    dem_array = in_band_dem.ReadAsArray()

    dem_array_0 = np.ma.masked_where(dem_array == -9999, dem_array)

    df_out = pd.DataFrame(columns=['year', 'mean'])

    value_dict = {}

    end = start + 500

    for tcc in tccs:
        year = tcc.split('/')[-1].split('_')[1].split('.')[0][-4:]  # Extract year

        ds_tcc = gdal.Open(tcc)
        in_band_tcc = ds_tcc.GetRasterBand(1)
        tcc_array = in_band_tcc.ReadAsArray()

        tcc_array_0 = np.ma.masked_where(tcc_array > 100, tcc_array)  # Mask NoData values in tree cover
        tcc_mask_array_1 = np.ma.masked_where(dem_array_0 < start, tcc_array_0)  # Mask tree cover values outside elevation range
        tcc_mask_array_2 = np.ma.masked_where(dem_array_0 >= end, tcc_mask_array_1)

        float_tcc_mask_array_2 = tcc_mask_array_2.astype(np.float64)

        value_mean = float_tcc_mask_array_2.mean()
        if value_mean == '--':
            value_mean = 0

        value_dict['year'] = [year]
        value_dict['mean'] = [value_mean]
        df_out = df_out.append(pd.DataFrame(value_dict))

        del ds_tcc
    df_out = df_out.sort_values(by='year')
    pathout_stat = pathout + '/' + 'stat'

    if os.path.isdir(pathout_stat):
        pass
    else:
        try:
            os.makedirs(pathout_stat)
        except:
            pass

    df_out.to_csv(pathout_stat + '/' + str(start) + '_' + str(end) + '.csv', index=False, header=True)

    del ds_dem

def divide(datas, n):
    """
    Divide data into n parts for parallel processing.
    """

    mpi_datas = {}
    step = len(datas)//n
    for i in range(n):
        if i < n-1:
            mpi_data = datas[i*step:(i+1)*step]
            mpi_datas[i] = mpi_data
        else:
            mpi_data = datas[i*step:]
            mpi_datas[i] = mpi_data

    j = 0
    while len(mpi_datas[n-1]) > step and j < n-1:
        mpi_datas[j].append(mpi_datas[n-1][-1])
        mpi_datas[n-1].remove(mpi_datas[n-1][-1])
        j = j + 1
    
    mpi_datas_out = []
    for mpi_data_out in mpi_datas.values():
        mpi_datas_out.append(mpi_data_out)
    return mpi_datas_out

def main():
    """
    Main function to perform MPI-based DEM-TCC statistics in parallel.
    """
    comm = MPI.COMM_WORLD
    comm_rank = comm.Get_rank()
    comm_size = comm.Get_size()

    dem = r'./dem.tif'
    pathin_tcc =  r'./treecoverData'
    pathout = r'./treeCover_DEM_sta'
    if comm_rank == 0:
        datas = [500*x for x in range(16)]
        random.shuffle(datas) 
        mpi_datas = divide(datas, comm_size)
    else:
        datas = None
        mpi_datas = None

    # Scatter divided ranges to all processes
    mpi_data_divide = comm.scatter(mpi_datas, root=0)

    # Each process performs analysis for its assigned elevation bands
    for start in mpi_data_divide:
        multi_stat_tcc_dem(pathin_tcc, dem, pathout,start)
        
    return

if __name__ == "__main__":
    main()