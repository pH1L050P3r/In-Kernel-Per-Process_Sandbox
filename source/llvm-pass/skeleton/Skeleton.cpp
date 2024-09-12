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

using namespace llvm;

namespace {
  struct SkeletonPass : public FunctionPass {
    static char ID;
    unsigned long int gID = 0;
    std::map<unsigned long int, std::set<void*>> mp;
    std::map<void*, unsigned long int> st;  // block and state
    SkeletonPass() : FunctionPass(ID) {}

    virtual bool runOnFunction(Function &Func) {
      unsigned long int gID = 0;
      errs() << "\ndigraph " << Func.getName() << " {" << "\n";
      for (auto &basicBlock : Func) {
        void *blockAddress = static_cast<void*>(&basicBlock);
        bool isState = false;
        for (auto &instruction : basicBlock) {
          CallInst *callInst = dyn_cast<CallInst>(&instruction);
          if (callInst == nullptr) continue;
          Function *calledFunction = callInst->getCalledFunction();
          if (calledFunction == nullptr) continue;

          if(st.find(blockAddress) == st.end()) {
            st.insert({blockAddress, gID});
            isState = true;
          }

          std::string start = Func.getName().str() + "_" + std::to_string(gID);
          std::string end= Func.getName().str() + "_" + std::to_string(++gID);
          errs() << "    " << start << " -> " << end << "[label=\"" << calledFunction->getName().str()<< "\"];\n";
        }

        if (Instruction *terminator = basicBlock.getTerminator()) {
          if (BranchInst *branch = dyn_cast<BranchInst>(terminator)) {
            if (branch->isConditional()) {
                mp[gID].insert(branch->getSuccessor(0));
                mp[gID].insert(branch->getSuccessor(1));
            } else {
                // Unconditional branch (only one successor)
                mp[gID].insert(branch->getSuccessor(0));
            }
          }
        }
        if(!isState){
          std::string start = Func.getName().str() + "_" + std::to_string(gID);
          std::string end= Func.getName().str() + "_" + std::to_string(1+gID);
          errs() << "    " << start << " -> " << end << "[label=\"e" << "\"];\n";
          st.insert({blockAddress, gID++});
        }
      }
      for(auto it : mp){
        for(auto index : it.second){
          std::string start = Func.getName().str() + "_" + std::to_string(it.first);
          std::string end = Func.getName().str() + "_" + std::to_string(st[index]);
          errs() << "    " << start << " -> " << end << "[label=\"e"<< "\"];\n";
        }
      }
      errs() << "}" << "\n";
      return false;
    }
  };
}

char SkeletonPass::ID = 0;

// Automatically enable the pass.
// http://adriansampson.net/blog/clangpass.html
static void registerSkeletonPass(const PassManagerBuilder &,
                         legacy::PassManagerBase &PM) {
  PM.add(new SkeletonPass());
}
static RegisterStandardPasses
  RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
                 registerSkeletonPass);