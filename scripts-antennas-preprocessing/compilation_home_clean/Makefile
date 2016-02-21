.PHONY: run clean debug

WARNING_OPTIONS = -Wall

LIB = -lboost_iostreams -lboost_filesystem -lboost_system -lboost_program_options
LIB_TEST = $(LIB) -lboost_unit_test_framework

FLAGS = -std=gnu++11 -pthread $(WARNING_OPTIONS)

COMPILE_OPTIONS = $(INC) $(LIB) $(FLAGS)
COMPILE_TEST_OPTIONS = $(INC) $(LIB_TEST) $(FLAGS)
RUN_OPTIONS = -p $(LINK_FILE) -o $(NODE_FILE)

home_clean_mexico: home_clean_mexico.cpp
	g++ -std=c++11  home_clean_mexico.cpp $(COMPILE_OPTIONS) -O3 -o home_clean_mexico

static: home_clean_mexico.cpp
	g++ -std=c++11 home_clean_mexico.cpp $(COMPILE_OPTIONS) -static -O3 -o home_clean_mexico 

debug:  home_clean_mexico.cpp
	g++ -std=c++11  home_clean_mexico.cpp $(COMPILE_OPTIONS) -g -o home_clean_mexico

run: $(NODE_FILE)

$(NODE_FILE): home_clean_mexico 
	./home_clean_mexico $(RUN_OPTIONS)

clean:
	rm -f home_clean_mexico $(NODE_FILE)

