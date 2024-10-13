# Build Instructions

This project involves compiling the `mbedTls` library with custom LLVM passes and the `musl` toolchain for sandboxing.

## Prerequisites

Ensure the following are installed:

- LLVM 12
- Clang 12
- Python 3.8
- `musl` toolchain

# In-Kernel Per-Process Sandbox

## Overview
This project is part of the E0-256 (Autumn 2024) course at IISc Bangalore. The goal of this project is to implement an in-kernel, per-process sandbox that enforces a statically-extracted policy of acceptable library calls. This sandbox aims to prevent unauthorized library calls within a process by monitoring and enforcing a pre-defined policy using a Linux kernel module.

## Features
- **Library Call Policy Extraction**: Analyzes C source programs and generates a policy of acceptable library calls.
- **Kernel-Level Enforcement**: Implements an in-kernel enforcement engine to monitor and restrict the execution of unauthorized library calls.
- **Dummy System Call Insertion**: Automatically instruments the C code with dummy system calls to enforce the extracted policy.
- **Visualization**: Outputs library call graphs compatible with Graphviz for visual representation.

## Project Components
1. **Library Call Policy Extraction**:
   - Extracts the control flow of library calls from a C source program.
   - Builds a finite automaton (library call graph) representing the sequence of valid library calls.
   - Instrumentation of the LLVM IR to insert dummy system calls before each library call.

2. **Kernel-Level Enforcement**:
   - Monitors the execution of processes and enforces the extracted library call policy using dummy system calls.
   - Implemented using eBPF or seccomp within the Linux kernel.

## Requirements
- **LLVM Toolchain**: Used for analyzing source code and modifying the IR.
- **Graphviz**: Used to visualize the library call graphs.
- **Linux Kernel 6.x**: Required for building and testing the in-kernel sandbox.
- **mbedTLS**: Used as a benchmark to evaluate the performance of the sandbox.

## Installation

1. **Clone the repository**:
   Download and navigate to the repository on your local machine.

2. **Install Dependencies**:
   Ensure that you have installed all necessary dependencies, including the LLVM toolchain and Graphviz.

3. **Build the Project**:
   Follow the steps outlined to build the project, including compiling any LLVM passes and preparing the environment for inserting dummy system calls.

4. **Build and Compile Linux Kernel**:
   Use the official documentation to build and compile the Linux kernel with the custom modules required for this project.

# In-Kernel Per-Process Sandbox

## How to Build and Run
==============================

Step 1: Compile LLVM Passes
----------------------------
Navigate to the `llvm-passes` directory and run the following command:

    make


Step 2: Compile MUSL
---------------------
To compile MUSL, follow these steps:

    ./configure --prefix=/usr/local/musl
    make
    sudo make install


Step 3: Compile `dummy.do`
----------------------------
Navigate to the `dummy` directory and compile the `dummy.do` file:

    make


Step 4: Compile `mbedTLS` Library
----------------------------------
Go to the `mbedtls` directory, create a build directory, and compile:

    mkdir build && cd build
    cmake ..
    make


Step 5: Compile `mbedTLS/programs/aes/crypt_and_hash`
-----------------------------------------------------
Navigate to the `mbedtls/programs/aes` directory and compile the `crypt_and_hash` program:

    gcc -o crypt_and_hash crypt_and_hash.c -lmbedtls -lmbedcrypto -lmbedx509


Step 6: Build `graph.dot`
-------------------------
Run the LLVM pass to generate a DOT format library call graph:

    ./extract_policy input_program.c -o graph.dot


Step 7: Build `graph.png`
-------------------------
Use Graphviz to convert the DOT file to a PNG image:

    dot -Tpng graph.dot -o graph.png



## Benchmarks

The project has been tested with the `mbedTLS` library. Compile `mbedTLS` and use the sandbox to enforce the policy on its binary programs.