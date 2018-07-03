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
};//事件数据结构，内含四个参数，id为事件种类标号，featureNum为特征种类标号数组，featureValue为特征数值数组，两者下标相同的位置存储统一特征。flag为此事件是否是化验事件（是否为标签事件）

map<int, multimap<string, Event> > patientMap;//从病人标号到事件序列的映射表
map<int, int> featureMap;//用于专门记录每个属于labevent的事件标号究竟是normal（0），abnormal（1）还是delta（2）的数据结构，从labevent的事件标号到（0,1,2）的映射表
map<int, int> matchMap;
int tempId[4000];
int labelCount[4000];
int eventCount[4000];
int spanCount[4000];
struct Lab{
	int id;
	int num;
} event[4000];

bool cmp(const Lab & a, const Lab & b){
	return a.num > b.num;
}

string toString(int c){
	string s = "";
	while (c > 0){
		s = (char)((c % 10) + '0') + s;
		c = c / 10;
	}
	while (s.size() < 2) s = '0' + s;
	return s;
}//将数字转化为字符串

string getTime(string time){
	int pos = time.find(" ", 0);
	int pos2 = time.find(":", 0);
	int c = atoi((time.substr(pos + 1, pos2 - pos - 1)).c_str());
	if (c > 12) c -= 12;
	else c = 0;
	string h = toString(c);
	if (c < 10) h = "0" + h;
	return time.substr(0, pos) + " " + h + ":" + time.substr(pos2 + 1, time.size() - pos2 - 1);
}//在将字符串格式的时间向前推12小时，若当天事件不足12点则推到0点，并以字符串格式返回前推后的时间

void getFeature(string s, Event & e){
	if (s == "") return;
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
}//拆解数据中的feature字段并将特征标号和数值分别储存在featureNum和featureValue中

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
}//拆解tsv文件中的字段，提取出事件的标号，特征存储到事件序列映射表中，之后以（病人，事件序列）的二元组形式存入病人到事件序列的映射表中

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
		if (featureMap.find(num) == featureMap.end()) continue;
		if (s.find("labevents", 0) == string::npos) continue;
		if (feature.find("abnormal", 0) != string::npos){
			featureMap[num] = 1;
		} else if (feature.find("delta", 0) != string::npos){
			featureMap[num] = 2;
		}else{
			featureMap[num] = 0;
		}
	}
}//提取feature_info.tsv的内容，将其储存在featureMap中

void match(){
	ifstream f0("feature_info.tsv");
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
		pos = s.find(".", 0);
		pos2 = s.find(",", 0);
		pos2 -= 1;
		pos += 1;
		int countId = atoi((s.substr(pos, pos2 - pos)).c_str());
		//cout<<countId<<endl;
		if (matchMap.find(countId) == matchMap.end()){
			matchMap.insert(make_pair(countId, num));
		}
		tempId[num] = matchMap[countId];
	}
}//原本tsv数据中每种labevent在normal abnromal时各自有一个对应的标号，这里将这两个标号匹配起来

int filter(){
	ifstream f0("labevents.tsv");
	string s;
	int sum = 4000;
	match();
	while (getline(f0, s)){
		s = s.substr(0, s.size() - 1);
		s = s + '\t';
		int pos = s.find("\t", 0);
		string tmp = s.substr(0, pos);
		int num = atoi(tmp.c_str());
		num = tempId[num];
		s.erase(0, pos + 1);
		pos = s.find("\t", 0);
		tmp = s.substr(0, pos);
		int patient = atoi(tmp.c_str());
		s.erase(0, pos + 1);
		pos = s.find("\t", 0);
		string feature = s.substr(0, pos);
		s.erase(0, pos + 1);
		pos = s.find("\t", 0);
		string date = s.substr(0, pos);
		s.erase(0, pos + 1);
		event[num].id = num;
		event[num].num++;
	}
	sort(event, event + sum, cmp);
	for (int i = 0; i < 20; i++){
		featureMap.insert(make_pair(event[i].id, 0));
	}
	for (int i = 0; i < 4000; i++){
		int id = i;
		if (tempId[id] == 0) continue;
		if (featureMap.find(tempId[id]) == featureMap.end()) continue;
		if (tempId[id] == id) continue;
		featureMap.insert(make_pair(id, 0));
	}
}//筛选labevent中出现频率最高的20种作为label

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
	//以上均为将各个类型事件拆解并储存如patientMap中形成医疗事件序列
	filter();
	getApart("feature_info.tsv");//读取featureMap
	ofstream f0("dataSeq.txt");
	map<int, multimap<string, Event> >::iterator i;
	int n = 0;
	for (i = patientMap.begin(); i != patientMap.end(); i++){
		int num = i->first;
		if (patientMap[num].size() < 20) continue;
		n++;
	}
	f0<<n<<endl;
	int maxLength = 0;
	int maxLabel = 0;
	int mmpcount = 0;
	int mmpcnt = 0;
	for (i = patientMap.begin(); i != patientMap.end(); i++){//遍历整个patientMap并输出医疗事件序列
		int num = i->first;
		int countLabel = 0;
		int sum = 0;
		multimap<string, Event>::iterator lastLabel = patientMap[num].begin();
		if (patientMap[num].size() < 20) continue;
		multimap<string, Event>::iterator j;
		//multimap<string, Event>::iterator start = patientMap[num].begin();
		for (j = patientMap[num].begin(); j != patientMap[num].end(); j++){
			Event e = j->second;
			sum++;
			if (sum > 5000) break;
			if (featureMap.find(e.id) != featureMap.end()){
				countLabel++;
				//spanCount[getMinus(j->first, lastLabel->first)]++;
				lastLabel = j;
			}
		}
		sum = 0;
		int Length = patientMap[num].size();
		if (Length > 5000) mmpcount++;
		maxLength = max(maxLength, Length);
		maxLabel = max(maxLabel, countLabel);
		labelCount[countLabel / 100]++;
		eventCount[Length / 100]++;
		Length = min(5000, Length);
		f0<<num<<'\t'<<Length<<'\t'<<countLabel<<endl;
		cout<<num<<endl;
		for (j = patientMap[num].begin(); j != patientMap[num].end(); j++){//遍历事件序列，若长于5000则截断，否则按照格式输出
			string time = j->first;
			Event e = j->second;
			int label = 0;
			if (featureMap.find(e.id) != featureMap.end()){
				label = 1;
				if (sum > 5000) mmpcnt++;
			}
			sum++;
			if (sum > 5000) break;
			//if (sum == 1000) start++;
			//else sum++;
			//if (!(j->second).flag) continue;
			//if (sum < 100) continue;
			//multimap<string, Event>::iterator l;
			//string sttime = getTime(j->first);
			/*int eventsum = 0;
			for (l = start; l != j; l++){
				if (l->first <= sttime){
					eventsum++;
				}else{
					break;
				}
			}
			if (eventsum < 100) continue;
			f0<<num<<'\t'<<eventsum<<endl;*/
			//for (l = start; l != j, eventsum > 0; l++, eventsum--){
				//string time = l->first;
				//Event e = l->second;
			f0<<label<<'\t'<<e.id<<'\t'<<time<<endl;
			if (label == 1) f0<<featureMap[e.id]<<endl;
			f0<<e.featureNum.size()<<endl;
			for (int k = 0; k < e.featureNum.size(); k++){
				f0<<e.featureNum[k]<<'\t'<<e.featureValue[k]<<endl;
			}
			//}
			//f0<<(j->second).id<<' '<<(j->second).featureValue[0]<<' '<<featureMap[(j->second).id]<<endl;
		}
		//f0<<"----------------------------"<<sum<<"---------------------------"<<endl;
	}
	f0<<maxLength<<' '<<maxLabel<<endl;
	/*cout<<mmpcount<<' '<<mmpcnt<<endl;
	ofstream f1("labelDistr.txt"), f2("eventDistr.txt"), f3("spanDistr.txt");
	for (int i = 0; i < 400; i++){
		f1<<i * 100<<' '<<(i + 1) * 100<<' '<<labelCount[i]<<' '<<double(labelCount[i]) / n<<endl;
		f2<<i * 100<<' '<<(i + 1) * 100<<' '<<eventCount[i]<<' '<<double(eventCount[i]) / n<<endl;
	}
	for (int i = 0; i < 400; i++){
		f3<<i * 3<<' '<<(i + 1) * 3<<' '<<spanCount[i]<<endl;
	}*/
}
