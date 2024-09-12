#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#if TVM_LLVM_VERSION < 170
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/InstrTypes.h"     // For CallInst class
#include "llvm/IR/Instructions.h"   
#endif

using namespace llvm;

namespace {
  struct SkeletonPass : public FunctionPass {
    static char ID;
    SkeletonPass() : FunctionPass(ID) {}

    virtual bool runOnFunction(Function &Func) {
      // errs() << "I saw a function called " << F.getName() << "!\n";
      for (auto &basicBlock : Func) {
        for (auto &instruction : basicBlock) {
          CallInst *callInst = dyn_cast<CallInst>(&instruction);
          if (callInst == nullptr)
            continue; // not a call instruction

          Function *calledFunction = callInst->getCalledFunction();

          if (calledFunction == nullptr)
            continue; // called Function details not found
            
          errs() << "Function Call From : " << Func.getName()  << " to : " << calledFunction->getName() << "\n";
        }
      }
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
