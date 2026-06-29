# \<Name of Project\>

# DETAIL DESIGN DOCUMENT

**Project Code:** \<Code of the project\>  
**Document Code:** \<82e-BM/DE/HDCV/FSOFT\> – DD – v\<1.5\>

---

## RECORD OF CHANGE

| No | Effective Date | Version | Change Description | Reason | Reviewer | Approver |
|----|----------------|---------|-------------------|---------|----------|----------|
| 1 | 15/Nov/2004 | 1.0 | Issued | IP | | |
| 2 | 15/Oct/2005 | 1.1 | Change logo | BOM decision | | |
| 3 | 10/Dec/2005 | 1.2 | Page 8: Section 2: Add data model | 20-PIP2005 | | |
| 4 | 8/Mar/2006 | 1.3 | Add 5. OTHER CONSIDERATIONS | For CMMI 5 | | |
| 5 | 10/Oct/2013 | 1.4 | - 1.3 Standards and Conventions => Add new<br>- 2.3 Store Procedure => Add new | Update to fit the actual | | |
| 6 | 20/Jun/2016 | 1.5 | Re-format template to make consistent in QDS | To fix comments of QAI from CMMi5-v1.3 assessment project (Gap Analysis phase) | | HyTQ |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
   - 1.1 [Purpose](#11-purpose)
   - 1.2 [Definitions, Acronyms and Abbreviations](#12-definitions-acronyms-and-abbreviations)
   - 1.3 [Standards and Conventions](#13-standards-and-conventions)
   - 1.4 [References](#14-references)
   - 1.5 [Overview](#15-overview)
2. [Common Package and Mechanism](#2-common-package-and-mechanism)
   - 2.1 [Common Package](#21-common-package)
   - 2.2 [Error, Exception Handling](#22-error-exception-handling)
   - 2.3 [Log, Trace and Debug](#23-log-trace-and-debug)
   - 2.4 [Performance Optimizing Mechanism](#24-performance-optimizing-mechanism)
   - 2.5 [Multilingual Processing](#25-multilingual-processing)
3. [Diagrams](#3-diagrams)
4. [Packages](#4-packages)
   - 4.1 [XXX Package](#41-xxx-package)
   - 4.2 [Implementation](#42-implementation)
5. [Database](#5-database)
   - 5.1 [ERDs](#51-erds)
   - 5.2 [XXX Table](#52-xxx-table)
   - 5.3 [Store Procedure](#53-store-procedure)
6. [File Design](#6-file-design)
   - 6.1 [File List](#61-file-list)
   - 6.2 [XXX File](#62-xxx-file)
7. [Code Design](#7-code-design)
8. [Edge Case Definition (エッジケース定義)](#8-edge-case-definition-エッジケース定義)
   - 8.1 [Abnormal Value Definition (異常値定義)](#81-abnormal-value-definition-異常値定義)
   - 8.2 [Boundary Value Definition (境界値定義)](#82-boundary-value-definition-境界値定義)
   - 8.3 [Exception Handling Definition (例外処理定義)](#83-exception-handling-definition-例外処理定義)
9. [Other Considerations](#9-other-considerations)
10. [Appendix](#10-appendix)

---

## RECORD OF CHANGE (of the project)

| No | Effective Date | Version | Change Description | Reason | Reviewer | Approver |
|----|----------------|---------|-------------------|---------|----------|----------|
| 1 | \<dd/mm/yyyy\> | \<x.y\> | \<Describe the change of document in detail\> | \<Describe reason for the change\> | | |

---

## 1. Introduction

### 1.1 Purpose

\<This part will give general description of the document including:
- Purpose of document.
- What are contained in the document.
- Reader of document.
- Other description about scope of document, limitation,...\>

**Example:**

XXX detail design document contains descriptions of all classes, data structures, and implementation details of the YYYY system including:
- Class diagrams that describe the static relation of all classes in the system
- Dynamic diagrams such as collaboration diagram, sequence diagram, activities diagram
- Description of class in detail
- Database design including ERDs, table definitions, and stored procedures
- File design specifications
- Common mechanism in implementing is also defined in this document

Developer and tester will base on this design to implement classes, database objects, and conduct unit testing.

### 1.2 Definitions, Acronyms and Abbreviations

| Abbreviations | Description | Comment |
|--------------|-------------|---------|
| TBD | To be decided | It means "not decided yet" |
| Windows DDK | Windows Device Development Kit | Development Kit from Microsoft to develop device driver for Windows 2000/XP/Server 2003 OS |
| ESC/P | Escape Printing command | A page description language used on Epson ink jet printers |

### 1.3 Standards and Conventions

\<Define all the conventions to write detail design:
- Design standards: what is the tool to design?
- Documentation standards: Font, color, style – formal style…
- Naming conventions: naming for package, class, variable, method, table, column… (Take from the coding convention document)\>

### 1.4 References

\<List all the reference document such as: other document of the system, or the technical article,...\>

| Document Number | Title |
|----------------|-------|
| \<01\> | \<Software Requirements Specification\> |
| \<02\> | \<System Architecture Document\> |
| | |

### 1.5 Overview

\<General overview of the detail design such as what is the structure of the document\>

---

## 2. Common Package and Mechanism

### 2.1 Common Package

#### 2.1.1 Class Diagram

\<Class diagram\>

| No | Class Name | Description |
|----|-----------|-------------|
| 01 | \<Name of class\> | \<Brief description about class ex. One sentence to tell what the class is for, what does it encapsulate\> |
| 02 | | |
| 03 | | |

#### 2.1.2 XXX Class

\<Class description\>

**Attributes**

| No | Attribute | Type | Default | Note | Description |
|----|-----------|------|---------|------|-------------|
| 01 | \<Attribute name\> | int | | Public/ Static | \<Description of attribute\> |
| 02 | | | | | |

**Methods**

| No | Method | Description |
|----|--------|-------------|
| 01 | \<method name\> | \<brief description of method. can be one sentence tell what the method does\> |
| 02 | | |
| 03 | | |

**xxxx Method**

\<Method declaration\>

\<method description, it must be compliance with the brief description in the upper class list\>

**Parameters & Return**

| No | Parameter | Type | In/out | Default | Description |
|----|-----------|------|--------|---------|-------------|
| 01 | parameter name | int | | | \<Description of parameter, special criteria such as boundary should be stated\> |
| 02 | | | | | |
| 03 | \<return\> | | | | |

**Implementation**

\<How to implement the method, it can be in pseudo code or activity diagram or just words\>

### 2.2 Error, Exception Handling

#### 2.2.1 Class Diagram

\< Describe class like in common package\>

#### 2.2.2 Usage Mechanism

\<Common mechanism of exception handling\>

### 2.3 Log, Trace and Debug

\<Describe logging mechanism, trace and debug strategies\>

### 2.4 Performance Optimizing Mechanism

\<Describe performance optimization approaches\>

### 2.5 Multilingual Processing

\<Describe multilingual support implementation\>

---

## 3. Diagrams

\<Describe diagrams in system such as collaboration diagram, sequence diagram, activities diagram and state chart for some functionalities of the system\>

**Example: Customer management**

- **Add customer**

![Figure 1 Add Customer sequence diagram]

- **Update customer**

\<Include relevant sequence/collaboration diagrams\>

---

## 4. Packages

| No | Package | Language | Description |
|----|---------|----------|-------------|
| 01 | \<package name\> | C++, Java | \<brief description of package; can be one sentence tell what the method does\> |
| 02 | | | |
| 03 | | | |

### 4.1 XXX Package

#### 4.1.1 Class Diagram

\<Class diagram figure\>

| No | Class Name | Description |
|----|-----------|-------------|
| 01 | \<Name of class\> | \<Brief description about class ex. One sentence to tell what the class is for, what does it encapsulate\> |
| 02 | | |
| 03 | | |

#### 4.1.2 External Interface

\<Describe the external interface of the package (exported classes, methods).\>

#### 4.1.3 XXX Class

\<Class description\>

**Attributes**

| No | Attribute | Type | Default | Note | Description |
|----|-----------|------|---------|------|-------------|
| 01 | \<Attribute name\> | int | | Public/ Static | \<Description of attribute\> |
| 02 | | | | | |
| 03 | | | | | |

**Methods**

| No | Method | Description |
|----|--------|-------------|
| 01 | \<method name\> | \<brief description of method. can be one sentence tell what the method does\> |
| 02 | | |
| 03 | | |

**xxxx Method**

\<Method declaration\>

\<method description, it must be compliance with the brief description in the upper class list\>

**Parameters & Return**

| No | Parameter | Type | in/out | Default | Description |
|----|-----------|------|--------|---------|-------------|
| 01 | \<parameter name\> | int | | | \<Description of parameter, the special criteria such as boundary should be stated\> |
| 02 | | | | | |
| 03 | \<return\> | | | | |

### 4.2 Implementation

\<How to implement the method, it can be in pseudo code or activity diagram or just words\>

......

---

## 5. Database

### 5.1 ERDs

\<Include Entity Relationship Diagrams showing the logical and/or physical data model\>

### 5.2 XXX Table

\<Table description\>

**Table Structure**

| No | Column Name | Data Type | Length | Null | Default | PK | FK | Description |
|----|------------|-----------|--------|------|---------|----|----|-------------|
| 01 | \<column name\> | \<VARCHAR\> | \<50\> | \<N\> | | \<Y\> | | \<Description of column\> |
| 02 | | | | | | | | |
| 03 | | | | | | | | |

**Indexes**

| No | Index Name | Type | Columns | Description |
|----|-----------|------|---------|-------------|
| 01 | \<index name\> | \<Unique/Non-unique\> | \<column list\> | \<Description\> |
| 02 | | | | |

**Constraints**

\<Describe any constraints, triggers, or business rules associated with the table\>

### 5.3 Store Procedure

#### 5.3.1 XXX Stored Procedure

**Purpose**

\<Describe the purpose and functionality of the stored procedure\>

**Parameters**

| No | Parameter Name | Data Type | In/Out | Default | Description |
|----|---------------|-----------|--------|---------|-------------|
| 01 | \<@parameter_name\> | \<VARCHAR(50)\> | \<IN\> | | \<Description\> |
| 02 | | | | | |
| 03 | \<@return_value\> | \<INT\> | \<OUT\> | | \<Description\> |

**Logic**

\<Describe the logic flow of the stored procedure\>

**Example**

```sql
CREATE PROCEDURE [dbo].[XXX_ProcedureName]
    @param1 VARCHAR(50),
    @param2 INT
AS
BEGIN
    -- Procedure logic here
END
```

---

## 6. File Design

### 6.1 File List

| No | File Name | Format | Description | Location |
|----|-----------|--------|-------------|----------|
| 01 | \<file name\> | \<CSV/XML/JSON\> | \<Brief description\> | \<Path or location\> |
| 02 | | | | |
| 03 | | | | |

### 6.2 XXX File

**File Description**

\<Describe the purpose and usage of the file\>

**File Format**

\<Specify the file format (CSV, XML, JSON, binary, etc.)\>

**File Structure**

| No | Field Name | Data Type | Length | Format | Description |
|----|-----------|-----------|--------|--------|-------------|
| 01 | \<field name\> | \<String\> | \<50\> | | \<Description\> |
| 02 | | | | | |
| 03 | | | | | |

**Sample Data**

\<Provide sample file content or record examples\>

**Processing Rules**

\<Describe any validation rules, processing logic, or constraints for the file\>

---

## 7. Code Design

\<Describe code-level design elements such as:
- Code organization and structure
- Key algorithms or complex logic
- Design patterns used
- Configuration management
- Constants and enumerations
- Utility functions\>

---

## 8. Edge Case Definition (エッジケース定義)

\<Define all edge cases per feature/function, covering abnormal inputs, boundary values, and runtime exceptions. Each subsection below should be filled per functional requirement ID (BD ID).\

### 8.1 Abnormal Value Definition (異常値定義)

\<Define invalid or unexpected inputs and the expected system behavior for each.\>

| Edge Case ID | BD ID | Input Item | Abnormal Condition | Expected System Behavior | Error Code | Log Level | User Message |
|--------------|-------|-----------|-------------------|-------------------------|------------|-----------|-------------|
| EC-001 | \<F-01\> | \<Email\> | \<Null\> | \<Reject request\> | \<ERR-001\> | \<WARN\> | \<Email is required\> |
| EC-002 | | | | | | | |
| EC-003 | | | | | | | |

### 8.2 Boundary Value Definition (境界値定義)

\<Define minimum, maximum, and limit cases for input fields.\>

| Boundary ID | BD ID | Field Name | Min | Max | Test Value | Expected Result |
|-------------|-------|-----------|-----|-----|------------|----------------|
| BV-001 | \<F-01\> | \<Username\> | \<1\> | \<50\> | \<0\> | \<Error\> |
| BV-002 | | | | | \<1\> | \<OK\> |
| BV-003 | | | | | \<50\> | \<OK\> |
| BV-004 | | | | | \<51\> | \<Error\> |

### 8.3 Exception Handling Definition (例外処理定義)

\<Define system-level or runtime exceptions, including transaction handling and retry policy.\>

| Exception ID | Scenario | Trigger Condition | System Behavior | Transaction Handling | Retry Policy | Log Level | User Impact |
|-------------|----------|------------------|----------------|--------------------|--------------|-----------|------------|
| EX-001 | \<DB connection failure\> | \<DB unavailable\> | \<Abort process\> | \<Rollback\> | \<No retry\> | \<ERROR\> | \<Show system error message\> |
| EX-002 | \<Duplicate data\> | \<Unique constraint violation\> | \<Reject insert\> | \<No rollback\> | \<No retry\> | \<WARN\> | \<Show duplication message\> |
| EX-003 | | | | | | | |

---

## 9. Other Considerations

\<This section provides a description of other design elements that were considered as alternatives in selection process for the above design, i.e. a brief explanation of advantages and disadvantages of the selected package relationships, class implementation, database structure, and/or file formats in comparison with others. It should be a clear answer to the question why the above design is selected for this system, not the others.\>

---

## 10. Appendix

\<Include any additional supporting information such as:
- Glossary
- Additional diagrams
- Code samples
- Reference materials
- Tools and technologies used\>
