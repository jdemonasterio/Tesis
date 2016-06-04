import pandas as pd; import numpy as np; import os;import random;
import graphlab as gl
pd.set_option('display.max_rows', 200)
#esto es para dibujar directo a la notebook
gl.canvas.set_target('ipynb')

#from matplotlib import pyplot as plt
#%matplotlib inline
import time
import os
import datetime
np.random.seed(2016)
import subprocess

#seteamos el lugar de trabajo
rootdir="/grandata/ca/voice/"
os.chdir(rootdir)
year = 2012; 

def get_input_file(month,day):
    return rootdir +"{y}/{m}/binaria_gsm_{y}{m:0=2d}{d:0=2d}.csv.gz"\
                .format(y=2012,m=month,d=day)

def get_output_file(month,group = -1,sample=False):
    output = "/home/juan/mobility-study/argentina-scripts/output/{0}/{1}/user_antenna_mapping".format(year,month)
    if sample == True:
        output = output + "_sample1"
    if group != -1:
        output = output + "_group{g}_1".format(g=group)
    return output 

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
            
## script para extraer todos los atributos del simple_format

#ver el tiempo que tarda
start_time = time.time()

#el chunk basicamente va leyendo el file de a 'chunksize' cantidad de filas
#subgroup = pd.DataFrame()
year = 2012

month = 1
days = range(1,32)

#check february days length
if month ==2:
    days = range(1,30)

#primero leemos todos los files que vamos a necesitar en ese mes y lo pasamos a formato sframe para cargar mas rapido cuando necesitemos
print("Transform all raw datasets to Sframe dirs, time elapsed is {t} ".format(t=(time.time()-start_time)))
for day in days:
    
    sframe_dir = '/home/juan/mobility-study/argentina-scripts/sframe_cdrs/{y}/{m:0=2d}/{d:0=2d}'.format(y=year,m=month,d=day)
    
    if not(os.path.exists(sframe_dir)):
        print("Reading disk file for day {d}-{ms}, time elapsed is {t} ".format(ms=month,d=day,t=(time.time()-start_time)))
        input_file= get_input_file(month,day)
        daily_table = gl.SFrame.read_csv( input_file, delimiter='|', 
                header=True, skip_initial_space=True, 
                column_type_hints = [str, str,str, str], 
                na_values=['NaN'],
                usecols = ['ORIGIN_NUMBER_ENC_B64',
                                    'FECHA','TIME','CLIENT_CELL_ID'],  
                error_bad_lines=False,
                verbose = False
                          )

        daily_table.rename({'ORIGIN_NUMBER_ENC_B64':'USER','FECHA':'DATE'})
                              #'TARGET_NUMBER_ENC_B64':'OTHER_USER
        daily_table.save(sframe_dir)    
    
    

print("Start processing data from Sframe dirs, time elapsed is {t} ".format(ms=month,d=day,t=(time.time()-start_time)))

#aca seteamos como vamos a partir la tabla segun el nro correspondiente a c/hash y tomando modulo
passes = 20 
#creo los grupos que despues van a filtrar c/chunk de la tabla para hacer varias pasadas
for group in range(0,passes):
    #voy a salvar c/file por separado y despues los appendeo todos en 1.
    output_file = get_output_file(month,group=group)
    
    if (os.path.exists(output_file)):
        continue
    
    print("working group number {it} of {pas}, time elapsed is {t} \n".format(it=group,pas=passes, t=(time.time()-start_time)))

    #itero sobre los meses
    table =  gl.SFrame()
    for day in days:
       
        sframe_dir = '/home/juan/mobility-study/argentina-scripts/sframe_cdrs/{y}/{m:0=2d}/{d:0=2d}'.format(y=year,m=month,d=day)        
        daily_table = gl.load_sframe(sframe_dir)
        #obs. NO levanto la columna Fecha pues esta info la puedo sacar del filename
        current_date = datetime.datetime(2012,month,day)

        #a cada tabla diaria filtro por todos los USERs por el hash del string (el hash es un int) y despue filtro modulo passes
        #y trabajo sobre la tabla subgroup nada mas que ahora tiene menos usuarios
        table = table.append(daily_table[daily_table['USER'].apply(lambda x: hash(x) % passes == group )])
    
    del daily_table
    
    #entonces la idea es que yo ahora solo voy a trabajar, dentro de esta tabla filtrada y para todos los dias del mes juntos
    print('finished day reading for group {g} of {p}, time elapsed is {t} '.format(g = group,
                                                                        p = passes, t=(time.time()-start_time)))
    
    
    table['TIMESTAMP'] = table['DATE','TIME'].apply(lambda x: x['DATE'][0:4]+'-'+x['DATE'][4:6]+'-'+x['DATE'][6:8]
                                     +'-'+x['TIME'][0:2]+'-'+x['TIME'][2:4]+'-'+x['TIME'][4:6])
    
    table['TIMESTAMP'] = table['TIMESTAMP'].str_to_datetime(str_format='%Y-%m-%d-%H:%M:%S')
    
    #limpio la antenna hash, sacandome el ultimo caracter pues este no identifica la antenna sino que modifica el tipo de
    #llamado utilizado en esa call solamente
    table['CLIENT_CELL_ID'] = table['CLIENT_CELL_ID'].apply(lambda x: x[:-1])
    
    table.remove_columns(['DATE','TIME'])
    
    ## leo si las llamadas fueron hechas durante el findesemana + viernes
    table['DURING_WEEKEND_FRIDAY'] = table['TIMESTAMP'].apply(lambda x: x.weekday()==5 or x.weekday()==6 or x.weekday()==4)

    # asigno el bool si la llamada fue en horario 'laboral'
    #notar que la hora < 20 significa que 19hs y 59 min da True
    table['DURING_WORK']= table['TIMESTAMP'].apply(lambda x: x.hour>=8 and x.hour<20 )

    table_no_work_friday = table[table['DURING_WEEKEND_FRIDAY']==True or table['DURING_WORK']==False ].copy()
    
    
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

    table_no_work_friday = table_no_work_friday.groupby(['USER','CLIENT_CELL_ID'],
                 {'ANTENNA_COUNT_NO_WORK_FRIDAY':gl.aggregate.COUNT()})

    table_no_work_friday = table_no_work_friday.groupby(['USER'],
                     {'ANTENNA_COUNT_DICT_NO_WORK_FRIDAY':gl.aggregate.CONCAT("CLIENT_CELL_ID","ANTENNA_COUNT_NO_WORK_FRIDAY")})

    table_no_work_friday['ANTENNA_ID_NO_WORK_FRIDAY'] = table_no_work_friday['ANTENNA_COUNT_DICT_NO_WORK_FRIDAY'].\
                                apply(lambda user: get_columns_from_dict(user))
    table_no_work_friday['COUNT_NO_WORK_FRIDAY'] = table_no_work_friday['ANTENNA_ID_NO_WORK_FRIDAY'].\
                        apply(lambda row: row[1])
    table_no_work_friday['ANTENNA_ID_NO_WORK_FRIDAY'] = table_no_work_friday['ANTENNA_ID_NO_WORK_FRIDAY'].\
                        apply(lambda row: row[0])
    table_no_work_friday = table_no_work_friday.unpack('ANTENNA_ID_NO_WORK_FRIDAY') 
    table_no_work_friday = table_no_work_friday.unpack('COUNT_NO_WORK_FRIDAY') 
    table_no_work_friday = table_no_work_friday.\
            rename(dict([(col,col.replace(".","_")) for col in table_no_work_friday.column_names() if ("." in col)]))

    ## falta dropear el column dict nomas
    table_no_work_friday= table_no_work_friday.remove_column('ANTENNA_COUNT_DICT_NO_WORK_FRIDAY')
    
    
    #juntamos las dos tablas procesadas
    table = table.join(table_no_work_friday,on = 'USER',how = 'left')
    
    del table_no_work_friday
    
    #relleno todos los NANs que van a aparecer
    for col in [col for col in table.column_names() if not("NO_WORK" in col) and ("ANTENNA" in col or "COUNT" in col )]:
        if "ANTENNA" in col:
            table = table.fillna(col,value="-1")
        if "COUNT" in col:
            table = table.fillna(col,value=-1)
    print('finished data processing from group {g} of {p}, time elapsed is {t}\n Start saving output files '.format(g = group,
                                                                        p = passes, t=(time.time()-start_time)))
        
    table.save(output_file)
    
    del table

    #comprimo a mano el archivo pues SFrame no comprime en gzip automaticamente los csvs
    #bashCommand = "gzip {0}".format(output_file)
    #process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    #output = process.communicate()[0]    
    #print('Output of bash gzip command is {0}'.format(output))
    
    print("Finished group {gr} of {p}, time elapsed is {t}\n ".format(gr=group,p=passes,t=(time.time()-start_time)))

then = start_time
seconds = time.time() - then
print("total running time of script is %d " % seconds)
