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
  struct DummyCallAddPass : public FunctionPass {
    static char ID;
    const std::string libc_function = "/home/siddharth/In-Kernel-Per-Process_Sandbox/source/llvm-pass/DummyCallAddPass/musl_functions.txt";
    std::map<std::string, uint32_t> libc_func; 

    DummyCallAddPass() : FunctionPass(ID) {
      std::ifstream inFile(libc_function);
      if (!inFile) {
          errs() << "Could not open the file for reading: " << libc_function << "\n";
          return;
      }
      std::string element;
      uint32_t elementId;
      for(int i = 0; i < 1613; i++){
          inFile >> element >> elementId;
          libc_func.insert({element, elementId});
      }
      inFile.close();
    }

    bool runOnFunction(Function &Func){
      errs() << libc_func.size() << "\n";
      LLVMContext &context = Func.getParent()->getContext();
      IRBuilder<> builder(context);
      FunctionCallee dummySyscallFunc = Func.getParent()->getOrInsertFunction("dummy", Type::getInt32Ty(context), Type::getInt32Ty(context));
      std::string values;
      for (auto &BB : Func) {
          for (auto &I : BB) {
              auto *callInst = dyn_cast<CallInst>(&I);
              if (callInst && callInst->getCalledFunction() && libc_func.find(callInst->getCalledFunction()->getName().str()) != libc_func.end()) {
                  errs() << "I am here " << callInst->getCalledFunction()->getName().str() << "\n"; 
                  builder.SetInsertPoint(&BB, std::next(BB.getFirstInsertionPt()));
                  Value *value = builder.getInt32(libc_func[callInst->getCalledFunction()->getName().str()]);
                  builder.SetInsertPoint(callInst);
                  builder.CreateCall(dummySyscallFunc, {value});
                  values = callInst->getCalledFunction()->getName().str() + " return \n";
              }
          }
      }
      return true;
    }
  };
}

char DummyCallAddPass::ID = 2;

static void registerFunctionPass(const PassManagerBuilder &, legacy::PassManagerBase &PM) {
  PM.add(new DummyCallAddPass());
}
static RegisterStandardPasses RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible, registerFunctionPass);