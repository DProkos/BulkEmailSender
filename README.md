<p align="center">
  <img src="icons/png.png" alt="Bulk Email Sender Logo" width="128" height="128">
</p>

<h1 align="center">Bulk Email Sender</h1>

<p align="center">
  <strong>Εφαρμογή μαζικής αποστολής εξατομικευμένων emails μέσω SMTP</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.6+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg" alt="Platform">
</p>

---

## 📋 Περιγραφή

Το **Bulk Email Sender** είναι μια desktop εφαρμογή για Windows που επιτρέπει τη μαζική αποστολή εξατομικευμένων emails. Ιδανικό για:

- 📧 Μαζική αποστολή newsletters
- 👥 Ενημερωτικά emails σε πελάτες
- 📢 Προωθητικές καμπάνιες
- 🏢 Εταιρική επικοινωνία

---

## ✨ Χαρακτηριστικά

| Χαρακτηριστικό | Περιγραφή |
|----------------|-----------|
| 🔒 **Ασφαλής αποθήκευση** | Οι κωδικοί αποθηκεύονται στο Windows Credential Manager |
| 📊 **Εισαγωγή από Excel** | Φόρτωση παραληπτών από αρχεία .xlsx |
| ✏️ **Template Editor** | Δημιουργία emails με μεταβλητές ({{name}}, {{company}}) |
| ⏱️ **Throttling** | Έλεγχος ρυθμού αποστολής για αποφυγή spam filters |
| 🔄 **Crash Recovery** | Αυτόματη ανάκτηση και συνέχιση αποστολής |
| 📝 **Opt-Out List** | Διαχείριση λίστας απεγγραφής |
| 🌙 **Dark Theme** | Σύγχρονο dark theme interface |
| 💾 **Αποθήκευση ρυθμίσεων** | Όλες οι ρυθμίσεις αποθηκεύονται αυτόματα |

---

## 🚀 Εγκατάσταση

### Επιλογή 1: Executable (Προτείνεται)

1. Κατεβάστε το `BulkEmailSender.exe` από τα [Releases](../../releases)
2. Εκτελέστε - δεν χρειάζεται εγκατάσταση!

### Επιλογή 2: Από τον κώδικα

```bash
# Clone το repository
git clone https://github.com/yourusername/bulk-email-sender.git
cd bulk-email-sender

# Εγκατάσταση dependencies
pip install -r requirements.txt

# Εκτέλεση
python main.py
```

---

## 📖 Οδηγίες Χρήσης

### 1️⃣ Ρύθμιση SMTP

Πηγαίνετε στο tab **SMTP Settings** και συμπληρώστε:

| Πάροχος | Host | Port |
|---------|------|------|
| Gmail | smtp.gmail.com | 587 |
| Outlook | smtp.office365.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |

> ⚠️ **Gmail**: Χρησιμοποιήστε [App Password](https://support.google.com/accounts/answer/185833) αν έχετε 2FA

### 2️⃣ Εισαγωγή Παραληπτών

- **Από Excel**: Επιλέξτε αρχείο .xlsx και αντιστοιχίστε τις στήλες
- **Χειροκίνητα**: Προσθέστε emails ένα-ένα ή με copy-paste

**Μορφή Excel:**
```
Email              | Name        | Company
-------------------|-------------|------------
john@example.com   | John Doe    | Acme Corp
jane@example.com   | Jane Smith  | Tech Inc
```

### 3️⃣ Δημιουργία Template

Πατήστε **📝 Edit Email Body** και γράψτε το email σας:

```html
<p>Αγαπητέ/ή {{name}},</p>

<p>Σας ευχαριστούμε για το ενδιαφέρον σας στην {{company}}.</p>

<p>Με εκτίμηση,<br>
Η ομάδα μας</p>
```

**Διαθέσιμες μεταβλητές:**
- `{{name}}` - Όνομα παραλήπτη
- `{{email}}` - Email παραλήπτη
- `{{company}}` - Εταιρεία
- `{{unsubscribe_link}}` - Link απεγγραφής

### 4️⃣ Αποστολή

1. Ρυθμίστε το **Throttle Rate** (προτείνεται 2-5 sec)
2. Πατήστε **▶️ Start Send**
3. Παρακολουθήστε την πρόοδο σε πραγματικό χρόνο

---

## 🛠️ Build από τον κώδικα

```bash
# Εγκατάσταση PyInstaller
pip install pyinstaller

# Build
pyinstaller bulk_email_sender.spec

# Το executable θα βρίσκεται στο dist/BulkEmailSender.exe
```

---

## 📁 Δομή Project

```
bulk-email-sender/
├── main.py                 # Entry point
├── ui/                     # User interface (PyQt6)
│   ├── main_window.py
│   ├── smtp_tab.py
│   ├── recipients_tab.py
│   ├── template_tab.py
│   └── send_tab.py
├── core/                   # Business logic
│   ├── smtp_manager.py
│   ├── template_renderer.py
│   └── queue_manager.py
├── storage/                # Data persistence
│   ├── database.py
│   └── config_manager.py
├── icons/                  # App icons
├── docs/                   # Documentation
└── requirements.txt
```

---

## 🔧 Απαιτήσεις

- **Python**: 3.10+
- **OS**: Windows 10/11
- **Dependencies**:
  - PyQt6
  - pandas
  - openpyxl
  - Jinja2
  - keyring

---

## 💡 Συμβουλές

### Αποφυγή Spam Filters
- ✅ Χρησιμοποιήστε throttle rate τουλάχιστον 2 sec
- ✅ Προσθέστε unsubscribe link
- ✅ Αποφύγετε ΚΕΦΑΛΑΙΑ και πολλά θαυμαστικά
- ✅ Μην στέλνετε πάνω από 100 emails/ώρα

### Ασφάλεια
- 🔐 Οι κωδικοί αποθηκεύονται στο Windows Credential Manager
- 🔐 Χρησιμοποιήστε App Passwords αντί για κανονικούς κωδικούς
- 🔐 Ποτέ μην μοιράζεστε το config.json

---

## 🐛 Αντιμετώπιση Προβλημάτων

| Πρόβλημα | Λύση |
|----------|------|
| Authentication Failed | Ελέγξτε username/password, χρησιμοποιήστε App Password |
| Connection Timeout | Ελέγξτε internet, host, port και firewall |
| Rate Limit | Αυξήστε το throttle rate |

---

## 👨‍💻 Ανάπτυξη

**Developed by:** Dionisis Prokos

---

## 📄 Άδεια

MIT License - Δείτε το αρχείο [LICENSE](LICENSE) για λεπτομέρειες.

---

<p align="center">
  Made with ❤️ in Greece
</p>
