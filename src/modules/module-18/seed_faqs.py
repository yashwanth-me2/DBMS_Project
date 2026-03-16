"""Bulk-insert the 150 Hospital QA FAQ entries into MongoDB."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import faq_repository, setup_database

setup_database()

FAQS = [
    ("What is the normal range for a fasting blood glucose test?", "A normal fasting blood glucose level is typically between 70 and 100 mg/dL.", "Lab Values"),
    ("How should a patient prepare for a thyroid fine needle aspiration (FNA) biopsy?", "Most medications can be continued, but blood thinners may need to be stopped. No fasting is required, and the patient can usually drive themselves home after the 15-45 minute procedure.", "Procedure"),
    ("What is the maximum number of acetaminophen doses a child can receive in 24 hours?", "A child should not receive more than 5 doses of acetaminophen in any 24-hour period.", "Medication"),
    ("What are the symptoms that should trigger a call to the oncology team after a bone marrow biopsy?", "Patients should call if they experience a persistent fever, bleeding that soaks through the bandage, worsening pain, or redness and drainage at the site.", "General"),
    ("What is the significance of an HbA1c level of 6.2%?", "An A1C level between 5.7% and 6.4% is classified as prediabetes, indicating a higher risk for developing Type 2 diabetes and cardiovascular disease.", "Lab Values"),
    ("How many midnights must a patient stay to generally qualify for inpatient status?", "Under the Two-Midnight Rule, inpatient admission is generally considered appropriate if the physician expects the patient to require hospital care for at least two midnights.", "General"),
    ("What skin care products should be avoided during radiation therapy?", "Patients should avoid deodorants, anti-perspirants, perfumes, talcum powders, and any lotions containing alcohol or fragrances in the treatment area.", "Procedure"),
    ("What is the recommended dosage of 160mg/5mL acetaminophen for a child weighing 30 pounds?", "For a child weighing 24-35 lbs, the recommended dose is 5 mL or 1 teaspoon.", "Medication"),
    ("What are the criteria for activating a Rapid Response Team based on heart rate?", "An RRT should be called if a patient's heart rate acutely falls below 40-45 bpm or rises above 130-140 bpm.", "Lab Values"),
    ("How long must a patient fast before a renal ultrasound?", "Patients must fast for 12 hours prior to the test and should hold their morning blood pressure medications until the exam is completed.", "Procedure"),
    ("What is the primary difference between a Health Care Proxy and a Power of Attorney?", "A Health Care Proxy is specifically for medical decisions when a patient is incapacitated, whereas a Power of Attorney primarily authorizes someone to make financial decisions.", "General"),
    ("What should a patient do if they miss a dose of weekly semaglutide and it has been 4 days?", "Since it is within the 5-day window, the patient should take the missed dose immediately and then resume their regular weekly schedule.", "Medication"),
    ("What is the normal reference range for serum potassium?", "The normal range for potassium is 3.7 to 5.2 mEq/L.", "Lab Values"),
    ("What are the requirements for a patient to be discharged from the hospital?", "Discharge requires a physician's order, completion of nursing documentation, removal of all IV lines, and the provision of follow-up education and prescriptions.", "General"),
    ("Why must calcium supplements be stopped before a DEXA bone density scan?", "Calcium supplements must be stopped for 24 hours before the test because they can interfere with the accuracy of the bone density measurements.", "Procedure"),
    ("What is the target TSH level for a patient being treated for hypothyroidism?", "The target TSH level for most individuals is between 0.5 and 4.5 milli-international units per liter (mIU/L).", "Lab Values"),
    ("How should a patient manage diarrhea caused by chemotherapy?", "Patients should drink at least 2 liters of fluids daily, avoid caffeine and dairy, and contact the hospital if they have more than 4 episodes in a day.", "Medication"),
    ("What is the MOON notice in hospital administration?", "The Medicare Outpatient Observation Notice (MOON) is a required document that informs patients they are receiving observation services as an outpatient for more than 24 hours.", "General"),
    ("What is the correct way to use a nebulizer with a face mask for a child?", "Place the mask over the child's mouth and nose with a snug fit and encourage slow, deep breaths for the 10-15 minute duration of the mist.", "Procedure"),
    ("How does grapefruit juice affect statin medications like atorvastatin?", "Grapefruit juice inhibits the CYP3A4 enzyme, leading to increased blood levels of the statin and a higher risk of muscle damage (rhabdomyolysis).", "Medication"),
    ("What is the systolic blood pressure threshold for a National Early Warning Score (NEWS) of 3?", "A systolic blood pressure of 90 mmHg or less is assigned a score of 3 on the NEWS scale.", "Lab Values"),
    ("What physical preparations are needed for an MRI scan?", "Patients must remove all jewelry, piercings, and clothing with metal fasteners, and should not wear eye makeup as it may contain metallic flecks.", "Procedure"),
    ("What is a Guarantor in the context of hospital billing?", "The guarantor is the person responsible for the final payment of the medical bill, usually the patient unless the patient is a minor.", "General"),
    ("When is the first dose of the MMR vaccine typically administered to children?", "The first dose of the Measles, Mumps, and Rubella (MMR) vaccine is routinely recommended between 12 and 15 months of age.", "Medication"),
    ("What is the purpose of the newborn hearing screening?", "The screening checks for hearing loss in infants before they leave the hospital, allowing for early intervention to support language development.", "Procedure"),
    ("What is the normal range for serum creatinine in adults?", "The normal range for creatinine is 0.6 to 1.3 mg/dL, which is used to assess kidney function.", "Lab Values"),
    ("How should a patient prepare for a fasting lipid panel?", "The patient must fast for 9 to 12 hours before the blood draw. Water is permitted, but coffee and other beverages are not.", "Procedure"),
    ("What is the recommended treatment for hypoglycemia in a conscious patient?", "The 15-15 rule is often used: consume 15 grams of fast-acting carbohydrates (like juice) and recheck blood sugar in 15 minutes.", "Medication"),
    ("What is the purpose of the Important Message from Medicare (IM) document?", "It is a notice given to hospital inpatients explaining their rights as a Medicare beneficiary, including how to appeal a discharge decision.", "General"),
    ("What are the common side effects of levothyroxine?", "Side effects are rare if the dose is correct but can include symptoms of hyperthyroidism like racing heart, tremors, or heat intolerance if the dose is too high.", "Medication"),
    ("What is the normal range for blood urea nitrogen (BUN)?", "The normal range for BUN is 6 to 20 mg/dL.", "Lab Values"),
    ("How should a patient care for their skin after a radiation treatment session?", "Wash gently with lukewarm water, pat dry, and apply only oncologist-approved moisturizers. Avoid direct sunlight and extreme temperatures on the treated area.", "Procedure"),
    ("What is the difference between a co-pay and co-insurance?", "A co-pay is a fixed dollar amount paid for a service, while co-insurance is a percentage of the total cost (e.g., 20%) paid after the deductible is met.", "General"),
    ("What is the age restriction for a child to receive ibuprofen for the first time?", "Ibuprofen should not be given to infants younger than 6 months of age without a direct order from a physician.", "Medication"),
    ("What is the normal range for serum albumin?", "The normal range for albumin is 3.4 to 5.4 g/dL.", "Lab Values"),
    ("What are the restrictions for a cardiac PET/CT scan regarding caffeine?", "Patients must have no caffeine for 24 hours prior to the test, including decaffeinated coffee, tea, chocolate, and certain soda.", "Procedure"),
    ("What happens if a patient misses a dose of daily liraglutide (Victoza)?", "The missed dose should be skipped entirely, and the next dose taken at the regular time the following day. Never take a double dose.", "Medication"),
    ("What is the Allowed Amount in health insurance?", "The allowed amount is the maximum price an insurance company will pay for a covered health care service.", "General"),
    ("What is the purpose of the pulse oximetry screen in newborns?", "It is used to screen for critical congenital heart defects (CCHD) by measuring oxygen levels in the baby's blood.", "Procedure"),
    ("What is the normal range for serum sodium?", "The normal range for sodium is 135 to 145 mEq/L.", "Lab Values"),
    ("How should a patient prepare for a bone marrow biopsy if they are nervous?", "Patients should discuss anxiety with their provider; light sedation or IV medication can often be provided to ensure comfort during the procedure.", "Procedure"),
    ("What is a Deductible in medical billing?", "A deductible is the amount a patient must pay out-of-pocket for covered services before their insurance plan begins to pay.", "General"),
    ("What should a patient do if their chemotherapy port site shows signs of redness or swelling?", "This could indicate an infection; the patient should contact their oncology team or the infusion center immediately.", "General"),
    ("What is the routine dosage for the HPV vaccine in 2026?", "As of 2026, the CDC recommends a single dose of the Human Papillomavirus (HPV) vaccine for most children.", "Medication"),
    ("What is the normal range for alkaline phosphatase (ALP)?", "The normal range for ALP is 20 to 130 U/L.", "Lab Values"),
    ("How should a patient prepare for a CT scan of the abdomen?", "Patients should fast for 4 to 6 hours before the exam and may be required to drink an oral contrast solution the night before or day of the test.", "Procedure"),
    ("What is the goal of a palliative care consult in oncology?", "Palliative care focuses on relieving the symptoms and stress of a serious illness, such as pain and nausea, to improve quality of life for the patient.", "General"),
    ("What is the interaction risk between warfarin and leafy green vegetables?", "Leafy greens are high in Vitamin K, which can make warfarin less effective. Patients should maintain a consistent intake rather than avoiding these foods.", "Medication"),
    ("What is the oxygen saturation trigger for a Rapid Response Team activation?", "An RRT should be called if a patient's oxygen saturation (SpO2) falls below 88% to 90% despite supplemental oxygen.", "Lab Values"),
    ("What is the preparation for a colonoscopy?", "Patients must follow a clear liquid diet the day before and consume a prescribed bowel preparation solution to ensure the colon is completely clear.", "Procedure"),
    ("What is a Living Will?", "A living will is a legal document that specifies the types of medical treatments a patient would or would not want in end-of-life situations.", "General"),
    ("What is the standard concentration of liquid ibuprofen for infants?", "Infant ibuprofen drops are typically concentrated at 50 mg per 1.25 mL.", "Medication"),
    ("What is the normal range for alanine aminotransferase (ALT)?", "The normal range for ALT is 4 to 36 U/L.", "Lab Values"),
    ("How should a patient prepare for a mammogram if they have had previous scans elsewhere?", "Patients should arrange to have their previous imaging records or films sent to the new facility for comparison by the radiologist.", "General"),
    ("What is the preparation for a gallbladder ultrasound?", "The patient must fast for at least 8 to 12 hours (NPO) to ensure the gallbladder is distended and easily visualized.", "Procedure"),
    ("What is In-network versus Out-of-network in insurance?", "In-network providers have a contract with your insurance for lower rates, while out-of-network providers do not, often leading to higher out-of-pocket costs.", "General"),
    ("What is the missed dose policy for weekly tirzepatide (Mounjaro)?", "A missed dose can be taken within 4 days (96 hours) of the scheduled time. If more than 4 days pass, skip it and wait for the next dose.", "Medication"),
    ("What is the normal range for serum calcium?", "The normal range for calcium is 8.5 to 10.2 mg/dL.", "Lab Values"),
    ("What is an Arthrography procedure?", "An arthrogram is a type of medical imaging (using X-ray, CT, or MRI) used to look at a joint after a contrast medium has been injected into the joint space.", "Procedure"),
    ("What is a Guarantor for a pediatric patient?", "For patients under 18, the guarantor is the parent or legal guardian who assumes financial responsibility for the medical bills.", "General"),
    ("What is the significance of bilateral blood pressure readings?", "Measuring blood pressure in both arms is recommended; if there is a consistent difference, the arm with the higher reading should be used for future monitoring.", "Lab Values"),
    ("How long should a patient remain still during an EKG?", "An EKG is very quick, usually taking only a few minutes, but the patient must remain completely still and relaxed for about 10-20 seconds while the tracing is recorded.", "Procedure"),
    ("What are the side effects of sudden withdrawal from blood pressure medication?", "Stopping blood pressure meds abruptly can lead to rebound hypertension, where blood pressure spikes dangerously high, increasing the risk of stroke or heart attack.", "Medication"),
    ("What is an Itemized Bill?", "An itemized bill is a detailed statement that lists every individual charge for services, supplies, and medications provided during a hospital stay.", "General"),
    ("What is the normal range for aspartate aminotransferase (AST)?", "The normal range for AST is 8 to 33 U/L.", "Lab Values"),
    ("How should a patient prepare for a Stress Echo test?", "Wear comfortable exercise clothing and sneakers. Patients may need to fast for 2-4 hours and may be told to hold certain heart medications like Beta Blockers.", "Procedure"),
    ("What is the worried criterion in hospital safety?", "It is a Rapid Response Team trigger that allows a nurse or family member to call the team simply because they feel something is not right with the patient.", "General"),
    ("What is the routine dosage of the DTaP vaccine for a 2-month-old infant?", "The DTaP vaccine is an injection given as part of a 5-dose series, starting with the first dose at 2 months of age.", "Medication"),
    ("What is the normal range for serum chloride?", "The normal range for chloride is 96 to 106 mEq/L.", "Lab Values"),
    ("What is the preparation for a Barium Swallow or UGI study?", "The patient must have nothing to eat or drink (NPO) after midnight on the night before the procedure.", "Procedure"),
    ("What is the role of a Case Manager in hospital discharge?", "A case manager helps arrange for post-hospital needs such as home health care, medical equipment, or placement in a rehabilitation facility.", "General"),
    ("What is the interaction risk between black licorice and certain heart medications?", "Black licorice contains glycyrrhizin, which can cause potassium levels to drop, potentially leading to dangerous arrhythmias or interfering with blood pressure meds.", "Medication"),
    ("What is the normal range for serum bicarbonate (CO2)?", "The normal range is 23 to 29 mEq/L.", "Lab Values"),
    ("What is the recovery time for a bone marrow biopsy with local anesthesia only?", "Patients are usually asked to lie on their back for 10-15 minutes to apply pressure to the site and can then resume normal activities immediately.", "Procedure"),
    ("What is a Durable Power of Attorney for Healthcare?", "It is a legal document that designates a specific person to make medical decisions on your behalf if you become unable to do so.", "General"),
    ("What is the impact of exercise on a fasting glucose test?", "Strenuous exercise can affect blood sugar levels; patients should avoid heavy physical activity for several hours before a fasting glucose draw.", "Lab Values"),
    ("How is the Rotavirus vaccine administered?", "The rotavirus vaccine is administered as liquid drops into the infant's mouth (orally), not as an injection.", "Medication"),
    ("What is the purpose of an MRI Screening for metal?", "Because MRI uses a powerful magnet, screening is essential to ensure the patient has no metallic implants or fragments that could be moved or heated.", "Procedure"),
    ("What is the Assignment of Benefits?", "It is a document signed by the patient that allows the insurance company to pay the hospital or doctor directly for services rendered.", "General"),
    ("What is the normal range for total bilirubin?", "The normal range for total bilirubin is 0.1 to 1.2 mg/dL.", "Lab Values"),
    ("What should a patient do if they miss a dose of daily liraglutide for more than 3 days?", "If liraglutide (Saxenda) is missed for more than 3 days, the patient should contact their doctor to discuss re-starting at a lower titration dose.", "Medication"),
    ("What is the preparation for a Pelvic Ultrasound?", "The patient must drink 32 ounces of water one hour before the test and not empty their bladder until the exam is finished.", "Procedure"),
    ("What is Observation Status versus Inpatient Status for billing?", "Observation is billed as an outpatient service under Medicare Part B, while Inpatient status is billed under Medicare Part A.", "General"),
    ("What is the trigger for a Rapid Response call regarding respiratory rate?", "An RRT should be called if a patient's respiratory rate falls below 8 breaths/min or rises above 28-30 breaths/min.", "Lab Values"),
    ("How should a child be prepared for their first nebulizer treatment?", "Use play therapy by letting them put a mask on a stuffed animal, and use fun names like space mask to reduce fear of the equipment.", "Procedure"),
    ("What is the Allowed Amount on an Explanation of Benefits (EOB)?", "It is the maximum dollar amount that the insurance company has agreed to pay for a specific medical service.", "General"),
    ("What is the interaction between Vitamin K and Warfarin?", "Warfarin is a blood thinner that works against Vitamin K; sudden changes in Vitamin K intake (like eating much more spinach) can make the drug less effective.", "Medication"),
    ("What is the normal range for magnesium in the blood?", "The normal range for serum magnesium is typically 1.7 to 2.2 mg/dL.", "Lab Values"),
    ("What is the preparation for a Nuclear Medicine bone scan?", "No fasting is required, but the patient should drink 4 to 5 glasses of water after the injection of the tracer to help with imaging.", "Procedure"),
    ("How should a patient manage metal taste in their mouth during chemotherapy?", "Sucking on sugar-free lemon drops or using plastic utensils instead of metal ones can help reduce the unpleasant metallic taste.", "Medication"),
    ("What is the normal range for Total Protein in the blood?", "The normal range is 6.0 to 8.3 g/dL.", "Lab Values"),
    ("What is the preparation for an Abdominal CT with contrast?", "Patients should fast for 4-6 hours and may need to drink a barium or iodine-based oral contrast to help highlight the digestive tract.", "Procedure"),
    ("What is a Health Care Agent?", "A health care agent is the person you choose in your Health Care Proxy to speak for you and make medical decisions if you cannot.", "General"),
    ("What should a patient do if they miss a weekly dose of dulaglutide and it has been 5 days?", "If it has been more than 3 days since the missed dose, the patient should skip the dose entirely and wait for their next regularly scheduled day.", "Medication"),
    ("What is the NEWS threshold for a Red high-risk alert?", "A total National Early Warning Score (NEWS) of 7 or more is considered a high-level clinical risk and usually triggers an immediate RRT or ICU review.", "Lab Values"),
    ("What is the preparation for a Small Bowel Follow-Through X-ray?", "The patient must be NPO (nothing by mouth) after midnight and will be asked to drink a barium suspension at the start of the test.", "Procedure"),
    ("What is the purpose of a Coordination of Benefits (COB)?", "COB is the process used by insurance companies to determine which plan is primary and which is secondary when a patient has more than one insurance.", "General"),
    ("How does Chemotherapy cause hair loss?", "Chemotherapy targets all rapidly dividing cells, which includes both cancer cells and the healthy cells in hair follicles.", "Medication"),
    ("What is the normal range for Lactate in the blood?", "A normal blood lactate level is typically less than 2.0 mmol/L; levels above 4.0 mmol/L can indicate severe illness or sepsis.", "Lab Values"),
    ("What is the preparation for a Thyroid Uptake and Scan?", "Patients must stop thyroid medications and avoid iodine-rich foods (like fish) and iodine-containing contrast for several weeks before the test.", "Procedure"),
    ("What is the missed dose policy for daily Liraglutide (Saxenda)?", "If you miss a dose, take the next dose as planned the next day. Do not take an extra dose or increase the dose the following day.", "Medication"),
    ("What is the normal range for Anion Gap?", "A normal anion gap is typically between 3 and 10 mEq/L, used to help evaluate acid-base disorders.", "Lab Values"),
    ("What is the preparation for an IVP (Intravenous Pyelogram)?", "Patients may be asked to take a laxative the night before and fast for several hours to ensure clear images of the kidneys and bladder.", "Procedure"),
    ("What is the interaction between Grapefruit Juice and Calcium Channel Blockers?", "Grapefruit juice can increase the blood levels of certain blood pressure meds, potentially causing a dangerous drop in blood pressure and heart rate.", "Medication"),
    ("What is the normal range for Platelets in a CBC?", "A normal platelet count is typically between 150,000 and 450,000 per microliter of blood.", "Lab Values"),
    ("What is the preparation for a Mammogram?", "On the day of the exam, do not use deodorants, powders, or lotions on the breasts or underarm area, as these can interfere with the image.", "Procedure"),
    ("What is a Health Care Proxy?", "It is a document that allows you to appoint someone you trust to make healthcare decisions for you if you lose the ability to make them yourself.", "General"),
    ("What is the routine dosing schedule for the Hepatitis B vaccine in infants?", "The HepB vaccine is typically given in a 3-dose series: at birth, at 1-2 months, and at 6-18 months of age.", "Medication"),
    ("What is the NEWS score for an oxygen saturation of 91%?", "On the National Early Warning Score (NEWS) scale, an SpO2 of 91% or less is assigned a score of 3.", "Lab Values"),
    ("What is the preparation for a Hepatobiliary (HIDA) scan?", "Patients must fast (NPO) for at least 4 hours before the test but should not have fasted for more than 24 hours.", "Procedure"),
    ("What is Observation status in the hospital?", "Observation status is used when a patient needs monitoring to determine if they should be admitted as an inpatient or can be safely discharged.", "General"),
    ("How should a patient manage Fatigue during cancer treatment?", "Establish a routine, prioritize essential activities for when energy is highest, and engage in light exercise like short walks to help combat exhaustion.", "Medication"),
    ("What is the normal range for White Blood Cell (WBC) count?", "A normal WBC count is typically between 4,500 and 11,000 cells per microliter of blood.", "Lab Values"),
    ("What is the preparation for a Cystogram?", "Generally, no special preparation is needed, though the patient will have a catheter inserted to fill the bladder with contrast during the test.", "Procedure"),
    ("What is a Copay?", "A copay is a fixed dollar amount that a patient pays for a specific medical service, such as $30 for a specialist visit.", "General"),
    ("What is the interaction between St. Johns Wort and many medications?", "St. John's Wort can speed up the breakdown of many drugs, including birth control and blood thinners, making them less effective.", "Medication"),
    ("What is the normal range for Hemoglobin in adult males?", "The normal range for hemoglobin in males is typically 13.5 to 17.5 grams per deciliter (g/dL).", "Lab Values"),
    ("What is the preparation for a Renal Scan?", "Patients should be well-hydrated, often asked to drink 16 ounces of water about 30 minutes before the scan begins.", "Procedure"),
    ("What is Inpatient status?", "Inpatient status is when a patient is formally admitted to the hospital with a doctor's order, usually for a stay expected to last two or more midnights.", "General"),
    ("What is the missed dose instruction for daily Liraglutide?", "If a dose is missed, wait and take the next dose at the usual time the following day. Never take two doses to make up for a missed one.", "Medication"),
    ("What is the normal range for Hematocrit in adult females?", "The normal range for hematocrit in females is typically 37% to 47%.", "Lab Values"),
    ("What is the preparation for a Vascular Ultrasound?", "Usually, no special preparation is required, though for certain abdominal vascular scans, fasting for 6-8 hours may be requested.", "Procedure"),
    ("What is a Deductible in health insurance?", "A deductible is the specific amount of money a patient must pay out-of-pocket for healthcare services before their insurance begins to pay.", "General"),
    ("How does Amiodarone interact with grapefruit juice?", "Grapefruit juice can significantly increase the absorption of amiodarone, potentially leading to toxic levels and dangerous heart rhythms.", "Medication"),
    ("What is the normal range for PH in arterial blood?", "A normal arterial blood pH is typically between 7.35 and 7.45.", "Lab Values"),
    ("What is the preparation for a Myelogram?", "Patients may be asked to increase fluid intake the day before and fast for several hours prior. They should also discuss stopping certain meds like blood thinners.", "Procedure"),
    ("What is Co-insurance?", "Co-insurance is the percentage of costs (e.g., 20%) that a patient pays for a covered service after they have met their deductible.", "General"),
    ("What is the interaction between Warfarin and Cranberry Juice?", "Cranberry juice may increase the effects of warfarin, leading to a higher risk of bleeding; patients should use caution and have their INR checked regularly.", "Medication"),
    ("What is the normal range for Partial Thromboplastin Time (PTT)?", "A normal PTT is typically 25 to 35 seconds, used to evaluate how well the blood is clotting.", "Lab Values"),
    ("What is the preparation for a Bone Densitometry (DEXA) scan?", "Patients should not take calcium supplements for 24 hours before the test and should wear clothes without metal zippers or buttons.", "Procedure"),
    ("What is Assignment of Benefits in medical billing?", "It is a document the patient signs allowing the insurance company to pay the healthcare provider directly for services.", "General"),
    ("What should a patient do if they miss a weekly dose of Semaglutide by 6 days?", "If it has been more than 5 days since the missed dose, they should skip the dose and wait for their next regularly scheduled day.", "Medication"),
    ("What is the normal range for Specific Gravity in a urinalysis?", "The normal range for urine specific gravity is 1.005 to 1.030, reflecting the concentration of the urine.", "Lab Values"),
    ("What is the preparation for an MRI with contrast?", "Patients must complete a safety screening and may need a blood test to check kidney function before receiving the gadolinium contrast.", "Procedure"),
    ("How does Metformin interact with CT contrast dye?", "Metformin should be held for 48 hours after a contrast study to prevent a rare but serious condition called lactic acidosis, especially if kidney function is impaired.", "Medication"),
    ("What is the normal range for Serum Ferritin?", "For adult males, the normal range is typically 20 to 250 ng/mL; for females, it is 10 to 120 ng/mL.", "Lab Values"),
    ("What is the preparation for a Thyroid FNA Biopsy?", "No fasting is required. Patients should discuss blood thinners with their doctor but can usually continue all other medications.", "Procedure"),
    ("What is a Power of Attorney?", "A power of attorney is a legal document giving someone the authority to act on your behalf in legal or financial matters.", "General"),
    ("What is the interaction between Aspirin and Ibuprofen?", "Ibuprofen can block the heart-protecting effects of low-dose aspirin if taken together; it is best to take aspirin at least 30 minutes before or 8 hours after ibuprofen.", "Medication"),
    ("What is the normal range for Troponin I?", "A normal Troponin I level is typically below 0.04 ng/mL; elevated levels are a primary indicator of heart muscle damage.", "Lab Values"),
    ("What is the preparation for a Renal Ultrasound?", "Patients should drink 24 ounces of water 1 hour before the exam and not empty their bladder; fasting for 8 hours is often also required.", "Procedure"),
    ("What is the interaction between Digoxin and many antibiotics?", "Certain antibiotics can increase the levels of digoxin in the blood, potentially leading to digoxin toxicity and heart rhythm problems.", "Medication"),
    ("What is the normal range for Serum Phosphorus?", "The normal range for phosphorus is typically 2.5 to 4.5 mg/dL.", "Lab Values"),
    ("What is the preparation for a Cardiac PET scan?", "Patients must be NPO for 4-6 hours and must strictly avoid all caffeine for 24 hours prior to the test.", "Procedure"),
    ("What is Advance Care Planning?", "It is the process of making decisions about the healthcare you would want to receive if you were unable to speak for yourself.", "General"),
]

# First, remove duplicates and count existing
existing_questions = set()
for doc in faq_repository.find({}, {"question_text": 1}):
    existing_questions.add(doc["question_text"])

inserted = 0
skipped = 0
errors = 0

for i, (question, answer, category) in enumerate(FAQS):
    faq_id = f"faq_{100 + i:03d}"
    
    if question in existing_questions:
        skipped += 1
        continue
    
    try:
        faq_repository.insert_one({
            "faq_id": faq_id,
            "question_text": question,
            "static_answer": answer,
            "category": category,
            "template_id": f"qt_{category.lower().replace(' ', '_')}_auto"
        })
        inserted += 1
    except Exception as e:
        errors += 1
        print(f"  ERROR on faq_{100+i:03d}: {e}")

total = faq_repository.count_documents({})
print(f"\n{'='*50}")
print(f"  Inserted: {inserted}")
print(f"  Skipped (duplicates): {skipped}")
print(f"  Errors: {errors}")
print(f"  Total FAQs in database: {total}")
print(f"{'='*50}")
