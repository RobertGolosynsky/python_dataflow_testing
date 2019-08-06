cmake_minimum_required(VERSION 3.14)
project(du_pairs)

set(CMAKE_CXX_STANDARD 17)

include_directories(cppitertools)
include_directories(cppitertools/internal)

#SHARED
add_executable(du_pairs
#        cppitertools/examples/accumulate_examples.cpp
#        cppitertools/examples/chain_examples.cpp
#        cppitertools/examples/chunked_examples.cpp
#        cppitertools/examples/combinatoric_examples.cpp
#        cppitertools/examples/compress_examples.cpp
#        cppitertools/examples/count_examples.cpp
#        cppitertools/examples/cycle_examples.cpp
#        cppitertools/examples/dropwhile_examples.cpp
#        cppitertools/examples/enumerate_examples.cpp
#        cppitertools/examples/filter_examples.cpp
#        cppitertools/examples/filterfalse_examples.cpp
#        cppitertools/examples/groupby_examples.cpp
#        cppitertools/examples/imap_examples.cpp
#        cppitertools/examples/mixed_examples.cpp
#        cppitertools/examples/range_examples.cpp
#        cppitertools/examples/repeat_examples.cpp
#        cppitertools/examples/reversed_examples.cpp
#        cppitertools/examples/samples.hpp
#        cppitertools/examples/slice_examples.cpp
#        cppitertools/examples/sliding_window_examples.cpp
#        cppitertools/examples/sorted_examples.cpp
#        cppitertools/examples/starmap_examples.cpp
#        cppitertools/examples/takewhile_examples.cpp
#        cppitertools/examples/unique_everseen_examples.cpp
#        cppitertools/examples/unique_justseen_examples.cpp
#        cppitertools/examples/zip_examples.cpp
#        cppitertools/examples/zip_longest_examples.cpp
#        cppitertools/internal/iter_tuples.hpp
#        cppitertools/internal/iterator_wrapper.hpp
#        cppitertools/internal/iteratoriterator.hpp
#        cppitertools/internal/iterbase.hpp
#        cppitertools/accumulate.hpp
#        cppitertools/chain.hpp
#        cppitertools/chunked.hpp
#        cppitertools/combinations.hpp
#        cppitertools/combinations_with_replacement.hpp
#        cppitertools/compress.hpp
#        cppitertools/count.hpp
#        cppitertools/cycle.hpp
#        cppitertools/dropwhile.hpp
#        cppitertools/enumerate.hpp
#        cppitertools/filter.hpp
#        cppitertools/filterfalse.hpp
#        cppitertools/groupby.hpp
#        cppitertools/imap.hpp
#        cppitertools/itertools.hpp
#        cppitertools/permutations.hpp
#        cppitertools/powerset.hpp
#        cppitertools/product.hpp
#        cppitertools/range.hpp
#        cppitertools/repeat.hpp
#        cppitertools/reversed.hpp
#        cppitertools/slice.hpp
#        cppitertools/sliding_window.hpp
#        cppitertools/sorted.hpp
#        cppitertools/starmap.hpp
#        cppitertools/takewhile.hpp
#        cppitertools/unique_everseen.hpp
#        cppitertools/unique_justseen.hpp
#        cppitertools/zip.hpp
#        cppitertools/zip_longest.hpp
        def_use_pairs_ext.cpp)
#        def_use_pairs_ext_bc.cpp
#        variable_index.cpp)
