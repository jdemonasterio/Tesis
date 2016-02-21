#este file automatiza todos los llamados de bash al calls_involving_GC_by_antenna_mexico.cpp asumiendo que ya tenemos la estructura del directorio necesaria y que esta realizado el build del .cpp

import os
import sys

#se puede pensar que estas tres listas en verdad es una lista de truplas
#donde en c/ una tenes el un mes, con el anyo al cual corresponde e informacion de cuantos dias tiene ese mes.
years = ["2011", "2011", "2012", "2012", "2012"]
months = [11, 12, 1, 2, 3]
###OJO CON anyos bisiestos!
daylims = [30, 31, 31, 29, 31]

#dir change
inpath = "../../surrogations_ca/output_direction/"
#padnum le agrega el 0 al string si el mes/dia es de un digito, si no lo deja como esta (todo queda 2 digitos)
def padNum(n):
	return ("0" if n < 10 else "") + str(n)

#el input es el numero del mes e itera sobre todos esos dias para generar un string del infile bien largo. 
def generateInfile(m):
	infile = ""
	for d in range(1, daylims[m]+1):
		#es clave notar aca que hay un espacio entre cada "infile" individual porque despues se hace bash zcat infile
		infile = infile + " " + inpath + "surrogated_ordered_" + years[m] + padNum(months[m]) + padNum(d) + ".csv.gz"
	infile = infile[1:]
	return infile

def callsToGC():
	for mode in ["in", "out"]:
		for i in range(5):
			for region in ['gran_chaco_limpiojuan', 'anatuya', 'pampa_del_indio']:	
				infile = generateInfile(i)
				outfile = "data/calls_involving_GC_by_antenna/" + region + "_" + years[i] + padNum(months[i]) + "_" + mode + ".csv.gz"
				file_antennas = "data/" + region + ".txt"
				file_home = "../../surrogations_ca/data_files/home_antenna_ca.csv"
				### es verdad que..? en este paso calls_involving_GC ya es un build del archivo con mismo nombre.cpp y por lo tanto es un ejecutable y donde le paso los aprametros file_antennas, file_home y mode?
				bash_command = "zcat " + infile + " | ./calls_involving_GC_by_antenna " + file_antennas + " " + file_home + " " + mode + " | gzip > " + outfile    #esta ultima parte comprime y lo escribe en el outfile
				print "Executing", bash_command
				os.system(bash_command)

#es muy similar al callsToGC solo que sobre el generate_calls_per_province.cpp				
def callsPerProvince():
	for i in range(5):	
		infile = generateInfile(i)
		outfile = "data/calls_per_province/" + years[i] + padNum(months[i]) + ".csv.gz"
		file_home = "../../surrogations_ca/data_files/home_antenna_ca.csv"

		bash_command = "zcat " + infile + " | ./generate_calls_per_province " + file_home + " | gzip > " + outfile
		#print "Executing", bash_command
		os.system(bash_command)
	return

#esta funcion crea el print de como usar bien este archivo para cuando estan mal el numero de parametros	
def printUsage():
	print "Usage:"
	print "python calls_involving_GC_by_antenna.py [mode]"
	print "mode = 'gc' to get the summary of traffic by antenna (total and vulnerable users and calls)"
	print "mode = 'prov' to get the amount of traffic between each pair of provinces"

def main(argc, argv):
	if argc == 1:
		printUsage()
		return 0
	if argv[1] == "gc": callsToGC()
	elif argv[1] == "prov": callsPerProvince()
	else: printUsage()

	#notifica por mail los resultados
	args = "echo $(date) | mail -s The_Mundo_Sano_program_finished_running carolang@grandata.com"
	os.system(args)

if __name__=='__main__':
	main(len(sys.argv), sys.argv)
