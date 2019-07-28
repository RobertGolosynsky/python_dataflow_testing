# import unittest
# import pickle
#
# import tracing.analizer as ta
# from model.cfg.project_cfg import ProjectCFG
# from model.project import Project
#
#
# class TestTraceAnalyzer(unittest.TestCase):
#
#     def test(self):
#         import time
#         p = Project("../../")
#         cfg = ProjectCFG(p)
#         st = time.time()
#         analyzer = ta.DataflowAnalyzer("../../"+".traces", cfg)
#         groups = analyzer._analyze()
#         print("time taken:", time.time() - st)
#
#         # with open("groups.pkl", "wb") as f:
#         #     pickle.dump(groups, f, protocol=2)
#
#     def test_load_trace_dict(self):
#         with open("groups.pkl", "rb") as f:
#             d = pickle.load(f)
#
#         print(d.keys())