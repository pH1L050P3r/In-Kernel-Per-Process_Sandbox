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
    const std::string libc_function = std::string(__FILE__).substr(0, std::string(__FILE__).find_last_of("/\\")) + "/library_functions.txt";
    std::map<std::string, uint32_t> libc_func;
    std::set<std::string> fname; 

    DummyCallAddPass() : FunctionPass(ID) {
      std::ifstream inFile(libc_function);
      if (!inFile) {
          errs() << "Could not open the file for reading: " << libc_function << "\n";
          return;
      }
      std::string element;
      uint32_t elementId;
      for(int i = 0; i < 2671; i++){
          inFile >> element >> elementId;
          libc_func.insert({element, elementId});
      }
      inFile.close();
    }

    virtual bool doInitialization(Module &)  {
      fname.clear();
      deserializeSet("called_lib_functions.txt"); 
      return false; 
    }

    virtual bool doFinalization(Module &) { 
      serializeSet("called_lib_functions.txt");
      return false; 
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
                  builder.SetInsertPoint(&BB, std::next(BB.getFirstInsertionPt()));
                  Value *value = builder.getInt32(libc_func[callInst->getCalledFunction()->getName().str()]);
                  builder.SetInsertPoint(callInst);
                  builder.CreateCall(dummySyscallFunc, {value});
                  values = callInst->getCalledFunction()->getName().str() + " return \n";
                  fname.insert(callInst->getCalledFunction()->getName().str());
              }
          }
      }
      return true;
    }

    void serializeSet(const std::string& filename) {
      std::ofstream outFile(filename, std::ios::trunc);
      if (!outFile) {
          errs() << "Could not open the file for writing: " << filename << "\n";
          return;
      }
      for (const std::string& element : fname)
          outFile << element <<  "\n"; // Write each element to a new line
      outFile.close();
    }

    void deserializeSet(const std::string& filename) {
      std::ifstream inFile(filename);
      if (!inFile) {
          errs() << "Could not open the file for reading: " << filename << "\n";
          return;
      }

      std::string element;
      while (inFile >> element)
          fname.insert(element); // Insert each element into the set
      inFile.close();
    }
  };
}

char DummyCallAddPass::ID = 2;

static void registerFunctionPass(const PassManagerBuilder &, legacy::PassManagerBase &PM) {
  PM.add(new DummyCallAddPass());
}
static RegisterStandardPasses RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible, registerFunctionPass);