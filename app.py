import pandas as pd
import streamlit as st
import numpy as np
import re
import string
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

@st.cache
def get_data():
    df = pd.read_csv('full_track_list')
    keys = pd.read_excel('harmonic_keys.xls', index_col=0).reset_index()
    return df, keys

df, keys = get_data()

filter_list = ['name', 'artist', 'energy', 'tempo', 'key_camelot', 'key_scale_degree']



search_word = st.sidebar.text_input('Enter a song')
search_artist = st.sidebar.text_input('Enter an artist')
harmonic_button = st.sidebar.checkbox('Harmonic?')
percentage_button = st.sidebar.checkbox('Select BPM %')
neighbours_button = st.sidebar.checkbox('Neighbours?')


def clean(word):
    # Remove Unicode
    clean_search_word = re.sub(r'[^\x00-\x7F]+', ' ', word)
    # Remove Mentions
    clean_search_word = re.sub(r'@\w+', '', clean_search_word)
    # Lowercase the document
    clean_search_word = clean_search_word.lower()
    # Remove punctuations
    clean_search_word = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', clean_search_word)
    # Lowercase the numbers
    clean_search_word = re.sub(r'[0-9]', '', clean_search_word)
    # Remove the doubled space
    clean_search_word = re.sub(r'\s{2,}', ' ', clean_search_word)
    
    return clean_search_word

def vert(letter):
    if letter == 'A':
        return 'B'
    else:
        return 'A'
    
def new_camelot(string):
    mask = keys['full_key'].str.contains(string)
    camelot_filter = keys[mask]['key_camelot'].values[0]
    if len (camelot_filter) == 3:
        first = camelot_filter[0:2]
        second = camelot_filter[-1]
        if first == '12':
            right = '1'
        else:
            right = str(int(first)+1)
        left = str(int(first)-1)
        vertical = vert(second)
        full_left = left+second
        full_right = right+second
        full_vertical = first+vertical
        return camelot_filter, full_left, full_right, full_vertical
    else:
        first = camelot_filter[0]
        second = camelot_filter[1]
        if first == '1':
            print('y')
            left = '12'
        else:
            left = str(int(first)-1)
        right = str(int(first)+1)
        vertical = vert(second)
        full_left = left+second
        full_right = right+second
        full_vertical = first+vertical
        return camelot_filter, full_left, full_right, full_vertical
    
def bpm_filter(bpm):
    bpm = float(bpm)
    lower = bpm*0.95
    higher = bpm*1.05
    return lower, higher

def neighbors(df, song):
    # change variables
    X = df.drop(columns=['name', 'artist', 'key_s', 'mode_s', 'full_key', 'key_piano', 'key_camelot', 'key_open','key_scale_degree','clean_name', 'clean_artist', 'tempo'],axis=1)
    song = song.drop(columns=['name', 'artist', 'key_s', 'mode_s', 'full_key', 'key_piano', 'key_camelot', 'key_open','key_scale_degree','clean_name', 'clean_artist', 'tempo'],axis=1)
    #scale
    minmax_scaler = MinMaxScaler()
    X_scaled = minmax_scaler.fit_transform(X)
    #PCA
    pca = PCA(n_components=6)
    pca.fit(X_scaled)
    pc = pd.DataFrame(pca.components_).T.iloc[:,:6]
    #Create PCA DF
    new_df = np.dot(X_scaled,pc)
    new_df = pd.DataFrame(new_df)
    #Kmeans
    kmeans = KMeans(n_clusters = 6)
    kmeans.fit(new_df)
    #Add cluster to new df and return filtered df
    df['cluster'] = kmeans.labels_
    df = df.reset_index()
    new_song = df[df['index'] == song.index[0]]
    #print(df.shape)
    #print(song.index[0])
    #print(df.iloc[song.index[0]])
    return df[df['cluster'] == df.iloc[new_song.index[0]]['cluster']]

# Search function
if search_word and not search_artist and not harmonic_button and not percentage_button and not neighbours_button:
    matched = df['clean_name'].str.contains(clean(search_word), na=False)
    df = df[matched]
    st.table(df[filter_list])
    
elif search_word and search_artist and not harmonic_button and not percentage_button and not neighbours_button:
    matched = df['clean_name'].str.contains(clean(search_word), na=False)
    df = df[matched]
    matched2 = df['clean_artist'].str.contains(clean(search_artist), na=False)
    df = df[matched2]
    st.table(df[filter_list])

elif search_word and search_artist and harmonic_button and not percentage_button and not neighbours_button:
    matched = df['clean_name'].str.contains(clean(search_word), na=False)
    df_2 = df[matched]
    matched2 = df_2['clean_artist'].str.contains(clean(search_artist), na=False)
    get_key = df_2[matched2]['full_key'].values[0]
    x = list(new_camelot(get_key))
    last_df = df[df['key_camelot'].isin(list(x))].sort_values('tempo',ascending=False)
    st.table(last_df[filter_list])
    
elif search_word and search_artist and harmonic_button and percentage_button and not neighbours_button:
    matched = df['clean_name'].str.contains(clean(search_word), na=False)
    df_2 = df[matched]
    matched2 = df_2['clean_artist'].str.contains(clean(search_artist), na=False)
    get_key = df_2[matched2]['full_key'].values[0]
    bpm_seed = df_2[matched2]['tempo'].values[0]
    x = list(new_camelot(get_key))
    last_df = df[df['key_camelot'].isin(list(x))].sort_values('tempo',ascending=False)
    filtered_bpm = last_df[last_df['tempo'].between(bpm_filter(bpm_seed)[0],bpm_filter(bpm_seed)[1])]
    st.table(filtered_bpm[filter_list])
    
elif search_word and search_artist and harmonic_button and percentage_button and neighbours_button:
    matched = df['clean_name'].str.contains(clean(search_word), na=False)
    df_2 = df[matched]
    matched2 = df_2['clean_artist'].str.contains(clean(search_artist), na=False)
    get_key = df_2[matched2]['full_key'].values[0]
    bpm_seed = df_2[matched2]['tempo'].values[0]
    song = df_2[matched2]
    x = list(new_camelot(get_key))
    last_df = df[df['key_camelot'].isin(list(x))].sort_values('tempo',ascending=False)
    filtered_bpm = last_df[last_df['tempo'].between(bpm_filter(bpm_seed)[0],bpm_filter(bpm_seed)[1])]
    new_df = neighbors(filtered_bpm, song)
    st.table(new_df[filter_list])
    
else:
    st.table(df[filter_list])
