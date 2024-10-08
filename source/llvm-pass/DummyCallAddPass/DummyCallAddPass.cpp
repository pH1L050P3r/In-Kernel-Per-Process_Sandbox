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

    DummyCallAddPass() : FunctionPass(ID) {}

    bool runOnFunction(Function &Func){
      LLVMContext &context = Func.getParent()->getContext();
      IRBuilder<> builder(context);
      FunctionType *printfType = FunctionType::get(IntegerType::getInt32Ty(context), PointerType::get(Type::getInt8Ty(context), 0), true);
      FunctionCallee printfFunc = Func.getParent()->getOrInsertFunction("printf", printfType);
      std::string values;
      bool isInsert = false;
      for (auto &BB : Func) {
          for (auto &I : BB) {
              if(isInsert){
                  builder.SetInsertPoint(&BB, std::next(BB.getFirstInsertionPt()));
                  Value *strValue = builder.CreateGlobalStringPtr(values);
                  builder.SetInsertPoint(&I);
                  builder.CreateCall(printfFunc, {strValue});
                  isInsert = false;
              }
              if (auto *callInst = dyn_cast<CallInst>(&I)) {
                  builder.SetInsertPoint(&BB, std::next(BB.getFirstInsertionPt()));
                  Value *strValue = builder.CreateGlobalStringPtr(callInst->getCalledFunction()->getName().str() + " Called \n");
                  builder.SetInsertPoint(callInst);
                  builder.CreateCall(printfFunc, {strValue});
                  isInsert = true;
                  values = callInst->getCalledFunction()->getName().str() + " return \n";
              }
          }
          if(isInsert){
            // TODO: Add new basic block and insert in between
              isInsert = false;
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