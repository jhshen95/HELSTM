#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>
#include <map>
#include <cstdlib>
#include <string>

using namespace std;

struct Event{
	int id;
	vector<int> featureNum;
	vector<double> featureValue;
	bool flag;
};

map<int, multimap<string, Event> > patientMap;
map<int, int> featureMap;

string toString(int c){
	string s = "";
	while (c > 0){
		s = (char)((c % 10) + '0') + s;
		c = c / 10;
	}
	while (s.size() < 2) s = '0' + s;
	return s;
}

string getTime(string time){
	int pos = time.find(" ", 0);
	int pos2 = time.find(":", 0);
	int c = atoi((time.substr(pos + 1, pos2 - pos - 1)).c_str());
	if (c > 12) c -= 12;
	else c = 0;
	string h = toString(c);
	if (c < 10) h = "0" + h;
	return time.substr(0, pos) + " " + h + ":" + time.substr(pos2 + 1, time.size() - pos2 - 1);
}

void getFeature(string s, Event & e){
	s = s + ' ';
	while (s.find(" ", 0) != string::npos){
		int pos = s.find(" ", 0);
		int p = s.find(":", 0);
		string sa = s.substr(0, p);
		string sb = s.substr(p + 1, pos - p - 1);
		s.erase(0, pos + 1);
		int num = atoi(sa.c_str());
		double value = atof(sb.c_str());
		e.featureNum.push_back(num);
		e.featureValue.push_back(value);	
	}
}

void getExt(string st, bool flag){
	ifstream f0(st.c_str());
	string s;
	while (getline(f0, s)){
		Event e;
		e.flag = flag;
		s = s.substr(0, s.size() - 1);
		s = s + '\t';
		int pos = s.find("\t", 0);
		string tmp = s.substr(0, pos);
		int num = atoi(tmp.c_str());
		s.erase(0, pos + 1);
		pos = s.find("\t", 0);
		tmp = s.substr(0, pos);
		int patient = atoi(tmp.c_str());
		s.erase(0, pos + 1);
		pos = s.find("\t", 0);
                string feature = s.substr(0, pos);
		getFeature(feature, e);
                s.erase(0, pos + 1);
		pos = s.find("\t", 0);
                string date = s.substr(0, pos);
                s.erase(0, pos + 1);
		if (patientMap.find(patient) == patientMap.end()){
			multimap<string, Event> eventMap;
			patientMap.insert(make_pair(patient, eventMap));
		}
		e.id = num;
		patientMap[patient].insert(make_pair(date, e));
	}
}

void getApart(string st){
	ifstream f0(st.c_str());
	string s;
	while (getline(f0, s)){
		s = s.substr(0, s.size() - 1);
		s = s.substr(1, s.size() - 2);
		s = s + ',';
		int pos = s.find(",", 0);
		int pos2 = s.find(":", 0);
		string tmp = s.substr(pos2 + 2, pos - pos2 - 2);
		int num = atoi(tmp.c_str());
		s.erase(0, pos + 2);
		pos = s.find(",", 0);
		s.erase(0, pos + 2);
		pos = s.find(",", 0);
		string feature = s.substr(0, pos);
		s.erase(0, pos + 2);
		if (s.find("labevents", 0) == string::npos) continue;
		if (feature.find("abnormal", 0) != string::npos){
			featureMap.insert(make_pair(num, 1));
		} else if (feature.find("delta", 0) != string::npos){
			featureMap.insert(make_pair(num, 2));
		}else{
			featureMap.insert(make_pair(num, 0));
		}
	}
}

int main(){
	getExt("chartevent_1.tsv", false);
	getExt("chartevent_2.tsv", false);
	getExt("chartevent_3.tsv", false);
	getExt("chartevent_4.tsv", false);
	getExt("chartevent_5.tsv", false);
        getExt("chartevent_6.tsv", false);
        getExt("chartevent_8.tsv", false);
	getExt("chartevent_9.tsv", false);
        getExt("chartevent_10.tsv", false);
        getExt("chartevent_11.tsv", false);
        getExt("chartevent_12.tsv", false);
        getExt("chartevent_13.tsv", false);
        getExt("chartevent_14.tsv", false);
        getExt("admissions.admittime.tsv", false);
        getExt("admissions.deathtime.tsv", false);
	getExt("admissions.dischtime.tsv", false);
        getExt("datetimeevents.tsv", false);
        getExt("icustays.tsv", false);
        getExt("inputevents_cv.tsv", false);
        getExt("inputevents_mv.tsv", false);
        getExt("labevents.tsv", true);
        getExt("outputevents.tsv", false);
        getExt("procedureevents.tsv", false);
	getApart("feature_info.tsv");
	ofstream f0("dataSeq.txt");
	map<int, multimap<string, Event> >::iterator i;
	for (i = patientMap.begin(); i != patientMap.end(); i++){
		int num = i->first;
		int sum = 0;
		multimap<string, Event>::iterator j;
		multimap<string, Event>::iterator start = patientMap[num].begin();
		//f0<<num<<'\t'<<patientMap[num].size()<<endl;
		for (j = patientMap[num].begin(); j != patientMap[num].end(); j++){
			sum++;
			if (sum == 1000) start++;
			else sum++;
			if (!(j->second).flag) continue;
			if (sum < 100) continue;
			multimap<string, Event>::iterator l;
			string sttime = getTime(j->first);
			int eventsum = 0;
			for (l = start; l != j; l++){
				if (l->first <= sttime){
					eventsum++;
				}else{
					break;
				}
			}
			if (eventsum < 100) continue;
			f0<<num<<'\t'<<eventsum<<endl;
			for (l = start; l != j, eventsum > 0; l++, eventsum--){
				string time = l->first;
	                        Event e = l->second;
				f0<<e.id<<'\t'<<time<<endl;
				f0<<e.featureNum.size()<<endl;
				for (int k = 0; k < e.featureNum.size(); k++){
					f0<<e.featureNum[k]<<'\t'<<e.featureValue[k]<<endl;
				}
			}
			f0<<(j->second).id<<' '<<(j->second).featureValue[0]<<' '<<featureMap[(j->second).id]<<endl;
		}
		//f0<<"----------------------------"<<sum<<"---------------------------"<<endl;
	}
	f0<<"0\t0"<<endl;
}
