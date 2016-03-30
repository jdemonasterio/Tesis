#este file automatiza el procesamiento de simple_format (el surrogado) de cada uno de los .txt.gz de goedata en mexico 
#el working directory va a ser datosgeo/ con 3 subdirectorios a ser utilizados: ./testdata, ./Prepago, ./Pospago

import os
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
	#if argv[1] == "Prepago": callsToGC
	if argv[1] == "Prepago": contract_type = "/Prepago"	
	elif argv[1] == "Pospago": contract_type = "/Pospago"
	else: printUsage()
	
	rootdir = "/home/juan/mobility-study/datosgeo"
	for dir in os.walk(rootdir).next()[1]:
    	#for subdir in subdirs:
		#ejecutamos en cada dir. dentro de				
		#movemos el directorio hacia abajo
		os.chdir(rootdir + '/' +dir)
		#creamos el archivo y el comando que va a crear el archivo de todo lo procesado por simple_format concatenado en ese dir
		concat_file = "Geo_Voz_"+ contract_type[1:]+"_"+ "all_" + dir + ".txt.gz"
		bash_concat = "cat" +" " 
		##creamos las carpetas ./simple-format y  ./testdata si es que no existen
		if not os.path.exists(os.getcwd()+ "/testdata"):
			os.makedirs(os.getcwd()+"/testdata")
		if not os.path.exists(os.getcwd()+ "/simple_format"):
			os.makedirs(os.getcwd()+"/simple_format")

		for f in os.listdir(os.getcwd()+contract_type):
			if not(f.endswith(".gz")):
				continue

			print "Muevo el file %s a ./testdata \n" % (f,)
			bash_command_move = "mv" +" "  + "." + contract_type +"/"+ f +  " " + "./testdata"     
			subprocess.call(bash_command_move,shell=True)
		
			subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)
			print "Processing file %s  with Simple_format\n" % (f,)
			output = "./simple_format/simple_format_"+ contract_type[1:] + "_" + f.split("_")[-1] 
			bash_command_process = "../../SimpleFormat -P ./testdata/ -O " + output   +" "  +  \
				 "-A ./../../surrogated_antennas.txt.gz -N ./../../surrogated_nodes.txt.gz"
			subprocess.check_call(bash_command_process,shell=True)

			print "Vuelvo el file %s a %s \n" % (f, contract_type)	
			subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)	
			bash_command_unmove = "mv"+" "+ "./testdata/*" + " " + "." +  contract_type + "/"
			subprocess.call(bash_command_unmove,shell=True)
	##falta eliminar los headers de los files sabiendo que el output es {'Target':np.int32,'Destination':np.uint32,'TimeStamp':np.uint32,
# 'Duration':np.uint16, 'AntennaID':np.uint16}. esto va a ayudar despues en el pipeline para hacer un cat de todos los simple_format y un pd.read_csv
# cuando quiera levantar el archivo general.
			#obs. es conveniente guardar el archivo primero en un tmp.txt.gz por un tema de buffering no llega a sobreescribirse
			print "Elimino el header del file %s\n" %output	
			bash_command_remove1 = "gzip -dc"+" "+ output+ " " + "| tail -n +2 | gzip -c >" + " " + "tmp.txt.gz;" +  \
					"mv -f tmp.txt.gz" + " " + output  	
			subprocess.check_call(bash_command_remove1,shell=True)
			bash_concat += output +" " 
		bash_concat +=">"+ " " + concat_file
		subprocess.check_call(bash_concat,shell=True)
####notifica por mail los resultados
	#args = "echo $(date) | mail -s The_Mundo_Sano_program_finished_running carolang@grandata.com"
	#os.system(args)

if __name__=='__main__':
	main(len(sys.argv), sys.argv)
