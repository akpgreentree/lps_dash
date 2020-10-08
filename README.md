# lps_dash
 
An app for looking at the results of topic modeling on some timecourse data. 

To run, from the parent directory: `python -m lps_dash`

It has three components:
* Timecourse topic plot: shows the percent of topics in each tissue over the timecourse
* Global correlation table: shows genes in order of Z-score for a given topic. Z-scores are calculated across the whole dataset.
* Intra-tissue table: shows genes in order of Z-score for a given topic and tissue. Z-scores are calculated within the tissue.

Click on a topic in the timecourse plot to look at that topic in the tables. Click on forward and back buttons in tables to page through the genes, and use the dropdowns to switch between positive and negative scores.

The line plots in the tables are normalized counts for the gene over the timecourse for each of the tissues.
