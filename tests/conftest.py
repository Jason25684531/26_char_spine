import json
import shutil

import pytest

from character_to_spine import pipeline
from synthetic import make


@pytest.fixture(scope="session")
def synth(tmp_path_factory):
    """synth(name) -> (圖片路徑, 真實 bbox)。每個角色只產生一次。"""
    cache = {}

    def get(name):
        if name not in cache:
            cache[name] = make(name, tmp_path_factory.mktemp(name))
        return cache[name]
    return get


@pytest.fixture(scope="session")
def built(synth, tmp_path_factory):
    """built(name) -> 跑完整流程後的工作目錄（唯讀，要修改請用 workcopy）。"""
    cache = {}

    def get(name):
        if name not in cache:
            wd = tmp_path_factory.mktemp(f"{name}_work")
            result = pipeline.run(synth(name)[0], "happy", workdir=wd)
            assert result["status"] != "needs_input", result
            cache[name] = wd
        return cache[name]
    return get


@pytest.fixture
def workcopy(built, tmp_path):
    """workcopy(name) -> 可修改的工作目錄複本。"""
    def get(name):
        dst = tmp_path / name
        shutil.copytree(built(name), dst)
        # 來源指向複本自己：--replace 的修補圖才會留在這個複本內，不會寫進共用的合成角色來源、影響其他測試
        parts = dst / "parts.json"
        doc = json.loads(parts.read_text(encoding="utf-8"))
        doc["source"] = str(parts)
        parts.write_text(json.dumps(doc), encoding="utf-8")
        return dst
    return get
