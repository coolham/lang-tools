## Logger类更新

### 新功能
- 当`fixed_filename=True`时，支持生成固定文件名的日志文件，不添加日期和时间戳。每次运行时覆盖旧的日志文件，方便AI工具查找问题。
- 当`fixed_filename=False`时，每次执行生成一个新的日志文件，日志文件名称带有日期和时间。

### 使用方法
- 在`main`中使用`Logger.set_defaults`设置默认日志参数。
- 在其他模块中使用`Logger.create_logger`创建日志实例，只需提供`name`参数，其余参数将使用默认值。
- 支持多个模块共享同一个日志文件或使用不同的日志文件。
