from typing import Dict, Tuple
import pandas as pd
import numpy as np
import dash 
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
import plotly.graph_objects as go

def _order_strings(str_series: pd.Series) -> pd.Series:
    '''Turns string series of the form cNN where c is a character and 
       NN is an integer into an order categorical'''
    # get unique ints
    num_series = str_series.str.slice(start = 1).astype(int)
    unique_num = np.unique(num_series)
    # append c to ints
    c = str_series[0][0]
    unique_str = c + pd.Series(unique_num).astype(str)
    # categorize the original series
    category_type = pd.CategoricalDtype(unique_str, ordered = True)
    return str_series.astype(category_type)
    
topic_palette = ['#F0A3FF', '#0075DC', '#993F00', '#4C005C',
                 '#191919', '#005C31', '#2BCE48', '#FFCC99', 
                 '#808080', '#94FFB5', '#8F7C00', '#9DCC00',
                 '#C20088', '#003380', '#FFA405', '#FFA8BB',
                 '#426600', '#FF0010', '#5EF1F2', '#00998F',
                 '#E0FF66', '#740AFF', '#990000', '#FFFF80',
                 '#FFFF00', '#FF5005']
topic_color_map = {'k' + str(i+1): c for i, c in enumerate(topic_palette)}

tissue_palette = ["#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", 
                 "#008941", "#006FA6", "#A30059", "#FFDBE5",
                 "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43"]



class TopicTimecourse:

    '''Manages the component for the main topics timecourse.
    
    Attributes:
        id: str - id for dash component
        topic_table: pd.DataFrame - table of topic values      
    
    '''

    def __init__(self, topic_path: str):
        self.id = 'topic-timecourse'
        self._prep_topic_table(topic_path)

    def _prep_topic_table(self, topic_path):
        topic_table = pd.read_csv(topic_path)
        topic_table = topic_table.rename(columns = {'Unnamed: 0': 'sample'})
        
        meta_cols = topic_table['sample'].str.extract(
            r'(?P<tissue>.*)_(?P<timepoint>.*)_(?P<mouse>.*)'
        )
        topic_table = pd.concat([topic_table, meta_cols], axis=1)
        topic_table = topic_table.melt(
            id_vars = ['sample', 'tissue', 'timepoint', 'mouse'],
            var_name = 'topic'
        )

        topic_table['timepoint'] = _order_strings(topic_table['timepoint'])
        topic_table['topic'] = _order_strings(topic_table['topic'])

        topic_mean = (topic_table
                      .groupby(['tissue', 'timepoint', 'topic'])
                      .mean()
                      .reset_index()
                     )

        self.topic_table = topic_mean

    def _get_fig(self) -> go.Figure:
        fig = px.bar(self.topic_table, 
                     x = 'timepoint', y = 'value', color = 'topic',
                     custom_data = ['tissue', 'topic'],
                     color_discrete_map = topic_color_map,
                     facet_row = 'tissue',
                     facet_row_spacing = 0.01,
                     height = 900,
                     width = 500)
        # clean up facet names
        fig.for_each_annotation(
            lambda a: a.update(text=a.text.replace("tissue=", ""))
        )
        return fig

    def get_component(self) -> dcc.Graph():
        fig = self._get_fig()
        graph = dcc.Graph(figure = fig, id = self.id)
        return graph
        

class CPMPlotter:
    
    '''Makes timecourse plots of cpm for the gene table.
    
    Attributes:
        cpm: pd.Dataframe - cpm data
        color_map: Dict[str: str] - map of tissues to colors
        tissue_key: html.Ul - html object for tissue color key
            
    '''

    def __init__(self, cpm_path: str):
        # this is a rather brittle way to read in the .gct
        cpm = pd.read_csv(cpm_path, 
                          sep = '\t', 
                          header  = list(range(2, 8)),
                          index_col = 0)
        # set proper timepoint order
        cpm_cols = cpm.columns.to_frame()
        cpm_cols['timepoint'] = _order_strings(cpm_cols['timepoint'])
        cpm.columns = pd.MultiIndex.from_frame(cpm_cols)
        
        cpm = cpm.groupby(['tissue', 'timepoint'], axis=1).mean()
        self.cpm = cpm
        
        tissues = np.unique(cpm_cols['tissue'])
        self.color_map = {tissue: color 
                          for tissue, color in zip(tissues, tissue_palette)}
        self._prep_tissue_key()
        
    def _prep_tissue_key(self):
        key = html.Ul(style = {'list-style-type': 'none',
                               'padding-left': 20},
                      children = [self._key_item(tissue) 
                                  for tissue in self.color_map])
        self.tissue_key = key
        
    def line_plot(self, gene: str, tissue: str = None) -> dcc.Graph:
        '''Makes cpm line plot'''

        data = self.cpm.loc[gene].reset_index()
        if tissue is not None:
            data = data[data['tissue'] == tissue]

        fig = px.line(data,
                      x = 'timepoint',
                      y = gene,
                      color = 'tissue',
                      color_discrete_map = self.color_map,
                      height = 50,
                      width = 250,
                      labels= {'timepoint':'', gene: ''})
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(tickvals = [int(min(data[gene])), 
                                     int(max(data[gene]))],
                         exponentformat = 'none',
                         showexponent = 'all')
        fig.update_layout(margin = dict(l=0, r=0, t=0, b=0),
                          showlegend = False)
        graph = dcc.Graph(figure = fig, 
                          config = {'staticPlot': True})
        return graph

    
    def _key_item(self, tissue: str) -> html.Li:
        box = html.Div(style = {'height': 10, 
                                'width': 10,
                                'background-color': self.color_map[tissue],
                                'display': 'inline-block'})
        item = html.Li([box, tissue])
        return item
        

class GeneTable:
    
    '''Manages the component for the gene table.
    
    Attributes:
        cpm_plotter: CPMPlotter - plotter for in-table plots
        pos_scores: Dict - dictionary of positive scores for each tissue/timepoint
        neg_scores: Dict - dictionary of negative scores for each tissue/timepoint
        _table_controls: html.Div - components for controlling the table      
        ids: Dict - names of various components
        ngenes: int - number of genes displayed at a time
        app: dash.Dash - dash application
    
    '''

    def __init__(self, score_path: str, cpm_plotter: CPMPlotter, 
                 app: dash.Dash, score_name: str):
        self._read_scores(score_path)
        self.cpm_plotter = cpm_plotter
        self.app = app
        self.score_name = score_name
        self.ids = {
            'table': f'{score_name}-gene-table',
            'title': f'{score_name}-gene-table-title',
            'forward_button': f'{score_name}-forward-button',
            'back_button': f'{score_name}-back-button',
            'dropdown': f'{score_name}-neg-pos-dropdown'            
        }
        self._setup_table_controls()
        self.ngenes = 5

    def _read_scores(self, score_path: str):
        score_mat = pd.read_csv(score_path)
        pos_scores = {}
        neg_scores = {}
        for topic in score_mat.columns[1:]:
            topic_scores = score_mat[['gene', topic]]
            
            pos_topic = topic_scores[topic_scores[topic] > 0]
            pos_topic = pos_topic.sort_values(topic, ascending = False)
            pos_topic = pos_topic.reset_index(drop=True)
            pos_scores[topic] = pos_topic
            
            neg_topic = topic_scores[topic_scores[topic] < 0]
            neg_topic = neg_topic.sort_values(topic)
            neg_topic = neg_topic.reset_index(drop=True)
            neg_scores[topic] = neg_topic
            
        self.pos_scores = pos_scores
        self.neg_scores = neg_scores
    
    def _setup_table_controls(self):
        pos_neg_dropdown = dcc.Dropdown(
            id = self.ids['dropdown'],
            style = {'width': 200},
            options = [
                {'label': 'positive score', 'value': 'pos'},
                {'label': 'negative score', 'value': 'neg'}
            ],
            value = 'pos'
        )
        forward_button = html.Button(id = self.ids['forward_button'],
                                     children = 'Next Genes')
        back_button = html.Button(id = self.ids['back_button'],
                                  children = 'Previous Genes')
        controls = html.Div(
            style = {'display': 'flex'},
            children = [
                pos_neg_dropdown,
                back_button,
                forward_button
            ]
        )
        self._table_controls = controls
    
    def get_component(self) -> html.Div:
        title = html.Div(id = self.ids['title'], 
                         children = self._get_title(('BM', 'k1')))
        table = html.Div(id = self.ids['table'],
                         children = self._get_table(('BM', 'k1'), 0, True))
        key = self.cpm_plotter.tissue_key
        table_key = html.Div(
            style = {'display': 'flex'},
            children = [
                table,
                key
            ]
        )
        div = html.Div(
            style = {'display': 'flex',
                     'flex-direction': 'column'},
            children = [
                title,
                self._table_controls,
                table_key
            ]
        )
        return div
    
    def _get_title(self, tissue_topic: Tuple[str, str]) -> html.H2:
        tissue = tissue_topic[0]
        topic = tissue_topic[1]
        title = html.H2(f'Global Correlation: {topic} in {tissue}')
        return title

    def _get_table(self, tissue_topic: Tuple[str, str], 
                   start_rank: int, pos: bool) -> html.Table:
        table = html.Table(
            style = {'cellspacing': '0', 'cellpadding': '0'},
            children = [
                self._table_header(),
                self._table_body(tissue_topic, start_rank, pos)
            ]
        )
        return table
    
    def _table_header(self) -> html.Thead:
        header = html.Thead([
            html.Td('rank'), 
            html.Td('gene'), 
            html.Td(self.score_name),
            html.Td('cpm'),
            html.Td('cpm')
        ])
        return header
    
    def _table_body(self, tissue_topic: Tuple[str, str], 
                    start_rank: int, pos: bool) -> html.Tbody:
        scores = self._get_scores(tissue_topic, pos)
        if start_rank < 0: 
            start_rank = 0
        if start_rank > max(scores.index) - (self.ngenes - 1):
            start_rank = max(scores.index) - (self.ngenes - 1)
            
        rows = [self._table_row(tissue_topic, rank, pos) 
                for rank in range(start_rank, start_rank + self.ngenes)]
        return html.Tbody(rows)
            
    def _table_row(self, tissue_topic: Tuple[str, str], rank: int, pos: bool):
        scores = self._get_scores(tissue_topic, pos)
        gene = scores.loc[rank, 'gene']
        score = scores.loc[rank, tissue_topic[1]]
        all_plot = self.cpm_plotter.line_plot(gene)
        tissue_plot = self.cpm_plotter.line_plot(gene, tissue_topic[0])
        
        row = html.Tr([
            html.Td(rank),
            html.Td(gene),
            html.Td('{:.2f}'.format(score)),
            html.Td(all_plot),
            html.Td(tissue_plot)
        ])
        return row

    def _get_scores(self, tissue_topic: Tuple[str, str], pos: bool) -> Dict:
        if pos:
            return self.pos_scores[tissue_topic[1]]
        else:
            return self.neg_scores[tissue_topic[1]]

    def _tissue_topic_from_title(self, title: str) -> Tuple[str, str]:
        title_str = title['props']['children']
        split = title_str.split()
        tissue = split[-1]
        topic = split[-3]
        return (tissue, topic)
    
    def _rank_from_table(self, table: html.Table):
        body = table['props']['children'][1]
        first_row = body['props']['children'][0]
        rank_cell = first_row['props']['children'][0]
        start_rank = rank_cell['props']['children']
        return start_rank

    def register(self):
        '''Register associated callbacks with the dash app'''
        
        @self.app.callback(
            dash.dependencies.Output(self.ids['table'], 'children'),
            [dash.dependencies.Input(self.ids['title'], 'children'),
             dash.dependencies.Input(self.ids['dropdown'], 'value'),
             dash.dependencies.Input(self.ids['forward_button'], 'n_clicks'),
             dash.dependencies.Input(self.ids['back_button'], 'n_clicks')],
            state = [dash.dependencies.State(self.ids['table'], 'children')]
        )
        def update_table(title, dropdown, 
                         forward, back, table) -> html.Table:
            ctx = dash.callback_context
            
            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            tissue_topic = self._tissue_topic_from_title(title)
            pos = dropdown == 'pos'
            if trigger_id in [self.ids['title'], self.ids['dropdown']]:
                return self._get_table(tissue_topic = tissue_topic, 
                                       start_rank = 0, pos = pos)
            
            start_rank = self._rank_from_table(table)
            if trigger_id == self.ids['forward_button']:
                return self._get_table(tissue_topic = tissue_topic, 
                                       start_rank = start_rank + self.ngenes,
                                       pos = pos)
            else:
                return self._get_table(tissue_topic = tissue_topic,
                                       start_rank = start_rank - self.ngenes,
                                       pos = pos)
                
        @self.app.callback(
            dash.dependencies.Output(self.ids['title'], 'children'),
            [dash.dependencies.Input('topic-timecourse', 'clickData')]
        )
        def update_title(timecourse_click):
            if timecourse_click is None:
                raise dash.exceptions.PreventUpdate
            tissue_topic = timecourse_click['points'][0]['customdata']
            return self._get_title(tissue_topic)
                

class TissueGeneTable(GeneTable):

    '''Manages the component for a gene table with scores split by tissue.'''

    def __init__(self, score_path: str, cpm_plotter: CPMPlotter, 
                 app: dash.Dash, score_name: str):
        super().__init__(score_path, cpm_plotter, app, score_name)
        self.ids = {
            'table': f'tissue-{score_name}-gene-table',
            'title': f'tissue-{score_name}-gene-table-title',
            'forward_button': f'tissue-{score_name}-forward-button',
            'back_button': f'tissue-{score_name}-back-button',
            'dropdown': f'tissue-{score_name}-neg-pos-dropdown'            
        }
        self._setup_table_controls()


    def _read_scores(self, score_path: str):
        score_mat = pd.read_csv(score_path)
        pos_scores = {}
        neg_scores = {}

        for tissue in np.unique(score_mat['tissue']):
            for topic in score_mat.columns[2:]:
                topic_scores = score_mat[['tissue','gene', topic]]
                topic_scores = topic_scores[topic_scores['tissue'] == tissue]
                
                pos_topic = topic_scores[topic_scores[topic] > 0]
                pos_topic = pos_topic.sort_values(topic, ascending = False)
                pos_topic = pos_topic.reset_index(drop=True)
                pos_scores[(tissue, topic)] = pos_topic
                
                neg_topic = topic_scores[topic_scores[topic] < 0]
                neg_topic = neg_topic.sort_values(topic)
                neg_topic = neg_topic.reset_index(drop=True)
                neg_scores[(tissue, topic)] = neg_topic
            
        self.pos_scores = pos_scores
        self.neg_scores = neg_scores

    def _get_scores(self, tissue_topic: Tuple[str, str], pos: bool) -> Dict:
        if pos:
            return self.pos_scores[tissue_topic]
        else:
            return self.neg_scores[tissue_topic]

    def _get_title(self, tissue_topic: Tuple[str, str]) -> html.H2:
        tissue = tissue_topic[0]
        topic = tissue_topic[1]
        title = html.H2(f'Intra-Tissue Correlation: {topic} in {tissue}')
        return title