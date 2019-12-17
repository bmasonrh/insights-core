from insights.parsr.query import startswith
from insights.models import Dict, List

api = Dict({
    "kind": "KubeAPIServer",
    "status": Dict({
        "conditions": List([
            Dict({
                "type": "Ready",
                "status": "True"
            }),
            Dict({
                "type": "Failing",
                "status": "False"
            }),
            Dict({
                "type": "Initializing",
                "status": "False"
            }),
        ])
    })
})

sched = Dict({
    "kind": "KubeScheduler",
    "status": Dict({
        "conditions": List([
            Dict({
                "type": "Ready",
                "status": "True"
            }),
            Dict({
                "type": "Failing",
                "status": "False"
            }),
            Dict({
                "type": "Initializing",
                "status": "False"
            }),
        ])
    })
})


def test_dict_access():
    assert api["kind"] == "KubeAPIServer"
    assert api.kind == "KubeAPIServer"


def test_dict_name_query():
    res = api[startswith("k")]
    assert res["kind"] == "KubeAPIServer"


def test_dict_tuple_access():
    res = api["kind", "KubeAPIServer"]
    assert res.kind == "KubeAPIServer"

    res = api["kind", startswith("Kube")]
    assert res.kind == "KubeAPIServer"

    res = api[startswith("k"), startswith("Kube")]
    assert res.kind == "KubeAPIServer"

    res = api[None, startswith("Kube")]
    assert res.kind == "KubeAPIServer"


def test_list_access():
    conf = List([api, sched])

    assert conf["kind"] == ["KubeAPIServer", "KubeScheduler"], conf["kind"]
    assert conf.kind == ["KubeAPIServer", "KubeScheduler"], conf


def test_list_name_query():
    conf = List([api, sched])

    res = conf[startswith("k")]
    assert len(res) == 2, res


def test_list_query_access():
    conf = List([api, sched])

    res = conf["kind", "KubeAPIServer"]
    assert res, res

    res = conf["kind", startswith("Kube")]
    assert res, res

    res = conf[startswith("k"), "KubeAPIServer"]
    assert res, res

    res = conf[startswith("k"), startswith("Kube")]
    assert res, res

    res = api[None, startswith("Kube")]
    assert res, res
