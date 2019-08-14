import staticfg


def try_create_moudule_cfg(name, source):

    return staticfg.builder.CFGBuilder().build_from_src(name, source)
