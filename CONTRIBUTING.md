# Development Guidelines

## PyQt6 Usage Guidelines

When developing UI components with PyQt, please ensure the following:

1. **Use PyQt6 Specific Features**:
   - Always use PyQt6 specific classes and enumerations. For example, use `Qt.Orientation.Horizontal` instead of `Qt.Horizontal`.

2. **Avoid PyQt5 Methods**:
   - Do not use methods or properties that are specific to PyQt5. Ensure compatibility with PyQt6.

3. **Consistent API Usage**:
   - Follow the PyQt6 API documentation for consistent and up-to-date usage of classes and methods.

By adhering to these guidelines, we ensure that our application remains compatible with the latest PyQt6 features and standards.


## UI Initialization Guidelines

When developing UI components, especially for methods like `init_ui`, please follow these guidelines:

1. **Separation of Concerns**: 
   - Break down the `init_ui` method into smaller, more manageable methods. For example, separate the initialization of different UI components into distinct methods like `init_top_layout` and `init_bottom_layout`.

2. **Modular Design**:
   - Each method should handle a specific part of the UI. This makes the code more readable and easier to maintain.

3. **Event Handling**:
   - Connect UI events (e.g., button clicks) to their respective handler methods within the initialization methods.

4. **Layout Management**:
   - Use layout managers (e.g., `QVBoxLayout`, `QHBoxLayout`) to organize widgets within the UI.

5. **Code Readability**:
   - Ensure that the code is well-commented and follows consistent naming conventions.

By adhering to these guidelines, we ensure that our UI components are well-structured and maintainable.

