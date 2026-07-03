# 🏥 Simplified GP CRM User Guide

## **For Non-Technical Users**

This guide shows you how to use the simplified interface. All complicated technical terms have been hidden.

---

## **Receptionist (Front Office) Workflow**

### **Step 1: Patient Arrives → Check In**

1. **At `/app/` → Click "Check In Patient"**
   - Or go directly to `/patients/checkin/`
2. **Type the patient's name or ID number**
   - System shows matching patients
3. **Click "✅ CHECK IN"**
   - Shows: patient name, age, insurance info, allergies warning
4. **Done!** Print the appointment slip if needed

### **What you see:**
- ✅ Patient name & age
- 🛡️ Insurance scheme  
- ⚠️ ALLERGY warnings (RED box—pay attention!)
- No medical details

---

## **Doctor Workflow**

### **Step 1: Dashboard → New Consultation**

1. **At `/app/` → Click "New Consultation"**
2. **Select patient** (search by name)
3. **Select appointment**
4. **Fill in:**
   - Blood pressure (e.g. "120/80")
   - Weight
   - Why patient came (chief complaint)
5. **Click "DONE"**

### **Step 2: Consultation Detail → What's Wrong?**

1. **From consultation page → Click big green "🩺 WHAT'S WRONG?" button**
2. **Tick all symptoms the patient has RIGHT NOW:**
   - ☐ Fever / high temperature
   - ☐ Cough
   - ☐ Sore throat
   - ☐ Shortness of breath
   - ☐ Headache
   - (and many more...)
3. **Click "📊 Get Diagnosis Suggestions"**

### **Step 3: Review Suggestions**

System shows **top 3 likely diagnoses:**
1. Diagnosis name
2. Number of matching symptoms
3. Confidence level (🟢 High / 🟡 Medium / 🔴 Low)

**Click "✓ Select this diagnosis"** → automatically saved!

### **Step 4: Finish Consultation**

Back on consultation page:
- Fill in clinical notes (optional)
- ✏️ **Edit** if you need to make changes
- 🖨️ **Print** if needed
- ✓ That's it!

---

## **Insurance Info (Receptionist)**

### **Check patient's medical aid:**

1. **Find patient** → Click "View Details"
2. **See:**
   - Insurance scheme name
   - Plan name
   - Member number
   - Visit count vs plan limit
   - ⚠️ Warning if over visits allowed

---

## **Dashboard Overview**

### **What you see:**

| Role | Quick Actions | Alerts |
|------|---------------|--------|
| **Receptionist** | Check In, Insurance Info | New bookings, Overdue payments |
| **Doctor** | New Consultation, Find Patient | Pending results, Overdue payments |

### **Traffic lights:**
- 🔵 Blue box = OK / Normal
- 🟡 Yellow box = Warning / Review needed
- 🔴 Red box = Critical / Allergies / Missing info

---

## **Common Tasks**

### **"Print a prescription"**
- Go to consultation → scroll down → **Print** button
- Or edit consultation → add prescription → Print

### **"Patient is allergic to..."**
- Add to patient profile (in patient detail)
- 🔴 RED warning appears everywhere!

### **"Patient has used too many visits"**
- System shows: "5 of 5 visits used"
- Call manager before scheduling more

### **"Diagnose a cough"**
1. Take patient to consultation
2. Click "WHAT'S WRONG?"
3. Tick: ☐ Cough, ☐ Fever, ☐ Shortness of breath
4. System suggests: Common Cold, Flu, Bronchitis
5. Pick one

---

## **Hidden Details (You Don't See)**

- ❌ ICD-10 codes
- ❌ Medical billing codes
- ❌ Insurance claim details  
- ❌ Diagnosis scores
- ❌ Complex statistics

*System handles these automatically in the background.*

---

## **Color Guide**

| Color | Meaning | Action |
|-------|---------|--------|
| 🔵 Blue | Primary button / Important info | Click to proceed |
| 🟢 Green | Success / Confirm | System is ready, click it! |
| 🟡 Yellow | Warning / Review | Check if there's an issue |
| 🔴 Red | Critical / Allergies | ⚠️ PAY ATTENTION |
| 🟣 Purple | Edit / Optional | Edit details if needed |

---

## **Quick Troubleshooting**

**"I can't find the patient"**
→ Try searching by first name instead of last name

**"What's the button for...?"**
→ If it's big and green 🟢, click it! That's the main action.

**"Can I see the diagnosis code?"**
→ No need! System stores it automatically. You just see the diagnosis name.

**"What if I made a mistake?"**
→ Click ✏️ **Edit** to fix it. No data is deleted, just updated.

---

## **Need Help?**

- 📞 **Can't find patient?** → Type name or ID number in search
- 🔴 **Red warning box?** → Read it carefully—usually allergies
- 🤔 **Don't know which diagnosis?** → Trust the top suggestion (🟢 green)
- 💾 **Forgot to save?** → Click "DONE" or "CHECK IN"—it auto-saves

---

**You're all set! The system is designed to be simple.  If you get stuck, use the big colored buttons and the rest usually works itself out.**
