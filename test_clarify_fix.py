"""
测试 lesson_session.py 中的数据清洗功能
"""
from app.ai.langchain.utils.lesson_session import _sanitize_clarify_data, merge_clarify
from app.ai.langchain.schema.lesson import LessonClarifySchema


def test_sanitize_data():
    """测试数据清洗函数"""
    
    print("=" * 50)
    print("测试数据清洗函数")
    print("=" * 50)
    
    # 测试用例 1: 带单位的字符串
    test_data_1 = {
        "class_duration": "2小时",
        "lesson_count": "2课时",
        "subject": "数学"
    }
    
    result_1 = _sanitize_clarify_data(test_data_1)
    print("\n测试用例 1: 带单位的字符串")
    print(f"输入: {test_data_1}")
    print(f"输出: {result_1}")
    print(f"class_duration 类型: {type(result_1['class_duration'])}, 值: {result_1['class_duration']}")
    print(f"lesson_count 类型: {type(result_1['lesson_count'])}, 值: {result_1['lesson_count']}")
    
    assert result_1["class_duration"] == 120, f"期望 120, 实际 {result_1['class_duration']}"
    assert result_1["lesson_count"] == 2, f"期望 2, 实际 {result_1['lesson_count']}"
    print("✅ 测试通过")
    
    # 测试用例 2: 分钟单位
    test_data_2 = {
        "class_duration": "45分钟",
        "lesson_count": "3课时"
    }
    
    result_2 = _sanitize_clarify_data(test_data_2)
    print("\n测试用例 2: 分钟单位")
    print(f"输入: {test_data_2}")
    print(f"输出: {result_2}")
    
    assert result_2["class_duration"] == 45, f"期望 45, 实际 {result_2['class_duration']}"
    assert result_2["lesson_count"] == 3, f"期望 3, 实际 {result_2['lesson_count']}"
    print("✅ 测试通过")
    
    # 测试用例 3: 已经是数字
    test_data_3 = {
        "class_duration": 45,
        "lesson_count": 2
    }
    
    result_3 = _sanitize_clarify_data(test_data_3)
    print("\n测试用例 3: 已经是数字")
    print(f"输入: {test_data_3}")
    print(f"输出: {result_3}")
    
    assert result_3["class_duration"] == 45
    assert result_3["lesson_count"] == 2
    print("✅ 测试通过")
    
    # 测试用例 4: 纯数字字符串
    test_data_4 = {
        "class_duration": "40",
        "lesson_count": "1"
    }
    
    result_4 = _sanitize_clarify_data(test_data_4)
    print("\n测试用例 4: 纯数字字符串")
    print(f"输入: {test_data_4}")
    print(f"输出: {result_4}")
    
    assert result_4["class_duration"] == 40
    assert result_4["lesson_count"] == 1
    print("✅ 测试通过")


def test_merge_clarify():
    """测试 merge_clarify 函数(包含数据清洗)"""
    
    print("\n" + "=" * 50)
    print("测试 merge_clarify 函数")
    print("=" * 50)
    
    # 创建一个初始的 clarify 对象
    existing = LessonClarifySchema(
        subject="数学",
        grade="高一"
    )
    
    # 模拟 LLM 返回的带单位的数据
    new_data = {
        "class_duration": "2小时",
        "lesson_count": "2课时",
        "lesson_title": "函数的概念"
    }
    
    print(f"\n原始数据: {existing.model_dump()}")
    print(f"新数据: {new_data}")
    
    # 这应该不会抛出 ValidationError
    try:
        result = merge_clarify(existing, new_data)
        print(f"\n合并后结果: {result.model_dump()}")
        
        assert result.class_duration == 120, f"期望 120, 实际 {result.class_duration}"
        assert result.lesson_count == 2, f"期望 2, 实际 {result.lesson_count}"
        assert result.subject == "数学"
        assert result.grade == "高一"
        assert result.lesson_title == "函数的概念"
        
        print("\n✅ merge_clarify 测试通过 - 成功将带单位的字符串转换为数字!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    test_sanitize_data()
    test_merge_clarify()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过!")
    print("=" * 50)
