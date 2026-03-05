# UI Layout Standard - Enterprise Professional Guidelines

## Overview
This document defines the **mandatory** layout rules for all UI components in the Bulk Email Sender application. These rules ensure consistent spacing, alignment, and professional appearance across all tabs and dialogs.

## Core Principle
**Spacing and margins are controlled ONLY by Qt layouts, NEVER by CSS margins on widgets.**

---

## 🧩 LAYOUT RULES (MANDATORY)

### 1️⃣ Every Tab / Dialog - Main Layout

```python
main_layout = QVBoxLayout()
main_layout.setContentsMargins(12, 12, 12, 12)  # left, top, right, bottom
main_layout.setSpacing(12)  # space between groups
```

**Purpose:**
- 12px margins around the entire tab/dialog
- 12px spacing between major sections (QGroupBox)
- Consistent "breathing room"

**Example:**
```python
def init_ui(self):
    layout = QVBoxLayout()
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(12)
    
    layout.addWidget(group1)
    layout.addWidget(group2)
    
    self.setLayout(layout)
```

---

### 2️⃣ Every Section (QGroupBox) - Group Layout

```python
group_layout = QVBoxLayout()
group_layout.setContentsMargins(12, 10, 12, 12)  # left, top, right, bottom
group_layout.setSpacing(10)  # space between elements inside group
group.setLayout(group_layout)
```

**Purpose:**
- 12px left/right margins (align with main layout)
- 10px top margin (slightly less for visual balance)
- 12px bottom margin (consistent with main)
- 10px spacing between internal elements

**Example:**
```python
def create_my_group(self) -> QGroupBox:
    group = QGroupBox("My Section")
    layout = QVBoxLayout()
    layout.setContentsMargins(12, 10, 12, 12)
    layout.setSpacing(10)
    
    layout.addWidget(widget1)
    layout.addWidget(widget2)
    
    group.setLayout(layout)
    return group
```

---

### 3️⃣ Every Form (Label + Field) - ONLY QFormLayout

```python
form = QFormLayout()
form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
form.setHorizontalSpacing(12)  # space between label and field
form.setVerticalSpacing(8)     # space between rows
```

**Purpose:**
- Right-aligned labels, vertically centered
- Fields expand to fill available width
- 12px between label and field (comfortable reading)
- 8px between rows (compact but not cramped)

**Example:**
```python
def create_form_section(self):
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    form.setHorizontalSpacing(12)
    form.setVerticalSpacing(8)
    
    # Add rows...
    return form
```

---

### 4️⃣ Labels - ALWAYS QLabel Objects (NEVER Strings)

```python
# ✅ CORRECT
label = QLabel("Email:*")
label.setMinimumWidth(140)  # Consistent label column width
form.addRow(label, widget)

# ❌ WRONG
form.addRow("Email:*", widget)  # No control over label properties
```

**Purpose:**
- Control label width for alignment
- Consistent label column across all forms
- Ability to style labels individually

**Label Width Guidelines:**
- English labels: `140px` minimum
- Greek labels: `150px` minimum (wider characters)

---

### 5️⃣ Input Widgets - Size Policy (NO Fixed Heights)

```python
widget = QLineEdit()
widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
# NO setFixedHeight() unless absolutely necessary
```

**Purpose:**
- Widgets expand horizontally to fill available space
- Widgets maintain natural height (from theme + padding)
- Responsive to window resizing

**❌ FORBIDDEN:**
- CSS `margin:` in stylesheets
- `setFixedHeight()` (except for specific cases like combo boxes)

---

### 6️⃣ Theme / CSS - What NOT to Include

**❌ FORBIDDEN in theme.py:**
```css
/* DO NOT USE */
QLineEdit {
    margin: 4px;
    margin-top: 6px;
}
```

**✅ ALLOWED in theme.py:**
```css
/* These are OK */
QLineEdit {
    padding: 8px;
    min-height: 24px;
    border: 1px solid #ccc;
    border-radius: 4px;
}
```

**Purpose:**
- Layouts control all spacing and margins
- Theme controls only visual appearance (colors, borders, padding)
- No conflicts between CSS margins and layout spacing

---

## 🧠 What This Standard Fixes

### ✅ Benefits

1. **Consistent Spacing**
   - Same gaps between label ↔ field everywhere
   - Same margins around all groups
   - Predictable, professional appearance

2. **Visual Breathing Room**
   - All QGroupBox sections have proper padding
   - Nothing feels cramped or "stuck together"
   - Clean, organized interface

3. **Alignment Perfection**
   - All labels align at the same position
   - All fields start at the same horizontal position
   - Professional form layout

4. **Cross-Tab Consistency**
   - Recipients Tab looks like Company Settings Tab
   - SMTP Tab looks like Template Tab
   - Unified design language

5. **Enterprise Professional**
   - Looks like a commercial product
   - Not a "hobby project"
   - Inspires confidence

---

## 📋 Implementation Checklist

### For Each Tab (Recipients, SMTP, Company Settings, Template, Send)

- [ ] Main layout has `setContentsMargins(12, 12, 12, 12)`
- [ ] Main layout has `setSpacing(12)`
- [ ] Each QGroupBox layout has `setContentsMargins(12, 10, 12, 12)`
- [ ] Each QGroupBox layout has `setSpacing(10)`
- [ ] All forms use QFormLayout (not QVBoxLayout/QHBoxLayout)
- [ ] All QFormLayout have proper configuration (4 settings)
- [ ] All labels are QLabel objects with `setMinimumWidth(140)`
- [ ] All input widgets have `setSizePolicy(Expanding, Fixed)`
- [ ] No CSS margins on input widgets in theme.py

### For Each Dialog (AddEmailManuallyDialog, SelectByCriteriaDialog, etc.)

- [ ] Dialog layout has `setContentsMargins(12, 12, 12, 12)`
- [ ] Dialog layout has `setSpacing(12)`
- [ ] Forms use QFormLayout with proper configuration
- [ ] Labels are QLabel objects with minimum width
- [ ] Input widgets have proper size policy

---

## 🎯 Standard Values Reference

| Element | Property | Value | Purpose |
|---------|----------|-------|---------|
| Main Layout | Contents Margins | `12, 12, 12, 12` | Outer padding |
| Main Layout | Spacing | `12` | Between groups |
| Group Layout | Contents Margins | `12, 10, 12, 12` | Inner padding |
| Group Layout | Spacing | `10` | Between elements |
| Form Layout | Horizontal Spacing | `12` | Label to field |
| Form Layout | Vertical Spacing | `8` | Between rows |
| Label | Minimum Width | `140` (EN) / `150` (GR) | Alignment |
| Widget | Size Policy | `Expanding, Fixed` | Responsive |

---

## 🔧 Code Templates

### Tab Template
```python
class MyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Add groups
        layout.addWidget(self.create_section1())
        layout.addWidget(self.create_section2())
        
        self.setLayout(layout)
    
    def create_section1(self) -> QGroupBox:
        group = QGroupBox("Section 1")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(12, 10, 12, 12)
        group_layout.setSpacing(10)
        
        # Add form
        form = self.create_form()
        group_layout.addLayout(form)
        
        group.setLayout(group_layout)
        return group
    
    def create_form(self) -> QFormLayout:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        
        # Add rows
        label = QLabel("Field Name:*")
        label.setMinimumWidth(140)
        widget = QLineEdit()
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form.addRow(label, widget)
        
        return form
```

### Dialog Template
```python
class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Add form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        
        label = QLabel("Field:")
        label.setMinimumWidth(140)
        widget = QLineEdit()
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form.addRow(label, widget)
        
        layout.addLayout(form)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
```

---

## 🚫 Common Mistakes to Avoid

### ❌ Don't Do This
```python
# Wrong: String labels
form.addRow("Email:", widget)

# Wrong: CSS margins
QLineEdit { margin: 4px; }

# Wrong: Fixed heights everywhere
widget.setFixedHeight(30)

# Wrong: No layout configuration
form = QFormLayout()
form.addRow(label, widget)  # Missing configuration!

# Wrong: QVBoxLayout for forms
layout = QVBoxLayout()
layout.addWidget(QLabel("Email:"))
layout.addWidget(QLineEdit())
```

### ✅ Do This Instead
```python
# Correct: QLabel objects
label = QLabel("Email:")
label.setMinimumWidth(140)
form.addRow(label, widget)

# Correct: No CSS margins
QLineEdit { padding: 8px; }

# Correct: Size policy, not fixed height
widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

# Correct: Full form configuration
form = QFormLayout()
form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
form.setHorizontalSpacing(12)
form.setVerticalSpacing(8)

# Correct: QFormLayout for forms
form = QFormLayout()
label = QLabel("Email:")
label.setMinimumWidth(140)
widget = QLineEdit()
widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
form.addRow(label, widget)
```

---

## 📊 Visual Comparison

### Before (Inconsistent)
```
┌─ Section ──────────────────┐
│Email:[input cramped]       │  ← No margins, cramped
│Name:[input]                │  ← Inconsistent spacing
│  [Button]                  │  ← Wrong alignment
└────────────────────────────┘
```

### After (Standard Applied)
```
┌─ Section ──────────────────────────────┐
│                                        │  ← 10px top margin
│       Email:*  [======= input =======] │  ← 12px label-field gap
│                                        │  ← 8px row spacing
│         Name:  [======= input =======] │  ← Aligned labels
│                                        │
│                        [Button]        │  ← Right-aligned
│                                        │  ← 12px bottom margin
└────────────────────────────────────────┘
```

---

## 🎓 Design Philosophy

### Why These Specific Values?

**12px Main Margins:**
- Standard in professional applications
- Comfortable breathing room
- Not too tight, not too loose

**12px Main Spacing:**
- Clear separation between major sections
- Visual hierarchy
- Easy to scan

**10px Group Spacing:**
- Slightly tighter than main spacing
- Elements feel grouped together
- Still comfortable

**12px Horizontal Spacing (Form):**
- Comfortable reading distance
- Labels don't touch fields
- Professional appearance

**8px Vertical Spacing (Form):**
- Compact but not cramped
- More rows visible without scrolling
- Standard form density

**140px Label Width:**
- Accommodates most English labels
- Creates clean alignment column
- Professional form layout

---

## 🔄 Migration Strategy

### Phase 1: Theme Cleanup
1. Remove all `margin:` declarations from input widgets in theme.py
2. Keep only `padding`, `min-height`, `border`, `border-radius`

### Phase 2: Tab-by-Tab Update
For each tab:
1. Update main layout margins and spacing
2. Update all QGroupBox layouts
3. Convert all forms to QFormLayout with proper configuration
4. Convert all string labels to QLabel objects
5. Add size policies to all input widgets

### Phase 3: Dialog Update
For each dialog:
1. Update dialog layout margins and spacing
2. Update all forms to QFormLayout
3. Convert labels to QLabel objects
4. Add size policies

### Phase 4: Verification
1. Visual inspection of all tabs
2. Check spacing consistency
3. Verify alignment
4. Test window resizing

---

## 📝 Summary

**TL;DR for Implementation:**

1. **Margins/Spacing**: Only from Qt layouts, never CSS
2. **Forms**: Always QFormLayout with 4-line configuration
3. **Labels**: Always QLabel objects with `setMinimumWidth(140)`
4. **Widgets**: Always `setSizePolicy(Expanding, Fixed)`
5. **Theme**: No `margin:` on input widgets

**Goal:** Clean spacing, perfect alignment, professional appearance across the entire application.

---

## 🎯 Success Criteria

When this standard is fully applied:

- ✅ All tabs have identical spacing and margins
- ✅ All forms have perfectly aligned labels
- ✅ All groups have comfortable breathing room
- ✅ Nothing feels cramped or "stuck together"
- ✅ The application looks enterprise-professional
- ✅ Users feel confident in the software quality

---

**This is the definitive layout standard for the Bulk Email Sender application. All UI code must follow these rules.**
