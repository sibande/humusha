// Auto reloads/compiles Twitter Bootstrap's .less files.
#include <iostream>
#include <unistd.h>
#include <sys/stat.h>
#include <ctime>
#include <cstdlib>

const std::string BOOTSTRAP_DIRECTORY = "zabalaza/static/less/",
	BOOTSTRAP_MAIN = "zabalaza/static/less/bootstrap.less",
	BOOTSTRAP_CSS = "zabalaza/static/css/bootstrap.css";
	
int main()
{
	using namespace std;

	struct tm* modified;
	struct stat file_stats;
	int modified_time, current_time = 0;
	// $ lessc input.less > output.css
	string cmd = "lessc " + BOOTSTRAP_MAIN + " > " + BOOTSTRAP_CSS;
	
	system(cmd.c_str());

	while (true) {
		stat(BOOTSTRAP_DIRECTORY.c_str(), &file_stats);
		modified = gmtime(&(file_stats.st_mtime));
		modified_time = mktime(modified);

		if (current_time == 0) {
			current_time = modified_time;
		}
		if (modified_time > current_time) {
			current_time = modified_time;
			cout << "Recompiling .less files..." << endl;
			system(cmd.c_str());
			cout << "Done." << endl;
		}

		cout << "Polling directory..." << endl;
		sleep(3);
	}

	return 0;
}
