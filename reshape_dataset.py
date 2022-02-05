# Drawful Submissions, matched with answers

# load python libraries
import pandas as pd
import numpy as np

# load source data sets
responses = pd.read_csv('data\\IronViz Art - Drawful Quiz (Responses) - Form Responses 1.csv')
answers = pd.read_csv('data\\answers.csv')
responders = pd.read_csv('data\\responder_lookup.csv')
sankey_model = pd.read_csv('data\\sankey_model.csv')

# rename columns for responses data set
responses.columns = ['timestamp','img-1','img-2','img-3','img-4','img-5','img-6']
responses['response_id'] = responses.index

# remove response at timestamp 1/20/2022 7:10:59
# Even Tom who originally knew all the answers still got one wrong!
responses = responses.loc[responses['timestamp'] != '1/20/2022 7:10:59']

# unpivot (wide to long) the responses data sets and lookup answers to responders
response_df = pd.melt(responses, id_vars=['response_id','timestamp'], var_name='image', value_name='response')
response_df = pd.merge(answers, response_df,how='left',left_on=['image','answer'],right_on=['image','response'])
response_df = pd.merge(response_df,responders,how='inner',on='Responder')

# create sankey data model
combo_df = response_df[['response_id','image','responder_id']]
combo_df = combo_df.loc[combo_df['response_id'] >= 0]
combo_df = combo_df.pivot(index='response_id',columns='image')['responder_id'].reset_index()
combo_df['Link'] = 'link'
combo_df['Size'] = 1
combo_df['type'] = 'response'

# rename columns
cols = ['ID', 'Step 1', 'Step 2', 'Step 3','Step 4', 'Step 5', 'Step 6','Link', 'Size', 'Type']
combo_df.columns = cols

# aggregrate to find answer combination size
combo_df = combo_df.groupby(['Step 1', 'Step 2', 'Step 3','Step 4', 'Step 5', 'Step 6','Link', 'Type']).agg(Size=('Size','sum')).reset_index()
combo_df['ID'] = combo_df.index
combo_df = combo_df[cols]

# create parameter entry in data set as a single point set to 0
# in tableau this entry will be updated by parameter actions
s1 = [0]
s2 = [0]
s3 = [0]
s4 = [0]
s5 = [0]
s6 = [0]

para_df = pd.DataFrame()
para_df['Step 1'] = s1
para_df['Step 2'] = s2
para_df['Step 3'] = s3
para_df['Step 4'] = s4
para_df['Step 5'] = s5
para_df['Step 6'] = s6

para_df['ID'] = -1
para_df['Link'] = 'link'
para_df['Size'] = 1
para_df['Type'] = 'parameter'
para_df = para_df[cols]

# combine parameter data with responses data for sankey
sankey_df = pd.concat([combo_df,para_df])

# create a general dataset that counts the responses for each image
ironviz_df = response_df.groupby(['image', 'responder_id', 'response']).agg(responses=('response_id','count')).reset_index()

# identify where answers have been correctly interpreted
response_df['correct_answer'] = np.where(response_df['responder_id']==1,1,0)
correct_answers_df = response_df.groupby(['response_id']).agg(correct_answers=('correct_answer','sum')).reset_index()
correct_answers_df = correct_answers_df.groupby(['correct_answers']).agg(player_frequency=('response_id','count')).reset_index()

# add in data for missed answers and concat
missed_options = pd.DataFrame()
missed_options['correct_answers']=[5,6]
missed_options['player_frequency']=[0,0]
correct_answers_df = pd.concat([correct_answers_df,missed_options])

# not sure this is needed
#fooled_by_df = response_df.groupby(['responder_id','response_id']).agg(responses=('response','count')).reset_index()
#fooled_by_df.pivot(index='response_id', columns='responder_id', values='responses')

# create a data set for the radar charts
radar_df = response_df.groupby(['responder_id','image']).agg(responses=('response','count')).reset_index()
radar_df['total_responses'] = len(response_df['response_id'].drop_duplicates())
radar_df['percentage_response'] = radar_df['responses'] / radar_df['total_responses'] 
radar_df['outer_radius'] = 0.5

# write output data sets to csv
sankey_df.to_csv('output\\sankey_df.csv', encoding='utf-8-sig', index=False)
ironviz_df.to_csv('output\\ironviz_df.csv', encoding='utf-8-sig', index=False)
radar_df.to_csv('output\\radar_df.csv', encoding='utf-8-sig', index=False)
correct_answers_df.to_csv('output\\correct_answers_df.csv', encoding='utf-8-sig', index=False)

# write sankey data to Excel
with pd.ExcelWriter('output\\Sankey Template Multi Level - Drawful.xlsx') as writer:  
    sankey_df.to_excel(writer, sheet_name='Data', index=False)
    sankey_model.to_excel(writer, sheet_name='Model', index=False)

