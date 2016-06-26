import numpy as np; 
import os;
import random;
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


#seteamos el lugar de trabajo
rootdir="/home/juan/mobility-study/argentina-scripts"
os.chdir(rootdir)

def get_output_file(group = -1,sample=False):
    output = "/home/juan/mobility-study/argentina-scripts/output/homeantenna_sframe"
    if sample == True:
        output = output + "_sample"
    if group != -1:
        output = output + "_group{g}_1".format(g=group)
    return output

#from dictionary output the order list of most_used_antennas with their corresponding counts
def get_columns_from_dict(user_dict):
    antenna_count_list = [-1]*10
    #por un problema de type consistency dentro de la listas que le meto al SFrame, aca los -1 tienen que ser strings
    antenna_list = ["-1"]*10
    sorted_user_dict = sorted(user_dict, key=user_dict.get, reverse=True)
    for i,ant in enumerate(sorted_user_dict):
        if(i>9):
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
    print("python userAntennaMapping-arg.py [mode]")
    print("python SumLinks-arg.py [mode] [month]")
    print("mode = 'true' to test out the algorithm on a sample of upto 7 days for a (random) particular month")
    print("mode = 'false' to run it for all available months")

def main(argc, argv):
    #notar aca que python toma 2 parametros, el script propiamente y el parametro que entra al script
    if argc != 2:
        print('argc != 2')
        printUsage()
        return 0
    if argv[1] == 'false': test = False 
    elif argv[1] == 'true': test = True
    else:  
        printUsage()    
        sys.exit()
        
    start_time = time.time()

    #generamos el diccionario que setea los parametros sobre el cual vamos a iterar
    year = 2011
    ms = [11,12,1,2,3]
    if test:
        ms = list(np.random.choice(ms,(1,)))
        
        print_str = 'test month is %s' %str(ms)
        print(print_str)
        logging.info( print_str )
    
    months = dict()
    
    for month in ms:
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
                length = np.random.choice(range(5,11),(1,))[0]
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
                sys.exit()

    #load necessary antennas_file. The idea is to filter calls which can't be geolocated since we don't have that cel_id in the database
    antennas_file = '/home/juan/mobility-study/argentina-scripts/data/celdas_limpio.csv'
    antennas = gl.SFrame.read_csv( antennas_file, delimiter='|', 
                                         header=True, skip_initial_space=True, 
                                         column_type_hints = [str,float, float, str, str, bool], 
                                         na_values=['NaN'],
                                         usecols = ['CEL_ID','LATITUD',
                                                    'LONGITUD','DEPARTAMENTO','PROVINCIA','EPIDEMIC'],  
                                         error_bad_lines=False,
                                         verbose = False
                                        )                
                
            #primero leemos todos los files que vamos a necesitar en ese mes y lo pasamos a formato sframe para cargar mas rapido cuando necesitemos
    local_time = time.localtime()

    print_str = "Read all Sframe dirs and append to one big table, time elapsed is {t}  localtime is {ho}:{mi:0=2d}".format(t=(time.time()-start_time), ho = local_time.tm_hour , mi = local_time.tm_min )
    print(print_str)
    logging.info( print_str )

    #aca seteamos como vamos a partir la tabla segun el nro correspondiente a c/hash y tomando modulo
    passes = 20 
    
    print('months are {ms}'.format(ms = str(months)))
    #creo los grupos que despues van a filtrar c/chunk de la tabla para hacer varias pasadas
    for group in range(0,passes):
        
        local_time = time.localtime()
        print_str = "working group number {it} of {pas}, time elapsed is {t} \n".format(it=group,pas=passes, t=(time.time()-start_time))
        print(print_str)
        logging.info( print_str )
        
        output_file = get_output_file(group=group)
        if test:
            output_file = get_output_file(group=group,sample = test)
        #si es un test ni hago el check
        if not(test) and (os.path.exists(output_file)):
            print_str = "skipping {gr} since output_dir exists".format(gr = group) 
            print(print_str)
            logging.info( print_str ) 
            continue

        #itero sobre todos los day-months
        
        table =  gl.SFrame()

        for month in months:
            year = months[month]['year']
            days = months[month]['days']
            print(year,month,str(days))
            for day in days:
                #si estoy "reiniciando" el algoritmo, chequeo que el output no exista ya
        
                sframe_dir = '/home/juan/mobility-study/argentina-scripts/sframe_cdrs/{y}/{m:0=2d}/{d:0=2d}'.format(y=year,m=month,d=day)

                local_time = time.localtime()
                print_str = "Reading sframe file for day {d}-{ms}, time elapsed is {t} localtime is {ho}:{mi:0=2d} ".\
                      format(d=day,ms=month,t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min) 
                print(print_str)
                logging.info( print_str )
                
                daily_table = gl.load_sframe(sframe_dir)
                daily_table.remove_columns(['OTHER_OPERATOR','DURATION'])

                 #a cada tabla diaria filtro por todos los USERs por el hash del string (el hash es un int) y despue filtro modulo passes
                #y trabajo sobre la tabla subgroup nada mas que ahora tiene menos usuarioss
                daily_table = daily_table[daily_table['USER'].apply(lambda x: hash(x) % passes == group )]
                
                ## por el problema de las antenas invisibles tipo 'CTI 1', 'CTI 2', etc. voy a quedarme con las filas del CDR para 
                # el cual se exactamente el lat/long de su antenna.
                daily_table['CLIENT_CELL_ID'] = daily_table['CLIENT_CELL_ID'].apply(lambda x: x[:-1] if len(x) ==6 else x)
                table = table.append(daily_table.filter_by(antennas['CEL_ID'],'CLIENT_CELL_ID'))

                del daily_table

            #entonces la idea es que yo ahora solo voy a trabajar, dentro de esta tabla filtrada y para todos los dias del mes juntos
        print_str = 'finished day reading for group {g} of {p}, time elapsed is {t} localtime is {ho}:{mi:0=2d} '.format(g = group,
                                            p = passes, t=(time.time()-start_time), ho=local_time.tm_hour,mi=local_time.tm_min)
        print(print_str)
        logging.info( print_str )
        
	if test:
		print_str = 'Final table size when using {p} groups and {d} days is {n} '.format(p = passes, d = len(days), n = len(table))
        print(print_str)
        logging.info( print_str )
        
        try:
            table['TIMESTAMP'] = table['DATE','TIME'].apply(lambda x: x['DATE'][0:4]+'-'+x['DATE'][4:6]+'-'+x['DATE'][6:8] +'-'+x['TIME'][0:2]+'-'+x['TIME'][2:4]+'-'+x['TIME'][4:6])
        except:
            print_str = table.column_names()
            print(print_str)
            logging.info( print_str )
            
        table['TIMESTAMP'] = table['TIMESTAMP'].str_to_datetime(str_format='%Y-%m-%d-%H:%M:%S')

        #limpio la antenna hash, sacandome el ultimo caracter pues este no identifica la antenna sino que modifica el tipo de
        #llamado utilizado en esa call solamente
        #dropeo todas las celdas 
        table =  table[table['CLIENT_CELL_ID'].apply(lambda x: len(x)>=5)]
        table['CLIENT_CELL_ID'] = table['CLIENT_CELL_ID'].apply(lambda x: x[:-1] if len(x) ==6 else x)

        table.remove_columns(['DATE','TIME'])

        ## leo si las llamadas fueron hechas durante el findesemana 
        table['DURING_WEEKEND'] = table['TIMESTAMP'].apply(lambda x: x.weekday()==5 or x.weekday()==6)

        # asigno el bool si la llamada fue en horario 'laboral' o DIURNO (cuando hay sol)
        #notar que la hora < 20 significa que 19hs y 59 min da True
        table['DURING_DAY']= table['TIMESTAMP'].apply(lambda x: x.hour>=5 and x.hour<20 )

        #me quedo con este pequenyo corte de la tabla
        table_weeknight = table[table['DURING_WEEKEND']==False and table['DURING_DAY']==False ]

        #hago el primer procesamiento aca
        table_weeknight = table_weeknight.groupby(['USER','CLIENT_CELL_ID'],
                                                            {'ANTENNA_COUNT_WEEKNIGHT':gl.aggregate.COUNT()})

        table_weeknight = table_weeknight.groupby(['USER'],                                             {'ANTENNA_COUNT_DICT_WEEKNIGHT':gl.aggregate.CONCAT("CLIENT_CELL_ID","ANTENNA_COUNT_WEEKNIGHT")})

        table_weeknight['ANTENNA_ID_WEEKNIGHT'] = table_weeknight['ANTENNA_COUNT_DICT_WEEKNIGHT'].\
        apply(lambda user: get_columns_from_dict(user))
        table_weeknight['COUNT_WEEKNIGHT'] = table_weeknight['ANTENNA_ID_WEEKNIGHT'].\
        apply(lambda row: row[1])
        table_weeknight['ANTENNA_ID_WEEKNIGHT'] = table_weeknight['ANTENNA_ID_WEEKNIGHT'].\
        apply(lambda row: row[0])
        table_weeknight = table_weeknight.unpack('ANTENNA_ID_WEEKNIGHT') 
        table_weeknight = table_weeknight.unpack('COUNT_WEEKNIGHT') 
        table_weeknight = table_weeknight.\
        rename(dict([(col,col.replace(".","_")) for col in table_weeknight.column_names() if ("." in col)]))

        ## falta dropear el column dict nomas
        table_weeknight= table_weeknight.remove_column('ANTENNA_COUNT_DICT_WEEKNIGHT')

        #continuo con el resto del procesamiento,pero en la tabla sin filtrar
        table = table.groupby(['USER','CLIENT_CELL_ID'],
                              {'ANTENNA_COUNT':gl.aggregate.COUNT()})

        table = table.groupby(['USER'],
                             {'ANTENNA_COUNT_DICT':gl.aggregate.CONCAT("CLIENT_CELL_ID","ANTENNA_COUNT")})

        table['ANTENNA_ID'] = table['ANTENNA_COUNT_DICT'].apply(lambda user: get_columns_from_dict(user))
        table['COUNT'] = table['ANTENNA_ID'].apply(lambda row: row[1])
        table['ANTENNA_ID'] = table['ANTENNA_ID'].apply(lambda row: row[0])
        table = table.unpack('ANTENNA_ID') 
        table = table.unpack('COUNT') 
        table = table.rename(dict([(col,col.replace(".","_")) for col in table.column_names() if ("." in col)]))

        ## falta dropear el column dict nomas
        table = table.remove_column('ANTENNA_COUNT_DICT')

        #juntamos las dos tablas procesadas
        table = table.join(table_weeknight,on = 'USER',how = 'left')

        del table_weeknight

        #relleno todos los NANs que van a aparecer
        for col in [col for col in table.column_names() if ("ANTENNA" in col or "COUNT" in col )]:
            if "ANTENNA" in col:
                table = table.fillna(col,value="-1")
                if "COUNT" in col:
                    table = table.fillna(col,value=-1)
                    print_str ='finished data processing from group {g} of {p}, time elapsed is {t}\n Start saving output files '.format(g = group, p = passes,t=(time.time()-start_time))
                    print(print_str)
                    logging.info( print_str )
                    
        table.save(output_file)

        del table
        
        print_str = "Finished saving group {gr} of {p}, time elapsed is {t}\n ".format(gr=group,p=passes,t=(time.time()-start_time)) 
        print(print_str)
        logging.info( print_str )
        
        then = start_time
        seconds = time.time() - then

    print("total running time of script is %d " % seconds)


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
