/*
<%
cfg['compiler_args'] = ['-std=c++17']
setup_pybind11(cfg)
%>
*/

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

class Helper {
private:
  std::vector<std::string> filesKeep;
  std::vector<std::string> dirsKeep;
  std::vector<std::string> filesExclude;
  std::vector<std::string> dirsExclude;

public:
  Helper( std::vector<std::string> filesKeep,
          std::vector<std::string> dirsKeep,
          std::vector<std::string> filesExclude,
          std::vector<std::string> dirsExclude) {
    this->filesKeep = filesKeep;
    this->dirsKeep = dirsKeep;
    this->filesExclude = filesExclude;
    this->dirsExclude = dirsExclude;

  }

  bool startsWith(const std::string& haystack, const std::string& needle) {
    return needle.length() <= haystack.length()
        && equal(needle.begin(), needle.end(), haystack.begin());
  }

  bool shouldTrace(std::string fileName) {
    return this->shouldKeep(fileName) && !this->shouldExclude(fileName);
  }

  bool shouldKeep(std::string fileName) {

    if (std::find(this->filesKeep.begin(), this->filesKeep.end(), fileName) != this->filesKeep.end()){
        return true;
    }
    else{
        for(auto &keepDir : this->dirsKeep){
            if (this->startsWith(fileName, keepDir)){
                return true;
            }
        }
    }
    return false;
  }

  bool shouldExclude(std::string fileName) {

    if (std::find(this->filesExclude.begin(), this->filesExclude.end(), fileName) != this->filesExclude.end()){
        return true;
    }
    else{
        for(auto &excludeDir : this->dirsExclude){
            if (this->startsWith(fileName, excludeDir)){
                return true;
            }
        }
    }
    return false;
  }

};


namespace py = pybind11;

PYBIND11_MODULE(matcher_ext, m) {
  m.doc() = "pybind11 example plugin"; // optional module docstring

  py::class_<Helper>(m, "FileMatcher")
      .def(py::init<
          std::vector<std::string>,
          std::vector<std::string>,
          std::vector<std::string>,
          std::vector<std::string>
      >()
        )
      .def("should_include", &Helper::shouldTrace)
      ;

//
//  m.def("findDefUsePairs", &findDefUsePairs, "Find definition-use pairs");
//  m.def("testCall", &testCall, "Test function for cpp speed estimation");
//  m.def("wrapper", &wrapper, "Test function for cpp speed estimation");

}