import pytest
from src.utils.text_refiner import TextRefiner

def test_jargon_mapping():
    refiner = TextRefiner()
    input_text = "i am working with python and javascript on aws"
    expected = "I am working with Python and JavaScript on AWS."
    assert refiner.refine(input_text) == expected

def test_sentence_capitalization():
    refiner = TextRefiner()
    input_text = "hello world. this is a test"
    expected = "Hello world. This is a test."
    assert refiner.refine(input_text) == expected

def test_spacing_fix():
    refiner = TextRefiner()
    input_text = "this  has   too   many spaces . and no space after punctuation.see?"
    # _fix_spacing handles multiple spaces, space before punct, and space after punct
    # refined = "This has too many spaces. And no space after punctuation. See?"
    # wait, the order is Mapping -> Spacing -> Capitalization -> Punctuation -> Contractions
    # Let's check _fix_spacing implementation:
    # 1. re.sub(r"\s+", " ", text) -> "this has too many spaces . and no space after punctuation.see?"
    # 2. re.sub(r"\s+([.,!?;:])", r"\1", text) -> "this has too many spaces. and no space after punctuation.see?"
    # 3. re.sub(r"([.,!?;:])([A-Za-z])", r"\1 \2", text) -> "this has too many spaces. and no space after punctuation. see?"
    # then _capitalize_sentences -> "This has too many spaces. And no space after punctuation. See?"
    # then _add_ending_punctuation -> "This has too many spaces. And no space after punctuation. See?"
    expected = "This has too many spaces. And no space after punctuation. See?"
    assert refiner.refine(input_text) == expected

def test_contractions():
    refiner = TextRefiner()
    input_text = "im going to the store because i dont have milk"
    expected = "I'm going to the store because i don't have milk."
    assert refiner.refine(input_text) == expected

def test_empty_input():
    refiner = TextRefiner()
    assert refiner.refine("") == ""
    assert refiner.refine("   ") == ""
