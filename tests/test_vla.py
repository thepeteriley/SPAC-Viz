import numpy as np
import pytest
from spac_viz.vla import write_vla,validate_vla,FILENAMES,VLA_HEADER

def test_syntax_separation_and_classes(tmp_path):
    classes={}
    for cls,name in FILENAMES.items():
        p=tmp_path/name
        stats=write_vla(p,[np.array([[1,0,0],[2,0,0]]),np.array([[0,1,0],[0,2,0]])],
                        {"classification":cls})
        lines,meta,parsed=validate_vla(p,cls)
        assert stats==parsed and parsed.polylines==2 and parsed.vertices==4
        assert p.read_text().count("\nP ")==2
        classes[cls]=set(map(tuple,np.concatenate(lines)))
    assert len(classes)==3

def test_required_header_and_left_handed_xzy_coordinates(tmp_path):
    p=tmp_path/"coordinates.vla"
    original=np.array([[1.25,2.5,3.75],[4.0,5.0,6.0]])
    write_vla(p,[original],{"classification":"closed"},scale=2)
    text=p.read_text().splitlines()
    assert tuple(text[:len(VLA_HEADER)])==VLA_HEADER
    assert "set intensity EXPLICIT" not in text
    lines,_,_=validate_vla(p,"closed")
    assert np.allclose(lines[0],[[2.5,7.5,5.0],[8.0,12.0,10.0]])

def test_minimal_has_no_header_but_still_uses_xzy(tmp_path):
    p=tmp_path/"minimal.vla"
    write_vla(p,[np.array([[1,2,3],[4,5,6]])],{},minimal=True)
    assert p.read_text().splitlines()==["P 1 3 2","L 4 6 5"]
    validate_vla(p)

def test_strict_rejects(tmp_path):
    p=tmp_path/"bad.vla"; p.write_text("L 1 2 3\n")
    with pytest.raises(ValueError): validate_vla(p)
    p.write_text("P nan 2 3\nL 1 2 3\n")
    with pytest.raises(ValueError): validate_vla(p)
    p.write_text("set coordsys RIGHT\nP 1 2 3\nL 1 2 4\n")
    with pytest.raises(ValueError): validate_vla(p)
    p.write_text("set coordsys LEFT\nP 1 2 3\nL 1 2 4\n")
    with pytest.raises(ValueError): validate_vla(p)
