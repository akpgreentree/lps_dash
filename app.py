import dash
import dash_html_components as html
import dash_core_components as dcc
import debug_component
import components

app = dash.Dash(__name__)

timecourse = components.TopicTimecourse('/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/topics.csv')
cpm_plotter = components.CPMPlotter('/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/cpm.gct')
z_table = components.GeneTable('/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/topic_Z.csv',
                               cpm_plotter, app, 'Z')
lfc_table = components.GeneTable('/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/topic_lfc.csv',
                                 cpm_plotter, app, 'beta')


input_debugger = debug_component.DebuggerComponent(app, 
                                                   'topic-timecourse', 
                                                   'clickData')


app.layout = html.Div(children = [
    html.Div(
        className = 'row', 
        style = {'height' : 700},
        children = [
            html.Div(className = 'four columns', children = [
                timecourse.get_component()
            ]),
            html.Div(className = 'four columns', children = [
                z_table.get_component(),
            ]),
            html.Div(className = 'four columns', children = [
                lfc_table.get_component()
            ])
        ]
    ),
    input_debugger.get_component()
])

input_debugger.register()
z_table.register()
lfc_table.register()

if __name__ == '__main__':
    from subprocess import run
    from random import randrange
    host = run(['hostname', '-i'], capture_output= True).stdout
    port = randrange(8000, 9000)
    app.run_server(debug=True, port=port, host=host[:-1].decode("utf-8"))