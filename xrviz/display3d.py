from .utils3d import *
from xrviz.sigslot import SigSlot
from .selection3d import Selection3d
import numpy as np
import panel as pn
import plotly
import plotly.graph_objects as go
import plotly.express as px
import xarray as xr
import warnings
from textwrap import wrap
import json
pn.extension('plotly')
warnings.filterwarnings('ignore')

class Display3d(SigSlot):
    """Displays a list of data variables for selection.
    """

    def __init__(self, data, skip_lat=20, skip_lon=20, skip_lev=2,colorscale="inferno"):
        super().__init__()
        self.data = data
        self.coords = self.data.coords
        self.sel3d = Selection3d()
        self.skip_lat = int(self.sel3d.kwargs['skip_lat'])
        self.skip_lon = int(self.sel3d.kwargs['skip_lon'])
        self.skip_lev = int(self.sel3d.kwargs['skip_lev'])
        self.X_map, self.Y_map = self.get_map_X_Y()

        self.colorscale = self.sel3d.kwargs['cmap_3d']
        self.levs_is_sorted = is_sorted(self.data['lev'])
        self.X,self.Y, self.Z = np.meshgrid(
                        self.data['lon'][::skip_lon],
                        self.data['lat'][::skip_lat],
                        check_levs(self.levs_is_sorted,self.data['lev'][::skip_lev]),
                        indexing='xy')

        self.name = 'Variables 3D'
        self.select_var_3d = pn.widgets.Select(
            min_width=100, max_width=200, width_policy='max',
            name=self.name)
        self.time_select_3d = pn.widgets.Select(
            min_width=100, max_width=200, width_policy='max',
            name='Time')
        self.plot_button_3d = pn.widgets.Button(name='Plot 3D', width=200)
        self.data_cube = pn.Row(pn.Spacer(name='Series Graph'))

        self.panel = pn.Column(
                    pn.Column(
                    pn.Row(self.select_var_3d, self.time_select_3d),
                    self.sel3d.panel,
                    ),
                    name='3D Cube',
            )
        
        self.set_variables()
        self.set_times()

        self._register(self.select_var_3d, "variable_selected")
        self._register(self.time_select_3d, "time_selected")
        self._register(self.plot_button_3d, 'plot_clicked', 'clicks')
        self.connect('plot_clicked', self.create_cube)

    def set_variables(self,):
        self.select_var_3d.options = [var for var in list(self.data.variables) if var not in self.coords]

    def set_times(self,):
        self.time_select_3d.options = [val for val in self.data.time.data]

    def create_cube(self, _):
        var =self.select_var_3d.value
        tval = self.time_select_3d.value
        self.ds = self.data[var].sel(time=tval).data#.compute()

        self.ds = np.transpose(self.ds, (2,1,0))
        isomin = round(self.ds.min())
        isomax = round(self.ds.max())

        volume = plotly.graph_objects.Volume(
            x=self.X.flatten(),
            y=self.Y.flatten(),
            z=self.Z.flatten(),
            value=get_vals(self.levs_is_sorted,
                           self.ds,
                           self.skip_lon,
                           self.skip_lat,
                           self.skip_lev).flatten(),
            isomin=isomin,
            isomax=isomax,
            opacity=self.sel3d.kwargs['opacity'], # needs to be small to see through all surfaces
            surface_count = self.sel3d.kwargs['surface_count'], # needs to be a large number for good volume rendering,
            colorscale = self.sel3d.kwargs['cmap_3d']
        )
    
        plotly_layout = go.Layout(
#             title = 'India 3D Plot',
            autosize = False,
            width = self.sel3d.kwargs['frame_width_3d'],
            height = self.sel3d.kwargs['frame_height_3d'],
            margin = dict(t=100, b=100, r=100, l=100),
            scene = dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Pressure',
            zaxis_autorange = "reversed",
            ))
        map_lines = go.Scatter3d(x = self.X_map, 
                                 y = self.Y_map, 
                                 z = [1000]*len(self.X_map),
                                 mode='lines')
        
        fig = dict(data=[volume, map_lines], layout=plotly_layout)
        self.data_cube[0] =  pn.pane.Plotly(fig)   
        
    def get_map_X_Y(self,):
        with open("data/INDIA_STATES.json") as json_file:
            jdata = json_file.read()
            geoJSON = json.loads(jdata)
        pts=[]#list of points defining boundaries of polygons
        for  feature in geoJSON['features']:
            if feature['geometry']['type']=='Polygon':
                pts.extend(feature['geometry']['coordinates'][0])    
                pts.append([None, None])#mark the end of a polygon   

            elif feature['geometry']['type']=='MultiPolygon':
                for polyg in feature['geometry']['coordinates']:
                    pts.extend(polyg[0])
                    pts.append([None, None])#end of polygon
            else: raise ValueError("geometry type irrelevant for map") 
        return zip(*pts)

    @property
    def kwargs(self):
        return {self.name: self.select.value}
