# 测试脚本目录

包含所有爬虫功能的测试脚本。

## 运行测试

```bash
cd D:\LLMProject\dtcg_judger
python scraper_skill/tests/test_scrapers.py
```

## 测试内容

1. **配置加载测试** - 验证配置文件正确加载
2. **模块导入测试** - 验证所有模块可正常导入
3. **实例化测试** - 验证爬虫类可正常实例化
4. **数据加载测试** - 验证现有数据文件可正常加载
5. **数据验证测试** - 验证数据验证功能正常工作

## 测试结果

所有测试通过后显示：
```
🎉 所有测试通过！
```

## 添加新测试

在 `tests/` 目录下创建新的测试文件，命名格式：`test_*.py`

示例：
```python
def test_my_feature():
    """测试我的功能"""
    from src.my_module import MyClass
    
    obj = MyClass()
    result = obj.do_something()
    
    assert result is not None
    print("✓ 测试通过")
```
