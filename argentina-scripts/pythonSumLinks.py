import pandas as pd;
import numpy as np;
import os;
import random;
import graphlab as gl
import time
import datetime
np.random.seed(2016)
    
def get_output_file(month,group = -1,sample=False):
    output = "/home/juan/mobility-study/argentina-scripts/output/2012/{0}/sum_links_1".format(month,group)
    if sample == True:
        output = output + "_sample"
    if group != -1:
        output = output + "_group{g}".format(g=group)
    return output


days = range(1,32)

year = 2012
month = 1
#check february days length
if month ==2:
    days = range(1,30)

start_time = time.time()

passes = 30
for group in range(0,passes):
    local_time = time.localtime()
    print("working group number {it} of {pas}, time elapsed is {t}, localtime is {ho}:{mi} \n".format(it=group,pas=passes, t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min))
    
    output_file = get_output_file(month,group)
    #agrego este control para cuando tuve que cortar antes el algo por alguna razon
    if (os.path.exists(output_file)):
        print('skipping group {gr} since output-dir exists: {di}'.format(gr = group, di =output_file)) 
	continue
    
    #itero sobre los meses
    table =  gl.SFrame()
    for day in days:

        sframe_dir = '/home/juan/mobility-study/argentina-scripts/sframe_cdrs/{y}/{m:0=2d}/{d:0=2d}'.format(y=year,m=month,d=day)        
        daily_table = gl.load_sframe(sframe_dir)
        daily_table.remove_column('DIRECTION')
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

    table_weekend_call = table_weekend.groupby(['USER','OTHER_USER'],
                     {'CallsWeekEnd':gl.aggregate.COUNT('TIMESTAMP')})

    table_weeknight = table[(table['DURING_DAYLIGHT']==False) &  (table['DURING_WEEKEND']==False)]

    table_weeknight_call = table_weeknight.groupby(['USER','OTHER_USER'],
                     {'CallsWeekNight':gl.aggregate.COUNT('TIMESTAMP')})

    table_weekday = table[(table['DURING_DAYLIGHT']==True) &  (table['DURING_WEEKEND']==False)]
    
    local_time = time.localtime()
    print("Finished categorizing, start grouping. Time elapsed is {t}, localtime is {ho}:{mi} \n".format(it=group,pas=passes, t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min))
    table_weekday_call = table_weekday.groupby(['USER','OTHER_USER'],
                     {'CallsWeekDay':gl.aggregate.COUNT('TIMESTAMP')})


    table_weekend_time = table_weekend.groupby(['USER','OTHER_USER'],
                     {'TimeWeekEnd':gl.aggregate.SUM('DURATION')})


    table_weeknight_time = table_weeknight.groupby(['USER','OTHER_USER'],
                     {'TimeWeekNight':gl.aggregate.SUM('DURATION')})


    table_weekday_time = table_weekday.groupby(['USER','OTHER_USER'],
                     {'TimeWeekDay':gl.aggregate.SUM('DURATION')})

    del table_weekend, table_weeknight, table_weekday
    
    table = table_weekend_call.join(table_weeknight_call,on = ['USER','OTHER_USER'], how = 'outer')
    del table_weekend_call, table_weeknight_call
    table =  table.join(table_weekday_call,on = ['USER','OTHER_USER'], how = 'outer')
    del table_weekday_call

    table =  table.join(table_weekend_time,on = ['USER','OTHER_USER'], how = 'outer')
    del table_weekend_time

    table =  table.join(table_weekday_time,on = ['USER','OTHER_USER'], how = 'outer')
    del table_weekday_time

    table =  table.join(table_weeknight_time,on = ['USER','OTHER_USER'], how = 'outer')
    del table_weeknight_time

    for col in table.column_names():
        if 'USER' in col:
            continue
        table = table.fillna(col,0)
    
    local_time = time.localtime()       
    print('finished data processing from group {g} of {p}, time elapsed is {t}\n Start saving output files , localtime is {ho}:{mi} \n'.format(g = group, p = passes, t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min))
    #salvo c/file por separado y despues los appendeo todos en 1.
    output_file = get_output_file(month,group)
    print('output_file is located at %s' % output_file)
    
    table.save(output_file)
    local_time = time.localtime()
    print("Finished group {gr} of {p}, time elapsed is {t}\, localtime is {ho}:{mi}\n ".format(gr=group,p=passes,t=(time.time()-start_time),ho=local_time.tm_hour,mi=local_time.tm_min))

then = start_time
seconds = time.time() - then
print("total running time of script is %d " % seconds)
