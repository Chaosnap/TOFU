#ifndef LOGGING_H
#define LOGGING_H
#include <iostream>

#define FATAL(msg)                                                                                         \
    do {                                                                                                   \
        std::cerr << "Fatal error in " << __FILE__ << " on line " << __LINE__ << ". " << msg << std::endl; \
        abort();                                                                                           \
    } while (0)

#define CHECK(condition)                           \
    do {                                           \
        if (!(condition)) {                        \
            FATAL("Check failed: " << #condition); \
        }                                          \
    } while (0)

#ifdef DEBUG
#define DCHECK(condition)    CHECK(condition)
#else
#define DCHECK(condition) do {} while(0)
#endif

#define UNREACHABLE()    FATAL("Unreachable");

#define UNIMPLEMENTED()    FATAL("Unimplemented");

#endif //LOGGING_H