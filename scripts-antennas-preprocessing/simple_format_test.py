#la idea es correr este script para probar el bash y ademas  procesar con simpleformat distintas combinaciones de corridas para probar.
#e..g con 3 dias con 15 dias con un mes.. y agarrando random..  


inpath= "./datosgeo/output_direction/"

def padNum(n):
	return ("0" if n < 10 else "") + str(n)
#padnum le agrega el 0 al string si el mes es de un digito, si no lo deja como esta (todo queda 2 digitos)

def generateInfile(m):
	infile = ""
	for d in range(1, daylims[m]+1):
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

				bash_command = "zcat " + infile + " | ./calls_involving_GC_by_antenna " + file_antennas + " " + file_home + " " + mode + " | gzip > " + outfile
				print "Executing", bash_command
				os.system(bash_command)
				
def callsPerProvince():
	for i in range(5):	
		infile = generateInfile(i)
		outfile = "data/calls_per_province/" + years[i] + padNum(months[i]) + ".csv.gz"
		file_home = "../../surrogations_ca/data_files/home_antenna_ca.csv"

		bash_command = "zcat " + infile + " | ./generate_calls_per_province " + file_home + " | gzip > " + outfile
		#print "Executing", bash_command
		os.system(bash_command)
	return
	
def printUsage():
	print "Usage:"
	print "python calls_involving_GC_by_antenna.py [number] [mode] [date]"
	print "number = number of contiguous date files to be selected from on same month. If 30 or more will select whole month"
	print "mode = 'Prepago' to get data from Prepaid numbers only"
	print "mode = 'Pospago' to get data from Postpaid  numbers only"
	print "date = '11/14' to get the summary of data for that month/year"


#va primero la cantidad de dias consecutivos  que quiero procesar N (con N = a 30 ya es todo el mes)
# despues va el tipo de contrato ya sea prepago/postpago y despues va el date en fromato month/year e.g. 09/15




def main(argc, argv):
##primero seteo locale a "en_US.UTF-8" para homogeneizar el encoding de los archivos porque tira muchos errores sino el SimpleFormat
	os.system("export LC_ALL=C")

	if argc == 1:
		printUsage()
		return 0
	if argv[1] == "gc": callsToGC()
	elif argv[1] == "prov": callsPerProvince()
	else: printUsage()
	
	arg= "echo $(date) | mail -s The_Mundo_Sano_program_finished_running carolang@grandata.com"
	os.system(args)

if __name__=='__main__':
	main(len(sys.argv), sys.argv)
