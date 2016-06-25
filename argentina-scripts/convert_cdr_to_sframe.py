import numpy as np; import os;import random;
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

def get_input_file(year,month,day):
    return rootdir +"{y}/{m}/binaria_gsm_{y}{m:0=2d}{d:0=2d}.csv.gz"\
                .format(y=year,m=month,d=day)

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
    
#ver el tiempo que tarda
start_time = time.time()


year = 2011

for month in [11,12,1,2,3]:
    days = range(1,32)
    
    #check november days length
    if month ==11:
        days = range(1,31)
    
    #check february days length
    if month ==2:
        days = range(1,30)
    
    #alterno el year para los meses que arrancan en enero
    if month <11:
        year = 2012
     
    print(month,year)
  
    #primero leemos todos los files que vamos a necesitar en ese mes y lo pasamos a formato sframe para cargar mas rapido
    print("Transform all raw datasets to Sframe dirs, time elapsed is {t} ".format(t=(time.time()-start_time)))
    for day in days:
        
        sframe_dir = '/home/juan/mobility-study/argentina-scripts/sframe_cdrs/{y}/{m:0=2d}/{d:0=2d}'.format(y=year,m=month,d=day)
        #print(sframe_dir)
        if (os.path.exists(sframe_dir)):
            print("skipping {m:0=2d}/{d:0=2d} since output_dir exists".format(m=month,d=day) ) 
            continue
            
        local_time = time.localtime()

        print("Reading disk file for day {d}-{ms}, time elapsed is {t} localtime is {ho}:{mi:0=2d} ".\
              format(d=day,ms=month,t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min))
        input_file= get_input_file(year,month,day)
        daily_table = gl.SFrame.read_csv( input_file, delimiter='|', 
                                         header=True, skip_initial_space=True, 
                                         column_type_hints = [str,str, str,str, str, str, int], 
                                         na_values=['NaN'],
                                         usecols = ['ORIGIN_NUMBER_ENC_B64',"TARGET_NUMBER_ENC_B64",'DIRECTION',
                                                    'FECHA','TIME','CLIENT_CELL_ID','DURATION'],  
                                         error_bad_lines=False,
                                         verbose = False
                                        )

        daily_table.rename({'ORIGIN_NUMBER_ENC_B64':'USER','FECHA':'DATE',
                            'TARGET_NUMBER_ENC_B64':'OTHER_USER'})
        
        print('original file shape is %s ' % str(daily_table.shape))
        #checking which calls have antennas which are ONLY in the approved list
        daily_table['CLIENT_CELL_ID'] = daily_table['CLIENT_CELL_ID'].apply(lambda x: x[:-1] if len(x) ==6 else x)
        daily_table = daily_table.filter_by(antennas['CEL_ID'],'CLIENT_CELL_ID')
        
        print('output file shape is %s ' % str(daily_table.shape))

        daily_table.save(sframe_dir)    

        print ('finished saving day {d} for month {m}, time elapsed is {t} localtime is {ho}:{mi:0=2d}'.\
               format(d=day,m=month,t=(time.time()-start_time), ho=local_time.tm_hour, mi=local_time.tm_min))
