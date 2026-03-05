# Dark Theme Guide - Οδηγός Σκούρου Θέματος

## Τι Άλλαξε / What Changed

### Πριν (Before) ❌
- Άσπρα backgrounds με άσπρο κείμενο (αδιάβαστο)
- White backgrounds with white text (unreadable)
- Δυσκολία στην ανάγνωση με Windows dark mode
- Difficulty reading with Windows dark mode

### Τώρα (Now) ✅
- Σκούρα backgrounds με ανοιχτό κείμενο (ευανάγνωστο)
- Dark backgrounds with light text (readable)
- Τέλεια ορατότητα με Windows dark mode
- Perfect visibility with Windows dark mode
- Επαγγελματική εμφάνιση
- Professional appearance

## Χαρακτηριστικά / Features

### 1. Σκούρα Χρώματα / Dark Colors
- **Background**: Σκούρο γκρι (#2b2b2b)
- **Text**: Ανοιχτό γκρι/λευκό (#bbbbbb / #ffffff)
- **Input Fields**: Σκούρο με λευκό κείμενο
- **Buttons**: Σκούρα με hover effects

### 2. Καλή Αντίθεση / Good Contrast
- Όλο το κείμενο είναι ευανάγνωστο
- All text is readable
- WCAG AA standards
- Κατάλληλο για μακρά χρήση
- Suitable for extended use

### 3. Συνεπής Εμφάνιση / Consistent Appearance
- Όλα τα tabs έχουν το ίδιο θέμα
- All tabs have the same theme
- Όλα τα dialogs είναι σκούρα
- All dialogs are dark
- Όλα τα widgets είναι styled
- All widgets are styled

## Πώς Λειτουργεί / How It Works

Το dark theme εφαρμόζεται αυτόματα όταν ανοίγετε την εφαρμογή:

The dark theme is applied automatically when you open the application:

```python
# Στο main.py / In main.py
from ui.theme import apply_dark_theme

app = QApplication(sys.argv)
apply_dark_theme(app)  # ✅ Αυτόματη εφαρμογή / Automatic application
```

## Τι Είναι Styled / What Is Styled

### ✅ Input Fields (Πεδία Εισαγωγής)
- Subject line
- Email body (HTML & Text)
- Company settings fields
- Recipient fields
- SMTP settings

### ✅ Buttons (Κουμπιά)
- Όλα τα κουμπιά
- All buttons
- Hover effects
- Disabled states
- Primary/Success/Danger variants

### ✅ Lists & Tables (Λίστες & Πίνακες)
- Recipients list
- Template list
- Attachment list
- Opt-out list

### ✅ Dialogs (Παράθυρα)
- Template Selection
- Email Preview
- Error messages
- Confirmation dialogs
- Progress dialogs

### ✅ Tabs (Καρτέλες)
- SMTP Settings
- Recipients
- Company Settings
- Template
- Send

### ✅ Other Elements (Άλλα Στοιχεία)
- Dropdown menus
- Checkboxes
- Radio buttons
- Progress bars
- Scroll bars
- Tooltips

## Χρώματα Κουμπιών / Button Colors

### Normal Buttons (Κανονικά)
- Σκούρο γκρι / Dark gray
- Hover: Ανοιχτότερο / Lighter on hover

### Primary Buttons (Κύρια)
- Μπλε-πράσινο / Teal (#0d7377)
- Για σημαντικές ενέργειες / For important actions

### Success Buttons (Επιτυχία)
- Πράσινο / Green (#28a745)
- "Start Send" button

### Danger Buttons (Κίνδυνος)
- Κόκκινο / Red (#dc3545)
- "Stop" button

## Focus Indicators (Ενδείξεις Εστίασης)

Όταν κάνετε κλικ σε ένα πεδίο, εμφανίζεται μπλε περίγραμμα:

When you click on a field, a blue border appears:

- **Color**: Μπλε / Blue (#4a9eff)
- **Purpose**: Δείχνει ποιο πεδίο είναι ενεργό / Shows which field is active
- **Visibility**: Πολύ ορατό / Highly visible

## Προειδοποιήσεις & Μηνύματα / Warnings & Messages

### Warning (Προειδοποίηση)
- Κίτρινο κείμενο / Yellow text (#ffcc00)
- Καφέ περίγραμμα / Brown border

### Error (Σφάλμα)
- Κόκκινο κείμενο / Red text (#ff6b6b)
- Κόκκινο περίγραμμα / Red border

### Info (Πληροφορία)
- Μπλε περίγραμμα / Blue border
- Ουδέτερο χρώμα / Neutral color

### Success (Επιτυχία)
- Πράσινο κείμενο / Green text (#90ee90)
- Πράσινο περίγραμμα / Green border

## Συμβατότητα / Compatibility

### ✅ Λειτουργεί με / Works with:
- Windows 11 dark mode
- Windows 10 dark mode
- Όλες τις λειτουργίες της εφαρμογής / All app features
- Όλα τα dialogs / All dialogs
- Όλα τα tabs / All tabs

### ✅ Δεν επηρεάζει / Does not affect:
- Λειτουργικότητα / Functionality
- Απόδοση / Performance
- Αποθηκευμένα δεδομένα / Saved data
- Ρυθμίσεις / Settings

## Απενεργοποίηση / Disabling

Αν θέλετε να απενεργοποιήσετε το dark theme:

If you want to disable the dark theme:

1. Ανοίξτε το `main.py`
2. Σχολιάστε τη γραμμή / Comment out the line:
```python
# apply_dark_theme(app)  # Σχολιασμένο / Commented
```
3. Αποθηκεύστε και επανεκκινήστε / Save and restart

## Προσαρμογή / Customization

Για να αλλάξετε χρώματα / To change colors:

1. Ανοίξτε το `ui/theme.py`
2. Αλλάξτε τις σταθερές χρωμάτων / Change color constants:
```python
class DarkTheme:
    BACKGROUND = "#2b2b2b"  # Αλλάξτε αυτό / Change this
    FOREGROUND = "#bbbbbb"  # Και αυτό / And this
    # κλπ... / etc...
```
3. Αποθηκεύστε και επανεκκινήστε / Save and restart

## Συχνές Ερωτήσεις / FAQ

### Γιατί dark theme;
- Καλύτερο για τα μάτια σε σκοτεινό περιβάλλον
- Better for eyes in dark environment
- Ταιριάζει με Windows dark mode
- Matches Windows dark mode
- Επαγγελματική εμφάνιση
- Professional appearance

### Επηρεάζει την απόδοση;
- Όχι! / No!
- Εφαρμόζεται μία φορά στην εκκίνηση
- Applied once at startup
- Μηδενικό overhead
- Zero overhead

### Μπορώ να το αλλάξω;
- Ναι! / Yes!
- Επεξεργαστείτε το `ui/theme.py`
- Edit `ui/theme.py`
- Ή σχολιάστε το στο `main.py`
- Or comment it out in `main.py`

### Λειτουργεί σε όλα τα Windows;
- Ναι! / Yes!
- Windows 10 ✅
- Windows 11 ✅
- Με ή χωρίς dark mode
- With or without dark mode

## Υποστήριξη / Support

Αν έχετε πρόβλημα με το dark theme:

If you have an issue with the dark theme:

1. Ελέγξτε ότι το `ui/theme.py` υπάρχει
2. Ελέγξτε ότι το `main.py` καλεί το `apply_dark_theme()`
3. Επανεκκινήστε την εφαρμογή
4. Ελέγξτε το console για errors

## Σύνοψη / Summary

✅ **Πριν**: Άσπρα backgrounds, αδιάβαστο κείμενο  
✅ **Τώρα**: Σκούρα backgrounds, ευανάγνωστο κείμενο  
✅ **Αποτέλεσμα**: Τέλεια ορατότητα με Windows dark mode!  

✅ **Before**: White backgrounds, unreadable text  
✅ **Now**: Dark backgrounds, readable text  
✅ **Result**: Perfect visibility with Windows dark mode!  

---

**Απολαύστε το νέο dark theme! / Enjoy the new dark theme!** 🎉
