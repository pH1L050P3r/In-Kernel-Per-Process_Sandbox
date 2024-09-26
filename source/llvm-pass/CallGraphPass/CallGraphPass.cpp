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
    std::map<void*, uint64_t> blockIds;
    std::map<std::string, std::vector<std::pair<std::string, std::string>>> graph;
    std::map<std::string, uint64_t> dOut;
    std::map<std::string, uint64_t> dIn;

    CallGraphPass() : FunctionPass(ID) {}

    virtual bool runOnFunction(Function &Func) {
      graph.clear();
      dOut.clear();
      dIn.clear();
      std::ofstream outfile("graph.txt", std::ios_base::app);
      uint64_t gID = 1;

      for (auto &basicBlock : Func) {
        void *blockAddress = static_cast<void*>(&basicBlock);
        blockIds.insert({blockAddress, gID++});
      }
      std::vector<uint64_t> funcReturn_vec;
      
      for(auto &basicBlock : Func){
        processBlockToGraph(basicBlock, Func, gID, outfile, funcReturn_vec);
        if (Instruction *terminator = basicBlock.getTerminator()) {
          unsigned numSuccessors = terminator->getNumSuccessors();
          for (unsigned i = 0; i < numSuccessors; ++i) {
            addEdgeToGraph(gID-1, blockIds[terminator->getSuccessor(i)], "e", Func, outfile);
          }
        }
      }

      addStartAndEndNode(funcReturn_vec, Func, gID);

      errs() << "\ndigraph " << Func.getName() << " {" << "\n";
      for(auto n : graph){
        for(auto e : n.second){
          outfile << Func.getName().str() << "," <<  n.first << "," << e.first << "," << e.second  << "\n";
          errs() << "    " <<  n.first << " -> " << e.first << "[label=\"" << e.second  << "\"];\n";
        }
      }
      errs() << "}" << "\n";
      outfile.close();
      return false;
    }


    void processBlockToGraph(BasicBlock &basicBlock, Function &func, uint64_t &gID, std::ofstream &file, std::vector<uint64_t> &funcReturn_vec){
      uint64_t start = blockIds[static_cast<void*>(&basicBlock)];
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
          addEdgeToGraph(start, blockIds[static_cast<void*>(&func.getEntryBlock())], "call_" + calledFunction->getName().str(),func, file);
        } else{
          start = end;
          end = gID++;
          addEdgeToGraph(start, end, calledFunction->getName().str(), func, file);
        }
      }
    }

    void addStartAndEndNode(std::vector<uint64_t> funcReturn_vec, Function &func, uint64_t &gID){
      uint64_t valueToFind = 0;
      uint64_t entry_node =  blockIds[static_cast<void*>(&func.getEntryBlock())];
      
      graph[getNodeName(0, func)].push_back({getNodeName(entry_node, func), "e"});
      std::string endNode = getNodeName(gID++, func);

      for(auto item : dOut){
        if(item.second == 0){
          graph[item.first].push_back({endNode, "e"});
          for(auto ret : funcReturn_vec){
            graph[item.first].push_back({getNodeName(ret, func), "e"});
          }
        }
      }
    }

    std::string getNodeName(uint64_t nodeId, Function &func){
      return func.getName().str() + "_" + std::to_string(nodeId);
    }

    void addEdgeToGraph(uint64_t src, uint64_t dst, std::string e, Function &func, std::ofstream &file){
      std::string start = getNodeName(src, func);
      std::string end = getNodeName(dst, func);
      dOut[start]++;
      dIn[end]++;
      if(dOut.find(end) == dOut.end()) dOut[end] = 0;
      if(dIn.find(start) == dIn.end()) dOut[start] = 0;
      graph[start].push_back({end, e});
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