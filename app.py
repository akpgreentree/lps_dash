import dash
import dash_html_components as html
import dash_core_components as dcc
import components

app = dash.Dash(__name__)

timecourse = components.TopicTimecourse('data/topics.csv')
cpm_plotter = components.CPMPlotter('data/cpm.gct')
z_table = components.GeneTable('data/topic_Z.csv',
                               cpm_plotter, app, 'Z')
lfc_table = components.GeneTable('data/topic_lfc.csv',
                                 cpm_plotter, app, 'beta')

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
    )
])

z_table.register()
lfc_table.register()

if __name__ == '__main__':
    app.run_server(debug=True)