import pandas as pd
import numpy as np
import os
import random;
import time

import matplotlib.pyplot as plt
from sklearn import cluster
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


np.random.seed(2015)
#rootdir="/Users/jampper/Repositories/analytics/UserAnalytics"



input_file= 'tables/test.txt.gz' #% (directory,contract_type,directory)

def get_output_file(input_file,hash_map=False,night_filter=False,week_end=False):
    output = input_file.replace(".txt.gz","")
    if week_end == True:
        output = output + "_wkend"
    if night_filter == True:
        output = output + "_ngtfilter"
    if hash_map == True:
        output = output + "_usr_hash_map"
    return output + "_output.txt.gz"

output_file = get_output_file(input_file)

selected_attributes = pd.read_csv(
            "DevicesTesting.csv.gz",
            engine = 'c',
#            chunksize = 5*10**5,
#            iterator =True,
            sep = ',',
            skipinitialspace=True,
#            skiprows=2,
            #skipfooter =1,
#            header = 0,
            index_col=0,
            compression = "gzip",    
#            names = ['user_id','event_id','lead_event'],
#            converters =  {'lead_event':strip},
#            na_values=na_val,
            #usecols = ['Target', 'AntennaID','TimeStamp']
            #dtype = {'event_id':np.uint16}
            )



def get_user_hash_map(table):
    if isinstance(table, str):
        pd.read_csv(
            table,
            engine = 'c',
#            chunksize = 5*10**5,
#            iterator =True,
            sep = ',',
            skipinitialspace=True,
#            skiprows=2,
            #skipfooter =1,#la ultima fila en la ultima columna viene vacia por el LEAD de SQL, la descarto
#            header = 0,
            index_col=0,
#            names = ['user_id','event_id','lead_event'],
#            converters =  {'lead_event':strip},
#            na_values=na_val,
            #usecols = ['Target', 'AntennaID','TimeStamp']
            #dtype = {'event_id':np.uint16}
            )
    
    #convertimos el indice de la tabla de selected attributes a una mapa para que sea mas facil
    vals = range(1, len(table)+1 ) #con +1 porque me gusta pensar que los datos son positivos y los NAn==-1
    user_hash_range_map = dict(zip(table.index.values, vals))
    user_hash_range_map = pd.DataFrame.from_dict(user_hash_range_map,orient='index',dtype=np.uint32)
    user_hash_range_map.columns=['int_map']
    user_hash_range_map.index.name = 'user_hash'
    user_hash_range_map.sort_values(by='int_map',inplace=True)
    user_hash_range_map = user_hash_range_map['int_map']

    #paso a diccionario y mapeo el indice
    user_hash_range_dict = user_hash_range_map.to_dict()
    
    return user_hash_range_dict


user_hash_range_dict=get_user_hash_map(selected_attributes)
selected_attributes.index = pd.Series({x: user_hash_range_dict[x] for x in selected_attributes.index})

X = selected_attributes

X.shape,
if (X.shape[0]*X.shape[1]) > 12*10**6:
    print("Warning, total # of cells is %d" %(X.shape[0]*X.shape[1]))

pca = PCA(n_components=0.9).fit(X)
reduced_data = PCA(n_components=0.9).fit_transform(X)



i_dataset =0
start_time = time.time()
def elapsed_time(start_time):
    return time.time() - start_time
print('Scaling Data \n elapsed time is: %s' % elapsed_time(start_time) )
X = StandardScaler().fit_transform(X)

# estimate bandwidth for mean shift
#print('estimate bandwidth for mean shift \n current time is: %s' % elapsed_time(start_time) )
#bandwidth = cluster.estimate_bandwidth(X, quantile=0.3)

# connectivity matrix for structured Ward
print('connectivity matrix for structured Ward \n current time is: %s' % elapsed_time(start_time) )
connectivity = kneighbors_graph(X, n_neighbors=10, include_self=False)

print('make connectivity symmetric \n elapsed time is: %s' % elapsed_time(start_time) )
# make connectivity symmetric
connectivity = 0.5 * (connectivity + connectivity.T)

print('create clustering estimators \n elapsed time is: %s' % elapsed_time(start_time) )
# create clustering estimators

#ms = cluster.MeanShift(bandwidth=bandwidth, bin_seeding=True)

kmeans = cluster.KMeans(n_clusters=4)
ward = cluster.AgglomerativeClustering(n_clusters=4, linkage='ward',
                                       connectivity=connectivity)
spectral = cluster.SpectralClustering(n_clusters=4,
                                      eigen_solver='arpack',
                                      affinity="nearest_neighbors")
dbscan = cluster.DBSCAN(eps=.2)
affinity_propagation = cluster.AffinityPropagation(damping=.9,
                                                   preference=-200)

average_linkage = cluster.AgglomerativeClustering(
    linkage="average", affinity="cityblock", n_clusters=4,
    connectivity=connectivity)

birch = cluster.Birch(n_clusters=4)
clustering_algorithms = [
    ward, affinity_propagation, spectral, kmeans, average_linkage,
    dbscan, birch] #+ [ms]
clustering_names = [
    'Ward','AffinityPropagation', 
    'SpectralClustering', 'KMeans',  'AgglomerativeClustering',
    'DBSCAN', 'Birch']  #+ ['MeanShift']

#plt.figure(figsize=(len(clustering_names) * 2 + 3, 9.5))
#plt.subplots_adjust(left=.02, right=.98, bottom=.001, top=.96, wspace=.05,
                  #  hspace=.01)
#plot_num = 1

time.time()
print('Algorithm iterator fitting \n elapsed time is: %s' % elapsed_time(start_time) )
for name, algorithm in zip(clustering_names, clustering_algorithms):
    # predict cluster memberships
    t0 = time.time()
    algorithm.fit(X)
    t1 = time.time()
    print('Testing clustering model %s \n elapsed time is: %s' % (name, elapsed_time(start_time)) )
    if hasattr(algorithm, 'labels_'):
        y_pred = algorithm.labels_.astype(np.int)
        selected_attributes['pred_%s'%name] = y_pred
    else:
        y_pred = algorithm.predict(X)

#agarro solo las columnas de la prediccion y lo guardo en un archivo comprimido
selected_attributes[selected_attributes.columns[-len(clustering_names)]].to_csv(
                    'clustering_test_output.gz', 
                           sep=',',
#                           float_format="%.4f",
                           header = True,
                           index=True,
                           compression = 'gzip'
                          )

