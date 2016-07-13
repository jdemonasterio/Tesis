## este analisis es total.. por mes!
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
from dateutil import rrule
from datetime import datetime


ms = [8,9,10,11,12] #all months
#el anyo ta fijo en 2015
year =  2015 #all possible year

#seteamos el lugar de trabajo
rootdir="/home/juan/mobility-study/mexico-scripts-ver2/"
os.chdir(rootdir)

def get_input_sframe(year,month,plan = "Pospago"):
    return rootdir +"sframe_cdrs/{y}/{m:0=2d}/{pl}"\
                .format(y=year,m=month,pl=plan)

def get_output_file(month,year):
    output = "/home/juan/mobility-study/mexico-scripts-ver2/output/sum_links1_month{m1:0=2d}{y1}_sframe".\
            format(m1 = month, y1 = year )

    return output

    
# PARA procesar el DIRECTION col
def get_correct_direction(cel):
    if cel == 'SALIENTE': rv = 'O'
    elif cel == 'ENTRANTE': rv = 'I'        
    else: rv = None
    return rv


def printUsage():
    print("Usage:")
    print("python SumLinks-arg.py [month]")
    print("month should be an int in the [8..12] range")

def main(argc, argv):
    #notar aca que python toma 2 parametros, el script propiamente y el parametro que entra al script
    if argc != 2:
        print('argc != 2')
        printUsage()
        return 0
    try:
        month = int(str(argv[1]))
        #print('month is {m}, int check is {i}, str check is {s}  '.format(m = month, i = isinstance( month, int ), s = isinstance( month, str )   ))
        #print('test is %s'%test)
        
        if not( isinstance( month, int ) and month in ms ): 
            printUsage()    
            sys.exit()
    except:
        print('type of argv[2] is %s' % type(argv[1]))
        print('argv[2] is %s'% argv[1] )
        printUsage()    
        sys.exit()
        
    start_time = time.time()
    month = int(argv[1])
    
    sframe_dir =  get_input_sframe(year,month,plan = "Pospago")
    
    if not(os.path.exists(sframe_dir)):
        print_str = "Unexistent sframe for {y}/{m:0=2d}. Stopping the algorithm, get sframes".format(y = year, m = month) 
        print(print_str)
        logging.info( print_str ) 
        sys.exit()    
        
    output_file = get_output_file(month = month, year = year)
    #creo los grupos que despues van a filtrar c/chunk de la tabla para hacer varias pasadas
                
    table = gl.load_sframe(sframe_dir)
    table.rename({'DATE':'TIMESTAMP'})
    
    table['DIRECTION'] = table['DIRECTION'].apply(lambda x : get_correct_direction(x))
    #tiro losn ulls
    table = table[table['DIRECTION']!=None]
    
    table['TIMESTAMP'] = table['TIMESTAMP'].str_to_datetime(str_format='%Y-%m-%d-%H:%M:%S')
    ## leo si las llamadas fueron hechas durante el findesemana
    table['DURING_WEEKEND'] = table['TIMESTAMP'].apply(lambda x: x.weekday()==5 or x.weekday()==6)
    # asigno el bool si la llamada fue en horario 'laboral'
    #notar que la hora < 19 significa que 18hs y 59 min da True
    table['DURING_DAYLIGHT']= table['TIMESTAMP'].apply(lambda x: x.hour>=8 and x.hour<20 )
    table_weeknight = table[(table['DURING_DAYLIGHT']==False) &  (table['DURING_WEEKEND']==False)]
    table_weekend = table[table['DURING_WEEKEND']==True]
    table_weekday = table[(table['DURING_DAYLIGHT']==True) &  (table['DURING_WEEKEND']==False)]

    local_time = time.localtime()
    print_str = "Finished categorizing, start grouping. Time elapsed is {t}, localtime is {ho}:{mi} \n"\
    .format( t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min)
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
    
    local_time = time.localtime()
    print_str = "Finished merging grouped tables, start home_antenna loading. Time elapsed is {t}, localtime is {ho}:{mi} \n"\
    .format( t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min)
    print(print_str)
    logging.info( print_str )

    
    for col in table.column_names():
        if ('USER' in col) or ('DIRECTION' in col):
            continue
            table = table.fillna(col,0)

            local_time = time.localtime()       

    #me quedo solo con los usuarios que me interesan i.e. con aquellos que puedo asegurar su home_antenna, luego lo cargo
    homeantenna_map =  gl.SFrame()
    for dirpath, dnames, fnames in os.walk(rootdir+"output/".format(y = year, m = month)):
        for d in dnames:
            if "homeantenna_from815to1215" in d and "full" in d:
                d = os.path.join(dirpath, d)
                group_map = gl.load_sframe(d)
                #keep weeknight home_antenna filter
                group_map = group_map['USER','ANTENNA_ID_WEEKNIGHT_0']
                #users with str(-1) values are those for which no calls were recorded in that period, thus we have to discard them
                group_map = group_map[group_map['ANTENNA_ID_WEEKNIGHT_0']!='-1']
                homeantenna_map = homeantenna_map.append(group_map)
            else:
                continue

    antennas_file = '/home/juan/mobility-study/mexico-scripts-ver2/data/celdas_limpio.csv'
    #obs el column_type str para el cel_id es para que matchee con el column_type que tengo en home_antenna ya y en table
    antennas = gl.SFrame.read_csv('data/celdas_limpio.csv', 
                                  delimiter= "|"
                                  ,usecols = ['CEL_ID','EPIDEMIC'],
                                  column_type_hints = [str,bool])
    #me quedo con la info que mas nos importa que es la epidemicidad de c/antenna
    #mergeo con la info de epidemicidad y me quedo solo si un usuario es o no epidemico.
    homeantenna_map = homeantenna_map.join(antennas['CEL_ID', 'EPIDEMIC'], on ={'ANTENNA_ID_WEEKNIGHT_0':'CEL_ID' },how='left')
    homeantenna_map.remove_columns(['ANTENNA_ID_WEEKNIGHT_0'])

    local_time = time.localtime()
    print_str = "Finished home_antenna loading start joining on output table. Time elapsed is {t}, localtime is {ho}:{mi} \n"\
    .format( t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min)
    print(print_str)
    logging.info( print_str )

    #agrego la info de epidemicidad a la tabla P/C/ user, todo aquel que no pueda etiquetar como epidemico o no-epidemico, lo tiro
    table = table.join(homeantenna_map, on = {'USER':'USER'} ,how='left')
    #filtro nulls
    table = table[ table['EPIDEMIC'] != None]

    table.rename({'EPIDEMIC':'EPIDEMIC.0'}) #la definicion .0 es la que un USER tiene una home_antenna epidemica (i.e. es epidemico)

    table = table.join(homeantenna_map, on = {'OTHER_USER':'USER'} ,how='left') # el on = dict() es una especie de left_on, right_on
    # aca el join es sobre la otra columna, el other_user y se interpeta como que USER es vulnerable pues habla con un OTHER_USER epidemico
    
    #filtro nulls
    table = table[ table['EPIDEMIC'] != None]

    #salvo c/file por separado y despues los appendeo todos en 1.
    table.save(output_file)
    local_time = time.localtime()
    print_str ='finished data processing and saving, time elapsed is {t}\n localtime is {ho}:{mi} \n'\
    .format( t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min)        
    print(print_str)
    logging.info( print_str )

    then = start_time

    seconds = time.time() - then
    print_str ="total running time of script is %d " % seconds        
    
    print(print_str)
    logging.info( print_str )

if __name__=='__main__':
    log_date = time.localtime()
    log_date = "{day:0=2d}".format(day = log_date.tm_mday) + "_" + "{mon:0=2d}".format(mon = log_date.tm_mon)
    
    log_dir = '/home/juan/mobility-study/mexico-scripts-ver2/logs/{log}'.format(log = log_date)
    
    log_file = log_dir + "/log.txt"
    
    if not(os.path.exists(log_dir)):
        os.mkdir( log_dir, 0755 );
        print("Creating the log dir" ) 

    logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode="a+",
                        format="%(asctime)-15s %(message)s")
    main(len(sys.argv), sys.argv)
