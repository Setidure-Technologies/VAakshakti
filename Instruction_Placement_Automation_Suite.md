# 📘 Placement Automation Suite – Detailed Instructions

The **Placement Automation Suite** is an AI-driven automation workflow built using [n8n](https://n8n.io), designed to streamline campus placement readiness. It takes a list of students and generates **personalized interview preparation documents**, delivering them automatically to their email addresses.

---

## 🧾 Overview

- 🛠 Built on: `n8n` automation platform  
- 🤖 Powered by: Local LLM (via Ollama), LangChain tools  
- 📄 Output: Personalized PDF/DOCX document with tips, GD topics, and role-based prep  
- 📬 Delivery: Automatically emailed to each student  
- 🔁 Bulk-capable: Supports CSV uploads for entire batches

---

## ✅ Steps to Use the Placement Automation Suite

### 1. **Access the Upload Form**

Open the following link in your browser:  
🔗 [https://n8n.erudites.in/form/FORE_placements](https://n8n.erudites.in/form/FORE_placements)

---

### 2. **Download the Sample MIS CSV Format**

Before uploading, ensure your CSV follows the correct format. You can download a sample template directly from the form or [click here](https://github.com/Setidure-Technologies/VAakshakti/blob/main/sample_mis_fore.csv).

### Required CSV Columns:
```
Name, Email, Degree, Branch, Job Role Applied, Past Experience (optional)
```

---

### 3. **Fill in Student Data**

Using the sample format:
- Fill student details for each row
- Ensure each email is valid and accessible
- Save the file in `.csv` format

---

### 4. **Upload the CSV File**

- Visit the upload form link
- Use the upload field to select your `.csv` file
- Click **Submit**

Once submitted:
- The file is parsed
- Each student’s details are processed individually

---

### 5. **Backend AI Workflow (Automated)**

Behind the scenes:
- Each row from the CSV is sent to an LLM-powered workflow
- The LLM generates personalized:
  - Interview preparation tips (based on job role)
  - Group discussion (GD) topics
  - Short certificate course recommendations
  - Sample structured answers (if enabled)
- A personalized PDF/DOCX is created for each student

---

### 6. **Automatic Email Delivery**

- Each student receives their personalized report directly via email
- Reports are delivered within a few minutes of submission
- Emails include:
  - A custom message
  - The attached preparation document (PDF/DOCX)

---

## 🛡️ Notes & Best Practices

- Do not upload files larger than **1MB**
- Make sure all fields are filled in English
- Avoid special characters in the CSV (especially in names and job roles)
- For large batches, test with 2–3 students first

---

## 🔧 Troubleshooting

| Issue                                | Solution                                                                 |
|-------------------------------------|--------------------------------------------------------------------------|
| File not uploading                  | Ensure it's a `.csv` file under 1MB                                       |
| Email not received by student       | Check spam folder; verify email address in the CSV                        |
| Incorrect formatting                | Download and strictly follow the [sample CSV](https://github.com/Setidure-Technologies/VAakshakti/blob/main/sample_mis_fore.csv) |
| System delay                        | Wait 2–5 minutes for processing; refresh mailbox                          |

---

## 📩 Contact Support

For queries or technical support, contact:

**Aashit Sharma**  
CTO, Setidure Technologies Pvt. Ltd.  
📧 Email: [aashit@erudites.in](mailto:aashit@erudites.in)  
📞 Phone: +91 9289920323
