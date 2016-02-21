import os
import gzip
import sys

def printUsage():
	sys.stderr.write("\nUsage\n")
	sys.stderr.write("python home_prediction.py STARTING_YEAR STARTING_MONTH ENDING_YEAR ENDING_MONTH\n")
	sys.stderr.write("The ending date must be greater or equal than the starting date.\n\n")
	
def strMonth(n):
	nn = int(n)
	if nn < 10:
		return '0'+str(nn)
	else:
		return str(nn)
		
def generateInfile(y, m):
	return '../../simplify_format/output_old/simple_format_' + str(y) + strMonth(m) + '.txt.gz'

def generateOutfile(sy, sm, ey, em):
	return 'output/home_pred_' + str(sy) + strMonth(sm) + '_' + str(ey) + strMonth(em) + '.txt.gz'

def main(argc, argv):
	if argc < 5:
		printUsage()
		return 1
		
	starting_year = int(argv[1])
	starting_month = int(argv[2])
	ending_year = int(argv[3])
	ending_month = int(argv[4])
	
	if (ending_year < starting_year) or (ending_year == starting_year and ending_month < starting_month):
		printUsage()
		return 1
	
	infiles = []
	for y in range(starting_year, ending_year + 1):				# These nested loops go over every month in [(starting_year,starting_month),(ending_year,ending_month)]
		sm = (starting_month if y == starting_year else 1)
		em = (ending_month if y == ending_year else 12)
		for m in range(sm, em + 1):
			infiles.append(generateInfile(y,m))
			
	zcat_command = ' '.join(['zcat', ' '.join(infiles)])
	gzip_command = 'gzip > ' + generateOutfile(starting_year, starting_month, ending_year, ending_month)
	
	command = ' | '.join([zcat_command, "grep ' [IO] '", "grep -v '  '", './home_clean', gzip_command])
	
	print command
	os.system(command)
	
	os.system('echo "Nos regocijaremos y embriagaremos en consecuencia." | mail -s "Termino Home Prediction" "carolang@grandata.com"')
	
	
if __name__=='__main__':
	main(len(sys.argv), sys.argv)
