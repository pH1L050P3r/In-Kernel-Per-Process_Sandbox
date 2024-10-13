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

## How to Build and Run

### Step 1: Compile LLVM Passes
Compile the necessary LLVM passes, which will extract the library call policies and insert dummy system calls into the C program.

### Step 2: Compile MUSL
Compile MUSL, which is needed for system-level operations. Make sure to configure it correctly and install it on your system.

### Step 3: Compile the `dummy.do` File
Next, compile the `dummy.do` file, which is responsible for inserting dummy system calls that will be used for tracking library calls in the sandbox.

### Step 4: Compile the `mbedTLS` Library
Compile the `mbedTLS` library, which will be used to benchmark and test your sandbox implementation.

### Step 5: Compile the `crypt_and_hash` Program
Within the `mbedTLS` library, compile the `crypt_and_hash` program, which will be used for testing the sandbox.

### Step 6: Generate the Library Call Graph (`graph.dot`)
Once the passes are compiled and run on the input C program, generate a `.dot` file that represents the library call graph. This file will be used for visualization and analysis.

### Step 7: Visualize the Call Graph (`graph.png`)
Convert the `.dot` file into a PNG image using Graphviz to visually represent the library call graph. This will allow you to inspect the call flow policy extracted from the program.

## Benchmarks

The project has been tested with the `mbedTLS` library. Compile `mbedTLS` and use the sandbox to enforce the policy on its binary programs.