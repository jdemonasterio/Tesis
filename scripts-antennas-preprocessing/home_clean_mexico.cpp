// This program picks a home only for users of the telco (first row in simple_format files). The home criteria is as follows: iff the most frequent antenna for which there are >5 calls from that place. Certain criteria can be established such as night time and if the number of calls from that place is at leats 20% larger than the number of calls from any other place. 
#include "boost/algorithm/string.hpp"
#include "boost/filesystem/fstream.hpp"
#include "boost/iostreams/filter/gzip.hpp"
#include "boost/iostreams/filtering_stream.hpp"
#include "boost/program_options.hpp"

namespace bpo = boost::program_options;

#include <iostream>
#include <fstream>
#include <vector>
#include <map>
#include <algorithm>
#include <string>

using namespace std;

#define f first
#define s second
//#define pb push_back
//#define mp make_pair
#define forsn(i,s,n) for(int i=(int)(s); i<(int)(n); i++)
#define forn(i,n) forsn(i,0,n)
#define fore(i,n) forn(i,n.size())
#define fori(i,n) for(auto i=n.begin(); i != n.end(); i++)
#define all(n) n.begin(),n.end()
#define rall(n) n.rbegin(),n.rend()

//hace un split del string en donde este el char c... podria fallar?? en el script original esta "' '" en vez de "c" en el cuerpo de la funcion 

vector<string> split(const string s, char c){
	int ini=0;
	vector<string> res;
	//salta los espacios al principio
	while(ini < (int)(s.size()) && s[ini]==' ') ini++;
	
	int fin=ini;
	while(fin < (int)(s.size())){
		//poner “int foobar” es lo mismo que “(int)(foobar)”, declara el tipo. pero a veces ayuda a que no se queje el 
//compilador		
		//aca va haciendo cortes en los char que sean igual a char c y guardando en res con .push_back
		if(s[fin]== c ){
			res.push_back(s.substr(ini, fin-ini));
			fin++;
			ini=fin;
		}
		fin++;
	}
//para agarrar el ultimo corte del final
	if(fin>ini) res.push_back(s.substr(ini, fin-ini));
	
	return res;
}


void load_antennas(string src_str,  map<int,int> &antenna_list){
        //el metodo c_str() transforma strings en char[] que es el datatype que maneja C
	// std::ifstream antennalist_file(antennalist_path);
	int antenna_id,epidemic;
	float latitude,longitude;
	std::string state;
	FILE* source = fopen(src_str.c_str(), "r");
	//el ==2 es el argumento que dice el tamanyo de la tupla levantada desde el archivo
	while(fscanf(source, "%d|%f|%f|%s|%d\n", &antenna_id, &latitude , &longitude ,&state , &epidemic) == 2){
       		antenna_list[antenna_id] = epidemic;
        }
        fclose(source);
}


//crea esta "clase" o estructura para leer lineas
struct line_data{
	// observar que la columna target son los usuarios de la telco.. destination son los demas. y la direction es relativa al target(in or out).
	// Target Destination Direction TimeStamp Duration AntennaID
	int origin, target, timestamp, duration, antennaID;
	char direction;
	
	line_data(string s, char c){
		//cerr << s << " '" << c << "'" << endl;
		vector<string> data_s = split(s, c);
		//stoi seria un metodo string_to_int
		// obs. el antennaID va atado al user que es de la telca. lo mismo si es entrante significa entrando el llamado al userTelco y saliente es que parte desde userTelco hacia cualquier otro (el otro tmb podria ser de la Telco eventualmente).	
		origin = stoi(data_s[0]);
		target = stoi(data_s[1]);
		//el [0] es del primer caracter del string "I" u "O"
		direction = data_s[2][0];
		timestamp = stoi(data_s[3]);
		duration = stoi(data_s[4]);
		antennaID = stoi(data_s[5]);
	}
	//estos son los metodos de la estructura.
	int getCallHour(){
		//notar que el tiempo 0 arranca el 01/01/2012 a la medianocha..
		return (timestamp/3600)%24;
//obs. la division entera 5/4 da 1 con lo cual el .25 desaparece. en el caso de las horas /3600 elimina todos los segundos excedentes por lo cual despues decir getCallHour()<=9 es en verdad decir que la hora 9.99 (con .99 los segundos excedentes) devuelve True . NO pasa lo mismo con >= 
	}
	bool isNight(){
		//definimos esta franja laboral
		int hour = getCallHour();
		return (hour >= 18) || (hour <= 7);
	}

	std::string getCallDay(){
	//notar que el tiempo 0 de los timestamps arranca el 01/01/2012 un domingo..
		int day_number =  timestamp/(3600*24) %7;
		std::string day;
		switch ( day_number ) {
			case 0:
			    day = "Sunday";
			  break;
			  case 1:            // Note the colon, not a semicolon
			    day = "Monday";
			    break;
			  case 2:            // Note the colon, not a semicolon
			    day = "Tuesday";
			    break;
			 case 3:
			    day = "Wednesday";
			  case 4:            // Note the colon, not a semicolon
			    day = "Thursday";
			    break;
			  case 5:            // Note the colon, not a semicolon
			    day = "Friday";
			    break;
			   case 6:            // Note the colon, not a semicolon
			    day = "Saturday";
			    break;
		}
		return day;
	}			    

	bool isWeekend(){
	
		std::string day  = getCallDay();
		return (day == "Sunday") || (day == "Saturday");
	}


	int antennaUser(){
		//como sabemos que los users de la telco son todos los de la primer columna. Tambien sucede que la antenna solo taggea a los usuarios de la primer columna.
		return origin;
		// return (direction=='O') ? origin : target;
	}
};

//la impresion de cada linea.
ostream& operator<<(ostream &os, const line_data &l){
	os << "(" << l.origin << ((l.direction=='O')?"->":"<-") << l.target << ") " << l.timestamp << " " << l.duration << " " << l.antennaID;
	return os;
}

// **************** Change manually if necessary *************
// TODO: User parameters
int saturday = 6;
// **************** Change manually if necessary *************

int main (int argc, char *argv[] ){
	std::ios_base::sync_with_stdio(true);

        bool help = false;
	bool night_time = false;
	bool week_end = false;
        std::string input_path = "";
        std::string output_path = "";
	std::string antennalist_path = "";

        bpo::options_description aggOptions("userData: Summarizes the nodes of a sum_links file");
        aggOptions.add_options()
 
                ("input_path,p", bpo::value<std::string>(&input_path), "Input file path. If this option isn't specified, the program will use standard input.")
                ("output_path, o", bpo::value<std::string>(&output_path), "Output for compressed sum_nodes file.")
                ("help,h", bpo::bool_switch(&help), "Show usage.")
 		("antennalist, l", bpo::value<std::string>(&antennalist_path), "List of antennas to epidemic mapping-->(INT, BOOL).")
		 ("night_time, n", bpo::bool_switch(&night_time)->default_value(false), "Night filter on CDR'S timestamp. Default is false")
               ("week_end, w",     bpo::bool_switch(&week_end)->default_value(false), "Week end filter on CDR'S timestamp. Default is false")
 
		;

        bpo::variables_map options;
        bpo::store(bpo::parse_command_line(argc, argv, aggOptions), options);
        bpo::notify(options);

        if (help | antennalist_path =="")
        {
                aggOptions.print(std::cout);
                return 1;
	}

	//bio::filtering_istream in;
        //bio::filtering_ostream out;
//        if (input_path == "")
//                in.push(std::cin);
//        else
//        {
 //               bfs::ifstream input_file(input_path, std::ios_base::in | std::ios_base::binary);
//                in.push(bio::gzip_decompressor());
//                in.push(input_file);
//        }
//
//        if (output_path == "")
//                out.push(std::cout);
//       else
//        {
//                bfs::ofstream output_file(output_path, std::ios_base::out | std::ios_base::binary);
//                out.push(bio::gzip_compressor());
//                out.push(output_file);
//        }


	 if (!input_path.empty())
                std::cin.rdbuf(std::ifstream(input_path).rdbuf());

        if (!output_path.empty())
//                std::cout.rdbuf(std::ifstream(output_path).rdbuf());

        std::string line;
	map<int,int> antenna_list;
         // Load the list of antennas in GC... haria falta crear un archivo de surr_ids para antennas_GC que sea input en argv[1] 
        cerr << "Loading the list of GC antennas..."; 
        load_antennas(antennalist_path, antenna_list); 
        cerr << " done (size = " << antenna_list.size() << ").\n"; 
 
        // Load the [user -> home] map .... faltaria el programa que crea el archivo del [user-->home] map 
        //cerr << "Loading the [user -> home] map..."; 
        //load_home(argv[2]); 
        //cerr << " done (size = " << home.size() << ").\n"; 


	//map de [user,home]
	map<int, map<int, int> > user_to_antenna;
	map<int,int> tot_calls;
	std:string line;	
    	
	printf("user|home|epidemic\n");

	// cin y getline son funciones del std library 
	//getline(cin, line);	// To get rid of the headers of the data file

	int qty_lines = 0;
	while(getline(cin, line) && line.size() > 0){
		//basicamente chequeo que no sea un header (los archivos vienen todos con nros..), sino paso.
		if( !isdigit(line[0])  ) continue;
		qty_lines++;
		//cada 2M de lineas de database entro en el if
		//en stderr guardo el output stream.
		if(!(qty_lines%7000000)) fprintf(stderr, "Processed %dM lines.\n", qty_lines/1000000);
		
		//para cada linea crea el objeto line_data y leo separado en espacios.
		line_data data = line_data(line, ' ');
		
		//solo observa los llamados hechos de noche o los llamados de fin de semana
		if( (night_time && !data.isNight() ) || (week_end && !data.isWeekend()) ) continue;

		//para cada linea, tomo el ID de origin de ese call y le sumo un lugar para esa antennaID...
		user_to_antenna[data.antennaUser()][data.antennaID]++;
		//le sumo una llamada mas al tipo antennaUser..
		tot_calls[data.antennaUser()]++;
	}
	//recorro la lista de map<int, map<int, int> > user_to_antenna  para encontrar el home
	int special_users[10] ={1,3,16,37,43,58,75,87,95,99};
	size_t special_users_size = sizeof(special_users) / sizeof(int);
	int *end = special_users + special_users_size;

	for(auto &it_user : user_to_antenna){
		//arme un print especial para ver si puedo debuggear algo..
		//seteo todos  los home en la antena -1
		
		int home = -1;
		//si tiene menos de 5 llamados o mas de 400 realizados en el dataset lo ignoro.. notar que en it_user.first guardo los usuarios
//y en it_user.second guardo el map<int,int> de <antenna: count>
		
		//este test_belonging seria basciamente para ver que sucede en esos casos de special_users y asi poder empezara debuggear
		int *test_belonging = std::find(special_users, end, it_user.first);
		//if (test_belonging != end) {
		//	 fprintf(stderr," tot_calls=%d, user=%d, antennas used =%d, \t",
		//	tot_calls[it_user.first],it_user.first,it_user.second.size())  ;}

		//no miro los casos patologicos con muchos/pocos llamados mensuales
		if(tot_calls[it_user.first] < 5 || tot_calls[it_user.first] > 400 ) continue;
		
		//p/c/user crea el vector de duplas (count,atenna) , notar el orden lexicografico!!
		vector<pair<int,int> > scores;
		
		//para cada usuario ahora va recorriendo todas las antenas que uso que estan en it_user.second
		
		for(auto &it_ant : it_user.second){
			//push_back va escribiendo en scores y make_pair crea la dupla para agregar la dupla (count,antenna)
			//el orden de la tupla esta dado porque luego el sort va ordenar el vector de duplas con orden lexicografico 			
			scores.push_back(make_pair(it_ant.second, it_ant.first));
		
		//	if(test_belonging != end) fprintf(stderr," antenna=%d, count=%d, \t",it_ant.first ,it_ant.second)  ;

		}
		//ordena en forma ascendente.. notar que scores.end() no es teoricamente el ultimo elemento sino lo que hay "despues"
		sort(scores.begin(), scores.end());
		//se fija que en caso que haya mas de 2 antenas posibles como home, que la primera le gane por 0.8 a la segunda	
		//if(scores.size()==1 || scores[0].first/1.19 > scores[1].first){		
		//if(scores.size()==1 ){
		//	home = scores.back().second;
		//}
		home = scores.back().second; //le pido el ultimo elemento que seria el de mas grande count..
		
		//if(test_belonging != end) fprintf(stderr,", home=%d \n",home)  ;
		
		
		//devolver el [user-->antenna,epidemic] map como texto
		printf("%d|%d|%d\n", it_user.first, home,antenna_list[home]);
	}
}
