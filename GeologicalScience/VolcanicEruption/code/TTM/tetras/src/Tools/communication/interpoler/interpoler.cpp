/**
* @author  Mohamed Ben Belgacem <Mohamed.BenBelgacem@gmail.com>
* @version 1.0
* @section LICENSE

* MAPPER communication module
* Copyright (C) 2015  University of Geneva, Switzerland
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.

* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.

* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "../musclemapper.h"
#ifdef USE_PARALLEL_MPI
#include <mpi.h>
#endif




//************************************** TransportInterpolationMapper *********************************
class TransportInterpolationMapper{

public:
    TransportInterpolationMapper(int * argc, char ***argv){
        int rank=0;
        interpoler.reset(new MuscleTransportInterpolation(rank, argc, argv));
    }
    void run(){

        this->interpoler->simulate();
    }
private:
    auto_ptr<TransportInterpolation> interpoler;
};

//---------------------------------------- main () ----------------------------------------------------------
int main( int argc, char **argv ) {

    MpiManager manager;
    manager.init(&argc, &argv);
    if(manager.isMainProcessor()){
        TransportInterpolationMapper interpoler(&argc, &argv);
        interpoler.run();
    }
}
