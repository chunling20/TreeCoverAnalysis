from osgeo import gdal
import numpy as np
import os
import scipy.stats as stats
from scipy.optimize import curve_fit
import rasterio


def func(x, a, b):
    # A simple linear function.
    return a * x + b

def listdatas(pathin):
    # Lists all GeoTIFF files in a given directory.
    a = []
    datas = os.listdir(pathin)
    datas.sort()
    print(datas)
    for i in datas:
        if i[-4:] == '.tif':
            fn_i = pathin + '/' + i
            a.append(fn_i)
    return a

def calculate_correlation(temp_path, tcc_path, output_path):
    """
    Calculates and saves the pixel-wise correlation between temperature and tree cover.

    Args:
        temp_path (str): Directory path for temperature GeoTIFF files.
        tcc_path (str): Directory path for tree cover (TCC) GeoTIFF files.
        output_path (str): Full file path for the output correlation GeoTIFF.
    """

# Read all temperature rasters into a 3D numpy array.
    files_temp = listdatas(temp_path)
    ds_temp = gdal.Open(files_temp[0])
    band_temp = ds_temp.GetRasterBand(1)
    temp_array = band_temp.ReadAsArray()
    nodata_temp = band_temp.GetNoDataValue()
    m, n = len(temp_array), len(temp_array[0])

    datas_temp = []
    for data in files_temp:
        in_ds = gdal.Open(data)
        in_band = in_ds.GetRasterBand(1)
        in_array = in_band.ReadAsArray()
        datas_temp.append(in_array)
        del in_ds
    temp_tmp = np.array(datas_temp)

 # Read all tree cover rasters into a 3D numpy array.
    files_tcc = listdatas(tcc_path)
    ds_tcc = gdal.Open(files_tcc[0])
    band_tcc = ds_tcc.GetRasterBand(1)
    nodata_tcc = band_tcc.GetNoDataValue()

    datas_tcc = []
    for data in files_tcc:
        in_ds = gdal.Open(data)
        in_band = in_ds.GetRasterBand(1)
        in_array = in_band.ReadAsArray()
        datas_tcc.append(in_array)
        del in_ds
    tcc_tmp = np.array(datas_tcc)

    res = [[0] * n for i in range(m)]
    for i in range(m):
        for j in range(n):
            new_tmp = []
            new_tcc = []
            pixels = tcc_tmp[:,i,j]
            masked_1 = np.ma.masked_where(pixels == 0, pixels)
            masked_2 = np.ma.masked_where(pixels == nodata_tcc, pixels)

            if masked_1.count() == 0 :
                r_value = 0
            elif masked_2.count() ==0 :
                r_value = nodata_temp           

            # This condition filters out non-forest areas. For pixels where tree cover is always below 10%, 
            # minor fluctuations are more likely due to sensor noise or classification errors rather than meaningful ecological change.
            
            elif masked_2.max() < 10:
                r_value = 0
            
            #Calculate the linear regression and get the r-value or other metrics.
            else:
                for k in range(len(tcc_tmp[:,i,j])):
                    if tcc_tmp[k,i,j] != nodata_tcc and temp_tmp[k,i,j] != nodata_temp:
                        new_tmp.append(temp_tmp[k,i,j])
                        new_tcc.append(tcc_tmp[k,i,j])
                if len(new_tmp) >= 26:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(new_tmp,new_tcc)
                else:
                    r_value = nodata_temp
            res[i][j] = r_value

    src_ds = rasterio.open(files_temp[0])
    src_profile = src_ds.profile.copy()
    src_band = src_ds.read(1)
    print(type(src_band))
    with rasterio.open(output_path, 'w', **src_profile) as dst_ds:
        dst_ds.write(np.array(res).astype(np.float32), 1)

if __name__ == "__main__":
    # Replace these paths with the actual paths on your system.
    temperature_data_path = './temperatureData'
    tree_cover_data_path = './treecoverData'
    output_file_path = './correlation_1990-2020.tif'

    # Run the main calculation function.
    calculate_correlation(temperature_data_path, tree_cover_data_path, output_file_path)



