// This program picks a home iff there are >5 calls from that place and if the number of calls from that place is at leats 25% larger than the number of calls from any other place.
// I.e. we ask a minimum number of calls and a minimum percentual difference between the first 2 places.

#include <iostream>
#include <fstream>
#include <vector>
#include <map>
#include <algorithm>
#include <string>

using namespace std;

#define f first
#define s second
#define pb push_back
#define mp make_pair
#define forsn(i,s,n) for(int i=(int)(s); i<(int)(n); i++)
#define forn(i,n) forsn(i,0,n)
#define fore(i,n) forn(i,n.size())
#define fori(i,n) for(auto i=n.begin(); i != n.end(); i++)
#define all(n) n.begin(),n.end()
#define rall(n) n.rbegin(),n.rend()

vector<string> split(const string s, char c){
	int ini=0;
	vector<string> res;
	
	while(ini < (int)(s.size())){
		int fin=s.find(c, ini);
		
		if (fin == (int)(string::npos)){
			fin = s.size();
		}
		
		res.push_back(s.substr(ini, fin-ini));
		ini = fin + 1;
	}
	return res;
}

struct line_data{
	// Target(origin) Destination(target) Direction TimeStamp Duration AntennaID
	string origin, target;
	int timestamp, duration, antennaID;
	char direction;
	
	line_data(string s, char c){
		//cerr << s << " '" << c << "'" << endl;
		vector<string> data_s = split(s, c);
		origin = data_s[0];
		target = data_s[1];
		direction = data_s[2][0];
		timestamp = stoi(data_s[3]);
		duration = stoi(data_s[4]);
		antennaID = stoi(data_s[5]);
	}
	
	int getCallHour(){
		return (timestamp/3600)%24;
	}
	bool isNight(){
		int hour = getCallHour();
		return (hour >= 17) || (hour <= 9);
	}
	string antennaUser(){
		return origin;
		// return (direction=='O') ? origin : target;
	}
};

ostream& operator<<(ostream &os, const line_data &l){
	os << "(" << l.origin << ((l.direction=='O')?"->":"<-") << l.target << ") " << l.timestamp << " " << l.duration << " " << l.antennaID;
	return os;
}

// **************** Change manually if necessary *************
// TODO: User parameters
int saturday = 6;
// **************** Change manually if necessary *************

int main (){
	map<string, map<int, int> > user_to_antenna;
	map<string,int> tot_calls;

    	
	printf("user|home\n");
	string line;
	getline(cin, line);	// To get rid of the headers
	long long int qty_lines = 0;
	while(getline(cin, line) && line.size() > 0){
		qty_lines++;		
		line_data data = line_data(line, ' ');
		
		if(!(qty_lines%10000000)){
			fprintf(stderr, "Processed %lldM lines.\n", qty_lines/1000000);
			cerr << data << endl;
		}

		
		//if(!data.isNight()) continue;
		user_to_antenna[data.antennaUser()][data.antennaID]++;
		tot_calls[data.antennaUser()]++;
	}
	
	for(auto &it_user : user_to_antenna){
		cerr << "User " << it_user.first << endl;
		int home = -1;
		if(tot_calls[it_user.first] < 5 || tot_calls[it_user.first] > 400  ) continue;
		
		vector<pair<int,int> > scores;
		for(auto &it_ant : it_user.second){
			scores.pb(mp(it_ant.second, it_ant.first));
		}
		
		sort(scores.begin(), scores.end());
		//if(scores.size()==1 || scores[0].f*0.8 > scores[1].f){
			//home = scores[0].s;
		//}
		home = scores[0].s;
		
		printf("%s|%d\n", it_user.first.c_str(), home);
	}
}
