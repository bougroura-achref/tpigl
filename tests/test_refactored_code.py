import pytest
from tests.sample_buggy_code import calculator, data_processor, string_utils

# Calculator Tests
def test_calculator_functions():
    assert calculator.add(1, 2) == 3
    assert calculator.subtract(5, 3) == 2
    assert calculator.multiply(2, 3) == 6
    assert calculator.divide(10, 2) == 5.0
    # Division by zero should raise ZeroDivisionError
    with pytest.raises(ZeroDivisionError):
        calculator.divide(5, 0)

def test_calculator_class():
    calc = calculator.Calculator()
    calc.set_values(10, 5)
    assert calc.add_values() == 15
    assert calc.subtract_values() == 5

# String Utils Tests
def test_string_utils():
    assert string_utils.reverse_string("abc") == "cba"
    assert string_utils.count_vowels("Hello") == 2
    assert string_utils.is_palindrome("Madam")
    assert not string_utils.is_palindrome("Hello")
    assert string_utils.capitalize_words("hello world") == "Hello World"
    assert string_utils.remove_duplicates("hello") == "helo"

def test_string_processor():
    sp = string_utils.StringProcessor("  test  ")
    sp.process()
    assert sp.text == "test"
    stats = sp.get_stats()
    assert stats['length'] == 4
    assert sp.transform("upper") == "TEST"

# Data Processor Tests
def test_data_processor_logic():
    items = [10, 60, 110]
    processed = data_processor.process_items(items)
    # 10 <= 50 -> 10
    # 60 > 50 -> 60*0.75 = 45
    # 110 > 100 -> 110*0.5 = 55
    assert processed == [10, 45.0, 55.0]

def test_data_processor_class(tmp_path):
    d_file = tmp_path / "data.json"
    o_file = tmp_path / "output.json"
    
    import json
    with open(d_file, 'w') as f:
        json.dump({"a": 10, "b": 60, "c": 110}, f)
        
    dp = data_processor.DataProcessor()
    assert dp.load(str(d_file))
    result = dp.process()
    assert 45.0 in result
    assert dp.save(str(o_file))
    
    with open(o_file, 'r') as f:
        data = json.load(f)
        assert data['a'] == 10
