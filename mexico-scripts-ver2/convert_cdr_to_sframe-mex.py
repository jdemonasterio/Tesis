import numpy as np; import os;import random;
import graphlab as gl
import time
import os
np.random.seed(2016)
import subprocess
import sys
import subprocess
import logging

from datetime import datetime


#seteamos el lugar de trabajo
rootdir="/grandata/voice/"
os.chdir(rootdir)

ys = [2014,2015,2016]



def get_raw_file(month,day,day2,year = 2015,plan = "Prepago"):
    return rootdir +"{y}{m:0=2d}_geo/Geo_Voz_{pl}_{d:0=2d}-{d2:0=2d}{m:0=2d}{y2}.txt.gz"\
                .format(y=year,y2= year%100, m=month, d=day, d2=day2, pl = plan)

def get_structured_date(row):
    try:
        end_str = row[-5:].replace(' ','').replace('.','')
        start_str = row[:-5].replace(' ','')
        rv = str(datetime.strptime(start_str + end_str  , '%d/%m/%Y%I:%M:%S%p'))
    
    except:
        rv = "NULL"
        
    return rv

#la idea es que se tiene que pedir el anyo a procesar (i.e. 2014 como int) como argc
def printUsage():
    print("Usage:")
    print("python SumLinks-arg.py [plan] [year]")
    print("plan should be Pospago or Prepago") 
    print("year should be 2014, 2015 or 2016") 
    
    
def main(argc, argv):
    if argc != 3:
        print('argc != 3')
        printUsage()
        return 0
    
    if argv[1] == 'Pospago': plan = 'Pospago' 
    elif argv[1] == 'Prepago': plan = 'Prepago'
    else:  
        printUsage()    
        return 0
    
    if not( isinstance( int(argv[2]), int ) and int(argv[2]) in ys ): 
        print_and_log('type of argv[2] is %s' % type(argv[2]) )
        print_and_log('argv[2] is %s'% argv[1] )
        printUsage()    
        return 0 
    
    #para loggear todo lo que pase en el main
    def print_and_log(string):
        if not( isinstance( string, str )):
            print('Error in argument, type should be string only')
        print(string)
        logging.info(string)
    
    year = int(argv[2])
    
    #log el tiempo que tarda
    start_time = time.time()

    ms = range(1,13)
    short_ms = [2,4,6,9,11]
    long_ms = [1,3,5,7,8,10,12]
    
    months = dict()
  
    
    for month in ms:
        
        days = range(1,32)
        #check short months days length
        if month in short_ms:
            days = range(1,31)
        #check february days length
        if month ==2:
            days = range(1,29)
        
        months[month] = days
    
    local_time = time.localtime()       
    print_str = "All processing metadata for {y} is\n {al} \n localtime is {ho}:{mi} ".format(y=year, al = months,
                                           ho=local_time.tm_hour,mi=local_time.tm_min)
    print_and_log(print_str)
    
    # arranco a procesar
    for month in months:
        # en table guardo el sframe a salvar
        table = table =  gl.SFrame()
        
        days = months[month]
        
        print(month,year)
        #thisi where the file will be saved
        sframe_dir = "/home/juan/mobility-study/mexico-scripts-ver2/sframe_cdrs/{y}/{m:0=2d}/{p}/".\
                    format(y=year,m=month,p=plan)

        # si ya habiamos procesado ese mes, seguimos
        if (os.path.exists(sframe_dir)):
            print_str = "skipping {m:0=2d} since output_dir exists".format(m=month)
            print_and_log(print_str)
            continue

        local_time = time.localtime()
        print_str = "Transforming month {m} raw CDRs to Sframe dirs, time elapsed is {t} localtime is {ho}:{mi}".format(m=month,t=(time.time()-start_time),
                                                 ho=local_time.tm_hour,mi=local_time.tm_min)
        print_and_log(print_str)
        
        #primero recorremos todos los files que vamos a necesitar en ese mes y lo pasamos a formato sframe para cargar mas rapido
        for dirpath, dnames, fnames in os.walk(rootdir+"{y}{m:0=2d}_geo/".format(y = year, m = month)):
            for f in fnames:
                if plan in f: 
                    csv_dir = os.path.join(dirpath, f)
                else:
                    continue
                
                #existe un csv super corrupto en mayo 2015 que rompe todo asi que lo skipeo
                if csv_dir == "/grandata/voice/201505_geo/Geo_Voz_Pospago_03-030515.txt.gz":
                    continue

                local_time = time.localtime()
                print_str = str(csv_dir) +"\n time elapsed is {t} localtime is {ho}:{mi}".format(t=(time.time()-start_time),
                                                         ho=local_time.tm_hour,mi=local_time.tm_min)
                print_and_log(print_str)
                #este try es basicamente porque en algunos dias, deja de venir fecha_llamada como columna y decidi registrar esas tablas igualmente pero rellenando esta columna de nulls
                try:
                    daily_table = gl.SFrame.read_csv( csv_dir, delimiter='\t', 
                            header=True, skip_initial_space=True, 
                            column_type_hints = [str, str,int, str,float, float,str], 
                            #nrows = 25*1e6,
                            usecols = ['TELEFONO','DESTINO','DURACION_SEGUNDOS', 'DIRECCION',
                                                'LATITUD','LONGITUD','FECHA_LLAMADA'],  
                            error_bad_lines=False
                                      )

                    daily_table.rename({'TELEFONO':'USER','DESTINO':'OTHER_USER', 'DIRECCION':'DIRECTION',
                                          'FECHA_LLAMADA':'DATE','DURACION_SEGUNDOS':'DURATION',
                                'LATITUD':'LATITUDE','LONGITUD':'LONGITUDE'})
                    with_date = True

                except Exception, e:
                    print_str = 'Exception when reading table is {e}'.format(e =e)
                    print_and_log(print_str)
                    with_date = False

                    daily_table = gl.SFrame.read_csv( csv_dir, delimiter='\t', 
                                                     header=True, skip_initial_space=True, 
                            column_type_hints = [str, str,int, str, float, float], 
                            #nrows = 25*1e6,
                            usecols = ['TELEFONO','DESTINO','DURACION_SEGUNDOS', 'DIRECCION',
                                                'LATITUD','LONGITUD'],  
                            error_bad_lines=False
                                      )

                    daily_table.rename({'TELEFONO':'USER','DESTINO':'OTHER_USER', 'DIRECCION':'DIRECTION',
                                          'DURACION_SEGUNDOS':'DURATION',
                                'LATITUD':'LATITUDE','LONGITUD':'LONGITUDE'})		    

                    daily_table['DATE'] = 'NULL'

                print_str ='original daily shape is %s ' % str(daily_table.shape)
                print_and_log(print_str)

                #checking which calls have antennas geo location, throw the rest
                daily_table = daily_table[ daily_table['LONGITUDE'] != None ]
                daily_table = daily_table[ daily_table['LATITUDE'] != None ]
                
                if with_date == True:
                    daily_table['DATE'] = daily_table['DATE'].apply(lambda row:  get_structured_date(row) )
                    print_str ='Null DATE rows appearing from date-parse conversion is %s ' % str(daily_table[daily_table['DATE']=='NULL'].shape[0])
                    print_and_log(print_str)
                    #drop date nulls
                    daily_table = daily_table[daily_table['DATE']!='NULL']
                
                print_str ='processed daily shape is %s ' % str(daily_table.shape)
                print_and_log(print_str)

                table = table.append(daily_table)
                #si es posible, libero ram
                del daily_table

        
        print_str = 'output sframe to save has shape %s ' % str(table.shape)
        print_and_log(print_str)
        print_and_log(sframe_dir)
        
        table.save(sframe_dir)    
        
        local_time = time.localtime()
        print_str = 'finished saving for month {m}, time elapsed is {t} localtime is {ho}:{mi:0=2d}'.\
                   format(m=month,t=(time.time()-start_time), ho=local_time.tm_hour, mi=local_time.tm_min)
        print_and_log(print_str)
        
        #si es posible, libero ram
        del table

        
if __name__=='__main__':
    #set logging environment, files will start logging when algorithm was first started 
    log_date = time.localtime()
    log_date = "{day:0=2d}".format(day = log_date.tm_mday) + "_" + "{mon:0=2d}".format(mon = log_date.tm_mon)
    
    log_dir = '/home/juan/mobility-study/mexico-scripts-ver2/logs/{log}/'.format(log = log_date)
    log_file = log_dir + "log.txt"
    
    if not(os.path.exists(log_dir)):
        print("Creating the log dir in %s " % log_dir ) 
        os.mkdir( log_dir );    
    
    logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode="a+",
                        format="%(asctime)-15s %(message)s")
    main(len(sys.argv), sys.argv)
