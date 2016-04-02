import pandas as pd; 
import numpy as np; 
import os;
import random;
import time
np.random.seed(2016)


#ejemplo  "/grandata/simple_format/01-02012014.txt.gz"
#seteamos el lugar de trabajo
rootdir="/grandata/simple_format/"
os.chdir(rootdir)
year = "2014"; 
month_start= "1";
if int(month_start )<10:
    month_start="0"+month_start
    
day_start = "01"
day_end = str(int(day_start)+1)
if int(day_end )<10:
    day_end="0"+ day_end

input_file= rootdir +"simple_format_{y}{ms}.txt.gz"\
                .format(y=year,ms=month_start,
                       ds=day_start,de=day_end)
    
def get_output_file(night_filter=False,week_end=False):
    output = "/home/juan/mobility-study/past_labels"
    if week_end == True:
        output = output + "_wkend"
    if night_filter == True:
        output = output + "_ngtfilter"
    return output + ".txt.gz"

output_file = get_output_file()


#para enriquecer el dataset de CDRs con info acerca de la zona epidemica etc.
antennas= pd.read_csv('/home/juan/mobility-study/antennas_mexico.csv',sep = "|",header=0,index_col=0)
antennas.index.rename("ANTENNA_ID",inplace=True)

user_hashes_file= "/home/juan/mobility-study/output_sum_links.txt.gz"

#levanto la tabla de users hash_map.
user_hashes = pd.read_csv("/home/juan/mobility-study/output_sum_links.txt.gz",
                                  sep="|",
                                  header=0,
        dtype = {'LineKeyOrigin':np.object_,'CallsWeekDaylight':np.uint16,'CallsWeekDaylight_EPI':np.uint16,'CallsWeekNight':np.uint16,
            'CallsWeekNight_EPI':np.uint16,'CallsWeekend':np.uint16,'CallsWeekend_EPI':np.uint16, 'TimeWeekDaylight':np.uint16,
                'TimeWeekDaylight_EPI':np.uint16,'TimeWeekNight':np.uint16,'TimeWeekNight_EPI':np.uint16,'TimeWeekEnd':np.uint16
                ,'TimeWeekEnd_EPI':np.uint16,'TOTAL_USERS':np.uint16,'EPI_USERS':np.uint16,'EXP_USERS':np.uint16},
                          usecols = ['LineKeyOrigin'],
                )

week_end = False
night_filter = False

output_file = get_output_file()
sample_file = output_file.replace(".txt.gz","_sample.txt.gz")
#para el manejo de las distintas salidas del programa


## script para extraer los labels de los simple_formats de 2014
#cada dataset tiene aprox 450M de datos, de los cuales aprox 45M son de los Telco users que nos intersan
# como hay 16 meses a analizar ---> tengo 720M registros que mirar, luego hago 15 pasadas filtrados por el user_hash

#ver el tiempo que tarda
start_time = time.time()

#el chunk basicamente va leyendo el file de a 'chunksize' cantidad de filas
#subgroup = pd.DataFrame()

#hay 12 meses del cual extraer atributos:
months14= ["2014"+ "0"+str(month) if int(month )<10 else "2014"+str(month) for month in range(1,13)]
months15= ["2015"+ "0"+str(month) if int(month )<10 else "2015"+str(month) for month in range(1,5)]
months = months14  + months15

#aca seteamos como vamos a partir la tabla segun el nro correspondiente a c/hash y tomando modulo
passes = 15
#creo los grupos que despues van a filtrar c/chunk de la tabla para hacer varias pasadas
for group in range(passes):
    print("\n working group number {it} of {pas}, time elapsed is {t} \n".\
          format(it=group,pas=passes, t=(time.time()-start_time)))

    #itero sobre los meses
    subgroup = pd.DataFrame()
    for month in months:
	if (month == '201404'):
            continue

        input_file= rootdir +"simple_format_{m}.txt.gz"\
		.format(m=month)

        table = pd.read_csv(
                input_file,
                engine = 'c',
                chunksize = 18*10**7,
    #            iterator =True,
                sep = ' ',
                header = 0,
                index_col=None,
                usecols = ['USER','ANTENNA_ID'],
                error_bad_lines= False,
                warn_bad_lines= True,
                dtype = {'ANTENNA_ID':np.uint16,'USER':np.object_}
                )

        #cuando entramos a este loop, table tiene tantos 'chunks' como el valor entero de la cantidad de lineas en el file
        #dividido el tamanyo del chunksize

        numb=0;
        for chunk in table:
                numb+=1
                #aca filtro por la cantidad 
                chunk = chunk[chunk['USER'].isin(user_hashes.loc[:,'LineKeyOrigin'].values)]
                #a cada chunk filtro por todos los USERs por el hash del string (el hash es un int) y despue filtro modulo passes
                #y trabajo sobre la tabla subgroup nada mas que ahora tiene menos usuarios
                subgroup = subgroup.append(chunk[chunk['USER'].apply(lambda x: hash(x) % passes == group )])
    
        print("Finished parsing month {ms}-{y}, time elapsed is {t} ".format(ms=month,y=year,t=(time.time()-start_time)))
        
    #entonces la idea es que yo ahora solo voy a trabajar, dentro de esta tabla filtrada y para todos los meses juntos
    
    #paso de segundos a horas
    #notar que TIMESTAMP arranca en 0 segundos para domingo 01/01/2012 00:00am 
    #con lo cual domingo es el dia 0, lunes el 1, asi..
    print('finished reading months for group {it} of {pas}: time elapsed is {t} \n'.\
    format(it=group,pas=passes, t=(time.time()-start_time)) )
    
    #filtro usuarios con pocos o demasiados llamados en general menos de 25 y mas de 2000 en 5 meses  
    grouped = subgroup.groupby(['USER', 'ANTENNA_ID'])['ANTENNA_ID'].agg({'count': np.size})
    
    del subgroup
    grouped.reset_index(inplace=True,drop=False)   
   
    #reordeno dentro de c/ USER por el count del antenna, esto me sirve para despues ordenar las antenas por uso
    grouped.sort_values(by=['USER','count'],ascending=False,inplace=True)
    grouped = pd.merge(grouped,antennas['EPIDEMIC'].reset_index(), on='ANTENNA_ID',how = 'left')

    ##enriquezco la muestra con datos epidemicos
    #primero agrego a cada antenna del df el dato de si es epidemica
    #despues agrupo por el USER y me fijo solo la columna epidemica en c/grupo
    #finalmente sumo en c/ grupo y tomo la parte superior 
    #entera de esa division con el largo del grupo. Si uso al menos una antena epidemica entonces esta expuesto(==1) Si no,
    # da 0 pues no estuvo expuesto.        
    ##enriquezco la muestra con datos epidemicos

    exposed_info = grouped.groupby('USER')['EPIDEMIC'].\
        agg({'EXPOSED' : lambda x: int( np.ceil(np.sum(x)*1.0/np.size(x)) )})

    #actualizo la tabla grouped
    grouped = grouped.join(exposed_info['EXPOSED'],on="USER",how="left")
    del exposed_info

    #creo la tabla filtrada solo por users, que es la que voy a terminar guardando (hay tantos rows como users)
    output_table = grouped.drop_duplicates(subset = 'USER', keep='first')
    del grouped

    #re indexo
    output_table.set_index('USER',inplace=True,drop=False)
    
    #agrupo ahora la tabla por USER para hacer todos los calculos en los grupos
    output_table.drop('count',axis=1,inplace=True)
    output_table = output_table.set_index('USER')
    #paso a ints todas las columnas (el hash ya esta de index)
    output_table = output_table.astype(int,copy=False)
    
    #aca termino guardando (en forma de append) el output final pero solo para esos usuarios % pass ==group

    #el primer write (first group==0) va con header
    if group ==0 :
        output_table.to_csv(output_file, index = True,
                   header = True,sep = "|", 
                            compression = "gzip", mode='w')
    else: 
        output_table.to_csv(output_file, index = True,
                   header = False,sep = "|", 
                    compression = "gzip", mode='a')

    print("Finished group {gr} of {ps}, time elapsed is {t}\n ".format(gr=group,ps=passes,t=(time.time()-start_time)))

print("total running time of script is %s " % (time.time() - start_time))

