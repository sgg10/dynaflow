# API Reference

Welcome to the **DynaFlow** API Reference! This section provides detailed technical documentation for the core components of the library. Whether you're integrating `DynaFlow` into your project or extending its functionality, this guide will help you navigate its API.

---

## **Table of Contents**

1. **[States](states.md)**
   - Overview of state types: Task, Choice, Map, Parallel, Wait, Succeed, Fail, and Pass.
   - Configuration parameters and usage.
   - Input and output processing details.

2. **[Executor](executor.md)**
   - Understanding the `DynaFlow` class.
   - Methods for executing flows.
   - Customizing function resolution and error handling.

3. **[Utilities](utilities.md)**
   - Helpers for data manipulation and validation.
   - JSONPath utilities for transforming input and output.
   - Tools for validating flow definitions.

4. **[Exceptions](exceptions.md)**
   - Custom exception classes used within the library.
   - Handling and extending error management in states and flows.

---

## **Key Concepts**

### **States**
`DynaFlow` uses state-based flow execution. Each state performs a specific operation and transitions to the next based on the flow definition. States are categorized as follows:
- **Task**: Executes a function.
- **Choice**: Implements conditional logic.
- **Parallel**: Runs multiple branches.
- **Map**: Iterates over items and processes them individually.
- Other auxiliary states like `Wait`, `Succeed`, `Fail`, and `Pass`.

### **DynaFlow**
The `DynaFlow` class orchestrates the execution of states based on a JSON-defined flow. It handles:
- Initialization and validation of the flow.
- State execution and error handling.
- Logging and integration with external function registries.

### **Utilities**
Utilities provide essential support for:
- Extracting and transforming JSON data.
- Applying advanced flow controls like retry and catch.
- Validating flow definitions against the expected schema.

---

## **How to Use the API Reference**

This section is divided into smaller modules for easier navigation. Begin with the **[States](states.md)** section to understand individual components, and proceed to **[Executor](executor.md)** to see how they integrate.

Looking for practical examples? Check out the **[Usage Guide](../usage/index.md)** for step-by-step tutorials and sample flows.

---

## **Next Steps**

- **[Dive into States →](./states.md)** Explore the building blocks of a flow and learn how to configure each state.
- **[Understand DynaFlow →](./executor.md)** Learn how the executor manages and runs your flow definitions.
- **[See Utilities →](./utilities.md)** Enhance your flows with powerful data manipulation tools.
