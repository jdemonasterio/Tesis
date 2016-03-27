#este file automatiza el mapping mensual de usuarios a una lista de antenas. Le entra un dataset de CDRs etiquetados con antenas de origin y
#outputea un file dictionary salvado en formato pickle 
#el working directory va a ser datosgeo/ y va a iterar sobre todos los meses ahi adentro

import pandas as pd; import numpy as np; import os;import random;
import cPickle as pickle
import sys
import subprocess

#esta funcion crea el print de como usar bien este archivo para cuando estan mal el numero de parametros	
def printUsage():
	print "Usage:"
	print "python to_simple_format_mexico.py [paid_type] \n"
	print "contract_type = 'Prepago' to get the surroation for prepaid contract lines \n"
	print "contract_type = 'Pospago' to surroagte for postpaid contract lines \n"

def main(argc, argv):
	if argc == 1:
		printUsage()
		return 0
	
	if argv[1] == "Prepago": contract_type = "Prepago"
	elif argv[1] == "Pospago": contract_type = "Pospago"	
	else: printUsage()
	
	rootdir = "/home/juan/mobility-study/datosgeo"
	for directory in os.walk(rootdir).next()[1]:
	    print "directory is currently %s "%  directory
	    subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)
	    tabla_mensual = pd.read_csv(directory +'/Geo_Voz_' + contract_type  +  '_all_' + directory + '.txt.gz',sep = " ", 
			  names = ['Target','Destination','Direction','TimeStamp','Duration','AntennaID'],
					 engine = 'c',index_col=None, lineterminator='\n', skipinitialspace=True, 
				header=None,dtype = {'Target':np.int32,'Destination':np.uint32,'TimeStamp':np.uint32,
						  'Duration':np.uint16,'AntennaID':np.uint16,'Direction':np.object_})
	    print "checking for insignificant users"
	    subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)
	    insignificant_users = tabla_mensual['Target'].value_counts()[(tabla_mensual['Target'].value_counts() <= 5) \
				| (tabla_mensual['Target'].value_counts() >= 400)].index.values.tolist()
	    #filtro los usuarios irrelevantes y armo el diccionario con key= users, values = antenna_list 
	    print "mapping user to antennas dict"
	    subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)
	    user_antenna_map = tabla_mensual[~tabla_mensual['Target'].isin(insignificant_users)] \
			.groupby('Target')['AntennaID'].apply(lambda x: x.tolist()).to_dict();
	    
	    name_file = directory + "/" + 'Geo_Voz_Pospago_user-antenna-map_' + directory +'.p' 
	    print "dumping to pickle file %s" %name_file
	    subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)	
	    with open(name_file, 'wb') as fp:
		pickle.dump(user_antenna_map, fp)

if __name__=='__main__':
	main(len(sys.argv), sys.argv)
