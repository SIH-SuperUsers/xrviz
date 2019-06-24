import panel as pn
import xarray as xr
import hvplot.xarray
from cartopy import crs as ccrs
from .sigslot import SigSlot
from .control import Control
from .utils import convert_widget, player_with_name_and_value


class Dashboard(SigSlot):
    """
    This section provides access to the complete generated dashboard,
    consisting of all subsections.

    Parameters
    ----------
    data: `xarray` instance: `DataSet` or `DataArray`
           datset is used to initialize.

    Attributes
    ----------
    panel: Displays the generated dashboard.
    control: Provides access to the generated control panel.
    plot: Plot button, upon click generates graph according to
          kwargs selected in other sub-sections.
    output: Provides access to generated graph.
    """

    def __init__(self, data):
        super().__init__()
        if not isinstance(data, xr.core.dataarray.DataWithCoords):
            raise ValueError("Input should be an xarray data object, not %s" % type(data))
        self.set_data(data)
        self.control = Control(self.data)
        self.plot_button = pn.widgets.Button(name='Plot', width=200, disabled=True)
        self.index_selectors = []
        self.output = pn.Row(pn.Spacer(name='Graph'),
                             pn.Column(name='Index_selectors'))

        self._register(self.plot_button, 'plot_clicked', 'clicks')
        self.connect('plot_clicked', self.create_plot)

        if self.is_dataset:
            self._register(self.control.coord_setter.set_coord_button, 'set_coords', 'clicks')
            self.connect("set_coords", self.set_coords)

        self.control.displayer.connect('variable_selected', self.check_is_plottable)

        self.panel = pn.Column(self.control.panel,
                               self.plot_button,
                               self.output)

        if not self.is_dataset:
            self.check_is_plottable(var=None)

    def create_plot(self, *args):
        self.kwargs = self.control.kwargs
        self.var = self.kwargs['Variables']
        if self.index_selectors:
            for selector in self.index_selectors:
                del selector
        self.index_selectors = []
        self.output[1].clear()  # clears Index_selectors

        if self.is_dataset:
            x = self.kwargs['x']
            if not self.is_non_indexed_coord(x):  # i.e is a var_dim
                self.var_dims = list(self.data[self.var].dims)
                #  var_selector_dims refers to dims for which index_selectors would be created
                self.var_selector_dims = self.kwargs['dims_to_select_animate']
                self.index_selectors = []
                self.output[1].clear()  # clears Index_selectors

                for dim in self.var_selector_dims:
                    ops = list(self.data[self.var][dim].values)

                    if self.kwargs[dim] == 'Select':
                        selector = pn.widgets.Select(name=dim, options=ops)
                    else:
                        selector = pn.widgets.DiscretePlayer(name=dim, value=ops[0], options=ops)
                    self.index_selectors.append(selector)
                    self._register(selector, selector.name)
                    self.connect(selector.name, self.create_indexed_graph )

                self.create_indexed_graph()
                for selector in self.index_selectors:
                    if isinstance(selector, pn.widgets.Select):
                        self.output[1].append(selector)
                    else:
                        player = player_with_name_and_value(selector)
                        self.output[1].append(player)
            else:   # is_indexed_coord
                graph_opts = {'x': self.kwargs['x'],
                              'y': self.kwargs['y'],
                              'title': self.var}
                dims_to_agg = self.kwargs['dims_to_agg']
                sel_data = self.data[self.var]

                for dim in dims_to_agg:
                    if self.kwargs[dim] == 'count':
                        sel_data = (~ sel_data.isnull()).sum(dim)
                    else:
                        agg = self.kwargs[dim]
                        sel_data = getattr(sel_data, agg)(dim)

                if self.var in list(sel_data.coords):  # When a var(coord) is plotted wrt itself
                    sel_data = sel_data.to_dataset(name=f'{sel_data.name}_')

                assign_opts = {dim: self.data[dim] for dim in sel_data.dims}
                graph = sel_data.assign_coords(**assign_opts).hvplot.quadmesh(**graph_opts)

                self.create_selectors_players(graph)

        else:  # if is_dataArray
            self.var_dims = list(self.data.dims)
            self.var_selector_dims = self.kwargs['dims_to_select_animate']

            self.index_selectors = []
            self.output[1].clear()  # clears Index_selectors

            for dim in self.var_selector_dims:
                ops = list(self.data[dim].values)

                if self.kwargs[dim] == 'Select':
                    selector = pn.widgets.Select(name=dim, options=ops)
                else:
                    selector = pn.widgets.DiscretePlayer(name=dim, value=ops[0], options=ops)
                self.index_selectors.append(selector)
                self._register(selector, selector.name)
                self.connect(selector.name, self.create_indexed_graph )

            self.create_indexed_graph()
            for selector in self.index_selectors:
                if isinstance(selector, pn.widgets.Select):
                    self.output[1].append(selector)
                else:
                    player = player_with_name_and_value(selector)
                    self.output[1].append(player)

    def create_indexed_graph(self, *args):
        """
        Creates graph for  selected indexes in selectors or players.
        """
        selection = {} # to collect the value of insex selectors
        for i, dim in enumerate(list(self.var_selector_dims)):
            selection[dim] = self.index_selectors[i].value
        x = self.kwargs['x']
        y = self.kwargs['y']
        dims_to_agg = self.kwargs['dims_to_agg']
        graph_opts = {'x': x,
                      'y': y,
                      'title': self.var}
        sel_data = self.data[self.var] if self.is_dataset else self.data

        for dim in dims_to_agg:
            if self.kwargs[dim] == 'count':
                sel_data = (~ sel_data.isnull()).sum(dim)
            else:
                agg = self.kwargs[dim]
                sel_data = getattr(sel_data, agg)(dim)

        # rename the sel_data in case it is a coordinate, because we
        # cannot create a Dataset from a DataArray with the same name
        #  as one of its coordinates
        if sel_data.name in self.data.coords:
                sel_data = sel_data.to_dataset(name=f'{sel_data.name}_')

        sel_data = sel_data.sel(**selection, drop=True)
        assign_opts = {dim: self.data[dim] for dim in sel_data.dims}
        graph = sel_data.assign_coords(**assign_opts).hvplot.quadmesh(**graph_opts)
        self.output[0] = graph

    def create_selectors_players(self, graph):
        """
        This function is applicable for non_indexed coords, in case
        sliders are generated. This function moves the sliders to bottom of
        graph if they are present and convert them into Selectors,Players.
        """
        graph = pn.Row(graph)
        try:  # `if graph[0][1]` or `len(graph[0][1])` results in error in case it is not present
            if graph[0][1]:  # if sliders are generated
                self.output[0] = graph[0][0]

                # link the generated slider with agg selector in fields 
                for slider in graph[0][1]:
                    for dim in self.kwargs['dims_to_select_animate']:
                        if slider.name == dim or slider.name == self.data[dim].long_name:
                            if self.kwargs[dim] == 'Select':
                                selector = convert_widget(slider, pn.widgets.Select())
                            else:
                                selector = convert_widget(slider, pn.widgets.DiscretePlayer())
                            self.index_selectors.append(selector)

                for selector in self.index_selectors:
                    if isinstance(selector, pn.widgets.Select):
                        self.output[1].append(selector)
                    else:
                        player = player_with_name_and_value(selector)
                        self.output[1].append(player)

        except:  # else return simple graph
            self.output[0] = graph

    def is_non_indexed_coord(self, x):
        indexed_coords = set(self.data[self.var].dims).intersection(set(self.data[self.var].coords))
        non_indexed_coords = set(self.data[self.var].coords) - indexed_coords
        return x in non_indexed_coords

    def set_data(self, data):
        self.data = data
        self.is_dataset = isinstance(data, xr.Dataset)

    def set_coords(self, *args):
        # We can't reset indexed coordinates so add them every time
        # in coord_selector.value
        self.data = self.data.reset_coords()
        indexed_coords = set(self.data.dims).intersection(set(self.data.coords))
        new_coords = set(self.control.coord_setter.coord_selector.value).union(indexed_coords)
        self.data = self.data.set_coords(new_coords)  # this `set_coords` belongs to xr.dataset
        self.control.set_coords(self.data)

    def check_is_plottable(self, var):
        """
        If a variable is 1-d, disable plot_button for it.
        """
        self.plot_button.disabled = False  # important to enable button once disabled
        data = self.data[var[0]] if self.is_dataset else self.data
        self.plot_button.disabled = len(data.dims) <= 1
