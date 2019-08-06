/*
<%
cfg['compiler_args'] = ['-std=c++17', '-g']
cfg['include_dirs'] = ['cppitertools']
setup_pybind11(cfg)
%>
*/



#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <itertools.hpp>
#include <map>

typedef long long variable;
typedef std::vector<variable> Vars;
typedef std::map<long long, Vars *> FileMap;
typedef std::map<long long, FileMap *> MyMap;


FileMap *asFileMap(std::map<long long, Vars> dict) {
    auto fileMap = new FileMap();
    for (auto const &x: dict) {
        fileMap->operator[](x.first) = new Vars(x.second);
    }
    return fileMap;
}

MyMap *asMyMap(std::map<long long, std::map<long long, Vars> > dict) {
    auto myMap = new MyMap();
    for (auto const &x : dict) {
        myMap->operator[](x.first) = asFileMap(x.second);
    }

    return myMap;
}

class VariableIndex {
//private:


public:
    MyMap *defs;
    MyMap *uses;


//    VariableIndex(std::map<long long, std::map<long long, Vars > > ddict,
//                  std::map<long long, std::map<long long, Vars > > udict){
//                  }
    VariableIndex(std::map<long long, std::map<long long, Vars> > ddict,
                  std::map<long long, std::map<long long, Vars> > udict) {


        this->defs = asMyMap(ddict);
        this->uses = asMyMap(udict);
    }

    Vars *getDefs(long long file, long long line) {
        auto fmap = this->defs->find(file);
        if (fmap == this->defs->end()) {
            return new Vars();
        } else {
            auto byLine = fmap->second;
            auto lmap = byLine->find(line);
            if (lmap == byLine->end()) {
                return new Vars();
            } else {
                return lmap->second;
            }
        }
    }

    Vars *getUses(long long file, long long line) {
        auto fmap = this->uses->find(file);
        if (fmap == this->uses->end()) {
            return new Vars();
        } else {
            auto byLine = fmap->second;
            auto lmap = byLine->find(line);
            if (lmap == byLine->end()) {
                return new Vars();
            } else {
                return lmap->second;
            }
        }
    }

};


class ReachIn {
private:
    long long idx;
    long long line;
    long long varName;

public:
    ReachIn(long long idx, long long line, long long varName) {
        this->idx = idx;
        this->line = line;
        this->varName = varName;
    }

    long long getIdx() {
        return this->idx;
    }

    long long getLine() {
        return this->line;
    }

    long long getVarName() {
        return this->varName;
    }
};

class DUPair {
private:
    long long useIdx;
    long long useLine;
    long long defIdx;
    long long defLine;
    long long varName;

public:
    DUPair(long long useIdx, long long useLine, long long defIdx, long long defLine, long long varName) {
        this->useIdx = useIdx;
        this->useLine = useLine;
        this->defIdx = defIdx;
        this->defLine = defLine;
        this->varName = varName;
    }

    long long getUseIdx() {
        return this->useIdx;
    }

    long long getUseLine() {
        return this->useLine;
    }

    long long getDefIdx() {
        return this->defIdx;
    }

    long long getDefLine() {
        return this->defLine;
    }

    long long getVarName() {
        return this->varName;
    }
};

//
class Row {
private:
    long long idx;
    long long file;
    long long line;
    long long self;
    long long scope;
    Vars *defs;
    Vars *uses;
    std::vector<ReachIn *> reachIns;
    std::vector<DUPair *> pairs;

public:
    Row(long long idx, long long file, long long line, long long self, long long scope, Vars *defs, Vars *uses) {
        this->idx = idx;
        this->file = file;
        this->line = line;
        this->self = self;
        this->scope = scope;
        this->defs = defs;
        this->uses = uses;
    }

    long long getIdx() {
        return this->idx;
    }

    long long getFile() {
        return this->file;
    }

    long long getLine() {
        return this->line;
    }

    long long getSelf() {
        return this->self;
    }

    long long getScope() {
        return this->scope;
    }

    Vars *getDefs() {
        return this->defs;
    }

    Vars *getUses() {
        return this->uses;
    }

    std::vector<ReachIn *> getReachIns() {
        return this->reachIns;
    }

    std::vector<DUPair *> getPairs() {
        return this->pairs;
    }

    void setReachIns(const std::vector<ReachIn *> &rIns) {
        this->reachIns = rIns;
    }

    void addPair(DUPair *pair) {
        this->pairs.push_back(pair);
    }

    friend std::ostream &operator<<(std::ostream &out, Row *r);
};

//
std::ostream &operator<<(std::ostream &out, Row *r) {
    out << "=============================================" << std::endl;
    out << "Index: " << r->getIdx() << std::endl;
    out << "File: " << r->getFile() << std::endl;
    out << "Line: " << r->getLine() << std::endl;
    out << "Self: " << r->getSelf() << std::endl;
    out << "Scope: " << r->getScope() << std::endl;
    return out;
}


std::vector<std::vector<Row *>> findDefUsePairs(std::vector<Row *> rows) {
    std::vector<std::vector<Row *>> result;
//    std::cout << "1" << std::endl;
    // sort by scope for correct work of groupBy
    std::sort(rows.begin(), rows.end(), [](Row *r1, Row *r2) { return r1->getScope() < r2->getScope(); });
//    std::cout << "2" << std::endl;
    // group by scope and add groups to resulting vector
    for (auto &&gb : iter::groupby(rows, [](Row *r) { return r->getScope(); })) {
        std::vector<Row *> temp;

        for (auto s : gb.second) {
            temp.push_back(s);
        }

        result.push_back(temp);
    }
//    std::cout << "3" << std::endl;
    for (auto grouped : result) {
        std::vector<ReachIn *> reachIns;

        std::sort(grouped.begin(), grouped.end(), [](Row *r1, Row *r2) { return r1->getIdx() < r2->getIdx(); });

        for (auto row : grouped) {
            std::vector<ReachIn *> reachInCopy(reachIns.begin(), reachIns.end()); // copy vector
            std::vector<ReachIn *> reachOut;

            std::vector<long long> *defs = row->getDefs();

            for (auto reachIn : reachIns) {
                if (std::find(defs->begin(), defs->end(), reachIn->getVarName()) == defs->end()) {
                    reachOut.push_back(reachIn);
                }
            }

            for (auto def : *defs) {
                reachOut.push_back(new ReachIn(row->getIdx(), row->getLine(), def));
            }

            reachIns = reachOut;
            row->setReachIns(reachInCopy);

            std::vector<long long> *uses = row->getUses();
//            std::vector<ReachIn *> reachIns = row->getReachIns();

            for (auto use : *uses) {
                for (auto reachIn : reachIns) {
                    if (use == reachIn->getVarName()) {
                        auto pair = new DUPair(row->getIdx(), row->getLine(), reachIn->getIdx(),
                                               reachIn->getLine(), reachIn->getVarName());
                        row->addPair(pair);
                    }
                }
            }


        }
    }

//
//   for (auto outer : result) {
//     for (auto inner : outer) {
//       std::cout << inner << std::endl;
//     }
//     std::cout << '\n';
//   }

    return result;
}

//std::vector<std::vector<Row*>> findDefUsePairs(std::vector<Row*> rows) {
//  std::vector<std::vector<Row*>> result;
//
//  // sort by scope for correct work of groupBy
//  std::sort(rows.begin(), rows.end(), [](Row* r1, Row* r2) { return r1->getScope() < r2->getScope(); });
//
//  // group by scope and add groups to resulting vector
//  for (auto&& gb : iter::groupby(rows, [](Row* r) { return r->getScope(); })) {
//    std::vector<Row*> temp;
//
//    for (auto s : gb.second) {
//      temp.push_back(s);
//    }
//
//    result.push_back(temp);
//  }
//
//  for (auto const &grouped : result) {
//    std::vector<ReachIn*> reachIns;
//
//    for (auto row : grouped) {
//      std::vector<ReachIn*> reachInCopy(reachIns.begin(), reachIns.end()); // copy vector
//      std::vector<ReachIn*> reachOut;
//
//      Vars* defs = row->getDefs();
//
//      for (auto reachIn : reachIns) {
//        if (std::find(defs->begin(), defs->end(), reachIn->getVarName()) == defs->end()) {
//          reachOut.push_back(reachIn);
//        }
//      }
//
//      for (auto def : *defs) {
//        reachOut.push_back(new ReachIn(row->getIdx(), row->getLine(), def));
//      }
//
//      reachIns = reachOut;
//      row->setReachIns(reachInCopy);
//
//      Vars* uses = row->getUses();
////      std::vector<ReachIn*> reachIns = row->getReachIns();
//      for (auto use : *uses) {
//        for (auto reachIn : reachInCopy) {
//          if (use == reachIn->getVarName()) {
//            auto pair = new DUPair(row->getIdx(), row->getLine(), reachIn->getIdx(),
//              reachIn->getLine(), reachIn->getVarName());
//            row->addPair(pair);
//          }
//        }
//      }
//
//
//    }
//  }
//
//  // print
//  // for (auto outer : result) {
//  //   for (auto inner : outer) {
//  //     std::cout << inner << std::endl;
//  //   }
//  //   std::cout << '\n';
//  // }
//
//  return result;
//}
std::vector<std::vector<Row *>> wrapper(
        std::vector<long long> idxs,
        std::vector<long long> files,
        std::vector<long long> lines,
        std::vector<long long> selfs,
        std::vector<long long> scopes,
        std::vector<Vars> defs,
        std::vector<Vars> uses) {

    std::vector<Row *> rows;
    std::cout << "before" << std::endl;
    for (unsigned long i = 0; i < idxs.size(); i++) {
        rows.push_back(new Row(idxs[i], files[i], lines[i], selfs[i], scopes[i], &defs[i], &uses[i]));
    }
    std::cout << "after" << std::endl;
    return findDefUsePairs(rows);
}


std::vector<std::vector<Row *>> findPairsIndex(
        std::vector<long long> idxs,
        std::vector<long long> files,
        std::vector<long long> lines,
        std::vector<long long> selfs,
        std::vector<long long> scopes,
        VariableIndex varIndex
) {

    std::vector<Row *> rows;
//    std::cout << "before" << std::endl;
//    std::cout << "definitions map size: " << varIndex.defs->size() << std::endl;
//    std::cout << "definitions of file 4 size: " << varIndex.defs[0].size() << std::endl;
//    std::cout << "definitions of file 4 size: " << varIndex.defs[1].size() << std::endl;
//    std::cout << "definitions of file 4 size: " << varIndex.defs[2].size() << std::endl;
//    std::cout << "definitions of file 4 size: " << varIndex.defs[3].size() << std::endl;
//    std::cout << "uses map size: " << varIndex.uses->size() << std::endl;

    for (unsigned long i = 0; i < idxs.size(); i++) {
        Vars *defs = varIndex.getDefs(files[i], lines[i]);
        Vars *uses = varIndex.getUses(files[i], lines[i]);
        rows.push_back(new Row(idxs[i], files[i], lines[i], selfs[i], scopes[i], defs, uses));
    }

    return findDefUsePairs(rows);
}

//int main() {
//    auto rows = std::vector<Row *>();
//
//    rows.push_back(new Row(0, 0, 0, 0, 0, new Vars({1, 2}), new Vars({})));
//    rows.push_back(new Row(0, 0, 1, 0, 0, new Vars({3, 4}), new Vars({1, 2})));
//    rows.push_back(new Row(0, 0, 2, 0, 1, new Vars({1, 2}), new Vars({})));
//    auto pairs = findDefUsePairs(rows);
//    // print
//    for (auto outer : pairs) {
//        for (auto inner : outer) {
//            std::cout << inner << std::endl;
//        }
//        std::cout << "-----" << '\n';
//    }
//    std::cout << rows[1]->getPairs().size() << std::endl;
//    return 0;
//}

//int main() {
//    auto file0_defs = new std::map<long long, Vars*>( {
//                                                              {0, new Vars({1, 2})},
//                                                              {1, new Vars({3, 4})},
//                                                              {2, new Vars({5})}
//                                                      });
//    auto file0_uses = new std::map<long long, Vars*>( {
//                                                              {0, new Vars()},
//                                                              {1, new Vars({1, 2})},
//                                                              {2, new Vars()}
//                                                      });
//
//    auto ds = MyMap({
//                            {0, file0_defs}
//
//                    });
//    auto us = MyMap({
//                            {0, file0_uses}
//
//                    });
//
//    VariableIndex vi = VariableIndex(ds, us);
//
//    auto pairs = findPairsIndex(
//            {0, 1, 2},
//            {0, 0, 0},
//            {0, 1, 2},
//            {0, 0, 0},
//            {0, 0, 1},
//            vi
//    );
//
//    for (const auto &outer : pairs) {
//        for (auto inner : outer) {
//            std::cout << inner << inner->getPairs().size() << std::endl;
//        }
//        std::cout << "-----" << '\n';
//    }
//    return 0;
//}


#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>


namespace py = pybind11;

PYBIND11_MODULE(def_use_pairs_ext, m
) {
m.

doc() = "pybind11 example plugin"; // optional module docstring
py::class_<Row>(m,
"Row")
//      .def(py::init<long long , long long ,long long ,long long ,long long
//        ,std::vector<long long>,std::vector<long long>>()
//        )
.def_property_readonly("idx", &Row::getIdx)
.def_property_readonly("scope", &Row::getScope)
.def_property_readonly("line", &Row::getLine)
.def_property_readonly("file", &Row::getFile)
.def_property_readonly("self", &Row::getSelf)

.def_property_readonly("defs", &Row::getDefs)
.def_property_readonly("uses", &Row::getUses)

.def_property_readonly("reach_ins", &Row::getReachIns)
.def_property_readonly("pairs", &Row::getPairs);
py::class_<VariableIndex>(m,
"VariableIndex")
.

def (py::init<std::map<long long, std::map<long long, Vars> >,
        std::map<long long, std::map<long long, Vars> > >()
)

.def("getDefs", &VariableIndex::getDefs)
.def("getUses", &VariableIndex::getUses);


py::class_<DUPair>(m,
"DUPair")
.def_property_readonly("use_idx", &DUPair::getUseIdx)
.def_property_readonly("use_line", &DUPair::getUseLine)
.def_property_readonly("var_name", &DUPair::getVarName)
.def_property_readonly("def_idx", &DUPair::getDefIdx)
.def_property_readonly("def_line", &DUPair::getDefLine);

py::class_<ReachIn>(m,
"ReachIn")
.def_property_readonly("idx", &ReachIn::getIdx)
.def_property_readonly("line", &ReachIn::getLine)
.def_property_readonly("var_name", &ReachIn::getVarName);


m.def("findDefUsePairs", &findDefUsePairs, "Find definition-use pairs");
m.def("findPairsIndex", &findPairsIndex, "Find definition-use pairs");
m.def("wrapper", &wrapper, "Test function for cpp speed estimation");

}