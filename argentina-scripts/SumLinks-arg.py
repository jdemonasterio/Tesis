## este analisis, como hace caro, es por mes!

import pandas as pd;
import numpy as np;
import os;
import random;
import graphlab as gl
import time
import datetime
import sys
import subprocess
import logging

rootdir="/home/juan/mobility-study/argentina-scripts"
os.chdir(rootdir)
#los meses a analizar
ms = [11,12,1,2,3]

def get_output_file(month,group = -1,sample=False):
    output = "/home/juan/mobility-study/argentina-scripts/output/2012/{0}/sum_links_".format(month,group)
    if sample == True:
        output = output + "_sample"
    if group != -1:
        output = output + "_group{g}_1".format(g=group)
    return output

def printUsage():
    print("Usage:")
    print("python SumLinks-arg.py [mode] [month]")
    print("mode = 'true' to test out the algorithm on a sample of upto 7 days for a (random) particular month")
    print("mode = 'false' to run it for all available months")
    print("month should be an int")

def main(argc, argv):
    #notar aca que python toma 2 parametros, el script propiamente y el parametro que entra al script
    if argc != 2:
        print('argc != 3')
        printUsage()
        return 0
    
    if argv[1] == 'false': test = False 
    
    elif argv[1] == 'true': test = True
    
    else:  
        printUsage()    
        sys.exit()
    
    if not( isinstance( argv[2], int ) and month in ms ): 
        printUsage()    
        sys.exit()
    
    month = argv[2]
    start_time = time.time()
    
    #generamos el diccionario que setea los parametros sobre el cual vamos a iterar
    year = 2011
    
    months = dict()
    
    #for month in ms:
    days = range(1,32)
    #check november days length
    if month ==11:
        days = range(1,31)
    #check february days length
    if month ==2:
        days = range(1,30)
    #alterno el year para los meses que arrancan en enero
    if month < 11:
        year = 2012
    #si es test elijo una tira de dias de random_length h/7
    if test:
# elijo entre 5 y 10 dias
        length = np.random.choice(range(3,8),(1,))[0]
        days = np.random.choice(range(1,30),(length,),replace=False)

        months[month] = {"year":year,"days":days}
        #print(month,year)

if test:
        print_str = 'we have this month {m} and these days {ds}'.format(m = month,ds = str(days))
        print(print_str)
        logging.info( print_str )

    ## we first check all the necessary sframe datasetes exist
    for month in months:
        year = months[month]['year']
        days = months[month]['days']
        for day in days:
            sframe_dir = '/home/juan/mobility-study/argentina-scripts/sframe_cdrs/{y}/{m:0=2d}/{d:0=2d}'.format(y=year,m=month,d=day)
            if not(os.path.exists(sframe_dir)):
                print_str = "Unexistent sframe for {y}/{m:0=2d}/{d:0=2d}. Stopping the algorithm, get sframes".format(y = year, m = month,d=day) 
                print(print_str)
                logging.info( print_str ) 
                sys.exit()    table =  gl.SFrame()
        
        for day in days:

            sframe_dir = '/home/juan/mobility-study/argentina-scripts/sframe_cdrs/{y}/{m:0=2d}/{d:0=2d}'.format(y=year,m=month,d=day)        
            daily_table = gl.load_sframe(sframe_dir)

            #a cada tabla diaria filtro por todos los USERs por el hash del string (el hash es un int) y despue filtro modulo passes
            #y trabajo sobre la tabla subgroup nada mas que ahora tiene menos usuarios
            table = table.append(daily_table[daily_table['USER'].apply(lambda x: hash(x) % passes == group )])
            
        #entonces la idea es que yo ahora solo voy a trabajar, dentro de esta tabla filtrada y para todos los dias del mes juntos
        
        #paso las fechas a un timestamp
        table['TIMESTAMP'] = table['DATE','TIME'].apply(lambda x: x['DATE'][0:4]+'-'+x['DATE'][4:6]+'-'+x['DATE'][6:8]
                                         +'-'+x['TIME'][0:2]+'-'+x['TIME'][2:4]+'-'+x['TIME'][4:6])

        table['TIMESTAMP'] = table['TIMESTAMP'].str_to_datetime(str_format='%Y-%m-%d-%H:%M:%S')

        ## leo si las llamadas fueron hechas durante el findesemana
        table['DURING_WEEKEND'] = table['TIMESTAMP'].apply(lambda x: x.weekday()==5 or x.weekday()==6)

        # asigno el bool si la llamada fue en horario 'laboral'
        #notar que la hora < 19 significa que 18hs y 59 min da True
        table['DURING_DAYLIGHT']= table['TIMESTAMP'].apply(lambda x: x.hour>=8 and x.hour<20 )
        
        table_weeknight = table[(table['DURING_DAYLIGHT']==False) &  (table['DURING_WEEKEND']==False)]
        
        table_weekend = table[table['DURING_WEEKEND']==True]

        #table_weeknight = table[(table['DURING_DAYLIGHT']==False) &  (table['DURING_WEEKEND']==False)]

        table_weekday = table[(table['DURING_DAYLIGHT']==True) &  (table['DURING_WEEKEND']==False)]
        
        local_time = time.localtime()
        
        print_str = "Finished categorizing, start grouping. Time elapsed is {t}, localtime is {ho}:{mi} \n"/
                .format(it=group,pas=passes, t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min)
        print(print_str)
        logging.info( print_str )

        table_weekend_call = table_weekend.groupby(['USER','OTHER_USER','DIRECTION'],
                         {'CallsWeekEnd':gl.aggregate.COUNT('TIMESTAMP')})

        table_weeknight_call = table_weeknight.groupby(['USER','OTHER_USER','DIRECTION'],
                         {'CallsWeekNight':gl.aggregate.COUNT('TIMESTAMP')})


        table_weekday_call = table_weekday.groupby(['USER','OTHER_USER','DIRECTION'],
                         {'CallsWeekDay':gl.aggregate.COUNT('TIMESTAMP')})


        table_weekend_time = table_weekend.groupby(['USER','OTHER_USER','DIRECTION'],
                         {'TimeWeekEnd':gl.aggregate.SUM('DURATION')})


        table_weeknight_time = table_weeknight.groupby(['USER','OTHER_USER','DIRECTION'],
                         {'TimeWeekNight':gl.aggregate.SUM('DURATION')})


        table_weekday_time = table_weekday.groupby(['USER','OTHER_USER','DIRECTION'],
                         {'TimeWeekDay':gl.aggregate.SUM('DURATION')})

        del table_weekend, table_weeknight, table_weekday
        
        table = table_weekend_call.join(table_weeknight_call,on = ['USER','OTHER_USER','DIRECTION'], how = 'outer')
        del table_weekend_call, table_weeknight_call
        table =  table.join(table_weekday_call,on = ['USER','OTHER_USER','DIRECTION'], how = 'outer')
        del table_weekday_call

        table =  table.join(table_weekend_time,on = ['USER','OTHER_USER','DIRECTION'], how = 'outer')
        del table_weekend_time

        table =  table.join(table_weekday_time,on = ['USER','OTHER_USER','DIRECTION'], how = 'outer')
        del table_weekday_time

        table =  table.join(table_weeknight_time,on = ['USER','OTHER_USER','DIRECTION'], how = 'outer')
        del table_weeknight_time

        for col in table.column_names():
            if ('USER' in col) or ('DIRECTION' in col):
                continue
            table = table.fillna(col,0)
        
        local_time = time.localtime()       
        
        #salvo c/file por separado y despues los appendeo todos en 1.
        output_file = get_output_file(month,group)
        table.save(output_file)
        local_time = time.localtime()
        print_str ='finished data processing from group {g} of {p}, time elapsed is {t}\n localtime is {ho}:{mi} \n'/
                    .format(g = group, p = passes, t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min)        
        print(print_str)
        logging.info( print_str )

    then = start_time

    seconds = time.time() - then
    print_str ="total running time of script is %d " % seconds        
    
    print(print_str)
    logging.info( print_str )

if __name__=='__main__':
    #set logging environment, files will start logging when algorithm was first started 
    log_date = time.localtime()
    log_date = "{day:0=2d}".format(day = log_date.tm_mday) + "_" + "{mon:0=2d}".format(mon = log_date.tm_mon)
    
    log_dir = '/home/juan/mobility-study/argentina-scripts/logs/{log}'.format(log = log_date)
    
    log_file = log_dir + "/log.txt"
    
    if not(os.path.exists(log_dir)):
                print("Creating the log dir" ) 
    
    logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode="a+",
                        format="%(asctime)-15s %(message)s")
    main(len(sys.argv), sys.argv)
