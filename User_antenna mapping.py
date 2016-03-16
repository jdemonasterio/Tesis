import pandas as pd
import numpy as np
import os
import random;
#pd.set_option('display.max_rows', 300)
from matplotlib import pyplot as plt
import time
import os
np.random.seed(2016)


#ejemplo  "/grandata/simple_format/01-02012014.txt.gz"
#seteamos el lugar de trabajo
rootdir="/grandata/simple_format/"
os.chdir(rootdir)
year = "2015"; 
month_start= "01";
#todos estos sum_links terminan 2 meses mas tardes
month_end= str(int(month_start)+2)
if int(month_end )<10:
    month_end="0"+month_end
    
day_start = "01"
day_end = str(int(day_start)+1)
if int(day_end )<10:
    day_end="0"+ day_end

input_file= rootdir +"simple_format_{y}{ms}.txt.gz"\
                .format(y=year,ms=month_start,me=month_end,
                       ds=day_start,de=day_end)
    
def get_output_file(hash_map=False,night_filter=False,week_end=False):
    output = "/home/juan/mobility-study/output"
    if week_end == True:
        output = output + "_wkend"
    if night_filter == True:
        output = output + "_ngtfilter"
    if hash_map == True:
        output = output + "_user_hash_map"
    return output + ".txt"


#para enriquecer el dataset de CDRs con info acerca de la zona epidemica etc.
antennas= pd.read_csv('/home/juan/mobility-study/antennas_mexico.csv',sep = "|",header=0,index_col=0)
antennas.index.rename("ANTENNA_ID",inplace=True)

sample_file = input_file.replace(".txt.gz","_sample.txt.gz")
#para el manejo de las distintas salidas del programa

week_end = False
night_filter = False
hash_map = False
output_file = get_output_file(hash_map,night_filter,week_end)

##MAIN ALGORITHM

## script para extraer todos los atributos del simple_format

#ver el tiempo que tarda
start_time = time.time()

#el chunk basicamente va leyendo el file de a 'chunksize' cantidad de filas
#subgroup = pd.DataFrame()

#hay cinco meses del cual extraer atributos:
months= ["0"+str(month) for month in range(5,10)]

year = "2015"

#aca seteamos como vamos a partir la tabla segun el nro correspondiente a c/hash y tomando modulo
passes = 45
#creo los grupos que despues van a filtrar c/chunk de la tabla para hacer varias pasadas
for group in range(passes):
    print("working group number {it} of {pas}, time elapsed is {t} \n".format(it=group,pas=passes, t=(time.time()-start_time)))

    #itero sobre los meses
    subgroup = pd.DataFrame()
    for month in months:
        print("Working on month {ms}-{y}, time elapsed is {t} ".format(ms=month,y=year,t=(time.time()-start_time)))
        input_file= rootdir +"simple_format_{y}{ms}.txt.gz"\
            .format(y=year,ms=month)

        table = pd.read_csv(
                input_file,
                engine = 'c',
                chunksize = 6*10**7,
    #            iterator =True,
                sep = ' ',
                header = 0,
                index_col=None,
                usecols = ['USER','OTHER_USER','ANTENNA_ID','TIMESTAMP'],
                dtype = {'TIMESTAMP':np.uint32,'ANTENNA_ID':np.uint16,'USER':np.object_,'OTHER_USER':np.object_}
                )

        #cuando entramos a este loop, table tiene tantos 'chunks' como el valor entero de la cantidad de lineas en el file
        #dividido el tamanyo del chunksize

        numb=0;
        for chunk in table:
                numb+=1
                #a cada chunk filtro por todos los USERs por el hash del string (el hash es un int) y despue filtro modulo passes
                #y trabajo sobre la tabla subgroup nada mas que ahora tiene menos usuarios
                
		print("Working on chunk {n} of month {ms}, time elapsed is {t} ".format(ms=month,n=numb,t=(time.time()-start_time)))
		subgroup = subgroup.append(chunk[chunk['USER'].apply(lambda x: hash(x) % passes == group )])
    
	#entonces la idea es que yo ahora solo voy a trabajar, dentro de esta tabla filtrada y para todos los meses juntos
    
    #paso de segundos a horas
    #notar que TIMESTAMP arranca en 0 segundos para domingo 01/01/2012 00:00am 
    #con lo cual domingo es el dia 0, lunes el 1, asi..
    print('finished month reading')
    subgroup['Hour'] =  (subgroup['TIMESTAMP'].values*1.0/3600)%24
    subgroup['Day']  =  (subgroup['TIMESTAMP'].values*1.0/(3600*24))%7

    #filtro usuarios con pocos o demasiados llamados en general menos de 5 mensuales y mas de 400  
    insignificant_users = subgroup['USER'].value_counts()[(subgroup['USER'].value_counts() < 5) \
                        | (subgroup['USER'].value_counts() > 400)].index.values.tolist()
    subgroup= subgroup.loc[~subgroup['USER'].isin(insignificant_users)]


    #filtro segun nightfilter y week_end. el day light seria de [7,19) segun la convencion de mexico/GranData
    if night_filter == True:
        subgroup = subgroup.loc[(subroup['Hour']<7) | (subgroup['Hour']>19)]
    if week_end == True:
        subgroup = subgroup.loc[(subgroup['Day']==0) | (subgroup['Day']==6)]


    #   

    grouped = subgroup.groupby(['USER', 'ANTENNA_ID'])['ANTENNA_ID'].agg({'count': np.size})
    grouped.reset_index(inplace=True,drop=False)

    del subgroup
    #reordeno dentro de c/ USER por el count del antenna, esto me sirve para despues ordenar las antenas por uso
    grouped.sort_values(by=['USER','count'],ascending=False,inplace=True)

    ##enriquezco la muestra con datos epidemicos
    #primero agrego a cada antenna del df el dato de si es epidemica
    #despues agrupo por el USER y me fijo solo la columna epidemica en c/grupo
    #finalmente sumo en c/ grupo y tomo la parte superior 
    #entera de esa division con el largo del grupo. Si uso al menos una antena epidemica entonces esta expuesto(==1) Si no,
    # da 0 pues no estuvo expuesto.        
    ##enriquezco la muestra con datos epidemicos

    exposed_info =grouped.join(antennas['EPIDEMIC'], on='ANTENNA_ID').\
    groupby('USER')['EPIDEMIC'].\
        agg({'EXPOSED' : lambda x: int( np.ceil(np.sum(x)*1.0/np.size(x)) )})

    #actualizo la tabla
    grouped = grouped.join(exposed_info['EXPOSED'],on="USER")
    del exposed_info


    #creo la tabla filtrada solo por users, que es la que voy a terminar guardando (hay tantos rows como users)
    output_table = grouped.drop_duplicates(subset = 'USER', keep='first')
    #re indexo
    output_table.index = output_table['USER'].values

    #agrupo ahora la tabla por USER para hacer todos los calculos en los grupos

    grouped = grouped.groupby('USER')

    #aca voy a ir agregando las top 10 antennas utilizadas por el user, Si no llego a 10 antennas, relleno con NaNs
    for i in range(10):
        #me quedo con la i-esima fila de c/grupo (si no hay fila, no toma en cuenta ese USER)

        buffer_table = grouped.nth(i)[['ANTENNA_ID','count']]
        #renombre a iesima ANTENNA_ID e iesimo count
        buffer_table.columns=['ANTENNA_ID_%i'%i,'count_%i'%i]
        #agrego esta info como nuevas columnas, dejando lo demas como NaNs
        output_table = pd.concat([output_table, buffer_table], axis=1, join_axes=[output_table.index])

    del grouped
    #los primeros ANTENNA_IDs ya no me sirven, idem con el primer
    output_table.drop('ANTENNA_ID', axis=1, inplace=True)
    output_table.drop('count', axis=1, inplace=True)
    #dropeo la columna USER que ya es redundante por el indice
    output_table.index.name = "USER"
    output_table.drop('USER', axis=1, inplace=True)

    #para los datos faltantes dentro del Top10, relleno con -1s, que vendrian a ser los NaNs
    output_table.fillna(-1,inplace=True)

    #como elimine la columan de hashes puedo convertir todo a int
    output_table = output_table.astype(int,copy=False)

    #agrego info de EPIDEMIC, asumiendo a alguien como epidemico si al antenna donde vive (la ANTENNA_ID_0) 
    #esta catalogada como EPIDEMIC

    output_table = output_table.join(antennas['EPIDEMIC'], on='ANTENNA_ID_0')

    #aca termino guardando (en forma de append) el output final pero solo para esos usuarios % pass ==group

    #el primer write (first group==0) va con header
    if group ==0 :
        output_table.to_csv(output_file, index = True,
                   header = True, mode='a')
    else: 
        output_table.to_csv(output_file, index = True,
                   header = False, mode='a')

    
then = start_time
seconds = time.time() - then
print("total running time of script is %d " % seconds)



