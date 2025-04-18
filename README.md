Pantheon Congestion Control Analysis

Overview
This repository contains scripts and analysis tools for evaluating various congestion control algorithms using the Pantheon framework with MahiMahi network emulation. The project focuses on comparing the performance of different congestion control algorithms (such as TCP Cubic, BBR, and Vivace) under varied network conditions.

Pantheon is a community-driven platform that integrates multiple congestion control algorithms under a single test harness. This project leverages Pantheon's capabilities to provide consistent evaluation of algorithm performance across different network scenarios.

Prerequisites

Ubuntu 20.04 or later
Python 3.8+
Git
MahiMahi network emulator

Installation

1. Clone the repository:

git clone https://github.com/premkiran2/pantheon.git


2. Navigate to the project directory:

cd pantheon/


3. Install all the dependencies

Install the dependencies related to the Pantheon and Mahimahi environments.


4. Running Full Experiments:

To run experiments with all supported congestion control algorithms:

sudo sysctl -w net.ipv4.ip_forward=1

python3 analyse_results.py


5. Output:

Upon running the analysis, the following directories and files will be created:

1. logs - pantheon/logs/ — Raw log files for each run

2. graphs - pantheon/graphs/ — Visual graphs of throughput, latency, and packet loss

3. csv files:

	a. pantheon/results/profile1/ — CSV output files from experiments using Profile 1

	b. pantheon/results/profile2/ — CSV output files from experiments using Profile 2

