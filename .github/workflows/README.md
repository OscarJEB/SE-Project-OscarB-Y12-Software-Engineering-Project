# 🎓 Student Quick Start Guide

## ⚠️ FIRST: Enable Issues (Required!)

**Before running any security scans, you MUST enable Issues in your repository:**

### 🔧 How to Enable Issues

1. Go to your repository's main page
2. Click **"Settings"** (last tab on the right)
3. Scroll down to **"Features"** section
4. Check the box next to **"Issues"** ✅
5. Click **"Save changes"**

### 🤔 Why Do I Need Issues?

The security scanner creates **Issues** to report problems it finds. Without Issues enabled:

- ❌ Security reports won't be saved
- ❌ The workflow will stop with an error
- ❌ You won't see what needs to be fixed

---

## 🚀 How to Run Your First Security Scan (2 Minutes!)

### Step 1: Go to Actions

1. Look at the tabs at the top of your repository: `Code`, `Issues`, `Pull requests`, **`Actions`**
2. Click on **`Actions`**

### Step 2: Find the Security Workflow

1. Look for **"🔐 Security Analysis (SAST) - Student/Teacher Friendly"** in the list
2. Click on it

### Step 3: Run the Scan

1. Click the **"Run workflow"** button (on the right side)
2. Check the box: **"🎯 Force run even if disabled"**
3. Click **"Run workflow"** again
4. Wait 2-3 minutes for it to complete

### Step 4: Check Results

1. Go to the **"Issues"** tab (next to Actions)
2. Look for issues with labels like `security`, `high`, `medium`, `low`
3. Click on each issue to read about security problems in your code

---

## 🚨 Troubleshooting Common Problems

### Problem: "Issues are disabled" Error

**Solution:** Follow the "Enable Issues" steps at the top of this guide.

### Problem: Workflow Shows "Skipped" Jobs

**Possible causes:**

1. ❌ Issues not enabled → Follow "Enable Issues" steps above
2. ❌ Repository is a fork → Ask your teacher about this
3. ❌ Wrong branch → Make sure you're on the `main` branch

### Problem: No Security Issues Found

**This is good!** It means:

- ✅ Your code doesn't have obvious security problems
- ✅ The scanner ran successfully
- 🎉 You can submit your assignment confidently

### Problem: Too Many Issues Found

**Don't panic!** This is normal for learning projects:

1. 🔴 Focus on **high priority** issues first
2. 🟡 Then work on **medium priority** issues
3. 🟢 **Low priority** issues can wait
4. 🤝 Ask your teacher if you get stuck

---

## 🎯 What Am I Looking For?

### 🔴 High Priority (Fix These First!)

Issues marked with 🔴 are serious security problems that could let hackers:

- Steal user data
- Break into your application
- Take control of your server

### 🟡 Medium Priority (Fix These Next)

Issues marked with 🟡 are moderate risks that could:

- Allow some data leakage
- Create opportunities for attacks
- Violate security best practices

### 🟢 Low Priority (Good to Fix)

Issues marked with 🟢 are minor concerns that:

- Don't follow security best practices
- Could become problems later
- Are good learning opportunities

---

## 📚 How to Read Security Issues

Each issue will tell you:

1. **📁 Which file** has the problem
2. **📍 Which line number** to look at
3. **🔍 What's wrong** with the code
4. **⚡ Why it's dangerous** in real applications
5. **🔧 How to fix it** step by step
