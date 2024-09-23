#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#if TVM_LLVM_VERSION < 170
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/InstrTypes.h"     // For CallInst class
#include "llvm/IR/Instructions.h"   
#endif

#include <map>
#include <set>
#include <string>
#include <vector>
#include <fstream>

using namespace llvm;

namespace {
  struct CallGraphPass : public FunctionPass {
    static char ID;
    uint64_t gID = 0;
    std::map<void*, std::pair<uint64_t, uint64_t>> blockStartEndState;
    std::map<std::string, std::map<std::string, std::vector<std::pair<std::string, std::string>>>> graphs;

    CallGraphPass() : FunctionPass(ID) {}

    

    virtual bool runOnFunction(Function &Func) {
      std::ofstream outfile("graph.txt", std::ios_base::app);
      uint64_t gID = 0;
      for (auto &basicBlock : Func) {
        void *blockAddress = static_cast<void*>(&basicBlock);
        blockStartEndState.insert({blockAddress, {gID++, -1}});
      }
      errs() << "\ndigraph " << Func.getName() << " {" << "\n";
      for(auto &basicBlock : Func){
        void *blockAddress = static_cast<void*>(&basicBlock);
        std::pair<uint64_t, uint64_t> nodes = blockStartEndState[blockAddress];
        processBlockToGraph(nodes, basicBlock, Func, gID, outfile);
        if (Instruction *terminator = basicBlock.getTerminator()) {
          unsigned numSuccessors = terminator->getNumSuccessors();
          for (unsigned i = 0; i < numSuccessors; ++i) {
            printEdge(nodes.second, blockStartEndState[terminator->getSuccessor(i)].first, "e", Func, outfile);
          }
        }
      }
      errs() << "}" << "\n";
      outfile.close();
      return false;
    }


    void processBlockToGraph(std::pair<unsigned long int, unsigned long int> &nodes, BasicBlock &basicBlock, Function &func, uint64_t &gID, std::ofstream &file){
        unsigned long int start = nodes.first;
        unsigned long int end = nodes.first;
        for (auto &instruction : basicBlock) {
          CallInst *callInst = dyn_cast<CallInst>(&instruction);
          if (callInst == nullptr) continue;
          Function *calledFunction = callInst->getCalledFunction();
          if (calledFunction == nullptr) continue;

          start = end;
          end = gID++;
          printEdge(start, end, calledFunction->getName().str(), func, file);
        }
        nodes.second = end;
    }

    std::string getNodeName(uint64_t nodeId, Function &func){
      return func.getName().str() + "_" + std::to_string(nodeId);
    }

    void printEdge(uint64_t src, uint64_t dst, std::string e, Function &func, std::ofstream &file){
      std::string start = getNodeName(src, func);
      std::string end = getNodeName(dst, func);
      file << func.getName().str() << "," << start << "," << end << "," << e << "\n";
      errs() << "    " << start << " -> " << end << "[label=\"" << e << "\"];\n";
    }
  };
}

char CallGraphPass::ID = 0;

// Automatically enable the pass.
// http://adriansampson.net/blog/clangpass.html
static void registerSkeletonPass(const PassManagerBuilder &,
                         legacy::PassManagerBase &PM) {
  PM.add(new CallGraphPass());
}
static RegisterStandardPasses
  RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
                 registerSkeletonPass);