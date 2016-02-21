//este archivo es el que realment mira el dataset de llamados para agregar toda la info y outputear el archivo de llamados por antenna. 
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <set>

using namespace std;

set<int> antennas_GC;
map<int,int> home;

// With work
map<int,int> users_per_antenna;
map<int,int> vuln_users_per_antenna;

map<int,int> calls_per_antenna;
map<int,int> vuln_calls_per_antenna;

set<int> users;
set<int> vuln_users;

//Nowork
map<int,int> users_per_antenna_nowork;
map<int,int> vuln_users_per_antenna_nowork;

map<int,int> calls_per_antenna_nowork;
map<int,int> vuln_calls_per_antenna_nowork;

set<int> users_nowork;
set<int> vuln_users_nowork;

void swap(int &a, int &b){
	int temp = a;
	a = b;
	b = temp;
}

void load_antennas(string src_str){
	//el metodo c_str() transforma strings en char[] que es el datatype que maneja C 
	FILE* source = fopen(src_str.c_str(), "r");
	int surr_id;
	
	//el ==1 del fscanf es para verificar  si pudo leer el archivo bajo el formato que le estamos dando o no (%d\n) donde levanta solo un dato por linea
	while(fscanf(source, "%d\n", &surr_id) == 1){
		antennas_GC.insert(surr_id);
	}
	fclose(source);
}

void load_home(string src_str){
	FILE* source = fopen(src_str.c_str(), "r");
	int id, h;
	//el ==2 es el argumento que dice el tamanyo de la tupla levantada desde el archivo
	while(fscanf(source, "%d|%d\n", &id, &h) == 2){
		home[id] = h;

		// This is a little bit redundant
		vuln_users_per_antenna[h] = 0;
		users_per_antenna[h] = 0;

		calls_per_antenna[h] = 0;
		vuln_calls_per_antenna[h] = 0;
	
	////NO DEBERIA haber un fclose(source); aca?... tal vez deberia haberlo
 	}
	fclose(source);
}


// Function that takes a set and a map of antennas, and bins the elements of the set according to the antenna
// es un contador que cuenta los usuarios totales para cada antena que tengo en la lista antennas_users
void addToCounter(set<int> &user_list, map<int,int> &antennas_users_list){
	for(set<int>::iterator it = user_list.begin(); it != user_list.end(); it++){
		int h = home[*it];
		antennas_users_list[h] = antennas_users_list[h] + 1;
	}
}
bool livesInGC(int u){
	int h = home[u];
///////// PORQUE compara la antenna home del usuario contra el final del set solamente y no compara a ver si pertenece al set? el .end() es un null?
	return (antennas_GC.find(h) != antennas_GC.end());
//por cuestion de sintaxis si no pertenece al conjunto antennas_GC te devuelve el puntero antenna_GC.end()... si esta, te devuelve el value
}

bool laborableHour(int ts){
//ts seria los segundos desde que arranco
	int start_day = 1;	// 0 -> Monday. First dataset day: Tuesday 11/1st/2011
	int hours_per_week = 7*24;

	int h = ts/3600 + start_day*24;
	int hour_of_week = h % hours_per_week;

	int day_of_week = hour_of_week / 24;
	int hour_of_day = hour_of_week % 24;

	// If weekend, return false . 
	if(day_of_week == 5 || day_of_week == 6) return false;

	// Return true iff inside the laborable hours
	return hour_of_day >= 9 && hour_of_day <= 18;
}

int main(int argc, char* argv[]){
	// chequea el buen formato	
	if(argc != 4){
		cerr << "Arguments missing.\n";
		return 0;
	}
	// este toma el parametro para ver entrada o salidas en los datos
	string s = argv[3];
	bool incoming = (s == "in");

	// Load the list of antennas in GC... haria falta crear un archivo de surr_ids para antennas_GC que sea input en argv[1]
	cerr << "Loading the list of GC antennas...";
	load_antennas(argv[1]);
	cerr << " done (size = " << antennas_GC.size() << ").\n";

	// Load the [user -> home] map .... faltaria el programa que crea el archivo del [user-->home] map
	cerr << "Loading the [user -> home] map...";
	load_home(argv[2]);
	cerr << " done (size = " << home.size() << ").\n";

	// Process every call
	cerr << "Processing calls...\n";
	int origin, target, timestamp, duration, antenna_o, antenna_t;
	char direction;
	int qty_lines = 1;
	while(scanf("%d|%d|%c|%d|%d|%d|%d\n", &origin, &target, &direction, &timestamp, &duration, &antenna_o, &antenna_t) == 7){
		// imprime el porcentaje de lineas procesadas hasta el millon.		
		if(qty_lines % 1000000 == 0)	cerr << "Processed " << (qty_lines * 1. /1000000.) << "M lines.\n";
		qty_lines++;

		// Insert all the people that made an outgoing(incoming) call into the set of users
		if((direction  == 'I' && !incoming) || (direction == 'O' && incoming)) continue;
		//////PORQUE HACE ESTE SWAP? Y porque solo en el caso que sea incoming.. tal vez por eso hay muchas mas llamadas entrantes tmb no.		// porque estan cambiadas estas dos columnas en la base de datos. por como esta escrito el codigo futuro que voy a termminar usando necesito que sean todas salientes las llamadas... es un parche rapido. 

		if(incoming){
			swap(origin, target);
			swap(antenna_o, antenna_t);
		}
		//los agrega a la lista de usuarios y sube el contador de llamadas hechas en esa antena
		users.insert(origin);
		calls_per_antenna[antenna_o] = calls_per_antenna[antenna_o] + 1;
		//if(calls_per_antenna[antenna_o] == 1) cerr << "New antenna " << antenna_o << endl;

		// The same only for non laborable hours...se fija si tiene que subir el contador en horario no laboral

		if(!laborableHour(timestamp)){
			users_nowork.insert(origin);
			calls_per_antenna_nowork[antenna_o] = calls_per_antenna_nowork[antenna_o] + 1;
		}

		// If the target lives in GC, the origin user is in the set of users that has communications with GC.
		// If the user communicates with GC, add it to the set of vulnerable users, and add the call
		//sube el contador de llamadas hechas en horario laboral y 
		if(!livesInGC(target)) continue;
		vuln_calls_per_antenna[antenna_o] = vuln_calls_per_antenna[antenna_o] + 1;
		vuln_users.insert(origin);

		// The same only for non laborable hours
		if(!laborableHour(timestamp)){
			vuln_calls_per_antenna_nowork[antenna_o] = vuln_calls_per_antenna_nowork[antenna_o] + 1;
			vuln_users_nowork.insert(origin);
		}

	}
	cerr << "Done processing calls.\n";

	cerr << "Adding all users to counters:\n" << "USERS:\n";
	addToCounter(users,users_per_antenna);
	cerr << "USERS_NOWORK:\n";
	addToCounter(users_nowork, users_per_antenna_nowork);
	cerr << "VULN_USERS\n";
	addToCounter(vuln_users, vuln_users_per_antenna);
	cerr << "VULN_USERS_NOWORK\n";
	addToCounter(vuln_users_nowork, vuln_users_per_antenna_nowork);
	cerr << "...done\n";

	// Output every antenna with its number of vulnerable users
	cerr << "Outputting list of antennas...";
	cout << "antenna|users|vuln_users|calls|vuln_calls|users_nowork|vuln_users_nowork|calls_nowork|vuln_calls_nowork\n";
	for(map<int,int>::iterator it = users_per_antenna.begin(); it != users_per_antenna.end(); it++){
		int antenna = it->first; //idem a pedirle it.first i.e. el primero de la tupla
		int u = it->second; //analogo el segundo de la tupla it.second
		int vuln_u = vuln_users_per_antenna[antenna];
		int c = calls_per_antenna[antenna];
		int vuln_c = vuln_calls_per_antenna[antenna];

		int u_nowork = users_per_antenna_nowork[antenna];
		int vuln_u_nowork = vuln_users_per_antenna_nowork[antenna];
		int c_nowork = calls_per_antenna_nowork[antenna];
		int vuln_c_nowork = vuln_calls_per_antenna_nowork[antenna];

		printf("%d|%d|%d|%d|%d|%d|%d|%d|%d\n", antenna, u, vuln_u, c, vuln_c, u_nowork, vuln_u_nowork, c_nowork, vuln_c_nowork);
	}
	cerr << " done.\n";

}
