import numpy as np
import os
import random
import graphlab as gl

#esto es para dibujar directo a la notebook
#gl.canvas.set_target('ipynb')
#from matplotlib import pyplot as plt
#%matplotlib inline

import time
import os
import datetime
import sys
import subprocess
import logging
from dateutil import rrule
from datetime import datetime

ms = range(1,13) #all months
ys =  [2014,2015] #all possible years

#seteamos el lugar de trabajo
rootdir="/home/juan/mobility-study/mexico-scripts-ver2/"
os.chdir(rootdir)

def get_input_sframe(year,month,plan = "Pospago"):
    return rootdir +"sframe_cdrs/{y}/{m:0=2d}/{pl}"\
                .format(y=year,m=month,pl=plan)


def get_output_file(date1,date2, group = -1,long_mode=True):
    if date2<date1:
        print('output dates  %s and %s and badly ordered ' % (str(date1), str(date2)))
    output = "/home/juan/mobility-study/mexico-scripts-ver2/output/homeantenna_from{m1:0=2d}{y1}to{m2:0=2d}{y2}_sframe".\
            format(m1=date1.month,y1= date1.year %100 ,m2= date2.month ,y2= date2.year %100 )
    
    if long_mode: output = output + "_full"
    else: output = output + "_gtruth"
    
    if group != -1:
        output = output + "_group{g}_1".format(g=group)
    return output

def get_columns_from_dict(user_dict, long_mode = True):
    if long_mode : array_length = 10        
    else: array_length = 3
    antenna_count_list = -1*np.ones(array_length, dtype=np.int32)
    
    #por un problema de type consistency dentro de la listas que le meto al SFrame, aca los -1 tienen que ser strings
    antenna_list =  (-1*np.ones(array_length,dtype=np.int32)).astype(np.str_)
    sorted_user_dict = sorted(user_dict, key=user_dict.get, reverse=True)
    
    for i,ant in enumerate(sorted_user_dict):
        if(i>(array_length-1)):
            break

        antenna_count_list[i] = user_dict[ant]
        antenna_list[i] =  ant
            #print(user_dict)
        #for other than the first case
        
        if i==0:
            continue
        #random permutation of current and previous antenna in case of a count tie
        if user_dict[sorted_user_dict[i-1]]==user_dict[ant]  and np.random.random() <= 0.5:
            #add past antennas data to current
            antenna_count_list[i] = antenna_count_list[i-1]
            antenna_list[i] =  antenna_list[i-1]
            ## add current data to past
            antenna_count_list[i-1] = user_dict[ant]
            antenna_list[i-1] =  ant
    
    rv = (antenna_list, antenna_count_list)
    return rv

def printUsage():
    print("Usage:")
    print("python userAntennaMapping-mex.py [mode] [start_month] [start_year] [end_month] [end_year]")
    #print("python SumLinks-arg.py [mode] [month]")
    print("mode = 'short' to only output the ML ground-truth (Y) for given months. AntennaID_All and AntennaID_Weeknight")
    print("mode = 'long' to run the full output mode for the given months (top 10 antennas with counts and by Weeknight filter)")
    print("(start_year, start_month) should be a date <= than ( end_year, end_month) and both should be in [1..12]")

def main(argc, argv):
    #notar aca que python toma 2 parametros, el script propiamente y el parametro que entra al script
    if argc != 6:
        print('argc != 6')
        printUsage()
        return 0
    if argv[1] == 'short': long_mode = False 
    elif argv[1] == 'long': long_mode = True
    else:  
        printUsage()    
        sys.exit()
    #check start month arg
    if not( isinstance( int(argv[2]), int ) and int(argv[2]) in ms ): 
        print_str ='type of argv[2] is %s' % type(argv[2]) 
        print_str +='argv[2] is %s'% argv[2] 
        print(print_str)
        printUsage()    
        return 0 
    
    #check start year arg
    if not( isinstance( int(argv[3]), int ) and int(argv[3]) in ys ): 
        print_str = 'type of argv[3] is %s' % type(argv[3])
        print_str += 'argv[3] is %s'% argv[3] 
        print(print_str)        
        printUsage()
        return 0 
    
    #check end month arg
    if not( isinstance( int(argv[4]), int ) and int(argv[4]) in ms ): 
        print_str ='type of argv[4] is %s' % type(argv[4]) 
        print_str +='argv[4] is %s'% argv[4] 
        print(print_str)
        printUsage()
        return 0
    
#check end year arg
    if not( isinstance( int(argv[5]), int ) and int(argv[5]) in ys ): 
        print_str ='type of argv[5] is %s' % type(argv[5]) 
        print_str +='argv[5] is %s'% argv[5] 
        print(print_str)        
        printUsage()    
        return 0 

    month_start = int(argv[2])
    year_start = int(argv[3])
    month_end = int(argv[4])
    year_end = int(argv[5])
    
    from datetime import date
    start_date = date(year_start, month_start,1)
    end_date = date(year_end, month_end,1)
    
    if ( end_date < start_date ): 
        print_and_log('end_date %s is < than start_date %s' % (end_date, start_date) )
        printUsage()
        return 0 
        
    start_time = time.time()
    
    antennas_file = '/home/juan/mobility-study/mexico-scripts-ver2/data/celdas_limpio.csv'
    antennas = gl.SFrame.read_csv('data/celdas_limpio.csv', delimiter= "|")
    #generamos el diccionario que setea los parametros sobre el cual vamos a iterar
    
    #months = dict()
    
    start_time = time.time()
    #generamos el date list sobre el cual vamos a iterar
    #list of dates
    dates = []
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date):
        dates+=[dt] 

    ## we first check all the necessary sframe datasetes exist
    for date in dates:
        year = date.year
        month = date.month
        sframe_dir = get_input_sframe(year,month)
        if not(os.path.exists(sframe_dir)):
            print_str = "Unexistent sframe for {y}/{m:0=2d}. Stopping the algorithm, get sframes".format(y = year, m = month) 
            print(print_str)
            logging.info( print_str ) 
            sys.exit()

    local_time = time.localtime()

    print_str = "Read all Sframe dirs and append to one big table, time elapsed is {t}  localtime is {ho}:{mi:0=2d}".format(t=(time.time()-start_time), ho = local_time.tm_hour , mi = local_time.tm_min )
    print(print_str)
    logging.info( print_str )

    #aca seteamos como vamos a partir la tabla segun el nro correspondiente a c/hash y tomando modulo
    passes = 10
    
    print('dates are {ds} \n Num of passes is {p}'.format(p= passes,ds = str(dates)))
    #creo los grupos que despues van a filtrar c/chunk de la tabla para hacer varias pasadas
    for group in range(0,passes):
        
        local_time = time.localtime()
        print_str = "working group number {it} of {pas}, time elapsed is {t} localtime is {ho}:{mi:0=2d}\n".format(it=group,pas=passes, t=(time.time()-start_time), ho=local_time.tm_hour,mi=local_time.tm_min)
        print(print_str)
        logging.info( print_str )
        
        output_file = get_output_file(start_date,end_date,group=group)
        #si es un test ni hago el check
        if (os.path.exists(output_file)):
            print_str = "skipping {gr} since output_dir exists".format(gr = group) 
            print(print_str)
            logging.info( print_str ) 
            continue

        #itero sobre todos los day-months
        
        table =  gl.SFrame()

        for date in dates:
            year = date.year
            month = date.month
            print(year,month)
            
            local_time = time.localtime()
            print_str = "working group number {it} of {pas}, time elapsed is {t} localtime is {ho}:{mi:0=2d}\n".format(it=group,pas=passes, t=(time.time()-start_time), ho=local_time.tm_hour,mi=local_time.tm_min)
            print(print_str)
            logging.info( print_str )
            
            #badly shaped raw files for 2014/04, thus we skip
            if year == 2014 and month == 4:
                local_time = time.localtime()
                print_str = "skipping month read of 2014/04 since raw datasets can't give timestamp info on each col, time elapsed is {t} localtime is {ho}:{mi:0=2d} \n".format(it=group,pas=passes, t=(time.time()-start_time), ho=local_time.tm_hour,mi=local_time.tm_min)
                print(print_str)
                logging.info( print_str )
                continue
             
            sframe_dir = get_input_sframe(year,month)

            local_time = time.localtime()
            print_str = "Reading sframe file for {y}-{ms}, time elapsed is {t} localtime is {ho}:{mi:0=2d} ".\
            format(y=year,ms=month,t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min) 
            print(print_str)
            logging.info( print_str )

            monthly_table = gl.load_sframe(sframe_dir)
            monthly_table.remove_columns(['DURATION','OTHER_USER','DIRECTION'])

            #a cada tabla diaria filtro por todos los USERs por el hash del string (el hash es un int) y despue filtro modulo passes
            #y trabajo sobre la tabla subgroup nada mas que ahora tiene menos usuarioss
            monthly_table = monthly_table[monthly_table['USER'].apply(lambda x: hash(x) % passes == group )]
            
            monthly_table['DATE'] = monthly_table['DATE'].str_to_datetime(str_format='%Y-%m-%d-%H:%M:%S')
            
            #etiqueto como timestamp mejor
            monthly_table.rename({'DATE':'TIMESTAMP'})
                        
            #agrego la data de antenas
            monthly_table = monthly_table.join(antennas['LATITUDE', 'LONGITUDE','CEL_ID'] , on = ['LATITUDE', 'LONGITUDE'],
                                               how = 'left')
            #NO necesitamos mas esto sino que esta surrogado por el ant_id
            monthly_table.remove_columns(['LATITUDE','LONGITUDE'])
            
            #dropeamos los nulls que no existen en la tabla de antennas
            monthly_table.dropna(how="any")
            
            table = table.append(monthly_table)

            del monthly_table

        #entonces la idea es que yo ahora solo voy a trabajar, dentro de esta tabla filtrada y para todos los dias del mes juntos
        local_time = time.localtime()
        print_str = 'finished loading/appending tables for group {g} of {p}, time elapsed is {t} localtime is {ho}:{mi:0=2d} '.format(g = group,
                                            p = passes, t=(time.time()-start_time), ho=local_time.tm_hour,mi=local_time.tm_min)
        print(print_str)
        logging.info( print_str )
        
        
        ## leo si las llamadas fueron hechas durante el findesemana 
        table['DURING_WEEKEND'] = table['TIMESTAMP'].apply(lambda x: x.weekday()==5 or x.weekday()==6)

        # asigno el bool si la llamada fue en horario 'laboral' o DIURNO (cuando hay sol)
        #notar que la hora < 20 significa que 19hs y 59 min da True
        table['DURING_DAY']= table['TIMESTAMP'].apply(lambda x: x.hour>=5 and x.hour<20 )

        #me quedo con este pequenyo corte de la tabla
        table_weeknight = table[(table['DURING_WEEKEND']==False) & (table['DURING_DAY']==False )]

        #hago el primer procesamiento aca
        table_weeknight = table_weeknight.groupby(['USER','CEL_ID'],
                                                            {'ANTENNA_COUNT_WEEKNIGHT':gl.aggregate.COUNT()})

        table_weeknight = table_weeknight.groupby(['USER'],                                             {'ANTENNA_COUNT_DICT_WEEKNIGHT':gl.aggregate.CONCAT("CEL_ID","ANTENNA_COUNT_WEEKNIGHT")})

        table_weeknight['ANTENNA_ID_WEEKNIGHT'] = table_weeknight['ANTENNA_COUNT_DICT_WEEKNIGHT'].\
        apply(lambda user: get_columns_from_dict(user, long_mode))
        
        
        #dropear el count_dict nomas
        table_weeknight = table_weeknight.remove_column('ANTENNA_COUNT_DICT_WEEKNIGHT')
        
        if long_mode: 
            table_weeknight['COUNT_WEEKNIGHT'] = table_weeknight['ANTENNA_ID_WEEKNIGHT'].\
                apply(lambda row: row[1])
            table_weeknight = table_weeknight.unpack('COUNT_WEEKNIGHT')
        
        table_weeknight['ANTENNA_ID_WEEKNIGHT'] = table_weeknight['ANTENNA_ID_WEEKNIGHT'].\
        apply(lambda row: row[0])
        
        #desarmo la lista de c/celda en varias columnas, una x/c/ elem de la lista
        table_weeknight = table_weeknight.unpack('ANTENNA_ID_WEEKNIGHT') 
        
        if not(long_mode): table_weeknight = table_weeknight['USER','ANTENNA_ID_WEEKNIGHT.0']
        
        table_weeknight = table_weeknight.\
        rename(dict([(col,col.replace(".","_")) for col in table_weeknight.column_names() if ("." in col)]))
        
        
        local_time = time.localtime()
        print_str = 'finished weeknight table for group {g} of {p}, time elapsed is {t} localtime is {ho}:{mi:0=2d} '.format(g = group,  p = passes, t=(time.time()-start_time), ho=local_time.tm_hour,mi=local_time.tm_min)
        print(print_str)
        logging.info( print_str )

        #continuo con el resto del procesamiento,pero en la tabla sin filtrar
        table = table.groupby(['USER','CEL_ID'],
                              {'ANTENNA_COUNT':gl.aggregate.COUNT()})

        table = table.groupby(['USER'],
                             {'ANTENNA_COUNT_DICT':gl.aggregate.CONCAT("CEL_ID","ANTENNA_COUNT")})

        table['ANTENNA_ID'] = table['ANTENNA_COUNT_DICT'].apply(lambda user: get_columns_from_dict(user,long_mode))
        
        table = table.remove_column('ANTENNA_COUNT_DICT')
        
        # si solo queremos el output para el ground_truth, no nos interesan los counts en absoluto
        if long_mode:
            table['COUNT'] = table['ANTENNA_ID'].apply(lambda row: row[1])
            table = table.unpack('COUNT') 
        
        table['ANTENNA_ID'] = table['ANTENNA_ID'].apply(lambda row: row[0])
        
        table = table.unpack('ANTENNA_ID') 
        
        if not(long_mode): table = table['USER','ANTENNA_ID.0']
        table = table.rename(dict([(col,col.replace(".","_")) for col in table.column_names() if ("." in col)]))

        
        #juntamos las dos tablas procesadas
        table = table.join(table_weeknight,on = 'USER',how = 'left')
        
        del table_weeknight

        #relleno todos los NANs que van a aparecer del join
        for col in [col for col in table.column_names() if ("ANTENNA" in col or "COUNT" in col )]:
            if "ANTENNA" in col:
                table = table.fillna(col,value="-1")
                if "COUNT" in col:
                    table = table.fillna(col,value=-1)
                    print_str ='finished data processing from group {g} of {p}, time elapsed is {t} \n Start saving output files '.format(g = group, p = passes,t=(time.time()-start_time))
                    print(print_str)
                    logging.info( print_str )
                    
        table.save(output_file)

        del table
        local_time = time.localtime()
        print_str = 'finished saving group {g} of {p}, time elapsed is {t} localtime is {ho}:{mi:0=2d} '.format(g = group,
                                            p = passes, t=(time.time()-start_time), ho=local_time.tm_hour,mi=local_time.tm_min)
        print(print_str)
        logging.info( print_str )
            
    then = start_time
    seconds = time.time() - then

    print("total running time of script is %d " % seconds)

if __name__=='__main__':
    #set logging environment, files will start logging when algorithm was first started 
    log_date = time.localtime()
    log_date = "{day:0=2d}".format(day = log_date.tm_mday) + "_" + "{mon:0=2d}".format(mon = log_date.tm_mon)
    print('log date is %s' %log_date)
    
    log_dir = '/home/juan/mobility-study/mexico-scripts-ver2/logs/{log}'.format(log = log_date)
    
    log_file = log_dir + "/log.txt"
    
    if not(os.path.exists(log_dir)):
        os.mkdir( log_dir, 0755 );
        print("Creating the log dir" ) 
    
    logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode="a+",
                        format="%(asctime)-15s %(message)s")
    main(len(sys.argv), sys.argv)
