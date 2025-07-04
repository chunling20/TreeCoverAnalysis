# TreeCoverAnalysis
This repository provides Python scripts to analyze long-term tree cover dynamics, including its correlation with temperature and its statistical distribution across elevation zones using parallel processing.

## Requirements

numpy, pandas, scipy, rasterio, mpi4py, gdal

Example of successful environment creation

It is highly recommended to use Conda to create the environment, as GDAL and mpi4py have complex dependencies that are best managed by Conda.

```bash
# 1. Create a new conda environment (e.g., named 'geo_env' with Python 3.9)
conda create -n geo_env python=3.9 -y

# 2. Activate the environment
conda activate geo_env

# 3. Install complex dependencies from the conda-forge channel
conda install -c conda-forge gdal mpi4py

# 4. Install the remaining packages using pip
pip install numpy pandas scipy rasterio
