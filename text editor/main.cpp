#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>

int writeInFile(const std::string &fileName, std::fstream &file, const std::string &contents) {
	file.close();

	file.open(fileName, std::ios::out | std::ios::trunc);
	if (!file) return 1;
	file << contents;
	file.close();

	file.open(fileName, std::ios::in | std::ios::out | std::ios::app);
	if (!file) return 1;

	return 0;
}

bool quit(std::fstream& file, const std::string &contents) {
	file.clear();
	file.seekg(0);

	std::stringstream bufferStream;
	bufferStream << file.rdbuf();
	return contents == bufferStream.str();
}

uint64_t countLines(const std::string& contents) {

	uint64_t count = 1;
	for (const auto& element : contents) {
		if (element == '\n')
			count++;
	}

	return count;
}

bool parseRange(const std::string& command, uint64_t range[3]) {
	std::string numbers[2];
	bool isCommaPresent = false;

	for (size_t i = 0; i < command.size(); i++) {
		if (command[i] == ',') {
			if (isCommaPresent == true) {
				return false;
			}
			else {
				isCommaPresent = true;
				continue;
			}
		}

		if (!isdigit(command[i])) {
			return false;
		}

		if (!isCommaPresent)
			numbers[0].push_back(command[i]);
		else
			numbers[1].push_back(command[i]);
	}

	if (isCommaPresent)
		range[2] = 1;

	for (int i = 0; i < 2; i++) {
		if (!numbers[i].empty()) {
			if (numbers[i][0] == '0') {
				return false;
			}
			if (numbers[i].size() > 19){
				return false;
			}
			range[i] = stoull(numbers[i]);
		}
	}

	if (range[1] != 0 && range[0] > range[1]) {
		return false;
	}

	//std::cout << range[0] << " " << range[1] << " " << range[2] << std::endl;

	return true;
}

void append(std::string &contents, const uint64_t &lineToAppendINT, const std::string &strToAppend) {
	uint64_t linesInFileCount = countLines(contents);

	if (lineToAppendINT == 0) {
		contents.append(strToAppend);
	}
	else {
		if (linesInFileCount < lineToAppendINT) {
			for (size_t i = 0; i <= lineToAppendINT - linesInFileCount; i++)
				contents.push_back('\n');
			contents.append(strToAppend);
		}
		else if (lineToAppendINT == linesInFileCount) {
			contents.push_back('\n');
			contents.append(strToAppend);
		}
		else {
			uint64_t curLineN = 1;
			uint64_t i = 0;
			for (; i < contents.size(); i++) {
				if (contents[i] == '\n') {
					curLineN++;
					if (curLineN - 1 == lineToAppendINT) {
						break;
					}
				}
			}
			contents.insert(i + 1, strToAppend);
		}
	}
}

std::string readFromConsole() {
	std::string strToAppend;

	std::string curLine;
	std::getline(std::cin, curLine);
	while (curLine != ".") {
		strToAppend.append(curLine);
		strToAppend.push_back('\n');
		std::getline(std::cin, curLine);
	}

	return strToAppend;
}

bool convertStrToNumber(const std::string &string, uint64_t &number) {
	std::string numberSTR;

	for (size_t i = 0; i < string.size(); i++) {
		if (!isdigit(string[i]))
			return false;
		numberSTR.push_back(string[i]);
	}
	if (numberSTR[0] == '0' || numberSTR.size() > 19)
		return false;

	number = stoull(numberSTR);

	return true;
}

std::string getLineFromOneliner(const std::string &command, int startingWord) {
	int wordCount = 0;
	std::string curWord;

	size_t i = 0;
	for (; i < command.length(); i++) {
		if (command[i] == ' ') {
			if (!curWord.empty()) {
				wordCount++;
				if (wordCount + 1 == startingWord)
					break;
				curWord.clear();
			}
		}
		else {
			curWord.push_back(command[i]);
		}
	}

	while (command[i] == ' ')
		i++;

	std::string result;
	for (; i < command.size(); i++) {
		result.push_back(command[i]);
	}

	result.push_back('\n');

	return result;

}

bool commandAppend(std::string& contents, const std::vector<std::string>& parsedCommand, const std::string& command) {
	uint64_t lineToAppendINT = 0;
	std::string strToAppend;

	if (parsedCommand.size() == 1) {	// * a
		strToAppend = readFromConsole();
	}
	else {
		if (!convertStrToNumber(parsedCommand[1], lineToAppendINT)) {	// * a abc
			strToAppend = getLineFromOneliner(command, 2); //(починаючи з другого слова включно)
		}
		else {
			if (parsedCommand.size() == 2) {	// * a 12
				strToAppend = readFromConsole();
			}
			else { //if size is bigger than 2	// * a 12 abc
				strToAppend = getLineFromOneliner(command, 3);
			}
		}
	}

	append(contents, lineToAppendINT, strToAppend);

	return true;
}


void deleteLines(const uint64_t range[3], std::string &contents) {
	std::string copy;
	if (range[0] == 0 && range[1] == 0 && range[2] == 1) { // [,]
		copy.clear();
	}
	else if (range[0] > 0 && range[1] > 0 && range[2] == 1) { // [1,10] [3,3]
		uint64_t curLine = 1;
		for (uint64_t i = 0; i < contents.size(); i++) {
			if (curLine < range[0] || curLine > range[1])
				copy.push_back(contents[i]);

			if (contents[i] == '\n')
				curLine++;
		}
	}
	else if (range[0] > 0 && range[1] == 0 && range[2] == 1) { // [1,]
		uint64_t curLine = 1;
		for (uint64_t i = 0; i < contents.size(); i++) {
			if (curLine < range[0])
				copy.push_back(contents[i]);

			if (contents[i] == '\n')
				curLine++;
		}
	}
	else if (range[0] == 0 && range[1] > 0 && range[2] == 1) { // [,10]
		uint64_t curLine = 1;
		for (uint64_t i = 0; i < contents.size(); i++) {
			if (curLine > range[1])
				copy.push_back(contents[i]);

			if (contents[i] == '\n')
				curLine++;
		}
	}
	else if (range[0] > 0 && range[1] == 0 && range[2] == 0) { // [1]
		uint64_t curLine = 1;
		for (uint64_t i = 0; i < contents.size(); i++) {
			if (curLine != range[0])
				copy.push_back(contents[i]);

			if (contents[i] == '\n')
				curLine++;
		}
	}
	//uint64_t linesInFileCount = countLines(contents);
	//if (range[1] == linesInFileCount || range[0] == linesInFileCount ||  // delete last line if the previous line end with \n
	//	(range[0] > 0 && range[1] == 0 && range[2] == 1 && range[0] <= linesInFileCount)) {	// 1,
	//	if (copy.ends_with('\n'))
	//		copy.pop_back();
	//}
	contents = copy;
}


void commandDelete(std::string &contents, const std::vector<std::string> &parsedCommand) {

	if (parsedCommand.size() > 2) {
		std::cout << "Unsupported command" << std::endl;
		return;
	}

	if (parsedCommand.size() == 1) {
		contents.clear();
	}
	else {
		uint64_t range[3] = { 0 };
		if (!parseRange(parsedCommand[1], range)) {
			std::cout << "Invalid range" << std::endl;
			return;
		}
		else {
			deleteLines(range, contents);
		}
	}
}

void print(const std::string& contents, const std::vector<std::string> &parsedCommand) {
	if (parsedCommand.size() > 2) {
		std::cout << "Unsupported command" << std::endl;
		return;
	}
	if (parsedCommand.size() == 1) {
		std::cout << contents;
	}
	else if (parsedCommand.size() == 2) {

		uint64_t range[3] = { 0 };
		if (!parseRange(parsedCommand[1], range)) {
			std::cout << "Invalid range" << std::endl;
			return;
		}
		else {
			if (range[0] == 0 && range[1] == 0 && range[2] == 1) { // [,]
				std::cout << contents;
			}
			else if (range[0] > 0 && range[1] > 0 && range[2] == 1) { // [1,10] [3,3]
				uint64_t curLine = 1;
				for (uint64_t i = 0; i < contents.size() && curLine <= range[1]; i++) {
					if (curLine >= range[0] && curLine <= range[1])
						std::cout << contents[i];

					if (contents[i] == '\n')
						curLine++;
				}
			}
			else if (range[0] > 0 && range[1] == 0 && range[2] == 1) { // [1,]
				uint64_t curLine = 1;
				for (uint64_t i = 0; i < contents.size(); i++) {
					if (curLine >= range[0])
						std::cout << contents[i];

					if (contents[i] == '\n')
						curLine++;
				}
			}
			else if (range[0] == 0 && range[1] > 0 && range[2] == 1) { // [,10]
				uint64_t curLine = 1;
				for (uint64_t i = 0; i < contents.size() && curLine <= range[1]; i++) {
					std::cout << contents[i];

					if (contents[i] == '\n')
						curLine++;
				}
			}
			else if (range[0] > 0 && range[1] == 0 && range[2] == 0) { // [1]
				uint64_t curLine = 1;
				for (uint64_t i = 0; i < contents.size() && curLine <= range[0]; i++) {
					if (curLine == range[0])
						std::cout << contents[i];

					if (contents[i] == '\n')
						curLine++;
				}
			}
		}
	}
}

void change(std::string& contents, const std::vector<std::string>& parsedCommand, const std::string& command) {
	if (parsedCommand.size() == 1) {
		contents.clear();
		contents.append(readFromConsole());
	}

	else if (parsedCommand.size() >= 2) {
		uint64_t range[3] = { 0 };
		if (!parseRange(parsedCommand[1], range)) {
			contents.clear();
			contents.append(getLineFromOneliner(command, 2));
		}
		else {
			std::string strToAppend;

			if (parsedCommand.size() == 2) {
				strToAppend = readFromConsole();
			}
			else {
				strToAppend = getLineFromOneliner(command, 3);
			}


			deleteLines(range, contents);
			if (range[0] == 1 || range[1] == 1) {
				contents.insert(0, strToAppend);
			}
			else if (range[0] == 0 && range[1] == 0 && range[2] == 1) { // [,]
				contents.append(strToAppend);
			}
			else if (range[0] > 0 && range[1] > 0 && range[2] == 1) { // [2,10] [3,3]
				append(contents, range[0] - 1, strToAppend);
			}
			else if (range[0] > 0 && range[1] == 0 && range[2] == 1) { // [2,]
				append(contents, range[0] - 1, strToAppend);
			}
			else if (range[0] == 0 && range[1] > 0 && range[2] == 1) { // [,10]
				contents.insert(0, strToAppend);
			}
			else if (range[0] > 0 && range[1] == 0 && range[2] == 0) { // [2]
				append(contents, range[0] - 1, strToAppend);
			}
		}
	}


}

std::vector<std::string> parseCommand(std::string command) {
	std::vector<std::string> words;
	std::string curWord;

	for (size_t i = 0; i < command.length(); i++) {
		if (command[i] == ' ') {
			if (!curWord.empty()) {
				words.push_back(curWord);
				curWord.clear();
			}
		}
		else {
			curWord.push_back(command[i]);
		}
	}

	if (!curWord.empty())
		words.push_back(curWord);

	//for (auto element : words)
	//	std::cout << element << ":" << element.size() << std::endl;


	return words;
}

int main(int argc, char* argv[])
{

	if (argc != 2)
		return 1;
	

	std::string fileName = argv[1]; //argv[1]
	std::fstream file;

	file.open(fileName, std::ios::in | std::ios::out | std::ios::app);
	if (!file) {
		return 2;
	}

	std::stringstream bufferStream;
	bufferStream << file.rdbuf();
	std::string contents = bufferStream.str();
	std::string command;

	while (true) {
		std::cout << "* ";
		std::getline(std::cin, command);
		std::vector<std::string> parsedCommand = parseCommand(command);

		if (parsedCommand.size() == 0) {
			std::cout << "Unsupported command" << std::endl;
			continue;
		}

		if (parsedCommand[0] == "w" && parsedCommand.size() == 1) {
			if (writeInFile(fileName, file, contents))
				return 2;
		}
		else if (parsedCommand[0] == "q" && parsedCommand.size() == 1) {
			if (quit(file, contents))
				break;
			else
				std::cout << "You have unsaved changes" << std::endl;
		}
		else if (parsedCommand[0] == "p") {
			print(contents, parsedCommand);
		}
		else if (parsedCommand[0] == "a") {
			if (!commandAppend(contents, parsedCommand, command))
				std::cout << "Unsupported command" << std::endl;
		}
		else if (parsedCommand[0] == "d") {
			commandDelete(contents, parsedCommand);
		}
		else if (parsedCommand[0] == "c") {
			change(contents, parsedCommand, command);
		}
		else if (parsedCommand[0] == "!q" && parsedCommand.size() == 1) {
			break;
		}
		else {
			std::cout << "Unsupported command" << std::endl;
		}
	}

	if (file.is_open())
		file.close();

	return 0;
}
