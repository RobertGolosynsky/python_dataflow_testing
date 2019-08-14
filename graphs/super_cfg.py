# import networkx as nx
# from graphs.create import INSTRUCTION_KEY, FakeBytecodeInstruction
#
#
# def call_sites(cfg: nx.DiGraph):
#     for node, data in cfg.nodes(data=True):
#         instr: FakeBytecodeInstruction = data.get(INSTRUCTION_KEY, None)
#         if instr:
#             if instr.opname == "CALL"
#
#
# def create_expanded_cfgs(methods):
#     cfgs = {}
#     for m_name, function_cfg in methods:
#         super_cfg = nx.DiGraph()
#
#         call_sites = call_sites(function_cfg.cfg)
