#include "file_mem_map.h"

#include <sys/stat.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

#include "logging.h"

const char* MapFile(const char* file_name, size_t& length) {
    const int fd = open(file_name, O_RDONLY);
    CHECK(fd != -1);

    struct stat sb;
    CHECK(fstat(fd, &sb) != -1);
    length = sb.st_size;

    const char* addr = static_cast<const char*>(mmap(NULL, length, PROT_READ, MAP_PRIVATE, fd, 0));
    CHECK(addr != MAP_FAILED);
    close(fd);

    return addr;
}