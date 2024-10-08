#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Module.h"
#if TVM_LLVM_VERSION < 170
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#else
#include "llvm/Pass.h"
#endif
#include "llvm/IR/IRBuilder.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/IR/InstrTypes.h"     // For CallInst class
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Function.h"

#include <map>
#include <set>
#include <string>
#include <vector>
#include <fstream>

using namespace llvm;

namespace {
  struct CallGraphPass : public FunctionPass {
    static char ID;
    uint64_t gID = 1;
    std::map<void*, uint64_t> bbID;
    std::map<uint64_t, std::vector<std::pair<uint64_t, std::string>>> graph;
    std::set<uint64_t> outDeg;

    CallGraphPass() : FunctionPass(ID) {}

    virtual bool runOnFunction(Function &Func) {
      gID = 1;
      graph.clear();
      outDeg.clear();
      // std::ofstream outfile("graph.txt", std::ios_base::app);
      std::vector<uint64_t> recursiveCallEnd;

      for(auto& bb : Func){
        bbID.insert({static_cast<void *>(&bb), gID++});
      }
      // Adding start basic block
      graph[0].push_back({bbID[(&Func.getEntryBlock())], "e"});
      outDeg.insert(0);
      
      for(auto &basicBlock : Func){
        uint64_t end = processBlockToGraph(basicBlock, Func, gID, recursiveCallEnd);
        if (Instruction *terminator = basicBlock.getTerminator()) {
          unsigned numSuccessors = terminator->getNumSuccessors();
          for (unsigned i = 0; i < numSuccessors; ++i) {
            graph[end].push_back({bbID[terminator->getSuccessor(i)], "e"});
            outDeg.insert(end);
          }
        }
      }

      std::vector<uint64_t> endNodes;
      for(int i = 0; i < gID; i++){
        if(outDeg.find(i) == outDeg.end()) {
          endNodes.push_back(i);
        }
      }

      for(uint64_t node : endNodes){
        errs() << "endnode : " << node << " \n"; 
      }


      for(auto n1 : endNodes){
        for(auto n2 : recursiveCallEnd){
          graph[n1].push_back({n2, "e"});
        }
      }
      
      for(auto node : endNodes){
        graph[node].push_back({gID, "e"});
      }
      to_epsillon_DFA(Func, 0, gID, graph);

      // outfile << "\ndigraph " << Func.getName().str() << " {" << "\n";
      // for(auto node : graph){
      //   for(auto e : node.second){
      //     outfile << node.first << " -> " << e.first << " [label=\"" << e.second << "\"]\n"; 
      //   }
      // }
      // outfile << "}\n";
      // outfile.close();
      return false;
    }


    uint64_t processBlockToGraph(BasicBlock &basicBlock, Function &func, uint64_t &gID, std::vector<uint64_t> &funcReturn_vec){
      uint64_t start = bbID[static_cast<void*>(&basicBlock)];
      uint64_t end = start;
      for (auto &instruction : basicBlock) {
        CallInst *callInst = dyn_cast<CallInst>(&instruction);
        if (callInst == nullptr) continue;
        Function *calledFunction = callInst->getCalledFunction();
        if (calledFunction == nullptr) continue;

        if(calledFunction->getName().str() == func.getName().str()){
          start = end;
          end = gID++;
          funcReturn_vec.push_back(end);
          errs() << " " << end << "\n";
          graph[start].push_back({bbID[(&func.getEntryBlock())], calledFunction->getName().str()});
        } else{
          start = end;
          end = gID++;
          graph[start].push_back({end, calledFunction->getName().str()});
        }
        outDeg.insert(start);
      }
      return end;
    }

    void to_epsillon_DFA(Function& func, uint64_t start, uint64_t endState, std::map<uint64_t, std::vector<std::pair<uint64_t, std::string>>> &graph){
      std::ofstream outfile("ENFA_"+ func.getName().str() +".txt");  //, std::ios_base::app);
      outfile << start << "\n";
      outfile << endState << "\n";
      for(auto item : graph){
        for(auto e : item.second)
          outfile << func.getName().str() << ","  << item.first << "," << e.first << "," << e.second << "\n";
      }
      outfile.close();
    }
  };

  struct FunctionListPass : public FunctionPass {
    static char ID;
    std::set<std::string> fname;

    FunctionListPass() : FunctionPass(ID) {}

    virtual bool doInitialization(Module &)  {
      fname.clear();
      deserializeSet("function_defined.txt"); 
      return false; 
    }

    virtual bool doFinalization(Module &) { 
      serializeSet("function_defined.txt");
      return false; 
    }

    virtual bool runOnFunction(Function &Func) {
      fname.insert(Func.getName().str());
      errs() << Func.getName().str() << "\n";
      return false;
    }

    void serializeSet(const std::string& filename) {
        std::ofstream outFile(filename, std::ios::trunc);
        if (!outFile) {
            errs() << "Could not open the file for writing: " << filename << "\n";
            return;
        }
        for (const std::string& element : fname) {
            outFile << element <<  "\n"; // Write each element to a new line
        }
        outFile.close();
    }

    void deserializeSet(const std::string& filename) {
      std::ifstream inFile(filename);
      if (!inFile) {
          errs() << "Could not open the file for reading: " << filename << "\n";
          return;
      }

      std::string element;
      while (inFile >> element) {
          fname.insert(element); // Insert each element into the set
      }
      inFile.close();
    }
  };
}

char CallGraphPass::ID = 0;
char FunctionListPass::ID = 1;

static void registerFunctionPass(const PassManagerBuilder &, legacy::PassManagerBase &PM) {
  PM.add(new CallGraphPass());
  PM.add(new FunctionListPass());
}
static RegisterStandardPasses RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible, registerFunctionPass);