#este file automatiza el procesamiento de home_clean_mexico.cpp:x  de cada uno de los .txt.gz de goedata en mexico 

#el working directory va a ser datosgeo/ con 3 subdirectorios a ser utilizados: ./testdata, ./Prepago, ./Pospago

import os
import sys
import subprocess

#esta funcion crea el print de como usar bien este archivo para cuando estan mal el numero de parametros	
def printUsage():
	print "Usage:"
	print "python to_simple_format_mexico.py [paid_type] \n"
	print "contract_type = 'Prepago'  to get the mapping for these contract types\n"
	print "contract_type = 'Pospago' to get the mapping for these contract types \n"
	print "python to_simple_format_mexico.py [paid_type] \n"
	print "night_filter = Bool  to filter for CDRs made in non-working hours \n"
	print "weekend = Bool to get the mapping for these contract types \n"
	
def main(argc, argv):
	if argc == 1:
		printUsage()
		return 0
	#if argv[1] == "Prepago": callsToGC
	if argv[1] == "Prepago": contract_type = "Prepago"	
	elif argv[1] == "Pospago": contract_type = "Pospago"
	else: printUsage()
	
	rootdir = "/home/juan/mobility-study/datosgeotest/"
	for dir in ["0114"]:
    	#for subdir in subdirs:
		#ejecutamos en cada dir. dentro del datosgeo				
		#movemos el directorio hacia abajo
		os.chdir(rootdir + dir)
		#creamos las carpetas si ya no existe de /testdata y /user_antenna_map
		if not os.path.exists(os.getcwd()+ "/testdata"):
                        os.makedirs(os.getcwd()+"/testdata")
                if not os.path.exists(os.getcwd()+ "/user_antenna_map"):
                        os.makedirs(os.getcwd()+"/user_antenna_map")

		f = "Geo_Voz_%s_all_%s.txt.gz" % (contract_type,dir)

		print "Muevo el file %s a ./testdata \n" % (f,)
		bash_command_move = "mv ./%s ./testdata" % (f,)    
		subprocess.call(bash_command_move,shell=True)
		subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)
		print "Processing file %s  with user_clean_mexico \n" % (f,)
		
		output = "./user_antenna_map/user_antenna_map_%s_%s.txt" %(contract_type,dir) 
		bash_command_process = "zcat ./testdata/%s | ./../../scripts-antennas-preprocessing/home_clean_mexico  | gzip > %s.gz" % (f,output )
		subprocess.check_call(bash_command_process,shell=True)
		
		print "Vuelvo el file %s al dir %s \n" % (f,dir)	
		subprocess.call("echo $(date);echo  \"UTC es+ 3 horas\" ",shell=True)
		bash_command_unmove = "mv ./testdata/* ./"
		subprocess.call(bash_command_unmove,shell=True)
	
		


####notifica por mail los resultados
	#args = "echo $(date) | mail -s The_Mundo_Sano_program_finished_running carolang@grandata.com"
	#os.system(args)

if __name__=='__main__':
	main(len(sys.argv), sys.argv)
