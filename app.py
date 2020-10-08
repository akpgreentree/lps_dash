import dash
import dash_html_components as html
import dash_core_components as dcc

import random
import subprocess

from . import components

class MainApp:

    def __init__(self, topic_path, cpm_path, z_path, lfc_path, is_local):
        self.is_local = is_local
        self.app = dash.Dash(__name__)
        self._set_layout(topic_path, cpm_path, z_path, lfc_path)

    def _set_layout(self, topic_path, cpm_path, global_z_path, tissue_z_path):

        timecourse = components.TopicTimecourse(topic_path)
        cpm_plotter = components.CPMPlotter(cpm_path)
        global_z_table = components.GeneTable(global_z_path, cpm_plotter,
                                              self.app, 'Z')
        tissue_z_table = components.TissueGeneTable(tissue_z_path, cpm_plotter,
                                                    self.app, 'Z')

        self.app.layout = html.Div(children = [
            html.Div(
                className = 'row', 
                style = {'height' : 700},
                children = [
                    html.Div(className = 'three columns', children = [
                        timecourse.get_component()
                    ]),
                    html.Div(className = 'four columns', children = [
                        global_z_table.get_component(),
                    ]),
                    html.Div(className = 'four columns', children = [
                        tissue_z_table.get_component()
                    ])
                    # html.Div(className = 'four columns', children = [
                    #     timecourse_debugger.get_component()
                    # ])
                ]
            ),
        ])

        global_z_table.register()
        tissue_z_table.register()
        # timecourse_debugger.register()

    def main(self):
        if self.is_local:
            self.app.run_server(debug=True)

        else:
            host = subprocess.run(['hostname', '-i'], capture_output = True)
            host = host.stdout[:-1].decode('utf-8')
            port = random.randrange(8000, 9000)
            self.app.run_server(debug = True, port = port, host = host)

