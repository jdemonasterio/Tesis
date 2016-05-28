import os
import time

start_time = time.time()

def padNum(n):
	return ("0" if n < 10 else "") + str(n)

def main():
	years = ["2012", "2012","2012"]
	# ["2011", "2011", "2012", "2012", "2012"]
	months = [1,2,3]
	# [11, 12, 1, 2, 3]
	daylims = [31,29,31] 
	#[30, 0, 13, 0, 0]
	#daylims = [30, 31, 31, 29, 31]
	if len(months) != len(years) or len(months)!= len(daylims):
		print('Error in month params setting')
	if sum([d>31 for d in daylims])>0:
		print('Error in monthly max days limit setting')
	
		
	for m in range(len(months)):
		for d in range(1, daylims[m]+1):
			infile = "/grandata/ca/voice/" + years[m] + "/" + str(months[m]) + "/binaria_gsm_" + years[m] + padNum(months[m]) + padNum(d) + ".csv.gz"
			outfile = "output_direction/surrogated_" + years[m] + padNum(months[m]) + padNum(d) + ".csv.gz"
			
			print("Current file:", padNum(d) + "/" + padNum(months[m]) + "/" + years[m])
			elapsed_time = time.time() - start_time
			print('Elapsed time is %s ' % elapsed_time)
			bash_command = "zcat " + infile + " | ./surrogate_files_ca | gzip > " + outfile
			os.system(bash_command)

if __name__=='__main__':
	main()

