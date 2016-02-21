/// toma los homes de los surr_ids y una lista antenas | provincias y devuelve la matriz M(i,j) donde en el lugar i,j habla de cuantos 
/// usuarios de la provincia i llamaron a la provincia j. (mira outgoing solamente)

#include <cstdio>
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <set>

using namespace std;

map<int,int> home;
map<int,int> province;

void load_home(string src_str){
	//el metodo c_str() transforma strings en char[] que es el datatype que maneja C 
	FILE* source = fopen(src_str.c_str(), "r");
	int id, h;
	
	while(fscanf(source, "%d|%d\n", &id, &h) == 2){
		home[id] = h;
	}
	fclose(source);
}

void load_provinces(){
	FILE* ant = fopen("data/antenna_to_province.txt", "r");
	int antenna, prov;
	while(fscanf(ant, "%d|%d", &antenna, &prov) == 2){
		province[antenna] = prov;
	}
	fclose(ant);
}

int main(int argc, char* argv[]){
	if(argc != 2){
		cerr << "Arguments missing.\n";
		return 0;
	}
	////PORQUE es que tengo que hace run clear() si home esta inicializado vacio?.... buenas practicas de programacion. hay veces que cuando inicializas una cosa viene con basura y hay que limpiarl. es bueno prevenir.	
	home.clear();
	//... faltaria el programa que crea el archivo del [user-->home] map
	cerr << "Loading the [user -> home] map...";
	load_home(argv[1]);
	cerr << " done (size = " << home.size() << ").\n";
	
	province.clear();
	cerr << "Loading antenna to province map...";
	load_provinces();
	cerr << " done (size = " << province.size() << ").\n";
	
	int qty_prov = 26; //////HABRIA QUE modificar esto para las antenas de...
	//long and long int specifiers have identical type. So are long long and long long int. In both cases, the int is optional.
	//long vs long long is speed vs amount of memory allocated
	long long int calls_between[qty_prov][qty_prov];	// calls_between[a][b] is the number of calls from a user living in 'a' to a user living in 'b'.

	////SIEMPRE hay que inicializar en 0 los objetos nuevos o esto es solo una "buena practica"?
	for(int i=0; i<qty_prov; i++){
		for(int j=0; j<qty_prov; j++){
			calls_between[i][j] = 0;
		}
	}
	
	// Process every call
	cerr << "Processing calls...\n";
	int origin, target, timestamp, duration, antenna_o, antenna_t;
	char d;
	long long int qty_lines = 1;
	long long int out_lines = 1;
	while(scanf("%d|%d|%c|%d|%d|%d|%d\n", &origin, &target, &d, &timestamp, &duration, &antenna_o, &antenna_t) == 7){
		if(qty_lines % 10000000 == 0)	cerr << "Processed " << (qty_lines * 1. /1000000.) << "M lines (" << (out_lines* 1. /1000000.) << "M valid, or " << out_lines*100./qty_lines << "%).\n";
		qty_lines++;
		
		/////PORQUE ignora incoming?....por eso que dijimos en el archivo calls_involving_GC_by_antenna_mexico donde cambiamos ciertas llamdas entrantes como salientes en verdad.
		if(d == 'I') continue;
		out_lines++;
		// Insert every call in the corresponding province intersection:
		calls_between[province[home[origin]]][province[home[target]]]++;
	}
	cerr << "Done processing calls.\n";

	// Output every antenna with its number of vulnerable users
	cerr << "Outputting matrix...";
	for(int o=0; o<qty_prov; o++){
		for(int t=0; t<qty_prov; t++){
			if(t>0){
				cout << "|";
			}
			cout << calls_between[o][t];
		}
		cout << endl;
	}
	cerr << " done.\n";
	cerr << "---------------------------------------------------------------------\n";
	cerr << "Run data:\nTotal calls: " << qty_lines << "\nTotal outgoing calls: " << out_lines << "\nPercentage: " << out_lines*100./qty_lines << endl;
	cerr << "---------------------------------------------------------------------\n";
	
}
