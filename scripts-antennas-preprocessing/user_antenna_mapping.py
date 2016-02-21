import pandas as pd; import numpy as np; import os;import random;
import time



def main():
    # parse command line options
    np.random.seed(2016)
    ##setting general params
    rootdir="/home/juan/mobility-study"
    os.chdir(rootdir)
    directory = "0315"; contract_type="Prepago";
    input_file= 'datosgeo/%s/Geo_Voz_%s_all_%s.txt.gz' % (directory,contract_type,directory)
    
    #para enriquecer el dataset de CDRs con info acerca de la zona epidemica etc.
    antennas= pd.read_csv('antennas_mexico.csv',sep = "|",header=0,index_col=0)
    antennas.index.rename("AntennaID",inplace=True) 
        
    sample_file = input_file.replace(".txt.gz","_sample.txt.gz")
    #para el manejo de las distintas salidas del programa
    def get_output_file(input_file,night_filter, week_end):
        output = input_file.replace(".txt.gz","")
        if week_end == True:
            output = output + "_wkend"
        if night_filter == True:
            output = output + "_ngtfilter"
        return output + "_test.txt.gz"
    week_end = False
    night_filter = False
    output_file = get_output_file(input_file,night_filter,week_end)
    

        ## scripot para convertir las columnas de otros types --> ints
    passes=5

    #ver el tiempo que tarda
    now = time.time()

    #el chunk basicamente va leyendo el file de a 'chunksize' cantidad de filas
    #subgroup = pd.DataFrame()

    for group in range(passes):
        subgroup = pd.DataFrame()
        table = pd.read_csv(
                input_file,
                engine = 'c',
                chunksize = 5*10**7,
    #            iterator =True,
                sep = ' ',
                header = None,
                index_col=None,
                names = ['Target','Destination','Direction','TimeStamp','Duration','AntennaID'],
                usecols = ['Target', 'AntennaID','TimeStamp'],
                dtype = {'Target':np.uint32,'Destination':np.uint32,'TimeStamp':np.uint32,
                                          'Duration':np.uint16,'AntennaID':np.uint16,'Direction':np.object_}
                )

        #cuando entramos a este loop, table tiene tantos 'chunks' como el valor entero de la cantidad de lineas en el file
        #dividido el tamanyo del chunksize
        for chunk in table:
                #a cada chunk filtro por todos los Targets que tengan resto group modulo passes. y trabajo sobre la tabla
                #subgroup nada mas que ahora tiene pocos usuarios
                subgroup = subgroup.append(chunk[chunk['Target'] % passes == group])
        #
        #entonces la idea es que yo ahora solo voy a trabajar, dentro de la tabla

        #paso de segundos a horas
        #notar que timestamp arranca en 0 segundos para domingo 01/01/2012 00:00am 
        #con lo cual domingo es el dia 0, lunes el 1, asi..

        subgroup['Hour'] =  (subgroup['TimeStamp'].values*1.0/3600)%24
        subgroup['Day']  =  (subgroup['TimeStamp'].values*1.0/(3600*24))%7

        #filtro usuarios con pocos o demasiados llamados en general menos de 5 mensuales y mas de 400  
        insignificant_users = subgroup['Target'].value_counts()[(subgroup['Target'].value_counts() < 5) \
                            | (subgroup['Target'].value_counts() > 400)].index.values.tolist()
        subgroup= subgroup.loc[~subgroup['Target'].isin(insignificant_users)]


        #filtro segun nightfilter y week_end
        if night_filter == True:
            subgroup = subgroup.loc[(subroup['Hour']<8) | (subgroup['Hour']>18)]
        if week_end == True:
            subgroup = subgroup.loc[(subgroup['Day']==0) | (subgroup['Day']==6)]



        grouped = subgroup.groupby(['Target', 'AntennaID'])['AntennaID'].agg({'count': np.size})
        grouped.reset_index(inplace=True,drop=False)

        del subgroup
        #reordeno dentro de c/ target por el count del antenna, esto me sirve para despues
        grouped.sort_values(by=['Target','count'],ascending=False,inplace=True)

        ##enriquezco la muestra con datos epidemicos
        #primero agrego a cada antenna del df el dato de si es epidemica
        #despues agrupo por el target y me fijo solo la columna epidemica en c/grupo
        #finalmente sumo en c/ grupo y tomo la parte superior 
    #entera de esa division con el largo del grupo. Si uso al menos una antena epidemica entonces esta expuesto(==1) Si no,
    # da 0 pues no estuvo expuesto.        
        ##enriquezco la muestra con datos epidemicos

        exposed_info =grouped.join(antennas['EPIDEMIC'], on='AntennaID').\
        groupby('Target')['EPIDEMIC'].\
            agg({'EXPOSED' : lambda x: int( np.ceil(np.sum(x)*1.0/np.size(x)) )}) 

        #actualizo la tabla
        grouped = grouped.join(exposed_info['EXPOSED'],on="Target")
        del exposed_info


        #creo la tabla filtrada solo por users, que es la que voy a terminar guardando (hay tantos rows como users)
        output_table = grouped.drop_duplicates(subset = 'Target', keep='first')
        #re indexo
        output_table.index = output_table['Target'].values

        #agrupo ahora la tabla por target para hacer todos los calculos en los grupos

        grouped = grouped.groupby('Target')  

        #aca voy a ir agregando las top 10 antennas utilizadas por el user, Si no llego a 10 antennas, relleno con NaNs
        for i in range(0,10):
            #me quedo con la i-esima fila de c/grupo (si no hay fila, no toma en cuenta ese Target)

            buffer_table = grouped.nth(i)[['AntennaID','count']]
            #renombre a iesima AntennaId e iesimo count
            buffer_table.columns=['AntennaID_%i'%i,'count_%i'%i]
            #agrego esta info como nuevas columnas, dejando lo demas como NaNs
            output_table = pd.concat([output_table, buffer_table], axis=1, join_axes=[output_table.index])

        del grouped
        #los primeros AntennaIDs ya no me sirven, idem con el primer
        output_table.drop('AntennaID', axis=1, inplace=True)
        output_table.drop('count', axis=1, inplace=True)

        #para los datos faltantes dentro del Top10, relleno con -1s, que vendrian a ser los NaNs
        output_table.fillna(-1,inplace=True)

        #ojo aca que en el caso que entren hashes entonces no los va a poder convertir
        output_table = output_table.astype(int,copy=False)

        #print(output_table.columns)
        #print("la tabla es:\n") 
        #print(output_table.head(5))
        #print("\n")

        #print(output_table.dytpes)
        #pd.to_numeric(output_table['EXPOSED'])

        #for i in range(3,22):
        #    pd.to_numeric(output_table[output_table.columns[i]]) 
        #print(output_table.dytpes)
        #aca termino guardando el output final pero solo para esos usuarios % pass ==group
        output_table.to_csv(output_file, index = False, 
                       header = False, mode='a',compression='gzip')
    then = now
    seconds = time.time() - then
    print("total running time of script is %d " % seconds)
    
    
if __name__ == "__main__":
    main()