import argparse
from . import app

lps_topic_path = '/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/topics.csv'
lps_cpm_path = '/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/cpm.gct'
lps_global_z_path = '/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/topic_Z.csv'
lps_tissue_z_path = '/project2/nchevrier/projects/cytokines/output/tables/bulkRNAseq/LPS/tissue_topic_Z.csv'

class CLI:

    '''Command Line Interface for running analyses'''
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description = "Dashboard for visualizing topics."
        )
        self.parser.add_argument('--topics', default = lps_topic_path,
                                 help = 'Path to topics csv.')                         
        self.parser.add_argument('--cpm', default = lps_cpm_path,
                                 help = 'Path to cpm gct.')
        self.parser.add_argument('--global_z', default = lps_global_z_path,
                                 help = 'Path to z-score csv.')
        self.parser.add_argument('--tissue_z', default = lps_tissue_z_path,
                                 help = 'Path to lfc csv.')
        self.parser.add_argument(
            '--local', action = 'store_true',
            help = 'Running on a local machine (instead of midway).'
        )

    def _setup_app(self):
        self.app = app.MainApp(self.args.topics, self.args.cpm,
                               self.args.global_z, self.args.tissue_z, 
                               self.args.local)

    def main(self, args=None):
        if args:
            self.args = self.parser.parse_args(args)
        else:
            self.args = self.parser.parse_args()

        self._setup_app()
        self.app.main()