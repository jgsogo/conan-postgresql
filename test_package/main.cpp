
#include <iostream>
#include <libpq-fe.h>

int main()
{
    std::cout << "libpq " << PQlibVersion() << std::endl;
    return 0;
}
