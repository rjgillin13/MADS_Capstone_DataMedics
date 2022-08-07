# + tags=["parameters"]
# # + tags=["parameters"]
# declare a list tasks whose products you want to use as inputs
upstream = []
random_seed = 42
# + tags=[]



# + tags=[]



# + tags=["injected-parameters"]



# + [markdown] tags=[]
# importing all the functions defined in tools_rjg.py

# + tags=[]
from tools_rjg import *

# + tags=[]
import pandas as pd
import re, nltk, spacy, gensim
nltk.download('punkt')
import pickle
import altair as alt
from sklearn.model_selection import GridSearchCV
from collections import defaultdict
from PIL import Image
import os
from altair_saver import save
from tqdm import tqdm

# + tags=[]
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD

# + tags=[]
import matplotlib.pyplot as plt
# %matplotlib inline

# + tags=[]



# + tags=[]



# + tags=[]
df_all = generate_disaster_type_dataframe(disaster_types = ('earthquake', 'fire', 'flood', 'hurricane')
                                          , dev_train_test= ('dev', 'train', 'test'))

# + tags=[]



# + tags=[]
df_all['tweet_text_cleaned'] = df_all['tweet_text'].apply(lambda x: tweet_preprocessing(x))
df_all['lemmatized'] = df_all['tweet_text_cleaned'].apply(lambda x: lemmatize_tweet_text(x, allowed_postags=('NOUN', 'ADJ', 'VERB', 'ADV')))

# + tags=[]
#limit records for testing purposes
# df_all = df_all.sample(100)
# -

with open("output\\vectorizer_countVec.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# +
## Grid Search Model Parameters

# Define Search Param
n_topics = [2, 3, 4, 5, 6]
search_params = {'n_components': n_topics, 'learning_decay': [.5, .7, .9]}

# -

disaster_types = ['earthquake','fire','flood','hurricane']

grid_search_results = defaultdict(dict)
log_liklihoods = defaultdict(dict)
for disaster_type in tqdm(disaster_types):
    if disaster_type == 'earthquake':
        tweets_vectorized =  vectorizer.transform(list(df_all[df_all['disaster_type']=='earthquake']['lemmatized']))
    elif disaster_type == 'fire':
        tweets_vectorized =  vectorizer.transform(list(df_all[df_all['disaster_type']=='fire']['lemmatized']))
    elif disaster_type == 'flood':
        tweets_vectorized =  vectorizer.transform(list(df_all[df_all['disaster_type']=='flood']['lemmatized']))
    elif disaster_type == 'hurricane':
        tweets_vectorized =  vectorizer.transform(list(df_all[df_all['disaster_type']=='hurricane']['lemmatized']))
        
    # Init the Model
    lda = LatentDirichletAllocation()

    # Init Grid Search Class
    model = GridSearchCV(lda, param_grid=search_params)

    # Do the Grid Search
    model.fit(tweets_vectorized)
    
    # Best model
    best_lda_model = model.best_estimator_
    
    # Model Parameters
    grid_search_results[disaster_type]['best_params'] = model.best_params_

    # Log Likelihood Score
    # Higher is better
    grid_search_results[disaster_type]['best_score'] = model.best_score_

    # Perplexity
    grid_search_results[disaster_type]['best_perplexity'] = best_lda_model.perplexity(tweets_vectorized)
    
    # Build log liklihood dict
    
    log_liklihoods[disaster_type]['0.5'] = [(model.cv_results_['params'][index]['n_components'],round(model.cv_results_['mean_test_score'][index])) for index, gscore in enumerate(model.cv_results_['params']) if gscore['learning_decay']==0.5]
    log_liklihoods[disaster_type]['0.7'] = [(model.cv_results_['params'][index]['n_components'],round(model.cv_results_['mean_test_score'][index])) for index, gscore in enumerate(model.cv_results_['params']) if gscore['learning_decay']==0.7]
    log_liklihoods[disaster_type]['0.9'] = [(model.cv_results_['params'][index]['n_components'],round(model.cv_results_['mean_test_score'][index])) for index, gscore in enumerate(model.cv_results_['params']) if gscore['learning_decay']==0.9]




log_liklihoods



log_scores_df = pd.DataFrame(log_liklihoods)
log_scores_df = log_scores_df.stack().reset_index().rename(columns={'level_0':'learning_decay','level_1':'disaster_type'})
log_scores_df = log_scores_df.explode(0)
log_scores_df['n_topics'] = log_scores_df[0].apply(lambda x: x[0])
log_scores_df['log_liklihood_score'] = log_scores_df[0].apply(lambda x: x[1])
log_scores_df = log_scores_df[['learning_decay','disaster_type','n_topics','log_liklihood_score']]
log_scores_df.head()

# ## Optimal Topics

# +
base = alt.Chart(log_scores_df).mark_line().encode(
    x=alt.X('n_topics:O',title = 'Number of Topics',axis=alt.Axis(labelAngle=0)),
    y=alt.Y('log_liklihood_score:Q',title = 'Log-Liklihood Score'),
    color='learning_decay',
    facet=alt.Facet('disaster_type:N', title=None,header=alt.Header(labelFontSize=20))
)

n_topics_chart = base.properties(
    title='Optimal Number of Topics (Log-Liklihood Scores)',
    width=600,
    height = 400).configure_title(
    fontSize=20,
    anchor='start',
    color='black'
).configure_axis(
    labelFontSize=20,
    titleFontSize=20
).configure_legend(
    labelFontSize=20,
    titleFontSize=20
)
# -

n_topics_chart

# + [markdown] tags=[]
#

# + tags=[]
# src_file_path = os.path.dirname(os.path.abspath("__file__"))
# filename = os.path.join(src_file_path, 'output\optimal_topics.png')
# n_topics_chart.save(filename)
# -


