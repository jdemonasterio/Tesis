import os

def padNum(n):
	return ("0" if n < 10 else "") + str(n)

def main():
	years = ["2011", "2011", "2012", "2012", "2012"]
	months = [11, 12, 1, 2, 3]
	daylims = [30, 0, 13, 0, 0]
	#daylims = [30, 31, 31, 29, 31]
	
	for i in range(5):
		for d in range(1, daylims[i]+1):
			infile = "/gd/ca/data/voice/" + years[i] + "/" + str(months[i]) + "/binaria_gsm_" + years[i] + padNum(months[i]) + padNum(d) + ".csv.gz"
			outfile = "output_direction/surrogated_" + years[i] + padNum(months[i]) + padNum(d) + ".csv.gz"
			
			print "Current file:", padNum(d) + "/" + padNum(months[i]) + "/" + years[i]
			
			bash_command = "zcat " + infile + " | ./surrogate_files_ca | gzip > " + outfile
			os.system(bash_command)

if __name__=='__main__':
	main()

