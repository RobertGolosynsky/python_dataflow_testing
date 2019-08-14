# import dis as py_dis
# import xdis.std as dis
#
# import networkx as nx
#
#
# class SomeClass:
#     def a(self):
#         self.print(self)
#         a = 3
#         a = len(self) / self.a.b
#         self.b()
#         return x
#
#     def a1(self):
#         c = nx
#         x = 1
#         m = 1
#         n = 1
#         self.b(self.b(1), n, nx, l=3, **some_dict)
#         return x
#
#     def b(self):
#         y = 1
#         return y
#
#
# FROM_ARG = 10001
# PUSHES_NEW_BLOCK = 10002
#
# op_footprint = {}
# op_footprint["POP_TOP"] = (1, 0)
# op_footprint["ROT_TWO"] = (0, 0)
# op_footprint["ROT_THREE"] = (0, 0)
# op_footprint["DUP_TOP"] = (0, 1)
# op_footprint["DUP_TOP_TWO"] = (0, 2)
# op_footprint["NOP"] = (0, 0)
# op_footprint["UNARY_POSITIVE"] = (0, 0)
# op_footprint["UNARY_NEGATIVE"] = (0, 0)
# op_footprint["UNARY_NOT"] = (0, 0)
# op_footprint["UNARY_INVERT"] = (0, 0)
# op_footprint["BINARY_POWER"] = (2, 1)
# op_footprint["BINARY_MULTIPLY"] = (2, 1)
# op_footprint["BINARY_MODULO"] = (2, 1)
# op_footprint["BINARY_ADD"] = (2, 1)
# op_footprint["BINARY_SUBTRACT"] = (2, 1)
# op_footprint["BINARY_SUBSCR"] = (2, 1)
# op_footprint["BINARY_FLOOR_DIVIDE"] = (2, 1)
# op_footprint["BINARY_TRUE_DIVIDE"] = (2, 1)
# op_footprint["INPLACE_FLOOR_DIVIDE"] = (2, 1)
# op_footprint["INPLACE_TRUE_DIVIDE"] = (2, 1)
# op_footprint["INPLACE_ADD"] = (2, 1)
# op_footprint["INPLACE_SUBTRACT"] = (2, 1)
# op_footprint["INPLACE_MULTIPLY"] = (2, 1)
# op_footprint["INPLACE_MODULO"] = (2, 1)
# op_footprint["STORE_SUBSCR"] = (2, 1)
# op_footprint["DELETE_SUBSCR"] = (2, 1)
# op_footprint["BINARY_LSHIFT"] = (2, 1)
# op_footprint["BINARY_RSHIFT"] = (2, 1)
# op_footprint["BINARY_AND"] = (2, 1)
# op_footprint["BINARY_XOR"] = (2, 1)
# op_footprint["BINARY_OR"] = (2, 1)
# op_footprint["INPLACE_POWER"] = (2, 1)
# op_footprint["GET_ITER"] = (1, 1)
# op_footprint["PRINT_EXPR"] = (1, 0)
# op_footprint["LOAD_BUILD_CLASS"] = (1, 0)
# op_footprint["INPLACE_LSHIFT"] = (2, 1)
# op_footprint["INPLACE_RSHIFT"] = (2, 1)
# op_footprint["INPLACE_AND"] = (2, 1)
# op_footprint["INPLACE_XOR"] = (2, 1)
# op_footprint["INPLACE_OR"] = (2, 1)
# op_footprint["BREAK_LOOP"] = (0, 0)
# op_footprint["RETURN_VALUE"] = (1, 0)  # or?
# op_footprint["IMPORT_STAR"] = (1, 0)
# op_footprint["YIELD_VALUE"] = (1, 0)
# op_footprint["POP_BLOCK"] = (-100, 0)  # I guess it removes everything
# op_footprint["END_FINALLY"] = (0, 0)
# op_footprint["POP_EXCEPT"] = (-100, 0)  # Should remove everything I guess
# op_footprint["STORE_NAME"] = (1, 0)
# op_footprint["DELETE_NAME"] = (0, 0)
# op_footprint["UNPACK_SEQUENCE"] = (1, FROM_ARG)
# op_footprint["FOR_ITER"] = (0, 1)
# op_footprint["UNPACK_EX"] = (1, FROM_ARG)
# op_footprint["STORE_ATTR"] = (2, 0)
# op_footprint["DELETE_ATTR"] = (0, 0)
# op_footprint["STORE_GLOBAL"] = (1, 0)
# op_footprint["DELETE_GLOBAL"] = (0, 0)
# op_footprint["LOAD_CONST"] = (1, 0)
# op_footprint["LOAD_NAME"] = (1, 0)
# op_footprint["BUILD_TUPLE"] = (FROM_ARG, 1)
# op_footprint["BUILD_LIST"] = (FROM_ARG, 1)
# op_footprint["BUILD_SET"] = (FROM_ARG, 1)
# op_footprint["BUILD_MAP"] = (FROM_ARG, 1)
# op_footprint["LOAD_ATTR"] = (1, 1)
# op_footprint["COMPARE_OP"] = (0, 0)
# op_footprint["IMPORT_NAME"] = (2, 1)
# op_footprint["IMPORT_FROM"] = (0, 1)
# op_footprint["JUMP_FORWARD"] = (0, 0)
# op_footprint["JUMP_IF_FALSE_OR_POP"] = (0, 0)
# op_footprint["JUMP_IF_TRUE_OR_POP"] = (0, 0)
# op_footprint["JUMP_ABSOLUTE"] = (0, 0)
# op_footprint["POP_JUMP_IF_FALSE"] = (1, 0)
# op_footprint["POP_JUMP_IF_TRUE"] = (1, 0)
# op_footprint["LOAD_GLOBAL"] = (1, 0)
# op_footprint["CONTINUE_LOOP"] = (0, 0)
# op_footprint["SETUP_LOOP"] = (PUSHES_NEW_BLOCK, 0)
# op_footprint["SETUP_EXCEPT"] = (PUSHES_NEW_BLOCK, 0)
# op_footprint["SETUP_FINALLY"] = (PUSHES_NEW_BLOCK, 0)
# op_footprint["LOAD_FAST"] = (0, 1)
# op_footprint["STORE_FAST"] = (1, 0)
# op_footprint["DELETE_FAST"] = (0, 0)
# op_footprint["RAISE_VARARGS"] = (FROM_ARG, 0)
# op_footprint["CALL_FUNCTION"] = (FROM_ARG, 1)
# op_footprint["MAKE_FUNCTION"] = (0, 0)
# op_footprint["BUILD_SLICE"] = (0, 0)
# op_footprint["LOAD_CLOSURE"] = (0, 0)
# op_footprint["LOAD_DEREF"] = (0, 0)
# op_footprint["STORE_DEREF"] = (0, 0)
# op_footprint["DELETE_DEREF"] = (0, 0)
# op_footprint["CALL_FUNCTION_KW"] = (0, 0)
# op_footprint["SETUP_WITH"] = (0, 0)
# op_footprint["LIST_APPEND"] = (0, 0)
# op_footprint["SET_ADD"] = (0, 0)
# op_footprint["MAP_ADD"] = (0, 0)
# op_footprint["EXTENDED_ARG"] = (0, 0)
# op_footprint["YIELD_FROM"] = (0, 0)
# op_footprint["LOAD_CLASSDEREF"] = (0, 0)
# op_footprint["BINARY_MATRIX_MULTIPLY"] = (0, 0)
# op_footprint["INPLACE_MATRIX_MULTIPLY"] = (0, 0)
# op_footprint["GET_AITER"] = (0, 0)
# op_footprint["GET_ANEXT"] = (0, 0)
# op_footprint["BEFORE_ASYNC_WITH"] = (0, 0)
# op_footprint["GET_YIELD_FROM_ITER"] = (0, 0)
# op_footprint["GET_AWAITABLE"] = (0, 0)
# op_footprint["WITH_CLEANUP_START"] = (0, 0)
# op_footprint["WITH_CLEANUP_FINISH"] = (0, 0)
# op_footprint["BUILD_LIST_UNPACK"] = (0, 0)
# op_footprint["BUILD_MAP_UNPACK"] = (0, 0)
# op_footprint["BUILD_MAP_UNPACK_WITH_CALL"] = (0, 0)
# op_footprint["BUILD_TUPLE_UNPACK"] = (0, 0)
# op_footprint["BUILD_SET_UNPACK"] = (0, 0)
# op_footprint["SETUP_ASYNC_WITH"] = (0, 0)
# op_footprint["STORE_ANNOTATION"] = (0, 0)
# op_footprint["FORMAT_VALUE"] = (0, 0)
# op_footprint["BUILD_CONST_KEY_MAP"] = (0, 0)
# op_footprint["CALL_FUNCTION_EX"] = (0, 0)
# op_footprint["SETUP_ANNOTATIONS"] = (0, 0)
# op_footprint["BUILD_STRING"] = (0, 0)
# op_footprint["BUILD_TUPLE_UNPACK_WITH_CALL"] = (0, 0)
#
# #
# # for op_name in dis.opmap.keys():
# #     print('op_footprint["{}"] = ({}, {})'.format(op_name, 0, 0))
# #     op_footprint["opname"] = (1, 2)
# dis.dis(SomeClass.a1)
# exit()
# instrs = dis.get_instructions(SomeClass.a)
# stack = []
# stack_effect = 0
#
# for ins in instrs:
#     if ins.opname.startswith("CALL_"):
#         print("CALLLLLLLLLLLLLing", stack[0])
#     print(ins.opname, ins.argrepr)
#     effect = py_dis.stack_effect(ins.opcode, ins.arg)
#     arg_count = ins.arg if ins.arg else 0
#     stack_effect += effect
#     print(ins)
#     print("effect:", effect, "args_count:", arg_count, 'stack_len:', stack_effect)
#     pushes = arg_count + effect
#
#     for _ in range(arg_count):
#         stack.pop()
#     if pushes == 1:
#         stack.append(ins)
# # if effect == 0:
# #     pass
# # elif effect == 1:
# #     stack.append(ins)
# # elif effect > 1:
# #     raise ValueError("Stack effect is larger than 2, wat?")
# # elif effect < 0:
# #     for _ in range(-effect):
# #         stack.pop()
# # print("stack:", ["{}: {}".format(op.opname, op.argval) for op in stack])
