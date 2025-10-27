import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from miner.miner import (
    split_method_name,
    extract_python_functions,
    extract_java_methods,
    process_file_content,
)


def test_split_method_name_snake_case():
    assert split_method_name("make_response") == ["make", "response"]

def test_split_method_name_camel_case():
    assert split_method_name("retainAllItems") == ["retain", "all", "items"]




def test_extract_python_functions_basic():
    code = '''
def make_response(*args):
    pass

def processData(data):
    return data
'''
    result = extract_python_functions(code)
    assert "make_response" in result
    assert "processData" in result

def test_extract_python_functions_invalid_code():
    bad_code = "def this(is invalid"
    result = extract_python_functions(bad_code)
    assert result == []


def test_extract_java_methods_basic():
    code = '''
public boolean retainAll(Collection<?> c) {
    return true;
}

private void makeResponse() {}
'''
    methods = extract_java_methods(code)
    assert "retainAll" in methods
    assert "makeResponse" in methods

def test_extract_java_methods_ignore_keywords():
    code = '''
public class Example {
    public void runIf() {}
}
'''
    methods = extract_java_methods(code)
    assert "runIf" in methods
    assert "class" not in methods
    assert "if" not in methods


def test_process_file_content_python():
    code = "def make_response(): pass"
    words = process_file_content(code, "python")
    assert "make" in words and "response" in words

def test_process_file_content_java():
    code = "public boolean retainAll() { return true; }"
    words = process_file_content(code, "java")
    assert "retain" in words and "all" in words
