#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <openssl/sha.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

static const char magicHash[] =
    "6767676767676767676767676767676767676767676767676767676767676767"
    "6767676767676767676767676767676767676767676767676767676767676767";

static void bytesToHex(const unsigned char *inputBytes, size_t inputLen, char *outputHex) {
    static const char hexTable[] = "0123456789abcdef";
    size_t byteIndex;

    for (byteIndex = 0; byteIndex < inputLen; byteIndex++) {
        outputHex[byteIndex * 2] = hexTable[(inputBytes[byteIndex] >> 4) & 0x0f];
        outputHex[byteIndex * 2 + 1] = hexTable[inputBytes[byteIndex] & 0x0f];
    }

    outputHex[inputLen * 2] = '\0';
}

__attribute__((noreturn))
void printFlag(void) {
    int flagFd;
    char flagBuffer[256];
    ssize_t flagLen;

    flagFd = open("/root/Flags/flag1", O_RDONLY);
    if (flagFd < 0) {
        printf("open failed for /root/Flags/flag1: %s\n", strerror(errno));
        _exit(1);
    }

    flagLen = read(flagFd, flagBuffer, sizeof(flagBuffer) - 1);
    if (flagLen < 0) {
        printf("read failed: %s\n", strerror(errno));
        close(flagFd);
        _exit(1);
    }

    close(flagFd);

    if (flagLen == 0) {
        puts("flag file is empty");
        _exit(1);
    }

    flagBuffer[flagLen] = '\0';

    puts("MAGIC ACCEPTED");
    puts(flagBuffer);

    _exit(0);
}

__attribute__((noinline))
static size_t readUpload(unsigned char *safeBuffer) {
    char fileBuffer[64];
    size_t fileLen;
    size_t copyLen;

    puts("Send raw file bytes now, then close your write side.");

    fileLen = fread(fileBuffer, 1, 256, stdin);
    if (ferror(stdin)) {
        return 0;
    }

    copyLen = fileLen;
    if (copyLen > sizeof(fileBuffer)) {
        copyLen = sizeof(fileBuffer);
    }

    memcpy(safeBuffer, fileBuffer, copyLen);

    return copyLen;
}

static void handleClient(void) {
    unsigned char safeBuffer[64];
    unsigned char digestBytes[SHA512_DIGEST_LENGTH];
    char digestHex[SHA512_DIGEST_LENGTH * 2 + 1];
    size_t safeLen;

    safeLen = readUpload(safeBuffer);
    if (safeLen == 0) {
        puts("No bytes received.");
        return;
    }

    SHA512(safeBuffer, safeLen, digestBytes);
    bytesToHex(digestBytes, sizeof(digestBytes), digestHex);

    if (memcmp(digestHex, magicHash, sizeof(magicHash) - 1) == 0) {
        printFlag();
    }

    puts("Nope, not the sacred 67-hash.");
}

static void setupChildIo(int clientFd) {
    dup2(clientFd, STDIN_FILENO);
    dup2(clientFd, STDOUT_FILENO);
    dup2(clientFd, STDERR_FILENO);
    close(clientFd);

    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

static int createServerSocket(uint16_t portNumber) {
    int serverFd;
    int enableReuse;
    struct sockaddr_in serverAddr;

    serverFd = socket(AF_INET, SOCK_STREAM, 0);
    if (serverFd < 0) {
        perror("socket");
        exit(1);
    }

    enableReuse = 1;
    if (setsockopt(serverFd, SOL_SOCKET, SO_REUSEADDR, &enableReuse, sizeof(enableReuse)) < 0) {
        perror("setsockopt");
        close(serverFd);
        exit(1);
    }

    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    serverAddr.sin_port = htons(portNumber);

    if (bind(serverFd, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) < 0) {
        perror("bind");
        close(serverFd);
        exit(1);
    }

    if (listen(serverFd, 32) < 0) {
        perror("listen");
        close(serverFd);
        exit(1);
    }

    return serverFd;
}

static void runServer(uint16_t portNumber) {
    int serverFd;
    int clientFd;

    serverFd = createServerSocket(portNumber);

    for (;;) {
        pid_t childPid;

        clientFd = accept(serverFd, NULL, NULL);
        if (clientFd < 0) {
            if (errno == EINTR) {
                continue;
            }

            perror("accept");
            continue;
        }

        childPid = fork();
        if (childPid < 0) {
            perror("fork");
            close(clientFd);
            continue;
        }

        if (childPid == 0) {
            close(serverFd);
            setupChildIo(clientFd);
            alarm(15);

            puts("=== Magic Hash Oracle ===");
            puts("We seek the blessed SHA-512:");
            puts(magicHash);
            puts("Only raw bytes are accepted.");

            handleClient();
            _exit(0);
        }

        close(clientFd);
    }
}

int main(int argc, char **argv) {
    uint16_t portNumber;

    signal(SIGCHLD, SIG_IGN);
    signal(SIGPIPE, SIG_IGN);

    portNumber = 31337;
    if (argc > 1) {
        int parsedPort;

        parsedPort = atoi(argv[1]);
        if (parsedPort <= 0 || parsedPort > 65535) {
            fprintf(stderr, "usage: %s [port]\n", argv[0]);
            return 1;
        }

        portNumber = (uint16_t)parsedPort;
    }

    runServer(portNumber);
    return 0;
}
