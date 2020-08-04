import xarray as xr
from xrviz.dashboard import Dashboard
data = xr.open_dataset("data/SAC_WRF_FCML_5KM_20191223.nc")
dash = Dashboard(data)
dash.panel.show()