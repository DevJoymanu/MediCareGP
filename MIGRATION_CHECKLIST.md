# 📋 Migration Checklist: From Old Dashboard to Simplified UI

This checklist guides staff through transitioning from the technical dashboard to the new simplified interface. All functionality is preserved; only the UI has changed.

---

## Pre-Migration Prep (1 day before)

### For IT / DevOps:
- [ ] Backup database: `python manage.py dumpdata > backup_pre_simplification.json`
- [ ] Create test accounts (doctor + receptionist if not already done)
- [ ] Test video calling via `/video/turn-test/` (ensure TURN servers are live)
- [ ] Verify all new templates are in place (see `medicaregp/templates/` directory)
- [ ] Run full test suite: `python manage.py test` (should see 53 passing)
- [ ] Test the simplified UI in a staging environment

### For Practice Staff:
- [ ] Read `SIMPLIFIED_USER_GUIDE.md` (10 minutes)
- [ ] Attend brief training session (optional)
- [ ] Note down new login credentials (same users, same passwords—no change)

---

## Migration Day Tasks

### 1. Deploy New Code to Production

```bash
# On main branch
git log --oneline -1  # Confirm current commit
git push origin main  # Triggers Railway auto-deploy
```

**Monitor:**
- [ ] Check Railway **Deployments** tab—should show green checkmark
- [ ] Run migrations: `railway run python manage.py migrate`
- [ ] Confirm no errors in Railway **Logs** tab

### 2. Verify Staff Can Access Dashboard

**For each staff member:**
- [ ] Doctor logs in at `/app/` → sees simplified dashboard (blue "New Consultation" button visible)
- [ ] Receptionist logs in at `/app/` → sees check-in button + insurance actions
- [ ] Both can navigate to patient list

**Common issues:**
- If seeing old dashboard → hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- If login fails → clear cookies, try again

### 3. Test Each Simplified Workflow

#### Receptionist Check-In Workflow:
- [ ] Go to Dashboard → click **"Check In Patient"**
- [ ] Search for patient "Thabo Mokoena" (demo patient)
- [ ] Confirm patient card shows allergies warning (red box)
- [ ] Click **"CHECK IN"** button
- [ ] Confirm check-in recorded (no error)

#### Doctor Consultation Workflow:
- [ ] Go to Dashboard → click **"New Consultation"**
- [ ] Select Thabo Mokoena
- [ ] Select today's appointment
- [ ] Enter vitals (BP 120/80, weight 75 kg)
- [ ] Enter chief complaint ("General checkup")
- [ ] Click **"DONE"**
- [ ] Click big green **"🩺 WHAT'S WRONG?"** button
- [ ] Check symptoms: Fever, Cough, Shortness of breath
- [ ] Click **"📊 Get Diagnosis Suggestions"**
- [ ] Confirm top 3 diagnoses appear with confidence levels (High/Medium/Low)
- [ ] Click **"✓ Select this diagnosis"** for top suggestion
- [ ] Confirm diagnosis saved to consultation
- [ ] Verify old dashboard no longer shows in navigation

#### Insurance Lookup:
- [ ] Find patient → click **"View Details"**
- [ ] Scroll to **"Medical Aid Information"** section
- [ ] Confirm scheme name, plan, member number visible
- [ ] Check visit usage (e.g., "3 of 6 visits used")
- [ ] Confirm warning appears if over limit (in yellow/red)

#### Video Call:
- [ ] Doctor creates online appointment
- [ ] Visit `/video/appointment/<id>/` and join as doctor
- [ ] Visit `/video/join/<token>/` in incognito window as "patient"
- [ ] Confirm video connection works (may take 5-10 seconds to establish)
- [ ] Check `/video/turn-test/` shows "Cloudflare Realtime TURN: OK"

### 4. Spot-Check Old Features Still Work

These shouldn't have changed, but verify:
- [ ] Patient list filters by name/ID (`/patients/`)
- [ ] Patient detail shows full history (doctors only)
- [ ] Appointments can be booked online (`/api/bookings`)
- [ ] Results portal works (`/lab/` and `/radiology/`)
- [ ] Invoice view works (`/billing/invoices/`)
- [ ] Analytics dashboard shows data (`/analytics/`)

### 5. Update Documentation

- [ ] Distribute `SIMPLIFIED_USER_GUIDE.md` to staff (print or email)
- [ ] Post troubleshooting section near reception desk
- [ ] Add link to guide on CRM homepage (optional)
- [ ] Update internal wiki/intranet if you maintain one

---

## Post-Migration (Day 1-7)

### Continuous Monitoring:

**Daily (first 3 days):**
- [ ] Check Railway logs for errors: `railway logs --follow`
- [ ] Confirm no staff reports are logging in as wrong role
- [ ] Spot-check 3-5 consultations to ensure they're saved correctly

**Weekly:**
- [ ] Review dashboard usage (who's using old vs new)
- [ ] Gather feedback from doctors and receptionists
- [ ] Check video call success rate (from logs)

### Troubleshooting:

**"I still see the old dashboard"**
→ Hard refresh (Ctrl+Shift+R), clear browser cache, or restart browser

**"Symptoms don't match the diagnosis"**
→ This is normal—diagnosis engine is probabilistic. Check if more symptoms help refine suggestions.

**"Video calls still hanging on 'Connecting…'"**
→ Check `/video/turn-test/` for TURN provider status. If Cloudflare down, may fall back to STUN (LAN only).

**"I can't find the patient"**
→ Try searching by first name instead of last name. System is case-insensitive.

**"Allergies warning not showing"**
→ Ensure patient record has allergies filled in (see patient detail page, doctor login)

### Rollback (if critical issues):

```bash
# Only if severe: database corruption, security breach, etc.
git revert HEAD
git push origin main
railway run python manage.py loaddata backup_pre_simplification.json
```

Otherwise, favor fixing forward (new commit) rather than reverting.

---

## Staff Training Script (10 minutes)

### For Receptionists:

*"The check-in screen is now simpler. Here's what changed:*

1. **Dashboard** → Click "Check In Patient" (was buried in a menu before)
2. **Search** → Type patient name or ID—much faster
3. **Patient card** → Red warnings for allergies—pay attention!
4. **CHECK IN button** → Big green button, can't miss it
5. **No medical codes** → You won't see ICD-10 codes or billing terms—we handle that automatically

*Questions? See the guide on the wall.*"

### For Doctors:

*"The consultation workflow is streamlined:*

1. **Dashboard** → "New Consultation" is the main button
2. **Enter vitals** → Same form, just cleaner
3. **What's wrong?** → Click the big green button → check symptoms
4. **Suggestions** → Engine suggests diagnoses automatically
5. **Pick one** → Click green checkmark, done

*No diagnosis codes to remember—system handles billing in the background.*

*Advanced users: Old views still work for full records (patient_detail, etc.). These haven't changed.*"

---

## Rollout Timeline

| Phase | Timeline | Who | Action |
|-------|----------|-----|--------|
| **Prep** | T-1 day | IT + Staff | Read guide, backup DB, test locally |
| **Deploy** | T-0 (morning) | IT | Push to main, run migrations |
| **Verify** | T-0 (midday) | IT | Test each workflow, check logs |
| **Train** | T-0 (afternoon) | Managers | Brief staff, answer questions |
| **Go live** | T-0 (EOD) or T+1 (early) | All | Start using in production |
| **Monitor** | T+1 to T+7 | IT | Daily logs, weekly feedback |
| **Feedback** | T+7 | All | Report issues, improvements |

---

## Success Criteria

Migration is **successful** when:

✅ All staff can log in and see the simplified dashboard  
✅ Receptionists can check in a patient in <2 minutes (was >5 before)  
✅ Doctors can create a consultation and get diagnosis suggestions in <5 minutes  
✅ Video calls connect within 15 seconds  
✅ All tests pass (53/53)  
✅ No critical errors in production logs  
✅ Staff report finding the new UI easier to use  

---

## FAQ for Staff

**Q: Did my password change?**  
A: No. Same username, same password.

**Q: Where's the old dashboard?**  
A: It's been replaced. But all your data is the same. You can still access patient records and appointments exactly as before.

**Q: Why are diagnosis codes hidden?**  
A: They clutter the interface. The system stores them automatically—you just see the diagnosis name.

**Q: What if I want to see more details (medical codes, ICD-10, etc.)?**  
A: If you're a doctor, click on "Patient Detail" page. Full clinical record is there (receptionists don't see it).

**Q: Can I go back to the old dashboard?**  
A: Only if we revert the code. Feature is new, not a toggle. But give it a week—you'll probably like it.

**Q: Video calls still don't work.**  
A: Check `/video/turn-test/` (staff only). Tells you exactly which TURN provider is failing. Likely needs env var fix.

**Q: I can't find a patient.**  
A: Try searching by first name or ID number. Double-check spelling.

**Q: Diagnosis suggestions seem wrong.**  
A: Try checking more symptoms. Engine gets more confident with more data.

---

## Support & Escalation

**Tier 1 (Receptionists/Doctors):**
- Check `SIMPLIFIED_USER_GUIDE.md` (on wall or emailed)
- Restart browser, clear cache
- Restart the app server if stuck

**Tier 2 (Practice Manager):**
- Check Railway **Logs** tab for errors
- Verify all staff have correct roles (Doctor vs Reception)
- Run `python manage.py setup_demo` to reset test data

**Tier 3 (IT/DevOps):**
- Check `railway logs --follow` for exceptions
- Verify all env vars are set in Railway **Variables**
- Rollback if critical: see "Rollback" section above

---

**Last updated:** 2026-07-03  
**Version:** Simplified UI v1.0  
**Estimated downtime:** 5-10 minutes (if during quiet hours)  
**Rollback time:** <30 minutes (if needed)
