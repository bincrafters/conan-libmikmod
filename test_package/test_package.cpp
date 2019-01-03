#include <mikmod.h>
#include <iostream>

int main()
{
    // register all the drivers
    MikMod_RegisterAllDrivers();

    // initialize the library
    if (int err = MikMod_Init("")) {
        std::cerr << "Couldn't initialize sound, reason: " << MikMod_strerror(MikMod_errno) << "\n";
        return err;
    }

    // cleanup
    MikMod_Exit();
}